"""商业类请求模型"""
from pydantic import BaseModel, Field, field_validator


class WatchCreate(BaseModel):
    company_id: int


class ReportCreate(BaseModel):
    company_id: int
    template: str = "standard"

    @field_validator("template")
    @classmethod
    def validate_template(cls, v: str) -> str:
        if v not in ("standard", "deep"):
            raise ValueError("template 须为 standard 或 deep")
        return v


class LeadFollowUpdate(BaseModel):
    status: str = "following"
    note: str = Field("", max_length=1000)
    next_action: str = Field("", max_length=256)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("new", "following", "won", "lost"):
            raise ValueError("status 须为 new/following/won/lost")
        return v


class MonitorScheduleUpdate(BaseModel):
    freq: str = "daily"
    scope: str = "watched"
    enabled: bool = True

    @field_validator("freq")
    @classmethod
    def validate_freq(cls, v: str) -> str:
        if v not in ("daily", "weekly"):
            raise ValueError("freq 须为 daily 或 weekly")
        return v

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: str) -> str:
        if v not in ("watched", "all"):
            raise ValueError("scope 须为 watched 或 all")
        return v
