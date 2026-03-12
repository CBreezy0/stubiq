import AuthenticationServices
import SwiftUI

struct AuthEntryView: View {
    @EnvironmentObject private var appState: AppState
    @EnvironmentObject private var authManager: AuthManager
    @EnvironmentObject private var themeManager: ThemeManager
    @StateObject private var onboardingViewModel = OnboardingViewModel()

    let showPager: Bool

    @State private var activeSheet: AuthFormMode?
    @State private var localError: String?
    @State private var isGoogleLoading = false
    @State private var isAppleLoading = false

    var body: some View {
        let palette = themeManager.palette

        ScrollView(showsIndicators: false) {
            VStack(spacing: 24) {
                Spacer(minLength: 24)

                GlassCard {
                    VStack(alignment: .leading, spacing: 18) {
                        HStack {
                            ZStack {
                                RoundedRectangle(cornerRadius: 20, style: .continuous)
                                    .fill(
                                        LinearGradient(
                                            colors: [palette.accent, palette.accentSecondary],
                                            startPoint: .topLeading,
                                            endPoint: .bottomTrailing
                                        )
                                    )
                                    .frame(width: 64, height: 64)
                                Image(systemName: "waveform.path.ecg.rectangle.fill")
                                    .font(.system(size: 28, weight: .bold))
                                    .foregroundStyle(.black.opacity(0.82))
                            }
                            Spacer()
                            StatusBadgeView(text: "Live Market", tone: .accent)
                        }

                        VStack(alignment: .leading, spacing: 10) {
                            Text("Show Intel")
                                .font(.system(size: 34, weight: .bold, design: .rounded))
                                .foregroundStyle(palette.textPrimary)
                            Text("Track flips, roster investments, and collection strategy in real time.")
                                .font(.subheadline)
                                .foregroundStyle(palette.textSecondary)
                        }
                    }
                }

                if showPager {
                    TabView(selection: $onboardingViewModel.currentPage) {
                        ForEach(Array(onboardingViewModel.pages.enumerated()), id: \.offset) { index, page in
                            GlassCard {
                                VStack(spacing: 14) {
                                    Image(systemName: page.symbol)
                                        .font(.system(size: 28, weight: .semibold))
                                        .foregroundStyle(palette.accent)
                                    Text(page.title)
                                        .font(.title3.weight(.semibold))
                                        .foregroundStyle(palette.textPrimary)
                                    Text(page.message)
                                        .font(.subheadline)
                                        .foregroundStyle(palette.textSecondary)
                                        .multilineTextAlignment(.center)
                                }
                                .frame(maxWidth: .infinity, minHeight: 180)
                            }
                            .tag(index)
                            .padding(.horizontal, 4)
                        }
                    }
                    .tabViewStyle(.page(indexDisplayMode: .never))
                    .frame(height: 220)

                    HStack(spacing: 8) {
                        ForEach(onboardingViewModel.pages.indices, id: \.self) { index in
                            Capsule()
                                .fill(index == onboardingViewModel.currentPage ? palette.accent : palette.surfaceSecondary)
                                .frame(width: index == onboardingViewModel.currentPage ? 26 : 8, height: 8)
                                .animation(.spring(response: 0.25, dampingFraction: 0.8), value: onboardingViewModel.currentPage)
                        }
                    }
                }

                VStack(spacing: 12) {
                    SignInWithAppleButton(.signIn) { request in
                        request.requestedScopes = [.fullName, .email]
                    } onCompletion: { result in
                        appState.completeOnboarding()
                        Task {
                            isAppleLoading = true
                            defer { isAppleLoading = false }
                            do {
                                switch result {
                                case .success(let authorization):
                                    try await authManager.signInWithApple(authorization: authorization)
                                case .failure(let error):
                                    throw error
                                }
                            } catch {
                                localError = error.localizedDescription
                            }
                        }
                    }
                    .signInWithAppleButtonStyle(.white)
                    .frame(height: 54)
                    .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                    .overlay(alignment: .trailing) {
                        if isAppleLoading {
                            ProgressView()
                                .tint(.black.opacity(0.82))
                                .padding(.trailing, 18)
                        }
                    }
                    .disabled(isAppleLoading || isGoogleLoading)

                    Button {
                        appState.completeOnboarding()
                        Task {
                            isGoogleLoading = true
                            do {
                                try await authManager.signInWithGoogle()
                            } catch {
                                localError = error.localizedDescription
                            }
                            isGoogleLoading = false
                        }
                    } label: {
                        HStack {
                            if isGoogleLoading {
                                ProgressView()
                                    .tint(.black.opacity(0.82))
                            } else {
                                Image(systemName: "globe")
                            }
                            Text("Sign in with Google")
                        }
                    }
                    .buttonStyle(GlowButtonStyle(filled: true))
                    .disabled(isGoogleLoading || isAppleLoading)

                    Button {
                        appState.completeOnboarding()
                        activeSheet = .signUp
                    } label: {
                        Text("Create account")
                    }
                    .buttonStyle(GlowButtonStyle(filled: false))

                    Button {
                        appState.completeOnboarding()
                        activeSheet = .signIn
                    } label: {
                        Text("Sign in")
                    }
                    .buttonStyle(GlowButtonStyle(filled: false))
                }
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 30)
        }
        .sheet(item: $activeSheet) { mode in
            AuthSheetView(mode: mode, authManager: authManager)
                .environmentObject(themeManager)
        }
        .alert("Authentication", isPresented: Binding(
            get: { localError != nil },
            set: { if !$0 { localError = nil } }
        )) {
            Button("OK", role: .cancel) {}
        } message: {
            Text(localError ?? "")
        }
    }
}

#Preview {
    PreviewHost(authenticated: false) {
        AuthEntryView(showPager: true)
    }
}
