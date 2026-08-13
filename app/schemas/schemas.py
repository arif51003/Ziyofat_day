from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    avatar_url: str | None = None

    model_config = {"from_attributes": True}


class RefreshTokenRequest(BaseModel):
    refresh_token: str
