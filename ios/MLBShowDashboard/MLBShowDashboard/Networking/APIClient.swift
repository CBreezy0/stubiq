import Foundation

protocol APIClienting {
    func fetchHealth() async throws -> HealthResponse
    func fetchDashboardSummary() async throws -> DashboardSummary
    func fetchMarketPhases() async throws -> MarketPhasesResponse
    func fetchFlips(limit: Int) async throws -> MarketOpportunityListResponse
    func fetchFloorBuys(limit: Int) async throws -> MarketOpportunityListResponse
    func fetchRosterTargets(limit: Int) async throws -> RosterUpdateRecommendationListResponse
    func fetchCollectionPriorities() async throws -> CollectionPriorityResponse
    func fetchPortfolio() async throws -> PortfolioResponse
    func fetchPortfolioRecommendations() async throws -> [PortfolioRecommendation]
    func fetchEngineThresholds() async throws -> EngineThresholds
    func patchEngineThresholds(_ payload: EngineThresholdsPatchRequest) async throws -> EngineThresholds
    func manualAddCard(_ payload: ManualAddRequest) async throws -> PortfolioResponse
    func manualRemoveCard(_ payload: ManualRemoveRequest) async throws -> PortfolioResponse
    func fetchCardDetail(itemId: String) async throws -> CardDetail
}

private enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case patch = "PATCH"
}

private struct APIErrorPayload: Decodable {
    let detail: String?
}

private struct AnyEncodable: Encodable {
    private let encodeHandler: (Encoder) throws -> Void

    init<T: Encodable>(_ value: T) {
        self.encodeHandler = value.encode
    }

    func encode(to encoder: Encoder) throws {
        try encodeHandler(encoder)
    }
}

enum APIClientError: LocalizedError {
    case invalidURL
    case invalidResponse
    case network(String)
    case decoding(String)
    case server(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "The API URL is invalid."
        case .invalidResponse:
            return "The server returned an unexpected response."
        case .network(let message):
            return message
        case .decoding(let message):
            return "Failed to decode the server response: \(message)"
        case .server(let message):
            return message
        }
    }
}

final class APIClient: APIClienting {
    private let session: URLSession
    private let environmentManager: EnvironmentManager
    private let tokenProvider: @Sendable () async -> String?
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder

