"""Pydantic v2 request/response schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LinkCreate(BaseModel):
    original_url: HttpUrl


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime


class ClickOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    clicked_at: datetime
    user_agent: str | None


class LinkStats(BaseModel):
    id: int
    short_code: str
    original_url: str
    click_count: int
    recent_clicks: list[ClickOut]
