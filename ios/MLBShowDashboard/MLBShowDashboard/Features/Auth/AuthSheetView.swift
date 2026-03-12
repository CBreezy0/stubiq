import AuthenticationServices
import SwiftUI

struct AuthSheetView: View {
    @Environment(\.dismiss) private var dismiss
    @EnvironmentObject private var themeManager: ThemeManager
    @ObservedObject private var authManager: AuthManager
    @StateObject private var viewModel: AuthViewModel
    @State private var isShowingForgotPassword = false

    let mode: AuthFormMode

    init(mode: AuthFormMode, authManager: AuthManager) {
        self.mode = mode
        self.authManager = authManager
        _viewModel = StateObject(wrappedValue: AuthViewModel(mode: mode, authManager: authManager))
    }

    var body: some View {
        NavigationStack {
            ZStack {
                AppBackgroundView()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 20) {
                        GlassCard {
                            VStack(alignment: .leading, spacing: 16) {
                                Text(mode.title)
                                    .font(.largeTitle.weight(.bold))

                                if mode == .signUp {
                                    field("Display name", text: $viewModel.displayName)
                                }
                                field("Email", text: $viewModel.email, keyboard: .emailAddress)
                                if mode != .forgotPassword {
                                    secureField("Password", text: $viewModel.password)
                                }
                                if mode == .signUp {
                                    secureField("Confirm password", text: $viewModel.confirmPassword)
                                }

                                if let errorMessage = viewModel.errorMessage {
                                    Text(errorMessage)
                                        .font(.caption)
                                        .foregroundStyle(themeManager.palette.danger)
                                }
                                if let successMessage = viewModel.successMessage {
                                    Text(successMessage)
                                        .font(.caption)
                                        .foregroundStyle(themeManager.palette.success)
                                }

                                Button {
                                    Task {
                                        await viewModel.submit()
                                        if authManager.isAuthenticated, mode != .forgotPassword {
                                            dismiss()
                                        }
                                    }
                                } label: {
                                    if viewModel.isSubmitting {
                                        ProgressView()
                                            .tint(.black.opacity(0.82))
                                    } else {
                                        Text(mode == .forgotPassword ? "Send reset link" : mode.title)
                                    }
                                }
                                .buttonStyle(GlowButtonStyle(filled: true))
                                .disabled(viewModel.isSubmitting)

                                if mode != .forgotPassword {
                                    SignInWithAppleButton(.signIn) { request in
                                        request.requestedScopes = [.fullName, .email]
                                    } onCompletion: { result in
                                        Task {
                                            await viewModel.signInWithApple(result: result)
                                            if authManager.isAuthenticated {
                                                dismiss()
                                            }
                                        }
                                    }
                                    .signInWithAppleButtonStyle(.white)
                                    .frame(height: 52)
                                    .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                                    .disabled(viewModel.isSubmitting)
                                }

                                if mode != .forgotPassword, authManager.supportsGoogleSignIn {
                                    Button {
                                        Task {
                                            await viewModel.signInWithGoogle()
                                            if authManager.isAuthenticated {
                                                dismiss()
                                            }
                                        }
                                    } label: {
                                        Text("Continue with Google")
                                    }
                                    .buttonStyle(GlowButtonStyle(filled: false))
                                    .disabled(viewModel.isSubmitting)
                                }

                                if mode == .signIn {
                                    Button("Forgot password?") {
                                        isShowingForgotPassword = true
                                    }
                                    .font(.subheadline.weight(.semibold))
                                    .foregroundStyle(themeManager.palette.accent)
                                }
                            }
                        }
                    }
                    .padding(20)
                }
            }
            .navigationTitle(mode.title)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") {
                        dismiss()
                    }
                }
            }
            .sheet(isPresented: $isShowingForgotPassword) {
                AuthSheetView(mode: .forgotPassword, authManager: authManager)
                    .environmentObject(themeManager)
            }
        }
    }

    private func field(_ title: String, text: Binding<String>, keyboard: UIKeyboardType = .default) -> some View {
        TextField(title, text: text)
            .textInputAutocapitalization(.never)
            .keyboardType(keyboard)
            .autocorrectionDisabled(true)
            .padding(14)
            .background(themeManager.palette.surfaceSecondary, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }

    private func secureField(_ title: String, text: Binding<String>) -> some View {
        SecureField(title, text: text)
            .textInputAutocapitalization(.never)
            .padding(14)
            .background(themeManager.palette.surfaceSecondary, in: RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

#Preview {
    PreviewHost(authenticated: false) {
        AuthSheetView(mode: .signIn, authManager: AuthManager(provider: MockAuthProvider(), environmentManager: EnvironmentManager(userDefaults: .previewDefaults), sessionStore: InMemorySessionStore()))
    }
}
