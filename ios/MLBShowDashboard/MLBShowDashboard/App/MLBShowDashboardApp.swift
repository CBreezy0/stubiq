import SwiftUI

@main
struct MLBShowDashboardApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    @StateObject private var themeManager: ThemeManager
    @StateObject private var environmentManager: EnvironmentManager
    @StateObject private var authManager: AuthManager
    @StateObject private var connectionManager: ConnectionManager
    @StateObject private var appState: AppState

    init() {
        let themeManager = ThemeManager()
        let environmentManager = EnvironmentManager()
        let authManager = AuthManager(provider: AuthProviderFactory.makeDefault(), environmentManager: environmentManager)
        let connectionManager = ConnectionManager(
            providers: [
                XboxConnectionProvider(authURL: environmentManager.authURL(for: .xbox), callbackScheme: environmentManager.connectionCallbackScheme),
                PlayStationConnectionProvider(authURL: environmentManager.authURL(for: .playStation), callbackScheme: environmentManager.connectionCallbackScheme)
            ]
        )
        let apiClient = APIClient(environmentManager: environmentManager) {
            await authManager.currentAccessToken()
        }
        let appState = AppState(apiClient: apiClient)

        _themeManager = StateObject(wrappedValue: themeManager)
        _environmentManager = StateObject(wrappedValue: environmentManager)
        _authManager = StateObject(wrappedValue: authManager)
        _connectionManager = StateObject(wrappedValue: connectionManager)
        _appState = StateObject(wrappedValue: appState)
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(themeManager)
                .environmentObject(environmentManager)
                .environmentObject(authManager)
                .environmentObject(connectionManager)
                .environmentObject(appState)
                .preferredColorScheme(.dark)
        }
    }
}
