import Charts
import SwiftUI

struct DashboardScreen: View {
    @StateObject private var viewModel: DashboardViewModel
    @EnvironmentObject private var appState: AppState
    @EnvironmentObject private var connectionManager: ConnectionManager

    init(apiClient: APIClienting) {
        _viewModel = StateObject(wrappedValue: DashboardViewModel(apiClient: apiClient))
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                LazyVStack(spacing: 18) {
                    if viewModel.isLoading, viewModel.summary == nil {
                        LoadingStateView(rows: 4)
                    } else if let summary = viewModel.summary {
                        hero(summary)
                        metrics(summary)

                        if !summary.launchWeekAlerts.isEmpty {
                            alerts(summary.launchWeekAlerts)
                        }

                        quickActions
                        flipSection(summary)
                        floorsSection(summary)
                        rosterSection(summary)
                        portfolioSection(summary)
                        collectionSection(summary)
                        grindSection(summary)
                    } else {
                        EmptyStateView(
                            symbol: "wifi.exclamationmark",
                            title: "No dashboard data",
                            message: viewModel.errorMessage ?? "Pull to refresh after the backend is running."
                        )
                    }
                }
                .padding(20)
            }
            .background(Color.clear)
            .refreshable {
                await viewModel.load(forceRefresh: true)
            }
            .navigationTitle("Dashboard")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    if let lastUpdated = viewModel.lastUpdated {
                        Text(lastUpdated, style: .time)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .task {
            await viewModel.load()
            viewModel.startAutoRefresh()
        }
        .onDisappear {
            viewModel.stopAutoRefresh()
        }
    }

