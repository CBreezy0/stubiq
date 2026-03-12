import Foundation

enum ConnectionProviderKind: String, Codable, CaseIterable, Hashable, Identifiable {
    case xbox
    case playStation

    var id: String { rawValue }

    var title: String {
        switch self {
        case .xbox:
            return "Xbox"
        case .playStation:
            return "PlayStation"
        }
    }

    var systemImage: String {
        switch self {
        case .xbox:
            return "gamecontroller.fill"
        case .playStation:
            return "circle.grid.2x2.fill"
        }
    }
}

enum ConnectionStatus: String, Codable, CaseIterable, Hashable {
    case connected = "Connected"
    case notConnected = "Not Connected"
    case needsReconnect = "Needs Reconnect"
}

enum ConnectionMode: String, Codable, CaseIterable, Hashable {
    case mock
    case official
}

struct ConsoleConnection: Codable, Hashable, Identifiable {
    let provider: ConnectionProviderKind
    let status: ConnectionStatus
    let connectedAccountName: String?
    let lastConnectedAt: Date?
    let mode: ConnectionMode
    let notes: String?

    var id: String { provider.rawValue }
}
