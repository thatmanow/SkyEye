"""通用响应模型"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageData(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[Any]


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "ok"
    data: Any = None
