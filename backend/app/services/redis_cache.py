"""Redis-backed response cache helpers for read-heavy endpoints."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from functools import lru_cache
from typing import Any, Mapping, TypeVar

from pydantic import BaseModel, ValidationError

try:
    import redis
    from redis.exceptions import RedisError
except ImportError:  # pragma: no cover - optional dependency in local dev
    redis = None

    class RedisError(Exception):
        """Fallback Redis error used when redis-py is unavailable."""


logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 60
CACHE_KEY_PREFIX = "api-cache:v1"

ModelT = TypeVar("ModelT", bound=BaseModel)


@lru_cache(maxsize=1)
def get_redis_client():
    if redis is None:
        return None
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return None
    return redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=0.25,
        socket_timeout=0.25,
        health_check_interval=30,
    )


def build_cache_key(namespace: str, params: Mapping[str, Any]) -> str:
    normalized = {key: value for key, value in params.items() if value is not None}
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{CACHE_KEY_PREFIX}:{namespace}:{digest}"


def load_cached_response(cache_key: str, model_type: type[ModelT]) -> ModelT | None:
    client = get_redis_client()
    if client is None:
        return None
    try:
        payload = client.get(cache_key)
    except RedisError as exc:
        logger.warning("Redis cache read failed for %s: %s", cache_key, exc)
        return None
    if not payload:
        return None
    try:
        return model_type.model_validate_json(payload)
    except ValidationError as exc:
        logger.warning("Redis cache payload validation failed for %s: %s", cache_key, exc)
        return None


def load_cached_json(cache_key: str) -> Any | None:
    client = get_redis_client()
    if client is None:
        return None
    try:
        payload = client.get(cache_key)
    except RedisError as exc:
        logger.warning("Redis cache read failed for %s: %s", cache_key, exc)
        return None
    if not payload:
        return None
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        logger.warning("Redis cache JSON decode failed for %s: %s", cache_key, exc)
        return None


def store_cached_response(cache_key: str, response: BaseModel) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(cache_key, CACHE_TTL_SECONDS, response.model_dump_json())
    except RedisError as exc:
        logger.warning("Redis cache write failed for %s: %s", cache_key, exc)
