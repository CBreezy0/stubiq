'use client';

import useSWR from 'swr';

import { api } from '@/lib/api';
import type { EngineThresholdsPatchRequest } from '@/lib/types';

export function useEngineThresholds() {
  const state = useSWR('engine-thresholds', () => api.getEngineThresholds());

  return {
    ...state,
    save: async (payload: EngineThresholdsPatchRequest) => {
      const result = await api.patchEngineThresholds(payload);
      await state.mutate(result, { revalidate: false });
      return result;
    },
  };
}
