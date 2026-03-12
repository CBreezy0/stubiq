"""Database-backed runtime configuration storage."""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import MarketPhaseHistory, SystemSetting
from app.utils.enums import MarketPhase
from app.utils.time import utcnow


class ConfigStore:
    """Persists runtime-tunable configuration values in PostgreSQL."""

    MARKET_PHASE_OVERRIDE_KEY = "market_phase_override"
    STRATEGY_WEIGHTS_KEY = "strategy_weights"
    ENGINE_THRESHOLDS_KEY = "engine_thresholds"

    ENGINE_THRESHOLD_PUBLIC_TO_INTERNAL = {
        "floor_buy_margin": "floor_buy_buffer",
        "launch_supply_crash_threshold": "launch_shock_drop_pct",
        "flip_profit_minimum": "low_risk_profit_min",
        "grind_market_edge": "launch_grind_ev_edge_pct",
        "collection_lock_penalty": "collection_early_access_penalty",
        "gatekeeper_hold_weight": "collection_owned_gatekeeper_priority_bonus",
    }
    ENGINE_THRESHOLD_INTERNAL_TO_PUBLIC = {
        internal: public for public, internal in ENGINE_THRESHOLD_PUBLIC_TO_INTERNAL.items()
    }

    def get_json(self, session: Session, key: str, default=None):
        setting = session.get(SystemSetting, key)
        return setting.value_json if setting else default

    def set_json(self, session: Session, key: str, value: Dict[str, Any], description: Optional[str] = None) -> SystemSetting:
        setting = session.get(SystemSetting, key)
        if setting is None:
            setting = SystemSetting(key=key)
        setting.value_json = value
        setting.description = description
        session.add(setting)
        return setting

    def get_market_phase_override(self, session: Session) -> Optional[MarketPhase]:
        payload = self.get_json(session, self.MARKET_PHASE_OVERRIDE_KEY)
        if not payload:
            return None
        value = payload.get("phase")
        return MarketPhase(value) if value else None

    def set_market_phase_override(self, session: Session, phase: Optional[MarketPhase], notes: Optional[str] = None):
        payload = {"phase": phase.value if phase else None, "notes": notes, "updated_at": utcnow().isoformat()}
        self.set_json(session, self.MARKET_PHASE_OVERRIDE_KEY, payload, description="Manual market phase override")
        if phase:
            latest = session.scalar(select(MarketPhaseHistory).order_by(MarketPhaseHistory.phase_start.desc()).limit(1))
            if latest and latest.phase == phase and latest.phase_end is None:
                latest.notes = notes or latest.notes
            else:
                if latest and latest.phase_end is None:
                    latest.phase_end = utcnow()
                session.add(MarketPhaseHistory(phase=phase, phase_start=utcnow(), notes=notes))
        return payload

    def get_strategy_weights(self, session: Session, default: Dict[str, float]) -> Dict[str, float]:
        payload = self.get_json(session, self.STRATEGY_WEIGHTS_KEY, default) or default
        merged = dict(default)
        merged.update(payload)
        return merged

    def get_engine_thresholds(self, session: Session, default: Dict[str, float]) -> Dict[str, float]:
        payload = self.get_json(session, self.ENGINE_THRESHOLDS_KEY, {}) or {}
        merged = dict(default)
        for key, value in payload.items():
            merged[self.ENGINE_THRESHOLD_PUBLIC_TO_INTERNAL.get(key, key)] = value
        return merged

    def get_public_engine_thresholds(self, session: Session, default: Dict[str, float]) -> Dict[str, float]:
        thresholds = self.get_engine_thresholds(session, default)
        return {
            public_key: float(thresholds[internal_key])
            for public_key, internal_key in self.ENGINE_THRESHOLD_PUBLIC_TO_INTERNAL.items()
        }

    def update_public_engine_thresholds(
        self,
        session: Session,
        updates: Dict[str, float],
        default: Dict[str, float],
    ) -> SystemSetting:
        current = self.get_engine_thresholds(session, default)
        for public_key, value in updates.items():
            internal_key = self.ENGINE_THRESHOLD_PUBLIC_TO_INTERNAL.get(public_key)
            if internal_key is not None:
                current[internal_key] = value
        return self.set_json(
            session,
            self.ENGINE_THRESHOLDS_KEY,
            current,
            description="Runtime-editable engine thresholds",
        )