    init(
        environmentManager: EnvironmentManager,
        session: URLSession = .shared,
        tokenProvider: @escaping @Sendable () async -> String? = { nil }
    ) {
        self.environmentManager = environmentManager
        self.session = session
        self.tokenProvider = tokenProvider

        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let value = try container.decode(String.self)
            let formatterWithFractional = ISO8601DateFormatter()
            formatterWithFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatterWithFractional.date(from: value) ?? formatter.date(from: value) {
                return date
            }
            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Invalid ISO8601 date: \(value)")
        }
        self.decoder = decoder

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        encoder.dateEncodingStrategy = .iso8601
        self.encoder = encoder
    }

    func fetchHealth() async throws -> HealthResponse {
        try await request(path: "health")
    }

    func fetchDashboardSummary() async throws -> DashboardSummary {
        try await request(path: "dashboard/summary")
    }

    func fetchMarketPhases() async throws -> MarketPhasesResponse {
        try await request(path: "market/phases")
    }

    func fetchFlips(limit: Int = 25) async throws -> MarketOpportunityListResponse {
        try await request(path: "market/flips", query: [URLQueryItem(name: "limit", value: String(limit))])
    }

    func fetchFloorBuys(limit: Int = 25) async throws -> MarketOpportunityListResponse {
        try await request(path: "market/floors", query: [URLQueryItem(name: "limit", value: String(limit))])
    }

    func fetchRosterTargets(limit: Int = 50) async throws -> RosterUpdateRecommendationListResponse {
        try await request(path: "investments/roster-update", query: [URLQueryItem(name: "limit", value: String(limit))])
    }

    func fetchCollectionPriorities() async throws -> CollectionPriorityResponse {
        try await request(path: "collections/priorities")
    }

    func fetchPortfolio() async throws -> PortfolioResponse {
        try await request(path: "portfolio")
    }

    func fetchPortfolioRecommendations() async throws -> [PortfolioRecommendation] {
        try await request(path: "portfolio/recommendations")
    }

    func fetchEngineThresholds() async throws -> EngineThresholds {
        try await request(path: "settings/engine-thresholds")
    }

    func patchEngineThresholds(_ payload: EngineThresholdsPatchRequest) async throws -> EngineThresholds {
        try await request(path: "settings/engine-thresholds", method: .patch, body: payload)
    }

    func manualAddCard(_ payload: ManualAddRequest) async throws -> PortfolioResponse {
        try await request(path: "portfolio/manual-add", method: .post, body: payload)
    }

    func manualRemoveCard(_ payload: ManualRemoveRequest) async throws -> PortfolioResponse {
        try await request(path: "portfolio/manual-remove", method: .post, body: payload)
    }

    func fetchCardDetail(itemId: String) async throws -> CardDetail {
        try await request(path: "cards/\(itemId)")
    }

    private func request<T: Decodable>(
        path: String,
        method: HTTPMethod = .get,
        query: [URLQueryItem] = [],
        body: Encodable? = nil,
        attempt: Int = 0
    ) async throws -> T {
        let baseURL = await MainActor.run { environmentManager.currentBaseURL }
        var url = baseURL
        for component in path.split(separator: "/") {
            url.appendPathComponent(String(component))
        }

        guard var components = URLComponents(url: url, resolvingAgainstBaseURL: false) else {
            throw APIClientError.invalidURL
        }
        if !query.isEmpty {
            components.queryItems = query
        }
        guard let requestURL = components.url else {
            throw APIClientError.invalidURL
        }

        var urlRequest = URLRequest(url: requestURL)
        urlRequest.httpMethod = method.rawValue
        urlRequest.timeoutInterval = 25
        urlRequest.setValue("application/json", forHTTPHeaderField: "Accept")

        if let token = await tokenProvider() {
            urlRequest.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        if let body {
            urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
            urlRequest.httpBody = try encoder.encode(AnyEncodable(body))
        }

        do {
            let (data, response) = try await session.data(for: urlRequest)
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIClientError.invalidResponse
            }

            guard (200..<300).contains(httpResponse.statusCode) else {
                let payload = try? decoder.decode(APIErrorPayload.self, from: data)
                let message = payload?.detail ?? HTTPURLResponse.localizedString(forStatusCode: httpResponse.statusCode)
                if method == .get, attempt < 2, (500..<600).contains(httpResponse.statusCode) {
                    try await Task.sleep(for: .milliseconds((attempt + 1) * 350))
                    return try await request(path: path, method: method, query: query, body: body, attempt: attempt + 1)
                }
                throw APIClientError.server(message)
            }

            do {
                return try decoder.decode(T.self, from: data)
            } catch {
                throw APIClientError.decoding(error.localizedDescription)
            }
        } catch let error as APIClientError {
            throw error
        } catch {
            if method == .get, attempt < 2 {
                try await Task.sleep(for: .milliseconds((attempt + 1) * 350))
                return try await request(path: path, method: method, query: query, body: body, attempt: attempt + 1)
            }
            throw APIClientError.network(error.localizedDescription)
        }
    }
}

final class MockAPIClient: APIClienting {
    private var thresholds = PreviewFixtures.thresholds
    private var portfolio = PreviewFixtures.portfolioResponse

    func fetchHealth() async throws -> HealthResponse {
        HealthResponse(
            status: "ok",
            appName: "Show Intel",
            gameYear: 26,
            schedulerRunning: true,
            databaseURL: "postgresql://hidden",
            marketPhase: PreviewFixtures.marketPhase,
            featureFlags: ["launch_phase_logic_enabled": true]
        )
    }

    func fetchDashboardSummary() async throws -> DashboardSummary {
        try await Task.sleep(for: .milliseconds(150))
        return DashboardSummary(
            marketPhase: PreviewFixtures.dashboardSummary.marketPhase,
            launchWeekAlerts: PreviewFixtures.dashboardSummary.launchWeekAlerts,
            topFlips: PreviewFixtures.dashboardSummary.topFlips,
            topFloorBuys: PreviewFixtures.dashboardSummary.topFloorBuys,
            topRosterUpdateTargets: PreviewFixtures.dashboardSummary.topRosterUpdateTargets,
            collectionPriorities: PreviewFixtures.dashboardSummary.collectionPriorities,
            portfolio: portfolio.items,
            topSells: PreviewFixtures.dashboardSummary.topSells,
            grindRecommendation: PreviewFixtures.dashboardSummary.grindRecommendation
        )
    }

    func fetchMarketPhases() async throws -> MarketPhasesResponse {
        PreviewFixtures.marketPhases
    }

