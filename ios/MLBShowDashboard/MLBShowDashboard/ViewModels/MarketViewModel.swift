import Foundation

enum MarketBoardMode: String, CaseIterable, Identifiable {
    case flips = "Flips"
    case floorBuys = "Floor Buys"

    var id: String { rawValue }
}

enum MarketSortOption: String, CaseIterable, Identifiable {
    case profit = "Profit"
    case confidence = "Confidence"
    case liquidity = "Liquidity"

    var id: String { rawValue }
}

@MainActor
final class MarketViewModel: ObservableObject {
    @Published var mode: MarketBoardMode = .flips
    @Published private(set) var flips: [MarketOpportunity] = []
    @Published private(set) var floorBuys: [MarketOpportunity] = []
    @Published var searchText = ""
    @Published var selectedRarity = "All"
    @Published var selectedSeries = "All"
    @Published var selectedTeam = "All"
    @Published var sortOption: MarketSortOption = .profit
    @Published private(set) var isLoading = false
    @Published var errorMessage: String?

    private let apiClient: APIClienting

    init(apiClient: APIClienting) {
        self.apiClient = apiClient
    }

    func load() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            async let flipsResponse = apiClient.fetchFlips(limit: 50)
            async let floorsResponse = apiClient.fetchFloorBuys(limit: 50)
            flips = try await flipsResponse.items
            floorBuys = try await floorsResponse.items
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    var availableRarities: [String] {
        ["All"] + Array(Set(currentItems.compactMap { $0.card.rarity })).sorted()
    }

    var availableSeries: [String] {
        ["All"] + Array(Set(currentItems.compactMap { $0.card.series })).sorted()
    }

    var availableTeams: [String] {
        ["All"] + Array(Set(currentItems.compactMap { $0.card.team })).sorted()
    }

    var currentItems: [MarketOpportunity] {
        mode == .flips ? flips : floorBuys
    }

    var filteredItems: [MarketOpportunity] {
        currentItems
            .filter { item in
                let matchesSearch = searchText.isEmpty || item.card.name.localizedCaseInsensitiveContains(searchText) || (item.card.team?.localizedCaseInsensitiveContains(searchText) ?? false) || (item.card.series?.localizedCaseInsensitiveContains(searchText) ?? false)
                let matchesRarity = selectedRarity == "All" || item.card.rarity == selectedRarity
                let matchesSeries = selectedSeries == "All" || item.card.series == selectedSeries
                let matchesTeam = selectedTeam == "All" || item.card.team == selectedTeam
                return matchesSearch && matchesRarity && matchesSeries && matchesTeam
            }
            .sorted(by: sort)
    }

    private func sort(lhs: MarketOpportunity, rhs: MarketOpportunity) -> Bool {
        switch sortOption {
        case .profit:
            return (lhs.expectedProfitPerFlip ?? 0) > (rhs.expectedProfitPerFlip ?? 0)
        case .confidence:
            return lhs.confidence > rhs.confidence
        case .liquidity:
            return lhs.liquidityScore > rhs.liquidityScore
        }
    }
}
