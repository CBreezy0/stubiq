import SwiftUI

struct ThemePalette {
    let backgroundTop: Color
    let backgroundBottom: Color
    let surface: Color
    let surfaceSecondary: Color
    let outline: Color
    let textPrimary: Color
    let textSecondary: Color
    let accent: Color
    let accentSecondary: Color
    let success: Color
    let warning: Color
    let danger: Color
    let shadow: Color
}

enum AppTheme: String, CaseIterable, Identifiable {
    case cyan
    case violet
    case lime

    var id: String { rawValue }

    var title: String {
        rawValue.capitalized
    }

    var palette: ThemePalette {
        switch self {
        case .cyan:
            return ThemePalette(
                backgroundTop: Color(red: 0.02, green: 0.03, blue: 0.08),
                backgroundBottom: Color(red: 0.01, green: 0.01, blue: 0.03),
                surface: Color.white.opacity(0.06),
                surfaceSecondary: Color.white.opacity(0.03),
                outline: Color.white.opacity(0.10),
                textPrimary: Color(red: 0.95, green: 0.97, blue: 1.0),
                textSecondary: Color(red: 0.65, green: 0.72, blue: 0.83),
                accent: Color(red: 0.19, green: 0.81, blue: 0.98),
                accentSecondary: Color(red: 0.46, green: 0.92, blue: 0.93),
                success: Color(red: 0.29, green: 0.88, blue: 0.58),
                warning: Color(red: 0.96, green: 0.76, blue: 0.29),
                danger: Color(red: 0.99, green: 0.37, blue: 0.48),
                shadow: Color.black.opacity(0.55)
            )
        case .violet:
            return ThemePalette(
                backgroundTop: Color(red: 0.04, green: 0.02, blue: 0.09),
                backgroundBottom: Color(red: 0.01, green: 0.01, blue: 0.03),
                surface: Color.white.opacity(0.06),
                surfaceSecondary: Color.white.opacity(0.03),
                outline: Color.white.opacity(0.10),
                textPrimary: Color(red: 0.95, green: 0.97, blue: 1.0),
                textSecondary: Color(red: 0.70, green: 0.68, blue: 0.86),
                accent: Color(red: 0.61, green: 0.35, blue: 0.98),
                accentSecondary: Color(red: 0.88, green: 0.45, blue: 0.98),
                success: Color(red: 0.29, green: 0.88, blue: 0.58),
                warning: Color(red: 0.96, green: 0.76, blue: 0.29),
                danger: Color(red: 0.99, green: 0.37, blue: 0.48),
                shadow: Color.black.opacity(0.55)
            )
        case .lime:
            return ThemePalette(
                backgroundTop: Color(red: 0.03, green: 0.05, blue: 0.06),
                backgroundBottom: Color(red: 0.01, green: 0.02, blue: 0.03),
                surface: Color.white.opacity(0.06),
                surfaceSecondary: Color.white.opacity(0.03),
                outline: Color.white.opacity(0.10),
                textPrimary: Color(red: 0.95, green: 0.97, blue: 1.0),
                textSecondary: Color(red: 0.68, green: 0.78, blue: 0.73),
                accent: Color(red: 0.62, green: 0.93, blue: 0.35),
                accentSecondary: Color(red: 0.85, green: 0.98, blue: 0.35),
                success: Color(red: 0.29, green: 0.88, blue: 0.58),
                warning: Color(red: 0.96, green: 0.76, blue: 0.29),
                danger: Color(red: 0.99, green: 0.37, blue: 0.48),
                shadow: Color.black.opacity(0.55)
            )
        }
    }
}

@MainActor
final class ThemeManager: ObservableObject {
    private enum Keys {
        static let selectedTheme = "mobile.theme.selected"
    }

    @Published var selectedTheme: AppTheme {
        didSet { userDefaults.set(selectedTheme.rawValue, forKey: Keys.selectedTheme) }
    }

    private let userDefaults: UserDefaults

    init(initialTheme: AppTheme? = nil, userDefaults: UserDefaults = .standard) {
        self.userDefaults = userDefaults
        if let initialTheme {
            self.selectedTheme = initialTheme
        } else {
            self.selectedTheme = AppTheme(rawValue: userDefaults.string(forKey: Keys.selectedTheme) ?? "") ?? .cyan
        }
    }

    var palette: ThemePalette {
        selectedTheme.palette
    }
}

struct AppBackgroundView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    @State private var animate = false

    var body: some View {
        let palette = themeManager.palette

        ZStack {
            LinearGradient(
                colors: [palette.backgroundTop, palette.backgroundBottom],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            Circle()
                .fill(palette.accent.opacity(0.22))
                .frame(width: 320, height: 320)
                .blur(radius: 80)
                .offset(x: animate ? 110 : -120, y: -260)

            Circle()
                .fill(palette.accentSecondary.opacity(0.18))
                .frame(width: 260, height: 260)
                .blur(radius: 90)
                .offset(x: animate ? -90 : 120, y: 240)

            RoundedRectangle(cornerRadius: 120, style: .continuous)
                .fill(palette.surface)
                .frame(width: 380, height: 220)
                .rotationEffect(.degrees(animate ? 18 : -12))
                .blur(radius: 120)
                .offset(x: -130, y: 120)
        }
        .ignoresSafeArea()
        .onAppear {
            withAnimation(.easeInOut(duration: 9).repeatForever(autoreverses: true)) {
                animate = true
            }
        }
    }
}
