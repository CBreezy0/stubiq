import SwiftUI

struct CollectionsView: View {
    @StateObject private var viewModel: CollectionsViewModel

    init(apiClient: APIClienting) {
        _viewModel = StateObject(wrappedValue: CollectionsViewModel(apiClient: apiClient))
    }

    var body: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 16) {
                if let priorities = viewModel.priorities {
                    overview(priorities)

                    VStack(alignment: .leading, spacing: 12) {
                        SectionHeaderView(title: "Division Priorities", subtitle: "Highest leverage division routes")
                        ForEach(priorities.rankedDivisionTargets) { item in
                            CollectionPriorityRowView(item: item)
                        }
                    }

                    VStack(alignment: .leading, spacing: 12) {
                        SectionHeaderView(title: "Team Priorities", subtitle: "Best team-level finishes")
                        ForEach(priorities.rankedTeamTargets) { item in
                            CollectionPriorityRowView(item: item)
                        }
                    }

                    cardsSection(title: "Lock Now", cards: priorities.recommendedCardsToLock)
                    cardsSection(title: "Delay", cards: priorities.recommendedCardsToDelay)
                } else if viewModel.isLoading {
                    LoadingStateView(rows: 4)
                } else {
                    EmptyStateView(symbol: "square.grid.2x2", title: "Collection data unavailable", message: viewModel.errorMessage ?? "Run the backend collection engine to populate this screen.")
                }
            }
            .padding(20)
        }
        .navigationTitle("Collections")
        .task {
            await viewModel.load()
        }
        .refreshable {
            await viewModel.load()
        }
    }

    private func overview(_ priorities: CollectionPriorityResponse) -> some View {
        LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
            MetricCardView(title: "Projected Cost", value: AppFormatter.stubs(priorities.projectedCompletionCost), subtitle: "Estimated total completion path", systemImage: "lock.shield")
            MetricCardView(title: "Market Phase", value: priorities.marketPhase.title, subtitle: "Current collection lens", systemImage: "waveform.path.badge.minus")
        }
    }

    private func cardsSection(title: String, cards: [String]) -> some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: title, subtitle: nil)
                if cards.isEmpty {
                    Text("No cards in this list yet.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(cards, id: \.self) { card in
                        Text(card)
                            .font(.subheadline.weight(.semibold))
                    }
                }
            }
        }
    }
}

#Preview {
    PreviewHost {
        NavigationStack {
            CollectionsView(apiClient: MockAPIClient())
        }
    }
}