    func fetchFlips(limit: Int) async throws -> MarketOpportunityListResponse {
        MarketOpportunityListResponse(phase: PreviewFixtures.marketPhase.phase, count: min(limit, PreviewFixtures.flips.count), items: Array(PreviewFixtures.flips.prefix(limit)))
    }

    func fetchFloorBuys(limit: Int) async throws -> MarketOpportunityListResponse {
        MarketOpportunityListResponse(phase: PreviewFixtures.marketPhase.phase, count: min(limit, PreviewFixtures.floors.count), items: Array(PreviewFixtures.floors.prefix(limit)))
    }

    func fetchRosterTargets(limit: Int) async throws -> RosterUpdateRecommendationListResponse {
        RosterUpdateRecommendationListResponse(count: min(limit, PreviewFixtures.rosterTargets.count), items: Array(PreviewFixtures.rosterTargets.prefix(limit)))
    }

    func fetchCollectionPriorities() async throws -> CollectionPriorityResponse {
        PreviewFixtures.collectionPriorities
    }

    func fetchPortfolio() async throws -> PortfolioResponse {
        portfolio
    }

    func fetchPortfolioRecommendations() async throws -> [PortfolioRecommendation] {
        PreviewFixtures.portfolioRecommendations
    }

    func fetchEngineThresholds() async throws -> EngineThresholds {
        thresholds
    }

    func patchEngineThresholds(_ payload: EngineThresholdsPatchRequest) async throws -> EngineThresholds {
        thresholds = EngineThresholds(
            floorBuyMargin: payload.floorBuyMargin ?? thresholds.floorBuyMargin,
            launchSupplyCrashThreshold: payload.launchSupplyCrashThreshold ?? thresholds.launchSupplyCrashThreshold,
            flipProfitMinimum: payload.flipProfitMinimum ?? thresholds.flipProfitMinimum,
            grindMarketEdge: payload.grindMarketEdge ?? thresholds.grindMarketEdge,
            collectionLockPenalty: payload.collectionLockPenalty ?? thresholds.collectionLockPenalty,
            gatekeeperHoldWeight: payload.gatekeeperHoldWeight ?? thresholds.gatekeeperHoldWeight,
            updatedAt: Date()
        )
        return thresholds
    }

    func manualAddCard(_ payload: ManualAddRequest) async throws -> PortfolioResponse {
        let baseCard = PreviewFixtures.cards.first ?? CardSummary(
            itemId: payload.itemId,
            name: payload.cardName,
            series: "Manual",
            team: nil,
            division: nil,
            league: nil,
            overall: nil,
            rarity: nil,
            displayPosition: nil,
            isLiveSeries: false,
            quicksellValue: nil,
            latestBuyNow: payload.avgAcquisitionCost,
            latestSellNow: payload.avgAcquisitionCost,
            latestBestBuyOrder: nil,
            latestBestSellOrder: nil,
            latestTaxAdjustedSpread: nil,
            observedAt: Date()
        )
        let card = CardSummary(
            itemId: payload.itemId,
            name: payload.cardName,
            series: baseCard.series,
            team: baseCard.team,
            division: baseCard.division,
            league: baseCard.league,
            overall: baseCard.overall,
            rarity: baseCard.rarity,
            displayPosition: baseCard.displayPosition,
            isLiveSeries: baseCard.isLiveSeries,
            quicksellValue: baseCard.quicksellValue,
            latestBuyNow: baseCard.latestBuyNow ?? payload.avgAcquisitionCost,
            latestSellNow: baseCard.latestSellNow ?? payload.avgAcquisitionCost,
            latestBestBuyOrder: baseCard.latestBestBuyOrder,
            latestBestSellOrder: baseCard.latestBestSellOrder,
            latestTaxAdjustedSpread: baseCard.latestTaxAdjustedSpread,
            observedAt: Date()
        )

        let newPosition = PortfolioPosition(
            itemId: payload.itemId,
            card: card,
            quantity: payload.quantity,
            avgAcquisitionCost: payload.avgAcquisitionCost,
            currentMarketValue: card.latestBuyNow ?? payload.avgAcquisitionCost,
            quicksellValue: card.quicksellValue,
            lockedForCollection: payload.lockedForCollection,
            duplicateCount: max(payload.quantity - 1, 0),
            source: payload.source,
            createdAt: Date(),
            updatedAt: Date(),
            totalCostBasis: payload.avgAcquisitionCost * payload.quantity,
            unrealizedProfit: ((card.latestBuyNow ?? payload.avgAcquisitionCost) - payload.avgAcquisitionCost) * payload.quantity,
            quicksellFloorTotal: (card.quicksellValue ?? 0) * payload.quantity
        )

        portfolio = PortfolioResponse(
            totalPositions: portfolio.items.count + 1,
            totalMarketValue: portfolio.totalMarketValue + ((newPosition.currentMarketValue ?? 0) * newPosition.quantity),
            totalCostBasis: portfolio.totalCostBasis + newPosition.totalCostBasis,
            totalUnrealizedProfit: portfolio.totalUnrealizedProfit + (newPosition.unrealizedProfit ?? 0),
            items: portfolio.items + [newPosition]
        )
        return portfolio
    }

