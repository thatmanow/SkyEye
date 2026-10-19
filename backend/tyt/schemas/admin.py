"""管理端请求模型"""
from pydantic import BaseModel, Field, field_validator


class AuditActionRequest(BaseModel):
    action: str = Field(..., description="approve/reject/offline")
    reason: str = Field("", max_length=256)

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in ("approve", "reject", "offline"):
            raise ValueError("action 须为 approve/reject/offline")
        return v


class ImportRequest(BaseModel):
    """管理端数据导入：来自官方公开渠道人工查询结果的 CSV 内容

    合规要求：source_code 必须是 data_sources 表中登记的合法来源；
    导入行为写入 collect_logs 审计。
    """
    source_code: str = "gsxt"
    entity: str = Field(..., description="companies/risks/personnel/shareholders")
    csv_content: str = Field(..., min_length=1)

    @field_validator("entity")
    @classmethod
    def validate_entity(cls, v: str) -> str:
        if v not in ("companies", "risks", "personnel", "shareholders"):
            raise ValueError("entity 非法")
        return v


class UserRoleUpdateRequest(BaseModel):
    role: str

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in ("user", "premium", "enterprise_admin", "platform_admin"):
            raise ValueError("role 非法")
        return v


class UserStatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ("normal", "banned"):
            raise ValueError("status 非法")
        return v


class KbAddDocumentRequest(BaseModel):
    """知识库手动录入文档"""
    title: str = Field(..., min_length=2, max_length=120)
    content: str = Field(..., min_length=10, max_length=8000)
    url: str = Field("", max_length=500)


class ViolationWordItem(BaseModel):
    """违规标准词条（词 + 第一版分类）"""
    word: str = Field(..., min_length=1, max_length=64)
    category: str = Field("通用", max_length=32)


class ViolationWordsUpdateRequest(BaseModel):
    """内容审核违规标准词库更新：优先 items（带分类），兼容 words（纯词列表）"""
    words: list[str] = Field(default_factory=list, max_length=500)
    items: list[ViolationWordItem] = Field(default_factory=list, max_length=500)
