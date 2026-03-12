import SwiftUI

struct MarketScreen: View {
    @StateObject private var viewModel: MarketViewModel
    @EnvironmentObject private var appState: AppState

    init(apiClient: APIClienting) {
        _viewModel = StateObject(wrappedValue: MarketViewModel(apiClient: apiClient))
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 16) {
                    header
                    filterBar

                    if viewModel.isLoading, viewModel.currentItems.isEmpty {
                        LoadingStateView(rows: 4)
                    } else if viewModel.filteredItems.isEmpty {
                        EmptyStateView(symbol: "magnifyingglass", title: "No matches", message: "Adjust your search or filters to surface more opportunities.")
                    } else {
                        ForEach(viewModel.filteredItems) { item in
                            NavigationLink {
                                CardDetailView(itemId: item.itemId, apiClient: appState.apiClient, marketOpportunity: item, marketPhase: item.marketPhase)
                            } label: {
                                OpportunityRowView(item: item)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .padding(20)
            }
            .navigationTitle("Market")
            .searchable(text: $viewModel.searchText, prompt: "Search cards, teams, series")
            .refreshable {
                await viewModel.load()
            }
            .task {
                await viewModel.load()
            }
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Menu("Sort") {
                        Picker("Sort", selection: $viewModel.sortOption) {
                            ForEach(MarketSortOption.allCases) { option in
                                Text(option.rawValue).tag(option)
                            }
                        }
                    }
                }
            }
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 12) {
            Picker("Mode", selection: $viewModel.mode) {
                ForEach(MarketBoardMode.allCases) { mode in
                    Text(mode.rawValue).tag(mode)
                }
            }
            .pickerStyle(.segmented)

            Text(viewModel.mode == .flips ? "Best current flip opportunities with liquidity and confidence context." : "Cards hovering near floor support with accumulation upside.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }

    private var filterBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                filterMenu(title: "Rarity", selection: $viewModel.selectedRarity, options: viewModel.availableRarities)
                filterMenu(title: "Series", selection: $viewModel.selectedSeries, options: viewModel.availableSeries)
                filterMenu(title: "Team", selection: $viewModel.selectedTeam, options: viewModel.availableTeams)
            }
        }
    }

    private func filterMenu(title: String, selection: Binding<String>, options: [String]) -> some View {
        Menu {
            Picker(title, selection: selection) {
                ForEach(options, id: \.self) { option in
                    Text(option).tag(option)
                }
            }
        } label: {
            Text("\(title): \(selection.wrappedValue)")
                .font(.subheadline.weight(.semibold))
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(.ultraThinMaterial, in: Capsule())
        }
    }
}

#Preview {
    PreviewHost {
        MarketScreen(apiClient: MockAPIClient())
    }
}
