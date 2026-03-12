import SwiftUI

struct TargetsScreen: View {
    @StateObject private var viewModel: TargetsViewModel
    @EnvironmentObject private var appState: AppState

    init(apiClient: APIClienting) {
        _viewModel = StateObject(wrappedValue: TargetsViewModel(apiClient: apiClient))
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 16) {
                    filters
                    if viewModel.isLoading, viewModel.items.isEmpty {
                        LoadingStateView(rows: 4)
                    } else if viewModel.filteredItems.isEmpty {
                        EmptyStateView(symbol: "scope", title: "No roster targets", message: "No player matches your current bucket or role filters.")
                    } else {
                        ForEach(viewModel.filteredItems) { item in
                            NavigationLink {
                                CardDetailView(itemId: item.itemId, apiClient: appState.apiClient, rosterTarget: item)
                            } label: {
                                RosterTargetRowView(item: item)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                }
                .padding(20)
            }
            .navigationTitle("Roster Targets")
            .searchable(text: $viewModel.searchText, prompt: "Search players")
            .refreshable {
                await viewModel.load()
            }
            .task {
                await viewModel.load()
            }
        }
    }

    private var filters: some View {
        VStack(spacing: 12) {
            Picker("Upgrade", selection: $viewModel.selectedBucket) {
                ForEach(TargetUpgradeBucket.allCases) { bucket in
                    Text(bucket.rawValue).tag(bucket)
                }
            }
            .pickerStyle(.segmented)

            Picker("Player Type", selection: $viewModel.selectedType) {
                ForEach(TargetPlayerType.allCases) { type in
                    Text(type.rawValue).tag(type)
                }
            }
            .pickerStyle(.segmented)
        }
    }
}

#Preview {
    PreviewHost {
        TargetsScreen(apiClient: MockAPIClient())
    }
}
