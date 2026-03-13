"""Dependency helpers for API routes."""

from __future__ import annotations

from fastapi import Request



def get_settings(request: Request):
    return request.app.state.settings



def get_scheduler(request: Request):
    return request.app.state.scheduler_manager



def get_recommendation_service(request: Request):
    return request.app.state.recommendation_service



def get_portfolio_service(request: Request):
    return request.app.state.portfolio_service



def get_config_store(request: Request):
    return request.app.state.config_store



def get_token_service(request: Request):
    return request.app.state.token_service



def get_auth_service(request: Request):
    return request.app.state.auth_service



def get_user_service(request: Request):
    return request.app.state.user_service



def get_connection_service(request: Request):
    return request.app.state.connection_service



def get_show_sync_service(request: Request):
    return request.app.state.show_sync_service



def get_inventory_service(request: Request):
    return request.app.state.inventory_service
