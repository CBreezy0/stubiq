'use client';

import useSWR from 'swr';

import { api } from '@/lib/api';

export function useDashboard() {
  const phase = useSWR('market-phases', () => api.getMarketPhases(), { refreshInterval: 60_000 });
  const flips = useSWR('market-flips-dashboard', () => api.getFlips({ limit: 5, sort_by: 'roi', sort_order: 'desc' }), {
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
  const biggestMovers = useSWR('market-biggest-movers-dashboard', () => api.getBiggestMovers(5), { refreshInterval: 60_000 });

  return {
    phase,
    flips,
    floors,
    rosterTargets,
    collections,
    portfolioRecommendations,
    grindRecommendation,
    portfolio,
    inventory,
    trending,
    biggestMovers,
  };
}
