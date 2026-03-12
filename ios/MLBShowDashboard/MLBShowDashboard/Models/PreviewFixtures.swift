import Foundation

enum PreviewFixtures {
    private static let now = Date()

    static let marketPhase = MarketPhaseSnapshot(
        phase: .fullLaunchSupplyShock,
        confidence: 0.86,
        rationale: "Supply is still flooding the market, but spreads are tightening on premium live series cards.",
        overrideActive: false,
        detectedAt: now
    )

    static let cards: [CardSummary] = [
        CardSummary(
            itemId: "live-ohtani-26",
            name: "Shohei Ohtani",
            series: "Live Series",
            team: "Dodgers",
            division: "NL West",
            league: "NL",
            overall: 95,
            rarity: "Diamond",
            displayPosition: "DH",
            isLiveSeries: true,
            quicksellValue: 10000,
            latestBuyNow: 142000,
            latestSellNow: 149000,
            latestBestBuyOrder: 140500,
            latestBestSellOrder: 147500,
            latestTaxAdjustedSpread: 7550,
            observedAt: now
        ),
        CardSummary(
            itemId: "live-skenes-26",
            name: "Paul Skenes",
            series: "Live Series",
            team: "Pirates",
            division: "NL Central",
            league: "NL",
            overall: 84,
            rarity: "Gold",
            displayPosition: "SP",
            isLiveSeries: true,
            quicksellValue: 3000,
            latestBuyNow: 6200,
            latestSellNow: 6900,
            latestBestBuyOrder: 6000,
            latestBestSellOrder: 6700,
            latestTaxAdjustedSpread: 355,
            observedAt: now
        ),
        CardSummary(
            itemId: "retro-jeter-26",
            name: "Derek Jeter",
            series: "Captain",
            team: "Yankees",
            division: "AL East",
            league: "AL",
            overall: 91,
            rarity: "Diamond",
            displayPosition: "SS",
            isLiveSeries: false,
            quicksellValue: 10000,
            latestBuyNow: 34500,
            latestSellNow: 38900,
            latestBestBuyOrder: 33900,
            latestBestSellOrder: 38200,
            latestTaxAdjustedSpread: 2355,
            observedAt: now
        )
    ]

    static let flips: [MarketOpportunity] = [
        MarketOpportunity(
            itemId: cards[0].itemId,
            card: cards[0],
            action: .flip,
            expectedProfitPerFlip: 7550,
            fillVelocityScore: 0.82,
            liquidityScore: 0.91,
            riskScore: 0.33,
            floorProximityScore: 0.18,
            marketPhase: .fullLaunchSupplyShock,
            confidence: 0.88,
            rationale: "Elite demand and deep order book keep the spread healthy despite heavy launch supply."
        ),
        MarketOpportunity(
            itemId: cards[2].itemId,
            card: cards[2],
            action: .flip,
            expectedProfitPerFlip: 2355,
            fillVelocityScore: 0.73,
            liquidityScore: 0.69,
            riskScore: 0.41,
            floorProximityScore: 0.26,
            marketPhase: .fullLaunchSupplyShock,
            confidence: 0.76,
            rationale: "Captain demand spikes every evening; the spread is still wide enough for repeated cycles."
        )
    ]

    static let floors: [MarketOpportunity] = [
        MarketOpportunity(
            itemId: cards[1].itemId,
            card: cards[1],
            action: .buy,
            expectedProfitPerFlip: 1350,
            fillVelocityScore: 0.59,
            liquidityScore: 0.64,
            riskScore: 0.25,
            floorProximityScore: 0.91,
            marketPhase: .fullLaunchSupplyShock,
            confidence: 0.79,
            rationale: "Gold pitcher is hugging quicksell support with strong upgrade demand building into the first attribute window."
        ),
        MarketOpportunity(
            itemId: cards[2].itemId,
            card: cards[2],
            action: .buy,
            expectedProfitPerFlip: 2200,
            fillVelocityScore: 0.61,
            liquidityScore: 0.58,
            riskScore: 0.28,
            floorProximityScore: 0.83,
            marketPhase: .stabilization,
            confidence: 0.71,
            rationale: "Program demand is steady while undercutting pressure is creating a clean floor entry band."
        )
    ]

