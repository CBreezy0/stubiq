import Foundation

protocol BackendAuthClienting {
    func signUp(email: String, password: String, displayName: String?, deviceName: String?, platform: String?) async throws -> AuthSession
    func login(email: String, password: String, deviceName: String?, platform: String?) async throws -> AuthSession
    func exchangeGoogleIDToken(_ idToken: String, deviceName: String?, platform: String?) async throws -> AuthSession
    func exchangeApple(identityToken: String, authorizationCode: String, deviceName: String?, platform: String?) async throws -> AuthSession
    func refresh(refreshToken: String, deviceName: String?, platform: String?) async throws -> AuthSession
    func logout(refreshToken: String) async throws
    func revokeSessions(accessToken: String) async throws -> Int
}

private enum AuthHTTPMethod: String {
    case get = "GET"
    case post = "POST"
}

private struct AuthErrorPayload: Decodable {
    let detail: String?
}

private struct AnyAuthEncodable: Encodable {
    private let encodeHandler: (Encoder) throws -> Void

    init<T: Encodable>(_ value: T) {
        self.encodeHandler = value.encode
    }

    func encode(to encoder: Encoder) throws {
        try encodeHandler(encoder)
    }
}

private struct SignupPayload: Encodable {
    let email: String
    let password: String
    let displayName: String?
    let deviceName: String?
    let platform: String?
}

private struct LoginPayload: Encodable {
    let email: String
    let password: String
    let deviceName: String?
    let platform: String?
}

private struct GooglePayload: Encodable {
    let idToken: String
    let deviceName: String?
    let platform: String?
}

private struct ApplePayload: Encodable {
    let identityToken: String
    let authorizationCode: String
    let deviceName: String?
    let platform: String?
}

private struct RefreshPayload: Encodable {
    let refreshToken: String
    let deviceName: String?
    let platform: String?
}

private struct LogoutPayload: Encodable {
    let refreshToken: String
}

private struct EmptyBody: Encodable {}
private struct EmptyResponse: Decodable {}

private struct BackendAuthUserPayload: Decodable {
    let id: String
    let email: String
    let displayName: String?
    let avatarURL: String?
    let authProvider: String
    let createdAt: Date
    let lastLoginAt: Date?
}

private struct BackendAuthResponsePayload: Decodable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
    let accessTokenExpiresIn: Int
    let refreshTokenExpiresIn: Int
    let user: BackendAuthUserPayload
}

private struct SessionRevocationPayload: Decodable {
    let success: Bool
    let revokedCount: Int
}

final class BackendAuthClient: BackendAuthClienting {
    private let environmentManager: EnvironmentManager
    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(environmentManager: EnvironmentManager, session: URLSession = .shared) {
        self.environmentManager = environmentManager
        self.session = session

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let value = try container.decode(String.self)
            let formatterWithFractional = ISO8601DateFormatter()
            formatterWithFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatterWithFractional.date(from: value) ?? formatter.date(from: value) {
                return date
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Invalid ISO8601 date: \(value)")
        }
        self.decoder = decoder

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
        self.encoder = encoder
    }

    func signUp(email: String, password: String, displayName: String?, deviceName: String?, platform: String?) async throws -> AuthSession {
        let payload = SignupPayload(email: email, password: password, displayName: displayName, deviceName: deviceName, platform: platform)
        let response: BackendAuthResponsePayload = try await request(path: "auth/signup", method: .post, body: payload)
        return response.toSession()
    }

    func login(email: String, password: String, deviceName: String?, platform: String?) async throws -> AuthSession {
        let payload = LoginPayload(email: email, password: password, deviceName: deviceName, platform: platform)
        let response: BackendAuthResponsePayload = try await request(path: "auth/login", method: .post, body: payload)
        return response.toSession()
    }

    func exchangeGoogleIDToken(_ idToken: String, deviceName: String?, platform: String?) async throws -> AuthSession {
        let payload = GooglePayload(idToken: idToken, deviceName: deviceName, platform: platform)
        let response: BackendAuthResponsePayload = try await request(path: "auth/google", method: .post, body: payload)
        return response.toSession(idToken: idToken)
    }

    func exchangeApple(identityToken: String, authorizationCode: String, deviceName: String?, platform: String?) async throws -> AuthSession {
        let payload = ApplePayload(identityToken: identityToken, authorizationCode: authorizationCode, deviceName: deviceName, platform: platform)
        let response: BackendAuthResponsePayload = try await request(path: "auth/apple", method: .post, body: payload)
        return response.toSession(idToken: identityToken)
    }

    func refresh(refreshToken: String, deviceName: String?, platform: String?) async throws -> AuthSession {
        let payload = RefreshPayload(refreshToken: refreshToken, deviceName: deviceName, platform: platform)
        let response: BackendAuthResponsePayload = try await request(path: "auth/refresh", method: .post, body: payload)
        return response.toSession()
    }

    func logout(refreshToken: String) async throws {
        let payload = LogoutPayload(refreshToken: refreshToken)
        let _: EmptyResponse = try await request(path: "auth/logout", method: .post, body: payload)
    }

    func revokeSessions(accessToken: String) async throws -> Int {
        let response: SessionRevocationPayload = try await request(path: "auth/revoke-sessions", method: .post, body: EmptyBody(), bearerToken: accessToken)
        return response.revokedCount
    }

    private func request<T: Decodable>(
        path: String,
        method: AuthHTTPMethod,
        body: Encodable? = nil,
        bearerToken: String? = nil
    ) async throws -> T {
        let baseURL = await MainActor.run { environmentManager.currentBaseURL }
        var url = baseURL
        for component in path.split(separator: "/") {
            url.appendPathComponent(String(component))
        }

        var urlRequest = URLRequest(url: url)
        urlRequest.httpMethod = method.rawValue
        urlRequest.timeoutInterval = 25
        urlRequest.setValue("application/json", forHTTPHeaderField: "Accept")

        if let bearerToken, !bearerToken.isEmpty {
            urlRequest.setValue("Bearer \(bearerToken)", forHTTPHeaderField: "Authorization")
        }

        if let body {
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            urlRequest.httpBody = try encoder.encode(AnyAuthEncodable(body))
        }

        do {
            let (data, response) = try await session.data(for: urlRequest)
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIClientError.invalidResponse
            }

            guard (200..<300).contains(httpResponse.statusCode) else {
                let payload = try? decoder.decode(AuthErrorPayload.self, from: data)
                let message = payload?.detail ?? HTTPURLResponse.localizedString(forStatusCode: httpResponse.statusCode)
                throw APIClientError.server(message)
            }

            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIClientError.decoding(error.localizedDescription)
            }
        } catch let error as APIClientError {
            throw error
        } catch {
            throw APIClientError.network(error.localizedDescription)
        }
    }
}

private extension BackendAuthResponsePayload {
    func toSession(idToken: String? = nil) -> AuthSession {
        AuthSession(
            userID: user.id,
            displayName: user.displayName,
            email: user.email,
            provider: AuthProviderKind(rawValue: user.authProvider) ?? .email,
            avatarURL: user.avatarURL,
            accessToken: accessToken,
            refreshToken: refreshToken,
            accessTokenExpiresIn: accessTokenExpiresIn,
            refreshTokenExpiresIn: refreshTokenExpiresIn,
            idToken: idToken,
            createdAt: user.createdAt,
            lastSignInAt: user.lastLoginAt ?? user.createdAt
        )
    }
}
