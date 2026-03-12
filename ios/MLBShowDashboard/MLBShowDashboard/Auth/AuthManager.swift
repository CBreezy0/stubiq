import AuthenticationServices
import Foundation
import SwiftUI
import UIKit

enum AuthFormMode: String, Identifiable {
    case signIn
    case signUp
    case forgotPassword

    var id: String { rawValue }

    var title: String {
        switch self {
        case .signIn:
            return "Sign In"
        case .signUp:
            return "Create Account"
        case .forgotPassword:
            return "Reset Password"
        }
    }
}

enum AuthProviderError: LocalizedError {
    case configurationMissing(String)
    case missingPresenter
    case missingToken
    case unsupported(String)

    var errorDescription: String? {
        switch self {
        case .configurationMissing(let message), .unsupported(let message):
            return message
        case .missingPresenter:
            return "Could not find a screen to present the sign-in flow."
        case .missingToken:
            return "The authentication provider did not return a valid token."
        }
    }
}

protocol AuthProviding {
    var supportsGoogleSignIn: Bool { get }
    var providerName: String { get }
    func restoreSession() async throws -> AuthSession?
    func fetchGoogleIdentityToken() async throws -> String
    func sendPasswordReset(email: String) async throws
    func signOut() async throws
}

final class MockAuthProvider: AuthProviding {
    private var storedSession: AuthSession?

    init(seedSession: AuthSession? = nil) {
        self.storedSession = seedSession
    }

    var supportsGoogleSignIn: Bool { true }
    var providerName: String { "Backend" }

    func restoreSession() async throws -> AuthSession? {
        storedSession
    }

    func fetchGoogleIdentityToken() async throws -> String {
        throw AuthProviderError.configurationMissing("Google Sign-In requires the Google/Firebase iOS packages and app configuration.")
    }

    func sendPasswordReset(email: String) async throws {
        try await Task.sleep(for: .milliseconds(250))
    }

    func signOut() async throws {
        storedSession = nil
    }
}

enum AuthProviderFactory {
    static func makeDefault() -> AuthProviding {
        #if canImport(FirebaseAuth) && canImport(GoogleSignIn)
        if FirebaseAuthProvider.isAvailable {
            return FirebaseAuthProvider()
        }
        #endif
        return MockAuthProvider()
    }
}

@MainActor
final class AuthManager: ObservableObject {
    @Published private(set) var session: AuthSession?
    @Published private(set) var state: AuthManagerState = .idle

    let provider: AuthProviding
    private let sessionStore: SessionStoring
    private let backendClient: BackendAuthClienting

    init(
        provider: AuthProviding,
        environmentManager: EnvironmentManager,
        sessionStore: SessionStoring = KeychainSessionStore(),
        backendClient: BackendAuthClienting? = nil
    ) {
        self.provider = provider
        self.sessionStore = sessionStore
        self.backendClient = backendClient ?? BackendAuthClient(environmentManager: environmentManager)
    }

    var isAuthenticated: Bool {
        session != nil
    }

    var currentUserName: String {
        session?.displayName ?? session?.email ?? "Trader"
    }

    var currentUserEmail: String? {
        session?.email
    }

    var currentAuthProvider: AuthProviderKind? {
        session?.provider
    }

    var supportsGoogleSignIn: Bool {
        provider.supportsGoogleSignIn
    }

    var supportsAppleSignIn: Bool {
        true
    }

    var providerDisplayName: String {
        session?.provider.title ?? provider.providerName
    }

    func restoreSessionIfNeeded() async {
        guard case .idle = state else { return }
        state = .restoring

        if let stored = sessionStore.loadSession() {
            if let refreshToken = stored.refreshToken, !refreshToken.isEmpty {
                do {
                    let refreshed = try await backendClient.refresh(
                        refreshToken: refreshToken,
                        deviceName: deviceName,
                        platform: platformName
                    )
                    persist(session: refreshed)
                    return
                } catch {
                    sessionStore.clearSession()
                    session = nil
                }
            } else {
                session = stored
                state = .authenticated
                return
            }
        }

        do {
            if let restored = try await provider.restoreSession() {
                session = restored
                sessionStore.saveSession(restored)
                state = .authenticated
            } else {
                state = .signedOut
            }
        } catch {
            state = .failed(error.localizedDescription)
        }
    }

    func signIn(email: String, password: String) async throws {
        let signedIn = try await backendClient.login(
            email: email,
            password: password,
            deviceName: deviceName,
            platform: platformName
        )
        persist(session: signedIn)
    }

    func signUp(email: String, password: String, displayName: String?) async throws {
        let signedUp = try await backendClient.signUp(
            email: email,
            password: password,
            displayName: displayName,
            deviceName: deviceName,
            platform: platformName
        )
        persist(session: signedUp)
    }

    func signInWithGoogle() async throws {
        let googleIdentityToken = try await provider.fetchGoogleIdentityToken()
        let signedIn = try await backendClient.exchangeGoogleIDToken(
            googleIdentityToken,
            deviceName: deviceName,
            platform: platformName
        )
        persist(session: signedIn)
    }

    func signInWithApple(authorization: ASAuthorization) async throws {
        guard let credential = authorization.credential as? ASAuthorizationAppleIDCredential else {
            throw AuthProviderError.unsupported("The Apple authorization payload was invalid.")
        }
        guard let identityTokenData = credential.identityToken,
              let identityToken = String(data: identityTokenData, encoding: .utf8),
              let codeData = credential.authorizationCode,
              let authorizationCode = String(data: codeData, encoding: .utf8)
        else {
            throw AuthProviderError.missingToken
        }

        let signedIn = try await backendClient.exchangeApple(
            identityToken: identityToken,
            authorizationCode: authorizationCode,
            deviceName: deviceName,
            platform: platformName
        )
        persist(session: signedIn)
    }

    func sendPasswordReset(email: String) async throws {
        try await provider.sendPasswordReset(email: email)
    }

    func revokeSessions() async throws -> Int {
        guard let accessToken = session?.accessToken ?? session?.idToken else {
            throw AuthProviderError.missingToken
        }
        let revokedCount = try await backendClient.revokeSessions(accessToken: accessToken)
        if let currentSession = session {
            let updated = currentSession.clearingRefreshToken()
            session = updated
            sessionStore.saveSession(updated)
        }
        return revokedCount
    }

    func signOut() async {
        if let refreshToken = session?.refreshToken, !refreshToken.isEmpty {
            try? await backendClient.logout(refreshToken: refreshToken)
        }
        try? await provider.signOut()
        session = nil
        sessionStore.clearSession()
        state = .signedOut
    }

    func currentAccessToken() async -> String? {
        session?.accessToken ?? session?.idToken
    }

    private func persist(session: AuthSession) {
        self.session = session
        sessionStore.saveSession(session)
        state = .authenticated
    }

    private var deviceName: String {
        UIDevice.current.name
    }

    private var platformName: String {
        "ios"
    }
}
