from backend.features.woven_costing.dto.ping_dto import PingRequest
from backend.features.woven_costing.services.ping_service import PingService


def test_ping_returns_message() -> None:
    response = PingService().handle(PingRequest(name="An"))
    assert "An" in response.message
