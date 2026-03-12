import AuthenticationServices
import Foundation
import UIKit

class PlaceholderConnectionProvider: NSObject, ConnectionProviding, ASWebAuthenticationPresentationContextProviding {
    let provider: ConnectionProviderKind
    private let displayName: String
    private let authURL: URL?
    private let callbackScheme: String?
    private var authSession: ASWebAuthenticationSession?

    init(provider: ConnectionProviderKind, displayName: String, authURL: URL? = nil, callbackScheme: String? = nil) {
        self.provider = provider
        self.displayName = displayName
        self.authURL = authURL
        self.callbackScheme = callbackScheme
    }

    var defaultConnection: ConsoleConnection {
        ConsoleConnection(
            provider: provider,
            status: .notConnected,
            connectedAccountName: nil,
            lastConnectedAt: nil,
            mode: authURL == nil ? .mock : .official,
            notes: authURL == nil ? "Mock placeholder mode. Real console linking can be wired in later without blocking the app." : "Official web auth is configured."
        )
    }

    func connect(current: ConsoleConnection?) async throws -> ConsoleConnection {
        if let authURL, let callbackScheme {
            _ = try await authenticate(url: authURL, callbackScheme: callbackScheme)
            return ConsoleConnection(
                provider: provider,
                status: .connected,
                connectedAccountName: "\(displayName) Account",
                lastConnectedAt: Date(),
                mode: .official,
                notes: "Connected using the provider's web authentication flow."
            )
        }

        try await Task.sleep(for: .milliseconds(850))
        return ConsoleConnection(
            provider: provider,
            status: .connected,
            connectedAccountName: provider == .xbox ? "Xbox Live Profile" : "PlayStation Network ID",
            lastConnectedAt: Date(),
            mode: .mock,
            notes: "Mock mode active until an approved platform integration is available."
        )
    }

    func disconnect(current: ConsoleConnection?) async throws -> ConsoleConnection {
        ConsoleConnection(
            provider: provider,
            status: .notConnected,
            connectedAccountName: nil,
            lastConnectedAt: nil,
            mode: current?.mode ?? defaultConnection.mode,
            notes: defaultConnection.notes
        )
    }

    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor {
        UIApplication.shared.connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .first(where: { !$0.windows.isEmpty })?
            .windows.first(where: \.isKeyWindow) ?? ASPresentationAnchor()
    }

    private func authenticate(url: URL, callbackScheme: String) async throws -> URL {
        try await withCheckedThrowingContinuation { continuation in
            let session = ASWebAuthenticationSession(url: url, callbackURLScheme: callbackScheme) { callbackURL, error in
                if let callbackURL {
                    continuation.resume(returning: callbackURL)
                } else if let error {
                    if (error as NSError).code == ASWebAuthenticationSessionError.canceledLogin.rawValue {
                        continuation.resume(throwing: ConnectionError.cancelled)
                    } else {
                        continuation.resume(throwing: ConnectionError.unavailable(error.localizedDescription))
                    }
                } else {
                    continuation.resume(throwing: ConnectionError.unavailable("The authentication session ended unexpectedly."))
                }
            }
            session.presentationContextProvider = self
            session.prefersEphemeralWebBrowserSession = true
            self.authSession = session
            if !session.start() {
                continuation.resume(throwing: ConnectionError.unavailable("Unable to start the provider's web authentication session."))
            }
        }
    }
}

final class XboxConnectionProvider: PlaceholderConnectionProvider {
    init(authURL: URL? = nil, callbackScheme: String? = nil) {
        super.init(provider: .xbox, displayName: "Xbox", authURL: authURL, callbackScheme: callbackScheme)
    }
}

final class PlayStationConnectionProvider: PlaceholderConnectionProvider {
    init(authURL: URL? = nil, callbackScheme: String? = nil) {
        super.init(provider: .playStation, displayName: "PlayStation", authURL: authURL, callbackScheme: callbackScheme)
    }
}
