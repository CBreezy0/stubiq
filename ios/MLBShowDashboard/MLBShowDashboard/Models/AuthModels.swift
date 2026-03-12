import Foundation

enum AuthProviderKind: String, Codable, CaseIterable, Hashable, Identifiable {
    case email
    case google
    case apple
    case firebase
    case mock

    var id: String { rawValue }

    var title: String {
        switch self {
        case .email:
            return "Email"
        case .google:
            return "Google"
        case .apple:
            return "Apple"
        case .firebase:
            return "Firebase"
        case .mock:
            return "Mock"
        }
    }
}

struct AuthSession: Codable, Hashable, Identifiable {
    let userID: String
    let displayName: String?
    let email: String
    let provider: AuthProviderKind
    let avatarURL: String?
    let accessToken: String?
    let refreshToken: String?
    let accessTokenExpiresIn: Int?
    let refreshTokenExpiresIn: Int?
    let idToken: String?
    let createdAt: Date
    let lastSignInAt: Date

    var id: String { userID }

    func clearingRefreshToken() -> AuthSession {
        AuthSession(
            userID: userID,
            displayName: displayName,
            email: email,
            provider: provider,
            avatarURL: avatarURL,
            accessToken: accessToken,
            refreshToken: nil,
            accessTokenExpiresIn: accessTokenExpiresIn,
            refreshTokenExpiresIn: nil,
            idToken: idToken,
            createdAt: createdAt,
            lastSignInAt: lastSignInAt
        )
    }
}

enum AuthManagerState: Equatable {
    case idle
    case restoring
    case authenticated
    case signedOut
    case failed(String)
}
