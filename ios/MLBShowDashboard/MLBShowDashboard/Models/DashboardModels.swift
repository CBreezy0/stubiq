import Foundation

struct CollectionTarget: Codable, Hashable, Identifiable {
    let name: String
    let level: String
    let priorityScore: Double
    let completionPct: Double
    let remainingCost: Int
    let ownedGatekeeperValue: Int
    let rewardValueProxy: Int
    let rationale: String

    var id: String { "\(level)-\(name)" }
}

struct CollectionPriorityResponse: Codable, Hashable {
    let marketPhase: MarketPhase
    let projectedCompletionCost: Int
    let rankedDivisionTargets: [CollectionTarget]
    let rankedTeamTargets: [CollectionTarget]
    let recommendedCardsToLock: [String]
    let recommendedCardsToDelay: [String]
}

struct PortfolioPosition: Codable, Hashable, Identifiable {
    let itemId: String
    let card: CardSummary
    let quantity: Int
    let avgAcquisitionCost: Int
    let currentMarketValue: Int?
    let quicksellValue: Int?
    let lockedForCollection: Bool
    let duplicateCount: Int
    let source: String?
    let createdAt: Date
    let updatedAt: Date
    let totalCostBasis: Int
    let unrealizedProfit: Int?
    let quicksellFloorTotal: Int?

    var id: String { itemId }
}

struct PortfolioResponse: Codable, Hashable {
    let totalPositions: Int
    let totalMarketValue: Int
    let totalCostBasis: Int
    let totalUnrealizedProfit: Int
    let items: [PortfolioPosition]
}

struct PortfolioRecommendation: Codable, Hashable, Identifiable {
    let itemId: String
    let action: RecommendationAction
    let confidence: Double
    let sellNowScore: Double
    let holdScore: Double
    let lockScore: Double
    let flipOutScore: Double
    let portfolioRiskScore: Double
    let rationale: String

    var id: String { itemId }
}

struct ModeValue: Codable, Hashable, Identifiable {
    let modeName: String
    let expectedValuePerHour: Double
    let rationale: String

    var id: String { modeName }
}

struct GrindRecommendation: Codable, Hashable {
    let action: RecommendationAction
    let bestModeToPlayNow: String
    let expectedMarketStubsPerHour: Double
    let expectedValuePerHourByMode: [ModeValue]
    let packValueEstimate: Double
    let rationale: String
}

struct RosterUpdateRecommendation: Codable, Hashable, Identifiable {
    let itemId: String
    let playerName: String
    let mlbPlayerId: Int
    let card: CardSummary
    let action: RecommendationAction
    let currentOvr: Int
    let currentPrice: Int
    let upgradeProbability: Double
    let downgradeProbability: Double
    let expectedQuicksellValue: Int
    let expectedMarketValue: Double
    let expectedProfit: Double
    let downsideRisk: Double
    let confidence: Double
    let rationale: String
    let rationaleJson: [String: JSONValue]
    let generatedAt: Date?

    var id: String { itemId }
}

struct RosterUpdateRecommendationListResponse: Codable, Hashable {
    let count: Int
    let items: [RosterUpdateRecommendation]
}

struct EngineThresholds: Codable, Hashable {
    let floorBuyMargin: Double
    let launchSupplyCrashThreshold: Double
    let flipProfitMinimum: Double
    let grindMarketEdge: Double
    let collectionLockPenalty: Double
    let gatekeeperHoldWeight: Double
    let updatedAt: Date?
}

struct EngineThresholdsPatchRequest: Encodable, Hashable {
    var floorBuyMargin: Double?
    var launchSupplyCrashThreshold: Double?
    var flipProfitMinimum: Double?
    var grindMarketEdge: Double?
    var collectionLockPenalty: Double?
    var gatekeeperHoldWeight: Double?
}

struct DashboardSummary: Codable, Hashable {
    let marketPhase: MarketPhaseSnapshot
    let launchWeekAlerts: [String]
    let topFlips: [MarketOpportunity]
    let topFloorBuys: [MarketOpportunity]
    let topRosterUpdateTargets: [RosterUpdateRecommendation]
    let collectionPriorities: CollectionPriorityResponse
    let portfolio: [PortfolioPosition]
    let topSells: [PortfolioRecommendation]
    let grindRecommendation: GrindRecommendation
}

struct ManualAddRequest: Encodable, Hashable {
    let itemId: String
    let cardName: String
    let quantity: Int
    let avgAcquisitionCost: Int
    let lockedForCollection: Bool
    let source: String

    init(itemId: String, cardName: String, quantity: Int, avgAcquisitionCost: Int, lockedForCollection: Bool, source: String = "manual") {
        self.itemId = itemId
        self.cardName = cardName
        self.quantity = quantity
        self.avgAcquisitionCost = avgAcquisitionCost
        self.lockedForCollection = lockedForCollection
        self.source = source
    }
}

struct ManualRemoveRequest: Encodable, Hashable {
    let itemId: String
    let quantity: Int?
    let removeAll: Bool

    init(itemId: String, quantity: Int? = nil, removeAll: Bool = false) {
        self.itemId = itemId
        self.quantity = quantity
        self.removeAll = removeAll
    }
}
