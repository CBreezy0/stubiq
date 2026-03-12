#if canImport(FirebaseAuth) && canImport(GoogleSignIn)
import Foundation
import FirebaseAuth
import GoogleSignIn

final class FirebaseAuthProvider: AuthProviding {
    static var isAvailable: Bool {
        Bundle.main.path(forResource: "GoogleService-Info", ofType: "plist") != nil
    }

    var supportsGoogleSignIn: Bool { Self.isAvailable }
    var providerName: String { "Backend" }

    func restoreSession() async throws -> AuthSession? {
        nil
    }

    func fetchGoogleIdentityToken() async throws -> String {
        guard Self.isAvailable else {
            throw AuthProviderError.configurationMissing("Add GoogleService-Info.plist and the reversed client ID URL scheme to enable Google Sign-In.")
        }
        guard let presenter = await MainActor.run(body: { UIApplication.topViewController() }) else {
            throw AuthProviderError.missingPresenter
        }

        let signInResult: GIDSignInResult = try await withCheckedThrowingContinuation { continuation in
            GIDSignIn.sharedInstance.signIn(withPresenting: presenter) { result, error in
                if let result {
                    continuation.resume(returning: result)
                } else {
                    continuation.resume(throwing: error ?? AuthProviderError.unsupported("Google Sign-In did not complete."))
                }
            }
        }

        guard let idToken = signInResult.user.idToken?.tokenString else {
            throw AuthProviderError.missingToken
        }
        return idToken
    }

    func sendPasswordReset(email: String) async throws {
        try await Task.sleep(for: .milliseconds(250))
    }

    func signOut() async throws {
        GIDSignIn.sharedInstance.signOut()
        try? Auth.auth().signOut()
    }
}
#endif
