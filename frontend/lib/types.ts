export type RecommendationAction = 'BUY' | 'SELL' | 'HOLD' | 'LOCK' | 'FLIP' | 'WATCH' | 'IGNORE' | 'GRIND' | 'AVOID';
export type MarketPhase =
  | 'EARLY_ACCESS'
  | 'FULL_LAUNCH_SUPPLY_SHOCK'
  | 'STABILIZATION'
  | 'PRE_ATTRIBUTE_UPDATE'
  | 'POST_ATTRIBUTE_UPDATE'
  | 'CONTENT_DROP'
  | 'STUB_SALE'
  | 'LATE_CYCLE';

export interface CardSummary {
  item_id: string;
  name: string;
  series: string | null;
  team: string | null;
  division: string | null;
  league: string | null;
  overall: number | null;
  rarity: string | null;
  display_position: string | null;
  is_live_series: boolean;
  quicksell_value: number | null;
  latest_buy_now: number | null;
  latest_sell_now: number | null;
  latest_best_buy_order: number | null;
  latest_best_sell_order: number | null;
  latest_tax_adjusted_spread: number | null;
  observed_at: string | null;
}

export interface MarketPhaseResponse {
  phase: MarketPhase;
  confidence: number;
  rationale: string;
  override_active: boolean;
  detected_at: string;
}

export interface MarketPhaseHistoryItem {
  id?: number;
  phase: MarketPhase;
  phase_start?: string | null;
  phase_end?: string | null;
  notes?: string | null;
}

export interface MarketPhasesResponse {
  current: MarketPhaseResponse;
  history: MarketPhaseHistoryItem[];
}

export interface MarketOpportunity {
  item_id: string;
  card: CardSummary;
  action: RecommendationAction;
  expected_profit_per_flip: number | null;
  fill_velocity_score: number;
  liquidity_score: number;
  risk_score: number;
  floor_proximity_score: number;
  market_phase: MarketPhase;
  confidence: number;
  rationale: string;
}

export interface MarketOpportunityListResponse {
  phase: MarketPhase;
  count: number;
  items: MarketOpportunity[];
}

export interface CollectionTarget {
  name: string;
  level: string;
  priority_score: number;
  completion_pct: number;
  remaining_cost: number;
  owned_gatekeeper_value: number;
  reward_value_proxy: number;
  rationale: string;
}

export interface CollectionPriorityResponse {
  market_phase: MarketPhase;
  projected_completion_cost: number;
  ranked_division_targets: CollectionTarget[];
  ranked_team_targets: CollectionTarget[];
  recommended_cards_to_lock: string[];
  recommended_cards_to_delay: string[];
}

export interface PortfolioPosition {
  item_id: string;
  card: CardSummary;
  quantity: number;
  avg_acquisition_cost: number;
  current_market_value: number | null;
  quicksell_value: number | null;
  locked_for_collection: boolean;
  duplicate_count: number;
  source: string | null;
  created_at: string;
  updated_at: string;
  total_cost_basis: number;
  unrealized_profit: number | null;
  quicksell_floor_total: number | null;
}

export interface PortfolioResponse {
  total_positions: number;
  total_market_value: number;
  total_cost_basis: number;
  total_unrealized_profit: number;
  items: PortfolioPosition[];
}

export interface PortfolioRecommendation {
  item_id: string;
  action: RecommendationAction;
  confidence: number;
  sell_now_score: number;
  hold_score: number;
  lock_score: number;
  flip_out_score: number;
  portfolio_risk_score: number;
  rationale: string;
}

export interface PortfolioImportResponse {
  imported_count: number;
  skipped_count: number;
  errors: string[];
}

export interface ManualAddPayload {
  item_id: string;
  card_name: string;
  quantity: number;
  avg_acquisition_cost: number;
  locked_for_collection: boolean;
  source?: string;
}

export interface ManualRemovePayload {
  item_id: string;
  quantity?: number;
  remove_all?: boolean;
}

export interface ModeValueResponse {
  mode_name: string;
  expected_value_per_hour: number;
  rationale: string;
}

export interface GrindRecommendationResponse {
  action: RecommendationAction;
  best_mode_to_play_now: string;
  expected_market_stubs_per_hour: number;
  expected_value_per_hour_by_mode: ModeValueResponse[];
  pack_value_estimate: number;
  rationale: string;
}

export interface RosterUpdateRecommendation {
  item_id: string;
  player_name: string;
  mlb_player_id: number;
  card: CardSummary;
  action: RecommendationAction;
  current_ovr: number;
  current_price: number;
  upgrade_probability: number;
  downgrade_probability: number;
  expected_quicksell_value: number;
  expected_market_value: number;
  expected_profit: number;
  downside_risk: number;
  confidence: number;
  rationale: string;
  rationale_json: Record<string, unknown>;
  generated_at: string | null;
}

export interface RosterUpdateRecommendationListResponse {
  count: number;
  items: RosterUpdateRecommendation[];
}

export interface EngineThresholdsResponse {
  floor_buy_margin: number;
  launch_supply_crash_threshold: number;
  flip_profit_minimum: number;
  grind_market_edge: number;
  collection_lock_penalty: number;
  gatekeeper_hold_weight: number;
  updated_at: string | null;
}

export interface EngineThresholdsPatchRequest {
  floor_buy_margin?: number;
  launch_supply_crash_threshold?: number;
  flip_profit_minimum?: number;
  grind_market_edge?: number;
  collection_lock_penalty?: number;
  gatekeeper_hold_weight?: number;
}

export interface DashboardSummaryResponse {
  market_phase: MarketPhaseResponse;
  launch_week_alerts: string[];
  top_flips: MarketOpportunity[];
  top_floor_buys: MarketOpportunity[];
  top_roster_update_targets: RosterUpdateRecommendation[];
  collection_priorities: CollectionPriorityResponse;
  portfolio: PortfolioPosition[];
  top_sells: PortfolioRecommendation[];
  grind_recommendation: GrindRecommendationResponse;
}

export interface ApiErrorPayload {
  detail?: string;
}
