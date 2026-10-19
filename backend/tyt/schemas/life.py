"""生活类请求模型"""
from pydantic import BaseModel, Field, field_validator

from tyt.config import REPORT_REASONS


class NetworkLocateRequest(BaseModel):
    """网络定位辅助（定位天气）：auto（融合）/ wifi / cellular"""
    method: str = Field("auto", description="auto / wifi / cellular")
    lat: float | None = Field(None, description="基准坐标纬度（GCJ-02，可选，缺省用默认城市中心）")
    lon: float | None = Field(None, description="基准坐标经度（GCJ-02，可选）")

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        v = (v or "auto").lower()
        if v not in ("auto", "wifi", "cellular", "bs", "base"):
            raise ValueError("method 须为 auto / wifi / cellular")
        return v


class MerchantReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    content: str = Field(..., min_length=10, max_length=500)


class ComplaintCreate(BaseModel):
    subject_type: str = Field(..., description="merchant/estate/landlord/agency")
    subject_id: int = Field(0, description="主体ID，无实体时为0")
    subject_label: str = Field(..., max_length=256, description="主体名称（房东/中介填脱敏名）")
    content: str = Field(..., min_length=10, max_length=1000)
    category: str = "其他"

    @field_validator("subject_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        if v not in ("merchant", "estate", "landlord", "agency"):
            raise ValueError("subject_type 须为 merchant/estate/landlord/agency")
        return v


class PostCreate(BaseModel):
    category: str = "avoid_pit"
    title: str = Field(..., min_length=2, max_length=100)
    content: str = Field(..., min_length=10, max_length=3000)
    is_anonymous: bool = True
    images: list[str] = Field(default_factory=list, max_length=6, description="帖子配图 URL（最多 6 张）")

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in ("avoid_pit", "recommend"):
            raise ValueError("category 须为 avoid_pit 或 recommend")
        return v

    @field_validator("images")
    @classmethod
    def validate_images(cls, v: list[str]) -> list[str]:
        import re
        for u in v:
            if not re.fullmatch(r"/uploads/posts/[0-9a-f]{32}\.(jpg|jpeg|png|webp|gif)", u):
                raise ValueError("图片地址非法")
        return v


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=2, max_length=500)
    is_anonymous: bool = True


class AbuseReportCreate(BaseModel):
    target_type: str = Field(..., description="post/comment/review/complaint")
    target_id: int
    reason: str
    description: str = Field("", max_length=500)

    @field_validator("target_type")
    @classmethod
    def validate_target(cls, v: str) -> str:
        if v not in ("post", "comment", "review", "complaint"):
            raise ValueError("target_type 非法")
        return v

    @field_validator("reason")
    @classmethod
    def validate_reason(cls, v: str) -> str:
        if v not in REPORT_REASONS:
            raise ValueError("reason 非法")
        return v


class PersonQueryRequest(BaseModel):
    """个人查询（严格受限）：仅支持公开合法的失信/涉诉/行政处罚检索

    合规约束：
    - 查询对象姓名必须 >= 2 个汉字
    - 结果仅返回脱敏姓名 + 公开风险记录，绝不返回身份证/手机号/住址
    - 游客无权限；普通用户每日 3 次；查询行为写入审计日志
    """
    name: str = Field(..., min_length=2, max_length=32)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re_fullmatch_chinese(v):
            raise ValueError("仅支持中文姓名查询")
        return v


def re_fullmatch_chinese(s: str) -> bool:
    import re
    return bool(re.fullmatch(r"[\u4e00-\u9fa5·]{2,32}", s))
