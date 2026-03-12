import Foundation

@MainActor
final class ConnectionsViewModel: ObservableObject {
    @Published var busyProvider: ConnectionProviderKind?
    @Published var alert: AlertMessage?

    private let manager: ConnectionManager

    init(manager: ConnectionManager) {
        self.manager = manager
    }

    func connect(_ provider: ConnectionProviderKind) async {
        busyProvider = provider
        defer { busyProvider = nil }
        do {
            try await manager.connect(provider)
        } catch {
            alert = AlertMessage(title: "Connection Failed", message: error.localizedDescription)
        }
    }

    func disconnect(_ provider: ConnectionProviderKind) async {
        busyProvider = provider
        defer { busyProvider = nil }
        do {
            try await manager.disconnect(provider)
        } catch {
            alert = AlertMessage(title: "Disconnect Failed", message: error.localizedDescription)
        }
    }
}
