import Foundation

enum TargetUpgradeBucket: String, CaseIterable, Identifiable {
    case all = "All"
    case seventyNineToEighty = "79 → 80"
    case eightyFourToEightyFive = "84 → 85"

    var id: String { rawValue }
}

enum TargetPlayerType: String, CaseIterable, Identifiable {
    case all = "All"
    case hitters = "Hitters"
    case pitchers = "Pitchers"

    var id: String { rawValue }
}

@MainActor
final class TargetsViewModel: ObservableObject {
    @Published private(set) var items: [RosterUpdateRecommendation] = []
    @Published var searchText = ""
    @Published var selectedBucket: TargetUpgradeBucket = .all
    @Published var selectedType: TargetPlayerType = .all
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
            items = try await apiClient.fetchRosterTargets(limit: 75).items
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    var filteredItems: [RosterUpdateRecommendation] {
        items
            .filter { item in
                let matchesSearch = searchText.isEmpty || item.playerName.localizedCaseInsensitiveContains(searchText) || item.card.name.localizedCaseInsensitiveContains(searchText)
                let matchesBucket: Bool
                switch selectedBucket {
                case .all:
                    matchesBucket = true
                case .seventyNineToEighty:
                    matchesBucket = item.currentOvr == 79
                case .eightyFourToEightyFive:
                    matchesBucket = item.currentOvr == 84
                }

                let position = item.card.displayPosition?.uppercased() ?? ""
                let isPitcher = ["SP", "RP", "CP", "P"].contains(position)
                let matchesType: Bool
                switch selectedType {
                case .all:
                    matchesType = true
                case .hitters:
                    matchesType = !isPitcher
                case .pitchers:
                    matchesType = isPitcher
                }

                return matchesSearch && matchesBucket && matchesType
            }
            .sorted { $0.expectedProfit > $1.expectedProfit }
    }
}
