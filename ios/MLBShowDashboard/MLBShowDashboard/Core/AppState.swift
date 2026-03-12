import Foundation
import SwiftUI

enum AppTab: Hashable {
    case dashboard
    case flips
    case targets
    case portfolio
    case settings
}

@MainActor
final class AppState: ObservableObject {
    private enum Keys {
        static let completedOnboarding = "mobile.onboarding.completed"
    }

    let apiClient: APIClienting

    @Published var selectedTab: AppTab = .dashboard
    @Published var hasCompletedOnboarding: Bool {
        didSet { userDefaults.set(hasCompletedOnboarding, forKey: Keys.completedOnboarding) }
    }

    private let userDefaults: UserDefaults

    init(apiClient: APIClienting, userDefaults: UserDefaults = .standard) {
        self.apiClient = apiClient
        self.userDefaults = userDefaults
        self.hasCompletedOnboarding = userDefaults.bool(forKey: Keys.completedOnboarding)
    }

    func completeOnboarding() {
        hasCompletedOnboarding = true
    }
}
