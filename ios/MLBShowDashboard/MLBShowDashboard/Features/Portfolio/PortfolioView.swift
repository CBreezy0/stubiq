import SwiftUI

struct PortfolioScreen: View {
    @StateObject private var viewModel: PortfolioViewModel
    @EnvironmentObject private var appState: AppState
    @State private var isPresentingAddSheet = false

    init(apiClient: APIClienting) {
        _viewModel = StateObject(wrappedValue: PortfolioViewModel(apiClient: apiClient))
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 16) {
                    if let portfolio = viewModel.portfolio {
                        summary(portfolio)

                        if portfolio.items.isEmpty {
                            EmptyStateView(symbol: "tray", title: "No holdings tracked", message: "Add cards manually to start monitoring your portfolio.")
                        } else {
                            ForEach(portfolio.items) { position in
                                NavigationLink {
                                    CardDetailView(itemId: position.itemId, apiClient: appState.apiClient, portfolioRecommendation: viewModel.recommendation(for: position.itemId))
                                } label: {
                                    PortfolioHoldingRowView(position: position, recommendation: viewModel.recommendation(for: position.itemId))
                                }
                                .buttonStyle(.plain)
                                .contextMenu {
                                    Button("Remove 1") {
                                        Task {
                                            _ = await viewModel.removePosition(itemId: position.itemId, quantity: 1, removeAll: false)
                                        }
                                    }
                                    Button("Remove All", role: .destructive) {
                                        Task {
                                            _ = await viewModel.removePosition(itemId: position.itemId, removeAll: true)
                                        }
                                    }
                                }
                            }
                        }
                    } else if viewModel.isLoading {
                        LoadingStateView(rows: 4)
                    } else {
                        EmptyStateView(symbol: "briefcase", title: "Portfolio unavailable", message: viewModel.errorMessage ?? "Connect to the backend to load your positions.")
                    }
                }
                .padding(20)
            }
            .navigationTitle("Portfolio")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        isPresentingAddSheet = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                    }
                }
            }
            .refreshable {
                await viewModel.load()
            }
            .task {
                await viewModel.load()
            }
        }
        .sheet(isPresented: $isPresentingAddSheet) {
            ManualPositionSheet { payload in
                let success = await viewModel.addPosition(payload)
                if success {
                    isPresentingAddSheet = false
                }
            }
        }
    }

    private func summary(_ portfolio: PortfolioResponse) -> some View {
        VStack(spacing: 14) {
            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 14) {
                MetricCardView(title: "Total Value", value: AppFormatter.stubs(portfolio.totalMarketValue), subtitle: "Current market value", systemImage: "chart.bar.fill", trend: AppFormatter.signedStubs(Double(portfolio.totalUnrealizedProfit)), highlight: true)
                MetricCardView(title: "Invested", value: AppFormatter.stubs(portfolio.totalCostBasis), subtitle: "Cost basis", systemImage: "dollarsign.circle")
                MetricCardView(title: "P/L", value: AppFormatter.signedStubs(Double(portfolio.totalUnrealizedProfit)), subtitle: "Unrealized gain/loss", systemImage: "arrow.up.right.circle")
                MetricCardView(title: "Holdings", value: String(portfolio.totalPositions), subtitle: "Tracked cards", systemImage: "square.stack.3d.up")
            }

            ChartCard(title: "Trend", subtitle: "Derived from current holdings updates") {
                if portfolio.items.trendPoints.isEmpty {
                    EmptyStateView(symbol: "chart.line.uptrend.xyaxis", title: "No trend data", message: "Add positions to generate a live portfolio curve.")
                } else {
                    ValueBarChartView(points: portfolio.items.trendPoints)
                }
            }
        }
    }
}

private struct ManualPositionSheet: View {
    @Environment(\.dismiss) private var dismiss
    @State private var itemId = ""
    @State private var cardName = ""
    @State private var quantity = "1"
    @State private var avgCost = ""
    @State private var lockedForCollection = false
    let onSave: (ManualAddRequest) async -> Void

    var body: some View {
        NavigationStack {
            Form {
                Section("Card") {
                    TextField("Item ID", text: $itemId)
                    TextField("Card name", text: $cardName)
                }

                Section("Position") {
                    TextField("Quantity", text: $quantity)
                        .keyboardType(.numberPad)
                    TextField("Average acquisition cost", text: $avgCost)
                        .keyboardType(.numberPad)
                    Toggle("Locked for collection", isOn: $lockedForCollection)
                }
            }
            .navigationTitle("Add Position")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Save") {
                        guard let parsedQuantity = Int(quantity), let parsedCost = Int(avgCost) else { return }
                        Task {
                            await onSave(ManualAddRequest(itemId: itemId.trimmed, cardName: cardName.trimmed, quantity: parsedQuantity, avgAcquisitionCost: parsedCost, lockedForCollection: lockedForCollection))
                        }
                    }
                    .disabled(itemId.trimmed.isEmpty || cardName.trimmed.isEmpty || Int(quantity) == nil || Int(avgCost) == nil)
                }
            }
        }
    }
}

#Preview {
    PreviewHost {
        PortfolioScreen(apiClient: MockAPIClient())
    }
}
