import Foundation

@MainActor
final class CollectionsViewModel: ObservableObject {
    @Published private(set) var priorities: CollectionPriorityResponse?
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
            priorities = try await apiClient.fetchCollectionPriorities()
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}

struct EngineThresholdsDraft {
    var floorBuyMargin = ""
    var launchSupplyCrashThreshold = ""
    var flipProfitMinimum = ""
    var grindMarketEdge = ""
    var collectionLockPenalty = ""
    var gatekeeperHoldWeight = ""

    init() {}

    init(thresholds: EngineThresholds) {
        floorBuyMargin = String(format: "%.2f", thresholds.floorBuyMargin)
        launchSupplyCrashThreshold = String(format: "%.2f", thresholds.launchSupplyCrashThreshold)
        flipProfitMinimum = String(format: "%.0f", thresholds.flipProfitMinimum)
        grindMarketEdge = String(format: "%.2f", thresholds.grindMarketEdge)
        collectionLockPenalty = String(format: "%.2f", thresholds.collectionLockPenalty)
        gatekeeperHoldWeight = String(format: "%.2f", thresholds.gatekeeperHoldWeight)
    }

    var payload: EngineThresholdsPatchRequest {
        EngineThresholdsPatchRequest(
            floorBuyMargin: Double(floorBuyMargin),
            launchSupplyCrashThreshold: Double(launchSupplyCrashThreshold),
            flipProfitMinimum: Double(flipProfitMinimum),
            grindMarketEdge: Double(grindMarketEdge),
            collectionLockPenalty: Double(collectionLockPenalty),
            gatekeeperHoldWeight: Double(gatekeeperHoldWeight)
        )
    }
}

@MainActor
final class SettingsViewModel: ObservableObject {
    @Published private(set) var thresholds: EngineThresholds?
    @Published private(set) var isLoading = false
    @Published private(set) var isSaving = false
    @Published var draft = EngineThresholdsDraft()
    @Published var alert: AlertMessage?

    private let apiClient: APIClienting

    init(apiClient: APIClienting) {
        self.apiClient = apiClient
    }

    func load() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let response = try await apiClient.fetchEngineThresholds()
            thresholds = response
            draft = EngineThresholdsDraft(thresholds: response)
        } catch {
            alert = AlertMessage(title: "Load Failed", message: error.localizedDescription)
        }
    }

    func save() async {
        isSaving = true
        defer { isSaving = false }

        do {
            let updated = try await apiClient.patchEngineThresholds(draft.payload)
            thresholds = updated
            draft = EngineThresholdsDraft(thresholds: updated)
            alert = AlertMessage(title: "Saved", message: "Engine thresholds were updated successfully.")
        } catch {
            alert = AlertMessage(title: "Save Failed", message: error.localizedDescription)
        }
    }
}
