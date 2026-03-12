import Foundation
import UIKit

struct PricePoint: Identifiable, Hashable {
    let label: String
    let value: Double

    var id: String { label }
}

struct PortfolioTrendPoint: Identifiable, Hashable {
    let label: String
    let value: Double

    var id: String { label }
}

enum AppFormatter {
    static func stubs(_ value: Int?) -> String {
        guard let value else { return "—" }
        return "\(value.formatted(.number.grouping(.automatic))) stubs"
    }

    static func signedStubs(_ value: Double?) -> String {
        guard let value else { return "—" }
        let sign = value >= 0 ? "+" : "−"
        return "\(sign)\(Int(abs(value)).formatted(.number.grouping(.automatic)))"
    }

    static func percentage(_ value: Double?, fractionDigits: Int = 0) -> String {
        guard let value else { return "—" }
        return value.formatted(.percent.precision(.fractionLength(fractionDigits)))
    }

    static func score(_ value: Double?) -> String {
        guard let value else { return "—" }
        return String(format: "%.0f", value * 100)
    }

    static func decimal(_ value: Double?, fractionDigits: Int = 2) -> String {
        guard let value else { return "—" }
        return value.formatted(.number.precision(.fractionLength(fractionDigits)))
    }

    static func shortDate(_ date: Date?) -> String {
        guard let date else { return "—" }
        return date.formatted(date: .abbreviated, time: .shortened)
    }
}

extension String {
    var trimmed: String {
        trimmingCharacters(in: .whitespacesAndNewlines)
    }
}

extension UIApplication {
    static func topViewController(base: UIViewController? = UIApplication.shared.connectedScenes
        .compactMap { $0 as? UIWindowScene }
        .flatMap(\.windows)
        .first(where: \.isKeyWindow)?.rootViewController) -> UIViewController? {
        if let navigationController = base as? UINavigationController {
            return topViewController(base: navigationController.visibleViewController)
        }
        if let tabBarController = base as? UITabBarController, let selected = tabBarController.selectedViewController {
            return topViewController(base: selected)
        }
        if let presented = base?.presentedViewController {
            return topViewController(base: presented)
        }
        return base
    }
}

extension Array where Element == PortfolioPosition {
    var trendPoints: [PortfolioTrendPoint] {
        let sorted = sorted { $0.updatedAt < $1.updatedAt }
        var runningTotal = 0.0
        return sorted.map { position in
            runningTotal += Double(position.currentMarketValue ?? 0) * Double(position.quantity)
            return PortfolioTrendPoint(label: position.updatedAt.formatted(date: .abbreviated, time: .omitted), value: runningTotal)
        }
    }
}

extension CardDetail {
    var priceTrendPoints: [PricePoint] {
        [
            PricePoint(label: "24H", value: avgPrice24h ?? 0),
            PricePoint(label: "6H", value: avgPrice6h ?? 0),
            PricePoint(label: "1H", value: avgPrice1h ?? 0),
            PricePoint(label: "15M", value: avgPrice15m ?? 0)
        ].filter { $0.value > 0 }
    }
}

extension UserDefaults {
    static let previewDefaults = UserDefaults(suiteName: "MLBShowDashboard.PreviewDefaults") ?? .standard
}
