'use client';

import { CollectionPriorityCard } from '@/components/CollectionPriorityCard';
import { EmptyState } from '@/components/EmptyState';
import { FlipTable } from '@/components/FlipTable';
import { FloorBuyTable } from '@/components/FloorBuyTable';
import { GrindRecommendationCard } from '@/components/GrindRecommendationCard';
import { LoadingState } from '@/components/LoadingState';
import { MarketMoversTable } from '@/components/MarketMoversTable';
import { MarketPhaseBanner } from '@/components/MarketPhaseBanner';
import { MetricCard } from '@/components/MetricCard';
import { RecommendationFeed } from '@/components/RecommendationFeed';
import { RequireAuth } from '@/components/RequireAuth';
import { RosterTargetsTable } from '@/components/RosterTargetsTable';
import { useDashboard } from '@/hooks/useDashboard';
import { formatSignedStubs, formatStubs, marketPhaseLabels } from '@/lib/utils';

function DashboardContent() {
  const {
    phase,
    flips,
    floors,
    rosterTargets,
    collections,
    portfolioRecommendations,
    grindRecommendation,
    inventory,
    trending,
    biggestMovers,
  } = useDashboard();

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
        <MetricCard title="Top Flips" value={String(flips.data?.count ?? 0)} hint="Live ROI-ranked opportunities" />
        <MetricCard title="Inventory Value" value={formatStubs(inventory.data?.total_market_value ?? 0)} hint="Imported binder marked-to-market" />
        <MetricCard title="Inventory P/L" value={formatSignedStubs(inventory.data?.total_profit_loss ?? 0)} hint="Estimated gain/loss on imported cards" />
      </section>

      <section className="grid gap-6 2xl:grid-cols-2">
        <FlipTable title="Top Flips" items={flips.data?.items ?? []} />
        <MarketMoversTable
          title="Trending Cards"
          items={trending.data?.items ?? []}
          emptyTitle="No trending cards yet"
          emptyDescription="StubIQ needs more live price history before trend scores become useful."
        />
      </section>

      <section className="grid gap-6 2xl:grid-cols-2">
        <MarketMoversTable
          title="Biggest Movers"
          items={biggestMovers.data?.items ?? []}
          emptyTitle="No big movers yet"
          emptyDescription="Biggest movers appear once the history cache captures enough price change over time."
        />
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
