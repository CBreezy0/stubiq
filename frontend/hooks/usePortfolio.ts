'use client';

import useSWR from 'swr';
import { mutate } from 'swr';

import { api } from '@/lib/api';
import type { ManualAddPayload, ManualRemovePayload } from '@/lib/types';

export function usePortfolio() {
  const portfolio = useSWR('portfolio', () => api.getPortfolio(), { refreshInterval: 60_000 });
  const recommendations = useSWR('portfolio-recommendations', () => api.getPortfolioRecommendations(), {
    refreshInterval: 60_000,
  });

  const refresh = async () => {
    await Promise.all([mutate('portfolio'), mutate('portfolio-recommendations')]);
  };

  return {
    portfolio,
    recommendations,
    addCard: async (payload: ManualAddPayload) => {
      const result = await api.manualAddCard(payload);
      await refresh();
      return result;
    },
    removeCard: async (payload: ManualRemovePayload) => {
      const result = await api.manualRemoveCard(payload);
      await refresh();
      return result;
    },
    importCsv: async (file: File) => {
      const result = await api.importPortfolioCsv(file);
      await refresh();
      return result;
    },
  };
}
