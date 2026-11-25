"""DTOs of the scaffolded "ping" use case. Replace them with real ones."""

from backend.core.base import BaseRequestDTO, BaseResponseDTO


class PingRequest(BaseRequestDTO):
    name: str = ""


class PingResponse(BaseResponseDTO):
    message: str
