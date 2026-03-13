"""Standalone Redis cache worker for read-heavy market endpoints."""

from __future__ import annotations

import logging
import time

from app.services.redis_cache import get_redis_client
from app.workers.market_worker import create_market_worker


logger = logging.getLogger(__name__)
SLEEP_SECONDS = 120
TOP_FLIPS_LIMIT = 50
MARKET_MOVERS_LIMIT = 50
MARKET_FLOORS_LIMIT = 50


def _store_payload(client, key: str, response) -> None:
    if client is None:
        logger.warning("Redis is unavailable; skipping cache write for %s", key)
        return
    client.set(key, response.model_dump_json())


def run_once(worker, redis_client) -> None:
    with worker.session_factory() as session:
        top_flips = worker.show_sync_service.get_top_flip_listings_response(session)
        market_movers = worker.show_sync_service.get_market_movers_response(session, limit=MARKET_MOVERS_LIMIT)
        market_floors = worker.recommendation_service.get_floor_buys(session, limit=MARKET_FLOORS_LIMIT)

    _store_payload(redis_client, "flips:top", top_flips)
    _store_payload(redis_client, "market:movers", market_movers)
    _store_payload(redis_client, "market:floors", market_floors)
    logger.info(
        "Redis market cache updated: flips=%s movers=%s floors=%s",
        top_flips.count,
        market_movers.count,
        market_floors.count,
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    worker = create_market_worker()
    redis_client = get_redis_client()
    while True:
        try:
            run_once(worker, redis_client)
        except Exception:
            logger.exception("Redis market cache worker run failed")
        time.sleep(SLEEP_SECONDS)


if __name__ == "__main__":
    main()
