import SwiftUI

struct RootView: View {
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var appState: AppState

    var body: some View {
        ZStack {
            AppBackgroundView()

            switch authManager.state {
            case .idle, .restoring:
                ProgressView("Loading session…")
                    .progressViewStyle(.circular)
            case .authenticated:
                MainTabView()
            case .signedOut, .failed:
                if appState.hasCompletedOnboarding {
                    AuthEntryView(showPager: false)
                } else {
                    AuthEntryView(showPager: true)
                }
            }
        }
        .task {
            await authManager.restoreSessionIfNeeded()
        }
    }
}