    private func hero(_ summary: DashboardSummary) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 16) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(summary.marketPhase.phase.title)
                            .font(.system(size: 28, weight: .bold, design: .rounded))
                        Text(summary.marketPhase.rationale)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    StatusBadgeView(text: "\(Int(summary.marketPhase.confidence * 100))%", tone: .accent)
                }
                ConfidenceBarView(value: summary.marketPhase.confidence)
                HStack(spacing: 12) {
                    TrendChipView(text: "Flips \(summary.topFlips.count)", positive: true)
                    TrendChipView(text: "Floors \(summary.topFloorBuys.count)", positive: true)
                    TrendChipView(text: "Targets \(summary.topRosterUpdateTargets.count)", positive: true)
                }
            }
        }
    }

    private func metrics(_ summary: DashboardSummary) -> some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
            MetricCardView(
                title: "Portfolio Value",
                value: AppFormatter.stubs(summary.portfolio.reduce(0) { $0 + (($1.currentMarketValue ?? 0) * $1.quantity) }),
                subtitle: "Live position valuation",
                systemImage: "dollarsign.circle.fill",
                trend: AppFormatter.signedStubs(Double(summary.portfolio.reduce(0) { $0 + ($1.unrealizedProfit ?? 0) })),
                highlight: true
            )

            MetricCardView(
                title: "Best Flip",
                value: AppFormatter.stubs(summary.topFlips.first?.expectedProfitPerFlip),
                subtitle: summary.topFlips.first?.card.name ?? "No flip data",
                systemImage: "arrow.triangle.2.circlepath",
                trend: AppFormatter.percentage(summary.topFlips.first?.confidence)
            )

            MetricCardView(
                title: "Best Floor",
                value: AppFormatter.percentage(summary.topFloorBuys.first?.floorProximityScore),
                subtitle: summary.topFloorBuys.first?.card.name ?? "No floor data",
                systemImage: "arrow.down.circle",
                trend: AppFormatter.percentage(summary.topFloorBuys.first?.confidence)
            )

            MetricCardView(
                title: "Play Edge",
                value: AppFormatter.stubs(Int(summary.grindRecommendation.expectedMarketStubsPerHour)),
                subtitle: summary.grindRecommendation.bestModeToPlayNow,
                systemImage: "gamecontroller.fill",
                trend: summary.grindRecommendation.action.title
            )
        }
    }

    private func alerts(_ alerts: [String]) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Launch Alerts", subtitle: "Current market context")
                ForEach(alerts, id: \.self) { alert in
                    HStack(alignment: .top, spacing: 10) {
                        Image(systemName: "bolt.fill")
                            .foregroundStyle(.yellow)
                        Text(alert)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    private var quickActions: some View {
        HStack(spacing: 12) {
            NavigationLink(destination: CollectionsView(apiClient: appState.apiClient)) {
                Label("Collections", systemImage: "square.grid.2x2")
            }
            .buttonStyle(GlowButtonStyle(filled: false))

            NavigationLink(destination: ConnectionsView(connectionManager: connectionManager).environmentObject(connectionManager)) {
                Label("Connections", systemImage: "link.circle")
            }
            .buttonStyle(GlowButtonStyle(filled: false))
        }
    }

    private func flipSection(_ summary: DashboardSummary) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionHeaderView(title: "Top Flips", subtitle: "Highest current edge")
            ForEach(summary.topFlips.prefix(3)) { item in
                NavigationLink {
                    CardDetailView(itemId: item.itemId, apiClient: appState.apiClient, marketOpportunity: item, marketPhase: summary.marketPhase.phase)
                } label: {
                    OpportunityRowView(item: item)
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func floorsSection(_ summary: DashboardSummary) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionHeaderView(title: "Floor Buys", subtitle: "Near support with upside")
            ForEach(summary.topFloorBuys.prefix(3)) { item in
                NavigationLink {
                    CardDetailView(itemId: item.itemId, apiClient: appState.apiClient, marketOpportunity: item, marketPhase: summary.marketPhase.phase)
                } label: {
                    OpportunityRowView(item: item)
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func rosterSection(_ summary: DashboardSummary) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionHeaderView(title: "Roster Targets", subtitle: "Upgrade windows to monitor")
            ForEach(summary.topRosterUpdateTargets.prefix(3)) { item in
                NavigationLink {
                    CardDetailView(itemId: item.itemId, apiClient: appState.apiClient, rosterTarget: item, marketPhase: summary.marketPhase.phase)
                } label: {
                    RosterTargetRowView(item: item)
                }
                .buttonStyle(.plain)
            }
        }
    }

    private func portfolioSection(_ summary: DashboardSummary) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionHeaderView(title: "Portfolio", subtitle: "Live trend from tracked positions")
            ChartCard(title: "Portfolio Trend", subtitle: "Derived from the latest holdings snapshot") {
                if summary.portfolio.trendPoints.isEmpty {
                    EmptyStateView(symbol: "chart.line.downtrend.xyaxis", title: "No portfolio history", message: "Add holdings to populate your portfolio view.")
                } else {
                    ValueBarChartView(points: summary.portfolio.trendPoints)
                }
            }
        }
    }

    private func collectionSection(_ summary: DashboardSummary) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            SectionHeaderView(title: "Collections", subtitle: "Best progression route right now")
            if let target = summary.collectionPriorities.rankedDivisionTargets.first ?? summary.collectionPriorities.rankedTeamTargets.first {
                NavigationLink(destination: CollectionsView(apiClient: appState.apiClient)) {
                    CollectionPriorityRowView(item: target)
                }
                .buttonStyle(.plain)
            } else {
                EmptyStateView(symbol: "square.grid.2x2", title: "No priorities yet", message: "Collection recommendations will appear after the backend strategy engine runs.")
            }
        }
    }

    private func grindSection(_ summary: DashboardSummary) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Quick Action", subtitle: "Play vs market recommendation")
                HStack {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(summary.grindRecommendation.bestModeToPlayNow)
                            .font(.headline)
                        Text(summary.grindRecommendation.rationale)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    StatusBadgeView(text: summary.grindRecommendation.action.title, tone: .success)
                }
            }
        }
    }
}

#Preview {
    PreviewHost {
        DashboardScreen(apiClient: MockAPIClient())
    }
}
