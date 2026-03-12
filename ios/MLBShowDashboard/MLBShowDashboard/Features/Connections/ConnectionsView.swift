import SwiftUI

struct ConnectionsView: View {
    @EnvironmentObject private var connectionManager: ConnectionManager
    @StateObject private var viewModel: ConnectionsViewModel

    init(connectionManager: ConnectionManager) {
        _viewModel = StateObject(wrappedValue: ConnectionsViewModel(manager: connectionManager))
    }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 16) {
                GlassCard {
                    VStack(alignment: .leading, spacing: 10) {
                        SectionHeaderView(title: "Account Connections", subtitle: "Console linking is abstracted so the rest of the app stays useful even before official APIs are ready.")
                        Text("Official Xbox and PlayStation linking can later replace the current placeholder providers without changing the UI or state model.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }

                ForEach(ConnectionProviderKind.allCases) { provider in
                    let connection = connectionManager.connection(for: provider)
                    ConnectionProviderCard(
                        connection: connection,
                        isBusy: viewModel.busyProvider == provider,
                        onConnect: {
                            Task { await viewModel.connect(provider) }
                        },
                        onDisconnect: {
                            Task { await viewModel.disconnect(provider) }
                        }
                    )
                }
            }
            .padding(20)
        }
        .navigationTitle("Connections")
        .alert(item: $viewModel.alert) { alert in
            Alert(title: Text(alert.title), message: Text(alert.message), dismissButton: .default(Text("OK")))
        }
    }
}

#Preview {
    PreviewHost {
        NavigationStack {
            ConnectionsView(connectionManager: ConnectionManager(providers: [XboxConnectionProvider(), PlayStationConnectionProvider()]))
                .environmentObject(ConnectionManager(providers: [XboxConnectionProvider(), PlayStationConnectionProvider()]))
        }
    }
}
