'use client';

import { CollectionPriorityCard } from '@/components/CollectionPriorityCard';
import { EmptyState } from '@/components/EmptyState';
import { FlipTable } from '@/components/FlipTable';
import { FloorBuyTable } from '@/components/FloorBuyTable';
import { GrindRecommendationCard } from '@/components/GrindRecommendationCard';
import { LoadingState } from '@/components/LoadingState';
import { MarketPhaseBanner } from '@/components/MarketPhaseBanner';
import { MetricCard } from '@/components/MetricCard';
import { RecommendationFeed } from '@/components/RecommendationFeed';
import { RequireAuth } from '@/components/RequireAuth';
import { RosterTargetsTable } from '@/components/RosterTargetsTable';
import { useDashboard } from '@/hooks/useDashboard';
import { formatStubs, marketPhaseLabels } from '@/lib/utils';

function DashboardContent() {
  const { phase, flips, floors, rosterTargets, collections, portfolioRecommendations, grindRecommendation, portfolio } = useDashboard();

  if (phase.isLoading && !phase.data) {
    return <LoadingState label="Loading dashboard..." />;
  }

  const topSells = (portfolioRecommendations.data ?? []).filter((item) => item.action === 'SELL').slice(0, 5);
  const phaseLabel = phase.data ? marketPhaseLabels[phase.data.current.phase] : 'Unknown';

  return (
    <div className="space-y-6">
      <MarketPhaseBanner phase={phase.data?.current} />

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard title="Market Phase" value={phaseLabel} hint={phase.data?.current.override_active ? 'Manual override active' : 'Auto-detected'} />
        <MetricCard title="Top Flips" value={String(flips.data?.count ?? 0)} hint="Refreshes every 30 seconds" />
        <MetricCard title="Roster Targets" value={String(rosterTargets.data?.count ?? 0)} hint="Live Series upgrade candidates" />
        <MetricCard title="Portfolio Value" value={formatStubs(portfolio.data?.total_market_value ?? 0)} hint="Current marked-to-market value" />
      </section>

      <section className="grid gap-6 2xl:grid-cols-[1.2fr_0.8fr]">
        <FlipTable title="Top Flips" items={flips.data?.items ?? []} />
        <RecommendationFeed items={topSells} />
      </section>

      <section className="grid gap-6 2xl:grid-cols-2">
        <FloorBuyTable items={floors.data?.items ?? []} />
        <GrindRecommendationCard data={grindRecommendation.data} />
      </section>

      <section className="grid gap-6">
        <RosterTargetsTable items={rosterTargets.data?.items ?? []} />
        <CollectionPriorityCard data={collections.data} error={collections.error as Error | undefined} />
      </section>

      {phase.error && !phase.data ? (
        <EmptyState title="Dashboard data is unavailable" description="The API could not be reached. Verify the deployed backend is healthy and reachable from the configured base URL." />
      ) : null}
    </div>
  );
}

export default function DashboardPage() {
  return (
    <RequireAuth>
      <DashboardContent />
    </RequireAuth>
  );
}
