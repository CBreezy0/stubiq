import Foundation

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published private(set) var summary: DashboardSummary?
    @Published private(set) var isLoading = false
    @Published var errorMessage: String?
    @Published private(set) var lastUpdated: Date?

    private let apiClient: APIClienting
    private var autoRefreshTask: Task<Void, Never>?
    private let refreshClock = AutoRefreshClock(interval: .seconds(45))

    init(apiClient: APIClienting) {
        self.apiClient = apiClient
    }

    func load(forceRefresh: Bool = false) async {
        if isLoading && !forceRefresh { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            summary = try await apiClient.fetchDashboardSummary()
            lastUpdated = Date()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func startAutoRefresh() {
        guard autoRefreshTask == nil else { return }
        autoRefreshTask = Task { [weak self] in
            guard let self else { return }
            for await _ in refreshClock.ticker() {
                if Task.isCancelled { return }
                await self.load(forceRefresh: true)
            }
        }
    }

    func stopAutoRefresh() {
        autoRefreshTask?.cancel()
        autoRefreshTask = nil
    }

    deinit {
        autoRefreshTask?.cancel()
    }
}
