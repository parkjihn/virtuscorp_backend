from pydantic import BaseModel

class YandexMarketCredentials(BaseModel):
    campaign_id: str
    business_id: str
    token: str
