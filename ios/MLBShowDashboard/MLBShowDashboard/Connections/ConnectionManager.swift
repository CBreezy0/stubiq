import Foundation

enum ConnectionError: LocalizedError {
    case missingProvider
    case cancelled
    case unavailable(String)

    var errorDescription: String? {
        switch self {
        case .missingProvider:
            return "The selected connection provider is unavailable."
        case .cancelled:
            return "The connection flow was cancelled."
        case .unavailable(let message):
            return message
        }
    }
}

protocol ConnectionProviding {
    var provider: ConnectionProviderKind { get }
    var defaultConnection: ConsoleConnection { get }
    func connect(current: ConsoleConnection?) async throws -> ConsoleConnection
    func disconnect(current: ConsoleConnection?) async throws -> ConsoleConnection
}

@MainActor
final class ConnectionManager: ObservableObject {
    private enum Keys {
        static let savedConnections = "mobile.connections.saved"
    }

    @Published private(set) var connections: [ConnectionProviderKind: ConsoleConnection] = [:]

    private let providers: [ConnectionProviderKind: ConnectionProviding]
    private let storage: UserDefaults

    init(providers: [ConnectionProviding], storage: UserDefaults = .standard) {
        self.providers = Dictionary(uniqueKeysWithValues: providers.map { ($0.provider, $0) })
        self.storage = storage
        loadSavedConnections()
        ensureDefaults()
    }

    func connection(for provider: ConnectionProviderKind) -> ConsoleConnection {
        connections[provider] ?? providers[provider]?.defaultConnection ?? ConsoleConnection(provider: provider, status: .notConnected, connectedAccountName: nil, lastConnectedAt: nil, mode: .mock, notes: nil)
    }

    func connect(_ provider: ConnectionProviderKind) async throws {
        guard let service = providers[provider] else { throw ConnectionError.missingProvider }
        let updated = try await service.connect(current: connection(for: provider))
        connections[provider] = updated
        persist()
    }

    func disconnect(_ provider: ConnectionProviderKind) async throws {
        guard let service = providers[provider] else { throw ConnectionError.missingProvider }
        let updated = try await service.disconnect(current: connection(for: provider))
        connections[provider] = updated
        persist()
    }

    private func loadSavedConnections() {
        guard let data = storage.data(forKey: Keys.savedConnections), let decoded = try? JSONDecoder().decode([ConsoleConnection].self, from: data) else {
            return
        }
        decoded.forEach { connections[$0.provider] = $0 }
    }

    private func ensureDefaults() {
        providers.values.forEach { provider in
            if connections[provider.provider] == nil {
                connections[provider.provider] = provider.defaultConnection
            }
        }
    }

    private func persist() {
        let values = Array(connections.values)
        if let data = try? JSONEncoder().encode(values) {
            storage.set(data, forKey: Keys.savedConnections)
        }
    }
}
