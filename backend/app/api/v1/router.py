from fastapi import APIRouter
from backend.app.api.v1.endpoints import dlq, events, health, webhooks

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(events.router)
api_router.include_router(webhooks.router)
api_router.include_router(dlq.router)
