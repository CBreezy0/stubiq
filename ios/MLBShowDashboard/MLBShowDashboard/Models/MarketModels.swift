import Foundation

enum RecommendationAction: String, Codable, CaseIterable, Hashable, Identifiable {
    case buy = "BUY"
    case sell = "SELL"
    case hold = "HOLD"
    case flip = "FLIP"
    case lock = "LOCK"
    case grind = "GRIND"
    case watch = "WATCH"
    case avoid = "AVOID"
    case ignore = "IGNORE"

    var id: String { rawValue }

    var title: String {
        rawValue.replacingOccurrences(of: "_", with: " ").capitalized
    }

    var isPositiveOpportunity: Bool {
        switch self {
        case .buy, .flip, .lock, .grind:
            return true
        default:
            return false
        }
    }
}

enum RecommendationType: String, Codable, CaseIterable, Hashable, Identifiable {
    case market = "MARKET"
    case collection = "COLLECTION"
    case rosterUpdate = "ROSTER_UPDATE"
    case portfolio = "PORTFOLIO"
    case grind = "GRIND"
    case orchestrated = "ORCHESTRATED"

    var id: String { rawValue }

    var title: String {
        rawValue.replacingOccurrences(of: "_", with: " ").capitalized
    }
}

enum MarketPhase: String, Codable, CaseIterable, Hashable, Identifiable {
    case earlyAccess = "EARLY_ACCESS"
    case fullLaunchSupplyShock = "FULL_LAUNCH_SUPPLY_SHOCK"
    case stabilization = "STABILIZATION"
    case preAttributeUpdate = "PRE_ATTRIBUTE_UPDATE"
    case postAttributeUpdate = "POST_ATTRIBUTE_UPDATE"
    case contentDrop = "CONTENT_DROP"
    case stubSale = "STUB_SALE"
    case lateCycle = "LATE_CYCLE"

    var id: String { rawValue }

    var title: String {
        switch self {
        case .earlyAccess:
            return "Early Access"
        case .fullLaunchSupplyShock:
            return "Launch Shock"
        case .stabilization:
            return "Stabilization"
        case .preAttributeUpdate:
            return "Pre Update"
        case .postAttributeUpdate:
            return "Post Update"
        case .contentDrop:
            return "Content Drop"
        case .stubSale:
            return "Stub Sale"
        case .lateCycle:
            return "Late Cycle"
        }
    }
}

struct CardSummary: Codable, Hashable, Identifiable {
    let itemId: String
    let name: String
    let series: String?
    let team: String?
    let division: String?
    let league: String?
    let overall: Int?
    let rarity: String?
    let displayPosition: String?
    let isLiveSeries: Bool
    let quicksellValue: Int?
    let latestBuyNow: Int?
    let latestSellNow: Int?
    let latestBestBuyOrder: Int?
    let latestBestSellOrder: Int?
    let latestTaxAdjustedSpread: Int?
    let observedAt: Date?

    var id: String { itemId }
}

struct MarketPhaseSnapshot: Codable, Hashable {
    let phase: MarketPhase
    let confidence: Double
    let rationale: String
    let overrideActive: Bool
    let detectedAt: Date
}

struct MarketPhaseHistoryItem: Codable, Hashable {
    let id: Int?
    let phase: MarketPhase
    let phaseStart: Date?
    let phaseEnd: Date?
    let notes: String?
}

struct MarketPhasesResponse: Codable, Hashable {
    let current: MarketPhaseSnapshot
    let history: [MarketPhaseHistoryItem]
}

struct MarketOpportunity: Codable, Hashable, Identifiable {
    let itemId: String
    let card: CardSummary
    let action: RecommendationAction
    let expectedProfitPerFlip: Int?
    let fillVelocityScore: Double
    let liquidityScore: Double
    let riskScore: Double
    let floorProximityScore: Double
    let marketPhase: MarketPhase
    let confidence: Double
    let rationale: String

    var id: String { itemId }
}

struct MarketOpportunityListResponse: Codable, Hashable {
    let phase: MarketPhase
    let count: Int
    let items: [MarketOpportunity]
}

struct RecommendationView: Codable, Hashable, Identifiable {
    let recommendationType: RecommendationType
    let action: RecommendationAction
    let confidence: Double
    let expectedProfit: Int?
    let expectedValue: Double?
    let marketPhase: MarketPhase
    let rationale: String
    let rationaleJson: [String: JSONValue]

    var id: String {
        [recommendationType.rawValue, action.rawValue, String(format: "%.3f", confidence)].joined(separator: "-")
    }
}

struct CardDetail: Codable, Hashable, Identifiable {
    let itemId: String
    let name: String
    let series: String?
    let team: String?
    let division: String?
    let league: String?
    let overall: Int?
    let rarity: String?
    let displayPosition: String?
    let isLiveSeries: Bool
    let quicksellValue: Int?
    let latestBuyNow: Int?
    let latestSellNow: Int?
    let latestBestBuyOrder: Int?
    let latestBestSellOrder: Int?
    let latestTaxAdjustedSpread: Int?
    let observedAt: Date?
    let metadataJson: [String: JSONValue]
    let aggregatePhase: String?
    let avgPrice15m: Double?
    let avgPrice1h: Double?
    let avgPrice6h: Double?
    let avgPrice24h: Double?
    let volatilityScore: Double?
    let liquidityScore: Double?
    let recommendations: [RecommendationView]

    var id: String { itemId }
}
