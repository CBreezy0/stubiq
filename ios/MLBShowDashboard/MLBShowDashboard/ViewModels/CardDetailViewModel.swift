import Foundation

@MainActor
final class CardDetailViewModel: ObservableObject {
    @Published private(set) var detail: CardDetail?
    @Published private(set) var isLoading = false
    @Published var errorMessage: String?

    let itemId: String
    let marketOpportunity: MarketOpportunity?
    let rosterTarget: RosterUpdateRecommendation?
    let portfolioRecommendation: PortfolioRecommendation?
    let marketPhase: MarketPhase?

    private let apiClient: APIClienting

    init(
        itemId: String,
        apiClient: APIClienting,
        marketOpportunity: MarketOpportunity? = nil,
        rosterTarget: RosterUpdateRecommendation? = nil,
        portfolioRecommendation: PortfolioRecommendation? = nil,
        marketPhase: MarketPhase? = nil
    ) {
        self.itemId = itemId
        self.apiClient = apiClient
        self.marketOpportunity = marketOpportunity
        self.rosterTarget = rosterTarget
        self.portfolioRecommendation = portfolioRecommendation
        self.marketPhase = marketPhase
    }

    func load() async {
        if isLoading { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            detail = try await apiClient.fetchCardDetail(itemId: itemId)
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    var floorBuyScore: Double? {
        marketOpportunity?.floorProximityScore
    }

    var flipConfidence: Double? {
        marketOpportunity?.confidence
    }

    var rosterUpgradeProbability: Double? {
        rosterTarget?.upgradeProbability
    }

    var portfolioAction: RecommendationAction? {
        portfolioRecommendation?.action
    }
}
