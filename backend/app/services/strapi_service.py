import httpx
import re
from typing import Dict, Any, Optional
from app.config import settings

class StrapiService:
    @staticmethod
    def generate_slug(title: str) -> str:
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s-]+', '-', slug).strip('-')
        return slug

    @classmethod
    async def publish_article(
        cls,
        title: str,
        content_body: str,
        category: Optional[str] = None,
        existing_cms_id: Optional[str] = None,
        existing_published_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Publishes final article content to Strapi CMS.
        Idempotency check: If existing_cms_id is provided, returns existing record.
        """
        if existing_cms_id and existing_published_url:
            return {
                "success": True,
                "cms_entry_id": str(existing_cms_id),
                "published_url": existing_published_url,
                "http_status": 200,
                "message": "Article already published (Idempotency check passed)."
            }

        slug = cls.generate_slug(title)
        
        # DEMO MODE fallback
        if settings.DEMO_MODE or not settings.STRAPI_API_TOKEN or settings.STRAPI_API_TOKEN.startswith("mock"):
            demo_id = f"strapi_demo_{existing_cms_id or '101'}"
            demo_url = f"{settings.STRAPI_URL}/articles/{slug}"
            return {
                "success": True,
                "cms_entry_id": demo_id,
                "published_url": demo_url,
                "http_status": 200,
                "message": "[DEMO MODE] Simulated successful Strapi publication."
            }

        headers = {
            "Authorization": f"Bearer {settings.STRAPI_API_TOKEN}",
            "Content-Type": "application/json"
        }

        endpoint = f"{settings.STRAPI_URL.rstrip('/')}/api/{settings.STRAPI_CONTENT_TYPE}"

        payload = {
            "data": {
                "title": title,
                "slug": slug,
                "content": content_body,
                "publishedAt": None # Draft or auto-publish depending on Strapi workflow
            }
        }

        if category:
            payload["data"]["category"] = category

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(endpoint, headers=headers, json=payload)
                
                if res.status_code in [200, 201]:
                    data = res.json()
                    entry_data = data.get("data", {})
                    entry_id = str(entry_data.get("id") or entry_data.get("documentId") or "published_entry")
                    published_url = f"{settings.STRAPI_URL.rstrip('/')}/articles/{slug}"
                    
                    return {
                        "success": True,
                        "cms_entry_id": entry_id,
                        "published_url": published_url,
                        "http_status": res.status_code,
                        "message": "Article successfully published to Strapi."
                    }
                else:
                    return {
                        "success": False,
                        "cms_entry_id": None,
                        "published_url": None,
                        "http_status": res.status_code,
                        "error_message": f"Strapi returned HTTP {res.status_code}: {res.text}"
                    }
        except Exception as e:
            return {
                "success": False,
                "cms_entry_id": None,
                "published_url": None,
                "http_status": 500,
                "error_message": f"Connection exception publishing to Strapi: {str(e)}"
            }
