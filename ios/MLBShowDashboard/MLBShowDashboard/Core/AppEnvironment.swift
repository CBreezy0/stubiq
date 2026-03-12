import Foundation
import SwiftUI

enum BackendEnvironment: String, CaseIterable, Identifiable {
    case local
    case production
    case custom

    var id: String { rawValue }

    var title: String {
        switch self {
        case .local:
            return "Local"
        case .production:
            return "Production"
        case .custom:
            return "Custom"
        }
    }

    var defaultBaseURLString: String {
        switch self {
        case .local:
            return "http://127.0.0.1:8000"
        case .production:
            return "https://api.example.com"
        case .custom:
            return ""
        }
    }
}

@MainActor
final class EnvironmentManager: ObservableObject {
    private enum Keys {
        static let selectedEnvironment = "mobile.environment.selected"
        static let customBaseURL = "mobile.environment.customBaseURL"
    }

    @Published var selectedEnvironment: BackendEnvironment {
        didSet { userDefaults.set(selectedEnvironment.rawValue, forKey: Keys.selectedEnvironment) }
    }

    @Published var customBaseURLString: String {
        didSet { userDefaults.set(customBaseURLString, forKey: Keys.customBaseURL) }
    }

    private let userDefaults: UserDefaults

    init(userDefaults: UserDefaults = .standard) {
        self.userDefaults = userDefaults
        self.selectedEnvironment = BackendEnvironment(rawValue: userDefaults.string(forKey: Keys.selectedEnvironment) ?? "") ?? .local
        self.customBaseURLString = userDefaults.string(forKey: Keys.customBaseURL) ?? ""
    }

    var currentBaseURL: URL {
        let candidate = selectedEnvironment == .custom ? customBaseURLString : selectedEnvironment.defaultBaseURLString
        return URL(string: candidate) ?? URL(string: BackendEnvironment.local.defaultBaseURLString)!
    }

    var connectionCallbackScheme: String? {
        nil
    }

    func authURL(for provider: ConnectionProviderKind) -> URL? {
        switch provider {
        case .xbox, .playStation:
            return nil
        }
    }
}
