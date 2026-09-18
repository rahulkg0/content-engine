from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database.database import get_db
from app.models.models import Website
from app.config import settings

router = APIRouter(prefix="/websites", tags=["Websites & Settings"])

class ConfigSettingsRequest(BaseModel):
    strapi_url: Optional[str] = None
    strapi_api_token: Optional[str] = None
    strapi_content_type: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    default_research_model: Optional[str] = None
    default_writer_model: Optional[str] = None
    default_quality_model: Optional[str] = None
    demo_mode: Optional[bool] = None

@router.get("/config")
async def get_system_config():
    return {
        "strapi_url": settings.STRAPI_URL,
        "strapi_api_token_configured": bool(settings.STRAPI_API_TOKEN and not settings.STRAPI_API_TOKEN.startswith("mock")),
        "strapi_content_type": settings.STRAPI_CONTENT_TYPE,
        "openrouter_api_key_configured": bool(settings.OPENROUTER_API_KEY and not settings.OPENROUTER_API_KEY.startswith("mock")),
        "default_research_model": settings.DEFAULT_RESEARCH_MODEL,
        "default_writer_model": settings.DEFAULT_WRITER_MODEL,
        "default_quality_model": settings.DEFAULT_QUALITY_MODEL,
        "demo_mode": settings.DEMO_MODE,
        "max_revision_attempts": settings.MAX_REVISION_ATTEMPTS
    }

@router.post("/config")
async def update_system_config(req: ConfigSettingsRequest):
    if req.strapi_url is not None:
        settings.STRAPI_URL = req.strapi_url
    if req.strapi_api_token is not None:
        settings.STRAPI_API_TOKEN = req.strapi_api_token
    if req.strapi_content_type is not None:
        settings.STRAPI_CONTENT_TYPE = req.strapi_content_type
    if req.openrouter_api_key is not None:
        settings.OPENROUTER_API_KEY = req.openrouter_api_key
    if req.default_research_model is not None:
        settings.DEFAULT_RESEARCH_MODEL = req.default_research_model
    if req.default_writer_model is not None:
        settings.DEFAULT_WRITER_MODEL = req.default_writer_model
    if req.default_quality_model is not None:
        settings.DEFAULT_QUALITY_MODEL = req.default_quality_model
    if req.demo_mode is not None:
        settings.DEMO_MODE = req.demo_mode

    return {
        "message": "System configuration updated successfully.",
        "config": await get_system_config()
    }
