import Charts
import SwiftUI

struct CardDetailView: View {
    @StateObject private var viewModel: CardDetailViewModel

    init(
        itemId: String,
        apiClient: APIClienting,
        marketOpportunity: MarketOpportunity? = nil,
        rosterTarget: RosterUpdateRecommendation? = nil,
        portfolioRecommendation: PortfolioRecommendation? = nil,
        marketPhase: MarketPhase? = nil
    ) {
        _viewModel = StateObject(wrappedValue: CardDetailViewModel(itemId: itemId, apiClient: apiClient, marketOpportunity: marketOpportunity, rosterTarget: rosterTarget, portfolioRecommendation: portfolioRecommendation, marketPhase: marketPhase))
    }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 18) {
                if viewModel.isLoading, viewModel.detail == nil {
                    LoadingStateView(rows: 3)
                } else if let detail = viewModel.detail {
                    header(detail)
                    scoreStrip(detail)
                    priceChart(detail)
                    recommendationSection(detail)
                    contextSection(detail)
                } else {
                    EmptyStateView(symbol: "creditcard.trianglebadge.exclamationmark", title: "Card detail unavailable", message: viewModel.errorMessage ?? "Try refreshing once the backend detail endpoint is available.")
                }
            }
            .padding(20)
        }
        .navigationTitle(viewModel.detail?.name ?? "Card Detail")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await viewModel.load()
        }
        .refreshable {
            await viewModel.load()
        }
    }

    private func header(_ detail: CardDetail) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 14) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(detail.name)
                            .font(.title2.weight(.bold))
                        Text([detail.series, detail.team, detail.displayPosition].compactMap { $0 }.joined(separator: " • "))
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    if let phase = viewModel.marketPhase?.title ?? detail.aggregatePhase {
                        StatusBadgeView(text: phase, tone: .accent)
                    }
                }

                HStack(spacing: 12) {
                    stat(title: "Buy Now", value: AppFormatter.stubs(detail.latestBuyNow))
                    stat(title: "Sell Now", value: AppFormatter.stubs(detail.latestSellNow))
                    stat(title: "Spread", value: AppFormatter.stubs(detail.latestTaxAdjustedSpread))
                }
            }
        }
    }

    private func scoreStrip(_ detail: CardDetail) -> some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
            MetricCardView(
                title: "Liquidity",
                value: AppFormatter.score(detail.liquidityScore),
                subtitle: "Order book depth",
                systemImage: "drop.fill",
                trend: AppFormatter.percentage(viewModel.flipConfidence),
                highlight: true
            )
            MetricCardView(
                title: "Volatility",
                value: AppFormatter.score(detail.volatilityScore),
                subtitle: "Recent variance",
                systemImage: "waveform.path.ecg"
            )
            MetricCardView(
                title: "Floor Score",
                value: AppFormatter.score(viewModel.floorBuyScore),
                subtitle: "Support proximity",
                systemImage: "arrow.down.circle"
            )
            MetricCardView(
                title: "Roster Edge",
                value: AppFormatter.percentage(viewModel.rosterUpgradeProbability),
                subtitle: "Upgrade probability",
                systemImage: "person.badge.key"
            )
        }
    }

    private func priceChart(_ detail: CardDetail) -> some View {
        ChartCard(title: "Price Trend", subtitle: "Short-term averages from the backend card detail endpoint") {
            if detail.priceTrendPoints.isEmpty {
                EmptyStateView(symbol: "chart.xyaxis.line", title: "No chart data", message: "Add richer card history later to unlock deeper market trend analysis.")
            } else {
                Chart(detail.priceTrendPoints) { point in
                    LineMark(
                        x: .value("Window", point.label),
                        y: .value("Price", point.value)
                    )
                    .interpolationMethod(.catmullRom)
                    .foregroundStyle(.cyan)

                    AreaMark(
                        x: .value("Window", point.label),
                        y: .value("Price", point.value)
                    )
                    .interpolationMethod(.catmullRom)
                    .foregroundStyle(.linearGradient(colors: [.cyan.opacity(0.32), .clear], startPoint: .top, endPoint: .bottom))
                }
                .chartYAxis {
                    AxisMarks(position: .leading)
                }
                .frame(height: 220)
            }
        }
    }

    private func recommendationSection(_ detail: CardDetail) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Recommendations", subtitle: "Why the engine likes this card")
                if detail.recommendations.isEmpty {
                    Text("No recommendation detail is available yet for this card.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(detail.recommendations) { recommendation in
                        VStack(alignment: .leading, spacing: 8) {
                            HStack {
                                Text(recommendation.recommendationType.title)
                                    .font(.headline)
                                Spacer()
                                StatusBadgeView(text: recommendation.action.title, tone: recommendation.action.isPositiveOpportunity ? .success : .neutral)
                            }
                            ConfidenceBarView(value: recommendation.confidence)
                            Text(recommendation.rationale)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                        if recommendation.id != detail.recommendations.last?.id {
                            Divider().overlay(Color.white.opacity(0.08))
                        }
                    }
                }
            }
        }
    }

    private func contextSection(_ detail: CardDetail) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Context", subtitle: "Current market lens")
                Text(detail.aggregatePhase ?? viewModel.marketPhase?.rawValue ?? "No aggregate phase returned")
                    .font(.headline)
                Text("Observed \(AppFormatter.shortDate(detail.observedAt))")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                if let action = viewModel.portfolioAction {
                    StatusBadgeView(text: "Portfolio: \(action.title)", tone: action == .sell ? .danger : .accent)
                }
            }
        }
    }

    private func stat(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.subheadline.weight(.semibold))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

#Preview {
    PreviewHost {
        NavigationStack {
            CardDetailView(itemId: PreviewFixtures.cardDetail.itemId, apiClient: MockAPIClient(), marketOpportunity: PreviewFixtures.flips.first, rosterTarget: PreviewFixtures.rosterTargets.first)
        }
    }
}
