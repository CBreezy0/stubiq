import Charts
import SwiftUI

struct OpportunityRowView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let item: MarketOpportunity

    var body: some View {
        let palette = themeManager.palette
        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(item.card.name)
                            .font(.headline)
                            .foregroundStyle(palette.textPrimary)
                        Text([item.card.series, item.card.team].compactMap { $0 }.joined(separator: " • "))
                            .font(.caption)
                            .foregroundStyle(palette.textSecondary)
                    }
                    Spacer()
                    StatusBadgeView(text: item.action.title, tone: item.action.isPositiveOpportunity ? .success : .neutral)
                }

                HStack(spacing: 12) {
                    metric(title: "Buy", value: AppFormatter.stubs(item.card.latestBuyNow))
                    metric(title: "Sell", value: AppFormatter.stubs(item.card.latestSellNow))
                    metric(title: "Profit", value: AppFormatter.stubs(item.expectedProfitPerFlip))
                }

                ConfidenceBarView(value: item.confidence)

                HStack {
                    TrendChipView(text: "Liq \(AppFormatter.score(item.liquidityScore))", positive: true)
                    TrendChipView(text: "Risk \(AppFormatter.score(1 - item.riskScore))", positive: item.riskScore < 0.45)
                    Spacer()
                }

                Text(item.rationale)
                    .font(.caption)
                    .foregroundStyle(palette.textSecondary)
                    .lineLimit(2)
            }
        }
        .overlay(
            RoundedRectangle(cornerRadius: 26, style: .continuous)
                .stroke(item.action.isPositiveOpportunity ? palette.accent.opacity(0.22) : .clear, lineWidth: 1)
        )
        .shadow(color: item.action.isPositiveOpportunity ? palette.accent.opacity(0.14) : .clear, radius: 18, x: 0, y: 12)
    }

    private func metric(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(themeManager.palette.textSecondary)
            Text(value)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(themeManager.palette.textPrimary)
                .minimumScaleFactor(0.7)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct RosterTargetRowView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let item: RosterUpdateRecommendation

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(item.playerName)
                            .font(.headline)
                            .foregroundStyle(themeManager.palette.textPrimary)
                        Text("OVR \(item.currentOvr) • \(item.card.displayPosition ?? "Player")")
                            .font(.caption)
                            .foregroundStyle(themeManager.palette.textSecondary)
                    }
                    Spacer()
                    StatusBadgeView(text: item.action.title, tone: .success)
                }

                HStack(spacing: 12) {
                    stat(title: "Upgrade", value: AppFormatter.percentage(item.upgradeProbability))
                    stat(title: "EV", value: AppFormatter.signedStubs(item.expectedProfit))
                    stat(title: "Downside", value: AppFormatter.stubs(Int(item.downsideRisk)))
                }

                ConfidenceBarView(value: item.confidence)

                Text(item.rationale)
                    .font(.caption)
                    .foregroundStyle(themeManager.palette.textSecondary)
                    .lineLimit(2)
            }
        }
    }

    private func stat(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(themeManager.palette.textSecondary)
            Text(value)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(themeManager.palette.textPrimary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct PortfolioHoldingRowView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let position: PortfolioPosition
    let recommendation: PortfolioRecommendation?

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(position.card.name)
                            .font(.headline)
                            .foregroundStyle(themeManager.palette.textPrimary)
                        Text("Qty \(position.quantity) • Avg \(AppFormatter.stubs(position.avgAcquisitionCost))")
                            .font(.caption)
                            .foregroundStyle(themeManager.palette.textSecondary)
                    }
                    Spacer()
                    if let recommendation {
                        StatusBadgeView(text: recommendation.action.title, tone: recommendation.action == .sell ? .danger : .accent)
                    }
                }

                HStack(spacing: 12) {
                    stat(title: "Value", value: AppFormatter.stubs(position.currentMarketValue))
                    stat(title: "P/L", value: AppFormatter.signedStubs(Double(position.unrealizedProfit ?? 0)))
                    stat(title: "Locked", value: position.lockedForCollection ? "Yes" : "No")
                }

                if let recommendation {
                    ConfidenceBarView(value: recommendation.confidence)
                    Text(recommendation.rationale)
                        .font(.caption)
                        .foregroundStyle(themeManager.palette.textSecondary)
                        .lineLimit(2)
                }
            }
        }
    }

    private func stat(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(themeManager.palette.textSecondary)
            Text(value)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(themeManager.palette.textPrimary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct CollectionPriorityRowView: View {
    @EnvironmentObject private var themeManager: ThemeManager
    let item: CollectionTarget

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(item.name)
                            .font(.headline)
                            .foregroundStyle(themeManager.palette.textPrimary)
                        Text(item.level)
                            .font(.caption)
                            .foregroundStyle(themeManager.palette.textSecondary)
                    }
                    Spacer()
                    StatusBadgeView(text: "\(Int(item.priorityScore * 100))", tone: .accent)
                }

                HStack(spacing: 12) {
                    stat(title: "Cost", value: AppFormatter.stubs(item.remainingCost))
                    stat(title: "Complete", value: AppFormatter.percentage(item.completionPct))
                    stat(title: "Reward", value: AppFormatter.stubs(item.rewardValueProxy))
                }

                Text(item.rationale)
                    .font(.caption)
                    .foregroundStyle(themeManager.palette.textSecondary)
            }
        }
    }

    private func stat(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(themeManager.palette.textSecondary)
            Text(value)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(themeManager.palette.textPrimary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct ConnectionProviderCard: View {
    let connection: ConsoleConnection
    let isBusy: Bool
    let onConnect: () -> Void
    let onDisconnect: () -> Void

    var body: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                HStack {
                    Label(connection.provider.title, systemImage: connection.provider.systemImage)
                        .font(.headline)
                    Spacer()
                    StatusBadgeView(text: connection.status.rawValue, tone: tone)
                }

                VStack(alignment: .leading, spacing: 6) {
                    Text(connection.connectedAccountName ?? "No account linked")
                        .font(.subheadline.weight(.semibold))
                    Text(connection.notes ?? "")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    if let lastConnectedAt = connection.lastConnectedAt {
                        Text("Updated \(AppFormatter.shortDate(lastConnectedAt))")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }

                HStack(spacing: 12) {
                    Button(connection.status == .connected ? "Reconnect" : "Connect", action: onConnect)
                        .buttonStyle(GlowButtonStyle(filled: true))
                        .disabled(isBusy)
                    if connection.status == .connected {
                        Button("Disconnect", action: onDisconnect)
                            .buttonStyle(GlowButtonStyle(filled: false))
                            .disabled(isBusy)
                    }
                }
            }
        }
    }

    private var tone: BadgeTone {
        switch connection.status {
        case .connected:
            return .success
        case .notConnected:
            return .neutral
        case .needsReconnect:
            return .warning
        }
    }
}

struct ValueBarChartView: View {
    let points: [PortfolioTrendPoint]

    var body: some View {
        Chart(points) { point in
            LineMark(
                x: .value("Time", point.label),
                y: .value("Value", point.value)
            )
            .interpolationMethod(.catmullRom)

            AreaMark(
                x: .value("Time", point.label),
                y: .value("Value", point.value)
            )
            .interpolationMethod(.catmullRom)
            .foregroundStyle(.linearGradient(colors: [.cyan.opacity(0.35), .clear], startPoint: .top, endPoint: .bottom))
        }
        .chartYAxis(.hidden)
        .chartXAxis {
            AxisMarks(values: .automatic(desiredCount: min(points.count, 4))) {
                AxisValueLabel()
                    .foregroundStyle(.secondary)
            }
        }
        .frame(height: 180)
    }
}
