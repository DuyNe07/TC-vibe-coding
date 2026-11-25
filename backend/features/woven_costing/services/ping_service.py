"""Scaffolded use case "ping". Delete it once real services exist."""

from backend.core.base import BaseService
from backend.features.woven_costing.dto.ping_dto import PingRequest, PingResponse


class PingService(BaseService[PingRequest, PingResponse]):
    def execute(self, request: PingRequest) -> PingResponse:
        self.logger.info("Ping from %s", request.name or "anonymous")  # written to logs/app.log
        greeting = f"Xin chào {request.name}! " if request.name else ""
        return PingResponse(message=f"{greeting}Backend của chức năng 'Tính giá vải dệt' đã sẵn sàng.")
