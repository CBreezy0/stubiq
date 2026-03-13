import type {
  AuthTokenResponse,
  CollectionPriorityResponse,
  DashboardSummaryResponse,
  EngineThresholdsPatchRequest,
  EngineThresholdsResponse,
  GrindRecommendationResponse,
  LoginPayload,
  ManualAddPayload,
  ManualRemovePayload,
  MarketOpportunityListResponse,
  MarketPhasesResponse,
  PortfolioImportResponse,
  PortfolioRecommendation,
  PortfolioResponse,
  RosterUpdateRecommendationListResponse,
  SignupPayload,
  AuthUser,
} from '@/lib/types';

const DEFAULT_API_BASE_URL = 'https://stubiq-production.up.railway.app';
const API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL).replace(/\/$/, '');
const ACCESS_TOKEN_STORAGE_KEY = 'stubiq.access_token';

type ApiRequestInit = RequestInit & {
  accessToken?: string | null;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function canUseDOM() {
  return typeof window !== 'undefined';
}

export function getStoredAccessToken() {
  if (!canUseDOM()) return null;
  return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
}

export function setStoredAccessToken(token: string) {
  if (!canUseDOM()) return;
  window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
}

export function clearStoredAccessToken() {
  if (!canUseDOM()) return;
  window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
}

async function request<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
  const { accessToken, headers, ...requestInit } = init;
  const requestHeaders = new Headers(headers ?? {});
  requestHeaders.set('Accept', 'application/json');

  const resolvedAccessToken = accessToken ?? getStoredAccessToken();
  if (resolvedAccessToken) {
    requestHeaders.set('Authorization', `Bearer ${resolvedAccessToken}`);
  }

  if (!(requestInit.body instanceof FormData) && requestInit.body && !requestHeaders.has('Content-Type')) {
    requestHeaders.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...requestInit,
    headers: requestHeaders,
    cache: 'no-store',
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload.detail) message = payload.detail;
    } catch {
      const text = await response.text();
      if (text) message = text;
    }
    throw new ApiError(message, response.status);
  }

  return response.json() as Promise<T>;
}

export const api = {
  signup: (payload: SignupPayload) =>
    request<AuthTokenResponse>('/auth/signup', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  login: (payload: LoginPayload) =>
    request<AuthTokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  getMe: (accessToken?: string | null) => request<AuthUser>('/auth/me', { accessToken }),
  getDashboardSummary: () => request<DashboardSummaryResponse>('/dashboard/summary'),
  getMarketPhases: () => request<MarketPhasesResponse>('/market/phases'),
  getFlips: (limit = 10) => request<MarketOpportunityListResponse>(`/market/flips?limit=${limit}`),
  getFloors: (limit = 10) => request<MarketOpportunityListResponse>(`/market/floors?limit=${limit}`),
  getRosterTargets: (limit = 10) => request<RosterUpdateRecommendationListResponse>(`/investments/roster-update?limit=${limit}`),
  getCollectionPriorities: () => request<CollectionPriorityResponse>('/collections/priorities'),
  getPortfolio: () => request<PortfolioResponse>('/portfolio'),
  getPortfolioRecommendations: () => request<PortfolioRecommendation[]>('/portfolio/recommendations'),
  getGrindRecommendation: () => request<GrindRecommendationResponse>('/grind/recommendations'),
  getEngineThresholds: () => request<EngineThresholdsResponse>('/settings/engine-thresholds'),
  patchEngineThresholds: (payload: EngineThresholdsPatchRequest) =>
    request<EngineThresholdsResponse>('/settings/engine-thresholds', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  manualAddCard: (payload: ManualAddPayload) =>
    request<PortfolioResponse>('/portfolio/manual-add', {
      method: 'POST',
      body: JSON.stringify({ source: 'manual', ...payload }),
    }),
  manualRemoveCard: (payload: ManualRemovePayload) =>
    request<PortfolioResponse>('/portfolio/manual-remove', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  importPortfolioCsv: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return request<PortfolioImportResponse>('/portfolio/import', {
      method: 'POST',
      body: formData,
    });
  },
};

export { ACCESS_TOKEN_STORAGE_KEY, API_BASE_URL };
