'use client';

import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import type { PriceHistoryPoint } from '@/lib/types';
import { buildPriceHistorySeries, formatPercent, formatStubs } from '@/lib/utils';

interface PriceHistoryChartProps {
  title: string;
  points: PriceHistoryPoint[];
  metric: 'price' | 'roi';
}

export function PriceHistoryChart({ title, points, metric }: PriceHistoryChartProps) {
  const data = buildPriceHistorySeries(points);
  const lineKey = metric === 'price' ? 'sellPrice' : 'roi';
  const lineColor = metric === 'price' ? '#38bdf8' : '#34d399';

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="text-sm text-slate-400">
          {metric === 'price' ? 'Tracks sell-side market pricing over the selected range.' : 'Estimated after-tax ROI based on each historical buy/sell pair.'}
        </p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="#1e293b" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} minTickGap={18} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: 16 }}
              formatter={(value) => {
                const normalized = typeof value === 'number' ? value : Number(value);
                return metric === 'price' ? formatStubs(Number.isFinite(normalized) ? normalized : null) : formatPercent(Number.isFinite(normalized) ? normalized : null);
              }}
            />
            <Line type="monotone" dataKey={lineKey} stroke={lineColor} strokeWidth={2.5} dot={false} connectNulls />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
