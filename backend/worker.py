"""Standalone Redis cache worker for read-heavy market endpoints."""

from __future__ import annotations

import json
import logging
import time

from app.services.redis_cache import get_redis_client
from app.workers.market_worker import create_market_worker


logger = logging.getLogger(__name__)
SLEEP_SECONDS = 120
TOP_FLIPS_LIMIT = 25
MARKET_MOVERS_LIMIT = 25
MARKET_FLOORS_LIMIT = 25
MARKET_TRENDING_LIMIT = 25


def _store_payload(client, key: str, payload) -> None:
    if client is None:
        logger.warning("Redis is unavailable; skipping cache write for %s", key)
        return
    if hasattr(payload, "model_dump_json"):
        client.set(key, payload.model_dump_json())
        return
    client.set(key, json.dumps(payload, default=str))


def refresh_caches(worker, redis_client) -> None:
    logger.info("worker refresh start")
    with worker.session_factory() as session:
        top_flips = worker.show_sync_service.get_top_flip_listings_response(session)
        market_movers = worker.show_sync_service.get_market_movers_response(session, limit=MARKET_MOVERS_LIMIT)
        market_floors = worker.recommendation_service.get_floor_buys(session, limit=MARKET_FLOORS_LIMIT)
        market_trending = worker.show_sync_service.get_trending_response(session, limit=MARKET_TRENDING_LIMIT)
        market_phase = worker.recommendation_service.get_phase(session)
        market_phase_history = worker.recommendation_service.get_phase_history(session)

    phases_payload = {
        "current": market_phase.model_dump(mode="json"),
        "history": market_phase_history,
    }

    _store_payload(redis_client, "flips:top", top_flips)
    _store_payload(redis_client, "market:movers", market_movers)
    _store_payload(redis_client, "market:floors", market_floors)
    _store_payload(redis_client, "market:trending", market_trending)
    _store_payload(redis_client, "market:phases", phases_payload)

    logger.info(
        "worker refresh success: flips=%s movers=%s floors=%s trending=%s phases=%s",
        top_flips.count,
        market_movers.count,
        market_floors.count,
        market_trending.count,
        len(market_phase_history),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger.info("worker starting")
    worker = create_market_worker()
    redis_client = get_redis_client()
    while True:
        try:
            refresh_caches(worker, redis_client)
        except Exception:
            logger.exception("worker refresh failure")
        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main()
