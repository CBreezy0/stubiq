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
export type AuthProvider = 'email' | 'google' | 'apple';
export type MarketSortField = 'profit' | 'roi' | 'spread' | 'flip_score' | 'name' | 'buy_price' | 'sell_price' | 'order_volume' | 'last_seen';
export type SortOrder = 'asc' | 'desc';

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

export interface CardRecommendation {
  recommendation_type: string;
  action: RecommendationAction;
  confidence: number;
  expected_profit: number | null;
  expected_value: number | null;
  market_phase: MarketPhase;
  rationale: string;
  rationale_json: Record<string, unknown>;
}

export interface CardDetailResponse extends CardSummary {
  metadata_json: Record<string, unknown>;
  aggregate_phase: string | null;
  avg_price_15m: number | null;
  avg_price_1h: number | null;
  avg_price_6h: number | null;
  avg_price_24h: number | null;
  volatility_score: number | null;
  liquidity_score: number | null;
  recommendations: CardRecommendation[];
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

export interface MarketListing {
  uuid: string;
  name: string;
  best_buy_price: number | null;
  best_sell_price: number | null;
  spread: number | null;
  profit_after_tax: number | null;
  roi: number | null;
  position: string | null;
  series: string | null;
  team: string | null;
  overall: number | null;
  rarity: string | null;
  order_volume: number;
  flip_score: number | null;
  last_seen_at: string;
}

export type LiveMarketListing = MarketListing;
export type FlipOpportunity = MarketListing;

export interface LiveMarketListingListResponse {
  count: number;
  items: MarketListing[];
}

export interface MarketListingsQuery {
  min_roi?: number | null;
  min_profit?: number | null;
  max_buy_price?: number | null;
  rarity?: string | null;
  series?: string | null;
  team?: string | null;
  position?: string | null;
  sort_by?: MarketSortField | null;
  sort_order?: SortOrder | null;
  limit?: number | null;
  refresh?: boolean | null;
}

export interface PriceHistoryPoint {
  timestamp: string;
  buy_price: number | null;
  sell_price: number | null;
}

export interface PriceHistoryResponse {
  uuid: string;
  name: string | null;
  days: number;
  points: PriceHistoryPoint[];
}

export interface MarketMover {
  uuid: string;
  name: string;
  current_price: number | null;
  previous_price: number | null;
  change_amount: number | null;
  change_pct: number | null;
  trend_score: number;
  position: string | null;
  series: string | null;
  team: string | null;
  rarity: string | null;
  points: number;
  last_seen_at: string | null;
}

export interface MarketMoverListResponse {
  count: number;
  items: MarketMover[];
}

export interface MetadataResponse {
  series: Array<Record<string, unknown>>;
  brands: Array<Record<string, unknown>>;
  sets: unknown[];
  fetched_at: string | null;
}

export interface PlayerSearchProfile {
  username: string;
  display_level: string | null;
  games_played: number | null;
  vanity_json: Record<string, unknown>;
  most_played_modes_json: Record<string, unknown>;
  lifetime_hitting_stats_json: Array<Record<string, unknown>>;
  lifetime_defensive_stats_json: Array<Record<string, unknown>>;
  online_data_json: Array<Record<string, unknown>>;
  last_synced_at: string;
}

export interface PlayerSearchResponse {
  count: number;
  items: PlayerSearchProfile[];
}

export interface ShowRosterUpdateItem {
  remote_id: string;
  title: string | null;
  summary: string | null;
  published_at: string | null;
  last_synced_at: string;
}

export interface ShowRosterUpdateListResponse {
  count: number;
  items: ShowRosterUpdateItem[];
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

export interface InventoryItem {
  item_uuid: string;
  card: CardSummary;
  quantity: number;
  is_sellable: boolean;
  synced_at: string;
  current_price: number | null;
  total_value: number | null;
  profit_loss: number | null;
}

export interface InventorySummary {
  count: number;
  total_quantity: number;
  total_market_value: number;
  total_profit_loss: number;
  items: InventoryItem[];
}

export interface InventoryImportItem {
  item_uuid: string;
  quantity: number;
  is_sellable: boolean;
  card_name?: string | null;
}

export interface InventoryImportPayload {
  items: InventoryImportItem[];
  replace_existing?: boolean;
}

export interface InventoryImportResponse {
  imported_count: number;
  replaced_existing: boolean;
  inventory: InventorySummary;
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

export interface AuthUser {
  id: string;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  auth_provider: AuthProvider;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export interface SignupPayload {
  email: string;
  password: string;
  display_name?: string | null;
  device_name?: string | null;
  platform?: string | null;
}

export interface LoginPayload {
  email: string;
  password: string;
  device_name?: string | null;
  platform?: string | null;
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_token_expires_in: number;
  refresh_token_expires_in: number;
  user: AuthUser;
}

export interface ApiErrorPayload {
  detail?: string;
}
