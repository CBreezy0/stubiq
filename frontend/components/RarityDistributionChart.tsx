'use client';

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import type { PortfolioPosition } from '@/lib/types';
import { summarizeRarityDistribution } from '@/lib/utils';

const colors = ['#38bdf8', '#a855f7', '#22c55e', '#f59e0b', '#ef4444', '#94a3b8'];

export function RarityDistributionChart({ positions }: { positions: PortfolioPosition[] }) {
  const data = summarizeRarityDistribution(positions);

  return (
    <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-5 shadow-lg">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white">Rarity Distribution</h3>
        <p className="text-sm text-slate-400">Portfolio composition by card rarity.</p>
      </div>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={90} paddingAngle={4}>
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: '#020617', border: '1px solid #1e293b', borderRadius: 16 }} />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
