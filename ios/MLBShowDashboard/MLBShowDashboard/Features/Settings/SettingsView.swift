import SwiftUI

struct SettingsScreen: View {
    @StateObject private var viewModel: SettingsViewModel
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var themeManager: ThemeManager
    @EnvironmentObject private var environmentManager: EnvironmentManager
    @EnvironmentObject private var connectionManager: ConnectionManager
    @State private var isRevokingSessions = false

    init(apiClient: APIClienting) {
        _viewModel = StateObject(wrappedValue: SettingsViewModel(apiClient: apiClient))
    }

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(spacing: 16) {
                    backendSection
                    themeSection
                    thresholdsSection
                    accountSection
                    accountSecuritySection
                    connectionSection
                }
                .padding(20)
            }
            .navigationTitle("Settings")
            .task {
                await viewModel.load()
            }
            .alert(item: $viewModel.alert) { alert in
                Alert(title: Text(alert.title), message: Text(alert.message), dismissButton: .default(Text("OK")))
            }
        }
    }

    private var backendSection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Backend", subtitle: "Swap local and production API targets quickly.")
                Picker("Environment", selection: $environmentManager.selectedEnvironment) {
                    ForEach(BackendEnvironment.allCases) { environment in
                        Text(environment.title).tag(environment)
                    }
                }
                .pickerStyle(.segmented)

                if environmentManager.selectedEnvironment == .custom {
                    TextField("https://api.example.com", text: $environmentManager.customBaseURLString)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled(true)
                        .padding(14)
                        .background(themeManager.palette.surfaceSecondary, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
                }

                Text(environmentManager.currentBaseURL.absoluteString)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var themeSection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Theme", subtitle: "Choose the accent system for the app.")
                Picker("Theme", selection: $themeManager.selectedTheme) {
                    ForEach(AppTheme.allCases) { theme in
                        Text(theme.title).tag(theme)
                    }
                }
                .pickerStyle(.segmented)
            }
        }
    }

    private var thresholdsSection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Engine Thresholds", subtitle: "Live tuning values from the backend.")
                thresholdField("floor_buy_margin", text: $viewModel.draft.floorBuyMargin)
                thresholdField("launch_supply_crash_threshold", text: $viewModel.draft.launchSupplyCrashThreshold)
                thresholdField("flip_profit_minimum", text: $viewModel.draft.flipProfitMinimum)
                thresholdField("grind_market_edge", text: $viewModel.draft.grindMarketEdge)
                thresholdField("collection_lock_penalty", text: $viewModel.draft.collectionLockPenalty)
                thresholdField("gatekeeper_hold_weight", text: $viewModel.draft.gatekeeperHoldWeight)

                Button {
                    Task { await viewModel.save() }
                } label: {
                    if viewModel.isSaving {
                        ProgressView()
                            .tint(.black.opacity(0.82))
                    } else {
                        Text("Save thresholds")
                    }
                }
                .buttonStyle(GlowButtonStyle(filled: true))
                .disabled(viewModel.isSaving)
            }
        }
    }

    private var accountSection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Account", subtitle: "Session and provider details")
                Text(authManager.currentUserName)
                    .font(.headline)
                if let email = authManager.currentUserEmail {
                    Text(email)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                Text("Provider: \(authManager.providerDisplayName)")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
    }

    private var accountSecuritySection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Account Security", subtitle: "Manage active sessions and connected consoles")

                securityRow(title: "Email", value: authManager.currentUserEmail ?? "—")
                securityRow(title: "Auth Provider", value: authManager.providerDisplayName)
                securityRow(title: "Connected Consoles", value: connectedConsoleSummary)

                Button {
                    Task {
                        isRevokingSessions = true
                        defer { isRevokingSessions = false }
                        do {
                            let revokedCount = try await authManager.revokeSessions()
                            viewModel.alert = AlertMessage(
                                title: "Sessions Revoked",
                                message: "Revoked \(revokedCount) active refresh token sessions. This device will stay signed in until its current access token expires."
                            )
                        } catch {
                            viewModel.alert = AlertMessage(title: "Revoke Failed", message: error.localizedDescription)
                        }
                    }
                } label: {
                    HStack {
                        if isRevokingSessions {
                            ProgressView()
                                .tint(.black.opacity(0.82))
                        }
                        Text("Revoke sessions")
                    }
                }
                .buttonStyle(GlowButtonStyle(filled: true))
                .disabled(isRevokingSessions)

                Button(role: .destructive) {
                    Task { await authManager.signOut() }
                } label: {
                    Text("Sign out")
                }
                .buttonStyle(GlowButtonStyle(filled: false))
            }
        }
    }

    private var connectionSection: some View {
        GlassCard {
            VStack(alignment: .leading, spacing: 12) {
                SectionHeaderView(title: "Console Connections", subtitle: "Xbox and PlayStation status")
                ForEach(ConnectionProviderKind.allCases) { provider in
                    let connection = connectionManager.connection(for: provider)
                    HStack {
                        Text(provider.title)
                            .font(.subheadline.weight(.semibold))
                        Spacer()
                        StatusBadgeView(text: connection.status.rawValue, tone: connection.status == .connected ? .success : .neutral)
                    }
                }

                NavigationLink(destination: ConnectionsView(connectionManager: connectionManager).environmentObject(connectionManager)) {
                    Text("Manage connections")
                }
                .buttonStyle(GlowButtonStyle(filled: false))
            }
        }
    }

    private func thresholdField(_ title: String, text: Binding<String>) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.caption.weight(.medium))
                .foregroundStyle(.secondary)
            TextField(title, text: text)
                .keyboardType(.decimalPad)
                .padding(14)
                .background(themeManager.palette.surfaceSecondary, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
    }

    private func securityRow(title: String, value: String) -> some View {
        HStack(alignment: .firstTextBaseline) {
            Text(title)
                .font(.caption.weight(.medium))
                .foregroundStyle(.secondary)
            Spacer()
            Text(value)
                .font(.subheadline.weight(.semibold))
                .multilineTextAlignment(.trailing)
        }
    }

    private var connectedConsoleSummary: String {
        let connected = ConnectionProviderKind.allCases.filter { connectionManager.connection(for: $0).status == .connected }
        if connected.isEmpty {
            return "None"
        }
        return connected.map(\.title).joined(separator: ", ")
    }
}

#Preview {
    PreviewHost {
        SettingsScreen(apiClient: MockAPIClient())
    }
}