    static let rosterTargets: [RosterUpdateRecommendation] = [
        RosterUpdateRecommendation(
            itemId: cards[1].itemId,
            playerName: "Paul Skenes",
            mlbPlayerId: 694973,
            card: cards[1],
            action: .buy,
            currentOvr: 84,
            currentPrice: 6200,
            upgradeProbability: 0.63,
            downgradeProbability: 0.08,
            expectedQuicksellValue: 10000,
            expectedMarketValue: 11800,
            expectedProfit: 5600,
            downsideRisk: 1400,
            confidence: 0.81,
            rationale: "Strikeout volume and market momentum both support an 84 to 85 path.",
            rationaleJson: ["bucket": .string("84_to_85")],
            generatedAt: now
        ),
        RosterUpdateRecommendation(
            itemId: "live-gunnar-26",
            playerName: "Gunnar Henderson",
            mlbPlayerId: 683002,
            card: CardSummary(
                itemId: "live-gunnar-26",
                name: "Gunnar Henderson",
                series: "Live Series",
                team: "Orioles",
                division: "AL East",
                league: "AL",
                overall: 79,
                rarity: "Silver",
                displayPosition: "3B",
                isLiveSeries: true,
                quicksellValue: 400,
                latestBuyNow: 950,
                latestSellNow: 1100,
                latestBestBuyOrder: 900,
                latestBestSellOrder: 1050,
                latestTaxAdjustedSpread: 95,
                observedAt: now
            ),
            action: .buy,
            currentOvr: 79,
            currentPrice: 950,
            upgradeProbability: 0.72,
            downgradeProbability: 0.05,
            expectedQuicksellValue: 1200,
            expectedMarketValue: 2200,
            expectedProfit: 980,
            downsideRisk: 140,
            confidence: 0.77,
            rationale: "The 79 to 80 window is live, and hitting indicators remain strong enough to hold through the next update.",
            rationaleJson: ["bucket": .string("79_to_80")],
            generatedAt: now
        )
    ]

    static let collectionPriorities = CollectionPriorityResponse(
        marketPhase: .fullLaunchSupplyShock,
        projectedCompletionCost: 512_000,
        rankedDivisionTargets: [
            CollectionTarget(
                name: "AL East",
                level: "Division",
                priorityScore: 0.91,
                completionPct: 0.68,
                remainingCost: 128_000,
                ownedGatekeeperValue: 224_000,
                rewardValueProxy: 138_000,
                rationale: "Best balance of near-finish cost and reward leverage."
            ),
            CollectionTarget(
                name: "NL West",
                level: "Division",
                priorityScore: 0.82,
                completionPct: 0.51,
                remainingCost: 181_000,
                ownedGatekeeperValue: 172_000,
                rewardValueProxy: 160_000,
                rationale: "Expensive, but elite reward path makes it a premium medium-term chase."
            )
        ],
        rankedTeamTargets: [
            CollectionTarget(
                name: "Pirates",
                level: "Team",
                priorityScore: 0.84,
                completionPct: 0.89,
                remainingCost: 7_800,
                ownedGatekeeperValue: 0,
                rewardValueProxy: 11_000,
                rationale: "Cheap close-out with a clean captain payoff."
            ),
            CollectionTarget(
                name: "Orioles",
                level: "Team",
                priorityScore: 0.79,
                completionPct: 0.74,
                remainingCost: 16_400,
                ownedGatekeeperValue: 0,
                rewardValueProxy: 22_000,
                rationale: "Moderate remaining cost and strong set fit."
            )
        ],
        recommendedCardsToLock: ["Paul Skenes", "Gunnar Henderson"],
        recommendedCardsToDelay: ["Shohei Ohtani"]
    )

    static let portfolioItems: [PortfolioPosition] = [
        PortfolioPosition(
            itemId: cards[1].itemId,
            card: cards[1],
            quantity: 18,
            avgAcquisitionCost: 5200,
            currentMarketValue: 6200,
            quicksellValue: 3000,
            lockedForCollection: false,
            duplicateCount: 17,
            source: "manual",
            createdAt: Calendar.current.date(byAdding: .day, value: -7, to: now) ?? now,
            updatedAt: Calendar.current.date(byAdding: .hour, value: -2, to: now) ?? now,
            totalCostBasis: 93_600,
            unrealizedProfit: 18_000,
            quicksellFloorTotal: 54_000
        ),
        PortfolioPosition(
            itemId: cards[2].itemId,
            card: cards[2],
            quantity: 3,
            avgAcquisitionCost: 31_000,
            currentMarketValue: 34_500,
            quicksellValue: 10_000,
            lockedForCollection: true,
            duplicateCount: 2,
            source: "manual",
            createdAt: Calendar.current.date(byAdding: .day, value: -12, to: now) ?? now,
            updatedAt: Calendar.current.date(byAdding: .day, value: -1, to: now) ?? now,
            totalCostBasis: 93_000,
            unrealizedProfit: 10_500,
            quicksellFloorTotal: 30_000
        )
    ]

    static let portfolioResponse = PortfolioResponse(
        totalPositions: portfolioItems.count,
        totalMarketValue: 215_100,
        totalCostBasis: 186_600,
        totalUnrealizedProfit: 28_500,
        items: portfolioItems
    )

    static let portfolioRecommendations: [PortfolioRecommendation] = [
        PortfolioRecommendation(
            itemId: cards[1].itemId,
            action: .hold,
            confidence: 0.74,
            sellNowScore: 0.36,
            holdScore: 0.81,
            lockScore: 0.18,
            flipOutScore: 0.41,
            portfolioRiskScore: 0.47,
            rationale: "Maintain through the next roster window; selling now leaves too much upgrade EV on the table."
        ),
        PortfolioRecommendation(
            itemId: cards[2].itemId,
            action: .lock,
            confidence: 0.67,
            sellNowScore: 0.42,
            holdScore: 0.58,
            lockScore: 0.71,
            flipOutScore: 0.23,
            portfolioRiskScore: 0.22,
            rationale: "Collection value outweighs the current market premium, especially with duplicates already in inventory."
        )
    ]