    func manualRemoveCard(_ payload: ManualRemoveRequest) async throws -> PortfolioResponse {
        let items = portfolio.items.compactMap { position -> PortfolioPosition? in
            guard position.itemId == payload.itemId else { return position }
            if payload.removeAll { return nil }
            let newQuantity = max(position.quantity - (payload.quantity ?? 1), 0)
            guard newQuantity > 0 else { return nil }
            return PortfolioPosition(
                itemId: position.itemId,
                card: position.card,
                quantity: newQuantity,
                avgAcquisitionCost: position.avgAcquisitionCost,
                currentMarketValue: position.currentMarketValue,
                quicksellValue: position.quicksellValue,
                lockedForCollection: position.lockedForCollection,
                duplicateCount: max(newQuantity - 1, 0),
                source: position.source,
                createdAt: position.createdAt,
                updatedAt: Date(),
                totalCostBasis: newQuantity * position.avgAcquisitionCost,
                unrealizedProfit: (position.currentMarketValue.map { ($0 - position.avgAcquisitionCost) * newQuantity }),
                quicksellFloorTotal: position.quicksellValue.map { $0 * newQuantity }
            )
        }

        let totalMarketValue = items.reduce(0) { $0 + (($1.currentMarketValue ?? 0) * $1.quantity) }
        let totalCostBasis = items.reduce(0) { $0 + $1.totalCostBasis }
        let totalUnrealized = items.reduce(0) { $0 + ($1.unrealizedProfit ?? 0) }
        portfolio = PortfolioResponse(
            totalPositions: items.count,
            totalMarketValue: totalMarketValue,
            totalCostBasis: totalCostBasis,
            totalUnrealizedProfit: totalUnrealized,
            items: items
        )
        return portfolio
    }

    func fetchCardDetail(itemId: String) async throws -> CardDetail {
        if itemId == PreviewFixtures.cardDetail.itemId {
            return PreviewFixtures.cardDetail
        }
        let fallbackCard = portfolio.items.first(where: { $0.itemId == itemId })?.card ?? PreviewFixtures.cards.first!
        return CardDetail(
            itemId: fallbackCard.itemId,
            name: fallbackCard.name,
            series: fallbackCard.series,
            team: fallbackCard.team,
            division: fallbackCard.division,
            league: fallbackCard.league,
            overall: fallbackCard.overall,
            rarity: fallbackCard.rarity,
            displayPosition: fallbackCard.displayPosition,
            isLiveSeries: fallbackCard.isLiveSeries,
            quicksellValue: fallbackCard.quicksellValue,
            latestBuyNow: fallbackCard.latestBuyNow,
            latestSellNow: fallbackCard.latestSellNow,
            latestBestBuyOrder: fallbackCard.latestBestBuyOrder,
            latestBestSellOrder: fallbackCard.latestBestSellOrder,
            latestTaxAdjustedSpread: fallbackCard.latestTaxAdjustedSpread,
            observedAt: Date(),
            metadataJson: [:],
            aggregatePhase: PreviewFixtures.marketPhase.phase.rawValue,
            avgPrice15m: Double(fallbackCard.latestBuyNow ?? 0),
            avgPrice1h: Double(fallbackCard.latestBuyNow ?? 0) * 0.98,
            avgPrice6h: Double(fallbackCard.latestBuyNow ?? 0) * 0.94,
            avgPrice24h: Double(fallbackCard.latestBuyNow ?? 0) * 0.89,
            volatilityScore: 0.42,
            liquidityScore: 0.71,
            recommendations: PreviewFixtures.cardDetail.recommendations
        )
    }
}
