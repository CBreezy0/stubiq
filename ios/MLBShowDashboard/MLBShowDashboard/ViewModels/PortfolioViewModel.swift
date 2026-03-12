import Foundation

@MainActor
final class PortfolioViewModel: ObservableObject {
    @Published private(set) var portfolio: PortfolioResponse?
    @Published private(set) var recommendations: [PortfolioRecommendation] = []
    @Published private(set) var isLoading = false
    @Published private(set) var isSaving = false
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
            async let portfolioResponse = apiClient.fetchPortfolio()
            async let recommendationResponse = apiClient.fetchPortfolioRecommendations()
            portfolio = try await portfolioResponse
            recommendations = try await recommendationResponse
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func addPosition(_ payload: ManualAddRequest) async -> Bool {
        isSaving = true
        defer { isSaving = false }
        do {
            portfolio = try await apiClient.manualAddCard(payload)
            recommendations = try await apiClient.fetchPortfolioRecommendations()
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func removePosition(itemId: String, quantity: Int? = nil, removeAll: Bool = false) async -> Bool {
        isSaving = true
        defer { isSaving = false }
        do {
            portfolio = try await apiClient.manualRemoveCard(ManualRemoveRequest(itemId: itemId, quantity: quantity, removeAll: removeAll))
            recommendations = try await apiClient.fetchPortfolioRecommendations()
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func recommendation(for itemId: String) -> PortfolioRecommendation? {
        recommendations.first(where: { $0.itemId == itemId })
    }
}