    static let grindRecommendation = GrindRecommendation(
        action: .grind,
        bestModeToPlayNow: "Mini Seasons",
        expectedMarketStubsPerHour: 12_400,
        expectedValuePerHourByMode: [
            ModeValue(modeName: "Mini Seasons", expectedValuePerHour: 12_400, rationale: "Best XP-to-pack loop and repeatable boss path."),
            ModeValue(modeName: "Events", expectedValuePerHour: 9_800, rationale: "Competitive but variance-heavy reward timing."),
            ModeValue(modeName: "Ranked", expectedValuePerHour: 8_100, rationale: "Excellent long tail value, slower immediate payout.")
        ],
        packValueEstimate: 4_300,
        rationale: "Grinding is slightly ahead of the live flip board while spreads are compressing."
    )

    static let dashboardSummary = DashboardSummary(
        marketPhase: marketPhase,
        launchWeekAlerts: [
            "Launch supply is still elevated; avoid treating sharp dips as permanent repricing.",
            "High-confidence live series flip windows are clustering around elite diamonds."
        ],
        topFlips: flips,
        topFloorBuys: floors,
        topRosterUpdateTargets: rosterTargets,
        collectionPriorities: collectionPriorities,
        portfolio: portfolioItems,
        topSells: portfolioRecommendations,
        grindRecommendation: grindRecommendation
    )

    static let thresholds = EngineThresholds(
        floorBuyMargin: 0.13,
        launchSupplyCrashThreshold: 0.22,
        flipProfitMinimum: 950,
        grindMarketEdge: 0.12,
        collectionLockPenalty: 0.18,
        gatekeeperHoldWeight: 0.42,
        updatedAt: now
    )

    static let cardDetail = CardDetail(
        itemId: cards[1].itemId,
        name: cards[1].name,
        series: cards[1].series,
        team: cards[1].team,
        division: cards[1].division,
        league: cards[1].league,
        overall: cards[1].overall,
        rarity: cards[1].rarity,
        displayPosition: cards[1].displayPosition,
        isLiveSeries: cards[1].isLiveSeries,
        quicksellValue: cards[1].quicksellValue,
        latestBuyNow: cards[1].latestBuyNow,
        latestSellNow: cards[1].latestSellNow,
        latestBestBuyOrder: cards[1].latestBestBuyOrder,
        latestBestSellOrder: cards[1].latestBestSellOrder,
        latestTaxAdjustedSpread: cards[1].latestTaxAdjustedSpread,
        observedAt: now,
        metadataJson: ["swing": .string("outlier")],
        aggregatePhase: "PRE_ATTRIBUTE_UPDATE",
        avgPrice15m: 6_050,
        avgPrice1h: 5_930,
        avgPrice6h: 5_710,
        avgPrice24h: 5_280,
        volatilityScore: 0.64,
        liquidityScore: 0.81,
        recommendations: [
            RecommendationView(
                recommendationType: .market,
                action: .buy,
                confidence: 0.79,
                expectedProfit: 1_350,
                expectedValue: 0.18,
                marketPhase: .preAttributeUpdate,
                rationale: "Near-floor entry with clean demand support.",
                rationaleJson: ["driver": .string("floor_buy")]
            ),
            RecommendationView(
                recommendationType: .rosterUpdate,
                action: .buy,
                confidence: 0.81,
                expectedProfit: 5_600,
                expectedValue: 0.42,
                marketPhase: .preAttributeUpdate,
                rationale: "Upgrade probability remains above the portfolio hurdle rate.",
                rationaleJson: ["driver": .string("upgrade_window")]
            )
        ]
    )

    static let authSession = AuthSession(
        userID: "preview-user",
        displayName: "Breezy Trader",
        email: "breezy@example.com",
        provider: .mock,
        avatarURL: nil,
        accessToken: "preview-access-token",
        refreshToken: "preview-refresh-token",
        accessTokenExpiresIn: 1800,
        refreshTokenExpiresIn: 2_592_000,
        idToken: "preview-id-token",
        createdAt: now,
        lastSignInAt: now
    )

    static let marketPhases = MarketPhasesResponse(
        current: marketPhase,
        history: [
            MarketPhaseHistoryItem(id: 1, phase: .earlyAccess, phaseStart: Calendar.current.date(byAdding: .day, value: -10, to: now), phaseEnd: Calendar.current.date(byAdding: .day, value: -6, to: now), notes: "Premium scarcity phase."),
            MarketPhaseHistoryItem(id: 2, phase: .fullLaunchSupplyShock, phaseStart: Calendar.current.date(byAdding: .day, value: -5, to: now), phaseEnd: nil, notes: "Main launch flood still in effect.")
        ]
    )
}
