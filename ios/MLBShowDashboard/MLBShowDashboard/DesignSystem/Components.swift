import SwiftUI

struct GlassCard<Content: View>: View {
    @EnvironmentObject private var themeManager: ThemeManager
    private let padding: CGFloat
    private let content: Content

    init(padding: CGFloat = 18, @ViewBuilder content: () -> Content) {
        self.padding = padding
        self.content = content()
    }

    var body: some View {
        let palette = themeManager.palette

        content
            .padding(padding)
            .background(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .fill(.ultraThinMaterial)
                    .overlay(
                        RoundedRectangle(cornerRadius: 26, style: .continuous)
                            .fill(palette.surface)
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .stroke(palette.outline, lineWidth: 1)
            )
            .shadow(color: palette.shadow, radius: 24, x: 0, y: 12)
    }
}

struct GlowButtonStyle: ButtonStyle {
    @EnvironmentObject private var themeManager: ThemeManager
    var filled: Bool = true

    func makeBody(configuration: Configuration) -> some View {
        let palette = themeManager.palette
        configuration.label
            .font(.headline.weight(.semibold))
            .foregroundStyle(filled ? Color.black.opacity(0.86) : palette.textPrimary)
            .padding(.vertical, 14)
            .padding(.horizontal, 18)
            .frame(maxWidth: .infinity)
            .background(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .fill(
                        filled ? AnyShapeStyle(
                            LinearGradient(
                                colors: [palette.accent, palette.accentSecondary],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        ) : AnyShapeStyle(palette.surfaceSecondary)
                    )
            )
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(filled ? Color.white.opacity(0.18) : palette.outline, lineWidth: 1)
            )
            .shadow(color: filled ? palette.accent.opacity(0.32) : .clear, radius: 18, x: 0, y: 10)
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(.spring(response: 0.25, dampingFraction: 0.78), value: configuration.isPressed)
    }
}

enum BadgeTone {
    case accent
    case success
    case warning
    case danger
    case neutral
}

struct StatusBadgeView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let text: String
    let tone: BadgeTone

    private var color: Color {
        let palette = themeManager.palette
        switch tone {
        case .accent:
            return palette.accent
        case .success:
            return palette.success
        case .warning:
            return palette.warning
        case .danger:
            return palette.danger
        case .neutral:
            return palette.textSecondary
        }
    }

    var body: some View {
        Text(text)
            .font(.caption.weight(.semibold))
            .foregroundStyle(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(color.opacity(0.14), in: Capsule())
            .overlay(Capsule().stroke(color.opacity(0.28), lineWidth: 1))
    }
}

struct SectionHeaderView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let title: String
    let subtitle: String?
    var actionTitle: String?
    var action: (() -> Void)?

    var body: some View {
        HStack(alignment: .bottom) {
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.title3.weight(.semibold))
                    .foregroundStyle(themeManager.palette.textPrimary)
                if let subtitle {
                    Text(subtitle)
                        .font(.subheadline)
                        .foregroundStyle(themeManager.palette.textSecondary)
                }
            }
            Spacer()
            if let actionTitle, let action {
                Button(actionTitle, action: action)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(themeManager.palette.accent)
            }
        }
    }
}

struct MetricCardView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let title: String
    let value: String
    let subtitle: String
    let systemImage: String
    var trend: String? = nil
    var highlight: Bool = false

    var body: some View {
        let palette = themeManager.palette

        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    Image(systemName: systemImage)
                        .font(.headline)
                        .foregroundStyle(highlight ? palette.accent : palette.textSecondary)
                    Spacer()
                    if let trend {
                        TrendChipView(text: trend, positive: !trend.contains("−"))
                    }
                }

                Text(value)
                    .font(.system(size: 28, weight: .bold, design: .rounded))
                    .foregroundStyle(palette.textPrimary)
                    .minimumScaleFactor(0.75)

                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.headline)
                        .foregroundStyle(palette.textPrimary)
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(palette.textSecondary)
                        .lineLimit(2)
                }
            }
        }
        .overlay(
            RoundedRectangle(cornerRadius: 26, style: .continuous)
                .stroke(highlight ? palette.accent.opacity(0.22) : .clear, lineWidth: 1)
        )
        .shadow(color: highlight ? palette.accent.opacity(0.18) : .clear, radius: 28, x: 0, y: 14)
    }
}

struct TrendChipView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let text: String
    let positive: Bool

    var body: some View {
        let color = positive ? themeManager.palette.success : themeManager.palette.danger
        Text(text)
            .font(.caption.weight(.semibold))
            .foregroundStyle(color)
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(color.opacity(0.12), in: Capsule())
    }
}

struct ConfidenceBarView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let value: Double

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            GeometryReader { proxy in
                ZStack(alignment: .leading) {
                    Capsule()
                        .fill(themeManager.palette.surfaceSecondary)
                    Capsule()
                        .fill(
                            LinearGradient(
                                colors: [themeManager.palette.accent, themeManager.palette.accentSecondary],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .frame(width: proxy.size.width * max(0, min(value, 1)))
                }
            }
            .frame(height: 8)

            Text("Confidence \(AppFormatter.percentage(value))")
                .font(.caption)
                .foregroundStyle(themeManager.palette.textSecondary)
        }
    }
}

struct EmptyStateView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let symbol: String
    let title: String
    let message: String

    var body: some View {
        GlassCard {
            VStack(spacing: 14) {
                Image(systemName: symbol)
                    .font(.system(size: 30, weight: .semibold))
                    .foregroundStyle(themeManager.palette.accent)
                Text(title)
                    .font(.headline)
                    .foregroundStyle(themeManager.palette.textPrimary)
                Text(message)
                    .font(.subheadline)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(themeManager.palette.textSecondary)
            }
            .frame(maxWidth: .infinity)
        }
    }
}

struct LoadingStateView: View {
    var rows: Int = 4

    var body: some View {
        VStack(spacing: 14) {
            ForEach(0..<rows, id: \.self) { _ in
                GlassCard {
                    VStack(alignment: .leading, spacing: 14) {
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.white.opacity(0.08))
                            .frame(width: 120, height: 14)
                            .shimmering()
                        RoundedRectangle(cornerRadius: 12)
                            .fill(Color.white.opacity(0.08))
                            .frame(height: 52)
                            .shimmering()
                        RoundedRectangle(cornerRadius: 8)
                            .fill(Color.white.opacity(0.08))
                            .frame(height: 10)
                            .shimmering()
                    }
                }
            }
        }
    }
}

struct ChartCard<Content: View>: View {
    let title: String
    let subtitle: String
    let content: Content

    init(title: String, subtitle: String, @ViewBuilder content: () -> Content) {
        self.title = title
        self.subtitle = subtitle
        self.content = content()
    }

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                SectionHeaderView(title: title, subtitle: subtitle)
                content
            }
        }
    }
}

private struct ShimmerModifier: ViewModifier {
    @State private var phase: CGFloat = -1

    func body(content: Content) -> some View {
        content
            .overlay {
                GeometryReader { proxy in
                    LinearGradient(
                        colors: [
                            .clear,
                            .white.opacity(0.15),
                            .clear
                        ],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                    .rotationEffect(.degrees(15))
                    .offset(x: phase * proxy.size.width * 1.8)
                }
                .mask(content)
            }
            .onAppear {
                withAnimation(.linear(duration: 1.25).repeatForever(autoreverses: false)) {
                    phase = 1
                }
            }
    }
}

extension View {
    func shimmering() -> some View {
        modifier(ShimmerModifier())
    }
}
