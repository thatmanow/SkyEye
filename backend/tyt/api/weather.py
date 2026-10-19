"""天气路由：当前天气 + 预报（含空气质量/生活指数/坐标，供前端地图渲染）+ 网络定位辅助"""
from fastapi import APIRouter, Depends

from tyt.config import AMAP_JS_KEY, DEFAULT_LAT, DEFAULT_LON
from tyt.core.rbac import Principal, get_principal
from tyt.schemas import ApiResponse
from tyt.schemas.life import NetworkLocateRequest
from tyt.services import weather_service

router = APIRouter(prefix="/api/v1/weather", tags=["定位天气"])


@router.post("/locate", response_model=ApiResponse)
def locate(req: NetworkLocateRequest, principal: Principal = Depends(get_principal)):
    """网络定位辅助（第一版同款）：WiFi / 基站 / GPS·WiFi·基站融合 -> 城市 + 精度 + 周边地点"""
    data = weather_service.network_locate(req.method, req.lat, req.lon)
    return ApiResponse(data=data)


@router.get("/now", response_model=ApiResponse)
def now(lat: float = DEFAULT_LAT, lon: float = DEFAULT_LON,
        principal: Principal = Depends(get_principal)):
    data = weather_service.get_weather(lat, lon)
    data["amap_key"] = AMAP_JS_KEY
    return ApiResponse(data=data)


@router.get("/position", response_model=ApiResponse)
def position(lat: float, lon: float, principal: Principal = Depends(get_principal)):
    """逆地理编码：GCJ-02（高德）坐标 -> {city, district}，供定位天气页展示精确位置"""
    return ApiResponse(data=weather_service.reverse_geocode(lat, lon))
