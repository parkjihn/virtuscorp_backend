from fastapi import APIRouter, Depends, HTTPException
from app.schemas.yandex import YandexMarketCredentials
from app.models.yandex import YandexIntegration
from app.models.user import User
from app.utils.helpers import get_current_user
import httpx

router = APIRouter()

@router.post("/yandex-market/save")
async def save_yandex_creds(
    creds: YandexMarketCredentials,
    current_user: User = Depends(get_current_user),
):
    existing = await YandexIntegration.get_or_none(user=current_user)
    if existing:
        existing.campaign_id = creds.campaign_id
        existing.business_id = creds.business_id
        existing.token = creds.token
        await existing.save()
    else:
        await YandexIntegration.create(
            user=current_user,
            campaign_id=creds.campaign_id,
            business_id=creds.business_id,
            token=creds.token,
        )

    return {"message": "Yandex credentials saved"}

@router.post("/yandex-market/test")
async def test_yandex_connection(
    creds: YandexMarketCredentials,
    current_user: User = Depends(get_current_user),
):
    url = f"https://api.partner.market.yandex.ru/campaigns/{creds.campaign_id}/stats"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        if response.status_code == 200:
            return {"success": True}
        return {"success": False, "detail": response.text}
    except Exception as e:
        return {"success": False, "detail": str(e)}
