import AuthenticationServices
import Foundation

struct OnboardingPage: Identifiable, Hashable {
    let id = UUID()
    let title: String
    let message: String
    let symbol: String
}

@MainActor
final class OnboardingViewModel: ObservableObject {
    @Published var currentPage = 0

    let pages: [OnboardingPage] = [
        OnboardingPage(
            title: "See the market instantly",
            message: "Track flips, roster investments, and collection strategy in real time.",
            symbol: "chart.line.uptrend.xyaxis"
        ),
        OnboardingPage(
            title: "Trade with confidence",
            message: "Find floor buys, high-liquidity flips, and upgrade windows with clean explanations.",
            symbol: "sparkles.rectangle.stack"
        ),
        OnboardingPage(
            title: "Manage the full portfolio",
            message: "Stay synced across investments, collections, thresholds, and console connection status.",
            symbol: "briefcase.circle"
        )
    ]
}

@MainActor
final class AuthViewModel: ObservableObject {
    @Published var displayName = ""
    @Published var email = ""
    @Published var password = ""
    @Published var confirmPassword = ""
    @Published var isSubmitting = false
    @Published var errorMessage: String?
    @Published var successMessage: String?

    let mode: AuthFormMode
    private let authManager: AuthManager

    init(mode: AuthFormMode, authManager: AuthManager) {
        self.mode = mode
        self.authManager = authManager
    }

    func submit() async {
        errorMessage = nil
        successMessage = nil

        guard validate() else { return }
        isSubmitting = true
        defer { isSubmitting = false }

        do {
            switch mode {
            case .signIn:
                try await authManager.signIn(email: email.trimmed, password: password)
            case .signUp:
                try await authManager.signUp(email: email.trimmed, password: password, displayName: displayName.trimmed)
            case .forgotPassword:
                try await authManager.sendPasswordReset(email: email.trimmed)
                successMessage = "Password reset is currently a placeholder flow. If email reset support is enabled later, this is where it will be triggered."
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func signInWithGoogle() async {
        errorMessage = nil
        isSubmitting = true
        defer { isSubmitting = false }
        do {
            try await authManager.signInWithGoogle()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func signInWithApple(result: Result<ASAuthorization, Error>) async {
        errorMessage = nil
        isSubmitting = true
        defer { isSubmitting = false }
        do {
            switch result {
            case .success(let authorization):
                try await authManager.signInWithApple(authorization: authorization)
            case .failure(let error):
                throw error
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func validate() -> Bool {
        guard !email.trimmed.isEmpty else {
            errorMessage = "Email is required."
            return false
        }

        switch mode {
        case .signIn:
            guard !password.isEmpty else {
                errorMessage = "Password is required."
                return false
            }
        case .signUp:
            guard !password.isEmpty else {
                errorMessage = "Password is required."
                return false
            }
            guard password.count >= 6 else {
                errorMessage = "Use at least 6 characters for the password."
                return false
            }
            guard password == confirmPassword else {
                errorMessage = "Passwords do not match."
                return false
            }
        case .forgotPassword:
            break
        }

        return true
    }
}
