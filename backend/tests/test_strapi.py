import pytest
from app.services.strapi_service import StrapiService

@pytest.mark.asyncio
async def test_strapi_idempotency_and_demo():
    # Test idempotency check when cms_entry_id already exists
    res = await StrapiService.publish_article(
        title="Career Options Test Title",
        content_body="# Content Body",
        existing_cms_id="strapi_101",
        existing_published_url="http://localhost:1337/articles/career-options-test-title"
    )

    assert res["success"] is True
    assert res["cms_entry_id"] == "strapi_101"
    assert "Idempotency" in res["message"]

    # Test DEMO mode fallback publish
    res_demo = await StrapiService.publish_article(
        title="New Fresh Article",
        content_body="# Fresh Body"
    )
    assert res_demo["success"] is True
    assert "strapi_demo" in res_demo["cms_entry_id"]
