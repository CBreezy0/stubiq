'use client';

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import type { PortfolioPosition } from '@/lib/types';
import { formatStubs, summarizePortfolioTrend } from '@/lib/utils';

export function PortfolioTrendChart({ positions }: { positions: PortfolioPosition[] }) {
  const data = summarizePortfolioTrend(positions);

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">Portfolio Value Trend</h3>
        <p className="text-sm text-slate-400">Uses the latest position update timeline until a dedicated historical portfolio endpoint is available.</p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="portfolioValue" x1="0" x2="0" y1="0" y2="1">
                <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.7} />
                <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.05} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1e293b" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip formatter={(value: number) => formatStubs(value)} contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: 16 }} />
            <Area type="monotone" dataKey="value" stroke="#38bdf8" fill="url(#portfolioValue)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
