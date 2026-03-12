import SwiftUI

struct MainTabView: View {
    @EnvironmentObject private var appState: AppState
    @EnvironmentObject private var themeManager: ThemeManager

    var body: some View {
        TabView(selection: $appState.selectedTab) {
            DashboardScreen(apiClient: appState.apiClient)
                .tabItem {
                    Label("Dashboard", systemImage: "chart.xyaxis.line")
                }
                .tag(AppTab.dashboard)

            MarketScreen(apiClient: appState.apiClient)
                .tabItem {
                    Label("Flips", systemImage: "arrow.left.arrow.right.circle")
                }
                .tag(AppTab.flips)

            TargetsScreen(apiClient: appState.apiClient)
                .tabItem {
                    Label("Targets", systemImage: "scope")
                }
                .tag(AppTab.targets)

            PortfolioScreen(apiClient: appState.apiClient)
                .tabItem {
                    Label("Portfolio", systemImage: "briefcase.fill")
                }
                .tag(AppTab.portfolio)

            SettingsScreen(apiClient: appState.apiClient)
                .tabItem {
                    Label("Settings", systemImage: "slider.horizontal.3")
                }
                .tag(AppTab.settings)
        }
        .tint(themeManager.palette.accent)
    }
}
