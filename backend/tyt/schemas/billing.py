"""会员订阅请求模型"""
from typing import Literal

from pydantic import BaseModel


class MemberOrderCreate(BaseModel):
    plan: Literal["monthly", "auto_monthly"]
    pay_channel: Literal["alipay", "wechat"] = "alipay"
