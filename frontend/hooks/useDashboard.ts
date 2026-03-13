'use client';

import useSWR from 'swr';

import { ACCESS_TOKEN_STORAGE_KEY, API_BASE_URL, api } from '@/lib/api';

type FlipListingsResponse = Awaited<ReturnType<(typeof api)['getFlips']>>;
type DashboardMarketMover = {
  item_id: string;
  name: string;
  best_buy_price?: number | null;
  best_sell_price?: number | null;
  price_change: number;
  change_percent: number;
  liquidity_score?: number | null;
};

type DashboardMarketMoversResponse = {
  count: number;
  items: DashboardMarketMover[];
};

async function getTopFlipsDashboard(): Promise<FlipListingsResponse> {
  const headers = new Headers({ Accept: 'application/json' });
  const accessToken = typeof window === 'undefined' ? null : window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}/flips/top?limit=10&sort_by=profit_per_minute`, {
    headers,
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
    throw new Error(message);
  }

  return response.json() as Promise<FlipListingsResponse>;
}

async function getDashboardMarketMovers(): Promise<DashboardMarketMoversResponse> {
  const headers = new Headers({ Accept: 'application/json' });
  const accessToken = typeof window === 'undefined' ? null : window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  const response = await fetch(`${API_BASE_URL}/market/movers?limit=10`, {
    headers,
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
    throw new Error(message);
  }

  return response.json() as Promise<DashboardMarketMoversResponse>;
}

export function useDashboard() {
  const phase = useSWR('market-phases', () => api.getMarketPhases(), { refreshInterval: 60_000 });
  const topFlips = useSWR('market-top-flips-dashboard', getTopFlipsDashboard, {
    refreshInterval: 30_000,
  });
  const floors = useSWR('market-floors', () => api.getFloors(8), { refreshInterval: 60_000 });
  const rosterTargets = useSWR('roster-targets', () => api.getRosterTargets(8), { refreshInterval: 60_000 });
  const collections = useSWR('collection-priorities', () => api.getCollectionPriorities(), { refreshInterval: 60_000 });
  const portfolioRecommendations = useSWR('portfolio-recommendations', () => api.getPortfolioRecommendations(), {
    refreshInterval: 60_000,
  });
  const grindRecommendation = useSWR('grind-recommendation', () => api.getGrindRecommendation(), { refreshInterval: 60_000 });
  const portfolio = useSWR('portfolio', () => api.getPortfolio(), { refreshInterval: 60_000 });
  const inventory = useSWR('inventory-dashboard', () => api.getInventory(), { refreshInterval: 60_000 });
  const trending = useSWR('market-trending-dashboard', () => api.getTrending(5), { refreshInterval: 60_000 });
  const marketMovers = useSWR('market-movers-dashboard', getDashboardMarketMovers, { refreshInterval: 60_000 });

  return {
    phase,
    topFlips,
    floors,
    rosterTargets,
    collections,
    portfolioRecommendations,
    grindRecommendation,
    portfolio,
    inventory,
    trending,
    marketMovers,
  };
}
