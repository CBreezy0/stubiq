import SwiftUI

struct PreviewHost<Content: View>: View {
    @StateObject private var themeManager: ThemeManager
    @StateObject private var environmentManager: EnvironmentManager
    @StateObject private var authManager: AuthManager
    @StateObject private var connectionManager: ConnectionManager
    @StateObject private var appState: AppState

    private let content: Content

    init(authenticated: Bool = true, apiClient: APIClienting = MockAPIClient(), @ViewBuilder content: () -> Content) {
        let defaults = UserDefaults.previewDefaults
        let themeManager = ThemeManager(initialTheme: .cyan, userDefaults: defaults)
        let environmentManager = EnvironmentManager(userDefaults: defaults)
        let seedSession = authenticated ? PreviewFixtures.authSession : nil
        let authManager = AuthManager(provider: MockAuthProvider(seedSession: seedSession), environmentManager: environmentManager, sessionStore: InMemorySessionStore(seedSession: seedSession))
        let connectionManager = ConnectionManager(providers: [XboxConnectionProvider(), PlayStationConnectionProvider()], storage: defaults)
        let appState = AppState(apiClient: apiClient, userDefaults: defaults)

        _themeManager = StateObject(wrappedValue: themeManager)
        _environmentManager = StateObject(wrappedValue: environmentManager)
        _authManager = StateObject(wrappedValue: authManager)
        _connectionManager = StateObject(wrappedValue: connectionManager)
        _appState = StateObject(wrappedValue: appState)
        self.content = content()
    }

    var body: some View {
        content
            .environmentObject(themeManager)
            .environmentObject(environmentManager)
            .environmentObject(authManager)
            .environmentObject(connectionManager)
            .environmentObject(appState)
            .preferredColorScheme(.dark)
            .task {
                await authManager.restoreSessionIfNeeded()
            }
    }
}
