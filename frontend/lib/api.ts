import type {
  CollectionPriorityResponse,
  DashboardSummaryResponse,
  EngineThresholdsPatchRequest,
  EngineThresholdsResponse,
  GrindRecommendationResponse,
  ManualAddPayload,
  ManualRemovePayload,
  MarketOpportunityListResponse,
  MarketPhasesResponse,
  PortfolioImportResponse,
  PortfolioRecommendation,
  PortfolioResponse,
  RosterUpdateRecommendationListResponse,
} from '@/lib/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://127.0.0.1:8000';

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(init?.headers ?? {}),
    },
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
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),
  manualAddCard: (payload: ManualAddPayload) =>
    request<PortfolioResponse>('/portfolio/manual-add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: 'manual', ...payload }),
    }),
  manualRemoveCard: (payload: ManualRemovePayload) =>
    request<PortfolioResponse>('/portfolio/manual-remove', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
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

export { API_BASE_URL };
