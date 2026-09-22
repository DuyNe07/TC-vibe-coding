"""Scaffold a new feature (backend + frontend + business doc) that already follows every rule.

Usage:
    python scripts/new_feature.py <feature_key> --title "Tên chức năng" [--description "..."]
                                  [--icon 🧩] [--group "Chức năng"] [--owner "Tên người phụ trách"]

Example:
    python scripts/new_feature.py leave_request --title "Đơn nghỉ phép" --icon 🏖️ --owner "Phòng HCNS"
"""

import argparse
import sys
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.core.naming import feature_url_slug, is_valid_feature_key, to_pascal_case  # noqa: E402

BACKEND_FILES: dict[str, str] = {
    "__init__.py": '''"""Feature "${title}". Business spec: docs/business/${key}.md

Public API = the top layer only. Pages use: gateway.open(${pascal}Controller)
Layers below (services, business, builders, repositories, models) are internal to this feature.
"""

from backend.features.${key}.controllers.${key}_controller import ${pascal}Controller

__all__ = ["${pascal}Controller"]
''',
    "constants.py": '''"""Constants of feature "${title}" (UPPER_CASE values only, no classes)."""

from typing import Final

FEATURE_KEY: Final = "${key}"
''',
    "exceptions.py": '''"""Errors of feature "${title}". Messages are shown to users."""

from backend.core.exceptions import AppError


class ${pascal}Error(AppError):
    code = "${key_upper}_ERROR"
    default_message = "Có lỗi trong chức năng ${title}."
''',
    "models/__init__.py": '''"""Entities (BaseEntity), value objects (BaseValueObject) and enums (StrEnum)."""
''',
    "dto/__init__.py": '''"""Input/output of each use case (BaseRequestDTO / BaseResponseDTO / BaseDTO)."""
''',
    "dto/ping_dto.py": '''"""DTOs of the scaffolded "ping" use case. Replace them with real ones."""

from backend.core.base import BaseRequestDTO, BaseResponseDTO


class PingRequest(BaseRequestDTO):
    name: str = ""


class PingResponse(BaseResponseDTO):
    message: str
''',
    "business/__init__.py": '''"""Pure business logic: rules (BaseBusinessRule, code="BR-xx") and BaseBusiness classes."""
''',
    "builders/__init__.py": '''"""Converters (BaseBuilder): file/raw -> models, models -> DTOs, models -> files."""
''',
    "repositories/__init__.py": '''"""Persistence (subclass JsonFileRepository[MyEntity])."""
''',
    "services/__init__.py": '''"""One file = one service class = one use case (BaseService[Request, Response])."""
''',
    "services/ping_service.py": '''"""Scaffolded use case "ping". Delete it once real services exist."""

from backend.core.base import BaseService
from backend.features.${key}.dto.ping_dto import PingRequest, PingResponse


class PingService(BaseService[PingRequest, PingResponse]):
    def execute(self, request: PingRequest) -> PingResponse:
        self.logger.info("Ping from %s", request.name or "anonymous")  # shown in the page log panel
        greeting = f"Xin chào {request.name}! " if request.name else ""
        return PingResponse(message=f"{greeting}Backend của chức năng '${title}' đã sẵn sàng.")
''',
    "controllers/__init__.py": '''"""The ONE controller of the feature (top layer). One public method = one use case = one service. No logic."""
''',
    "controllers/${key}_controller.py": '''"""Top layer of feature "${title}". Pages call it through gateway.open(...)."""

from backend.core.base import BaseController
from backend.features.${key}.dto.ping_dto import PingRequest, PingResponse
from backend.features.${key}.services.ping_service import PingService


class ${pascal}Controller(BaseController):
    def ping(self, request: PingRequest) -> PingResponse:
        """Kiểm tra kết nối backend (scaffold)."""
        return PingService().handle(request)
''',
    "tests/__init__.py": "",
    "tests/test_ping_service.py": """from backend.features.${key}.dto.ping_dto import PingRequest
from backend.features.${key}.services.ping_service import PingService


def test_ping_returns_message() -> None:
    response = PingService().handle(PingRequest(name="An"))
    assert "An" in response.message
""",
}

FRONTEND_FILES: dict[str, str] = {
    "__init__.py": '''"""Frontend of feature "${title}"."""
''',
    "manifest.py": '''"""How "${title}" appears on Home and in the sidebar menu."""

from frontend.core.feature_manifest import FeatureManifest
from frontend.features.${key}.pages.main_page import ${pascal}MainPage

FEATURE = FeatureManifest(
    key="${key}",
    title="${title}",
    description="${description}",
    icon="${icon}",
    group="${group}",
    owner="${owner}",
    pages=(${pascal}MainPage,),
)
''',
    "pages/__init__.py": '''"""Pages (BasePage subclasses). The first page in FEATURE.pages is the landing page."""
''',
    "pages/main_page.py": '''"""Landing page of "${title}" (URL: /${slug})."""

import streamlit as st

from backend.core.gateway import gateway
from backend.features.${key} import ${pascal}Controller
from backend.features.${key}.dto.ping_dto import PingRequest
from frontend.core.base_page import BasePage
from frontend.core.components import panel


class ${pascal}MainPage(BasePage):
    title = "${title}"
    icon = "${icon}"
    description = "${description}"

    def render(self) -> None:
        feature = gateway.open(${pascal}Controller)
        with panel("Trạng thái", icon="🔌"):
            st.success(feature.ping(PingRequest()).message)
        st.info("Chức năng đang được xây dựng theo docs/business/${key}.md", icon="🚧")
''',
    "components/__init__.py": '''"""Widgets used only by this feature (functions). Shared widgets live in frontend/core/components."""
''',
}


def render(template: str, values: dict[str, str]) -> str:
    return Template(template).substitute(values)


def write_tree(base: Path, files: dict[str, str], values: dict[str, str]) -> list[Path]:
    created = []
    for relative, content in files.items():
        path = base / render(relative, values)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(content, values), encoding="utf-8", newline="\n")
        created.append(path)
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new feature (backend + frontend + docs).")
    parser.add_argument("key", help="snake_case feature key, e.g. leave_request")
    parser.add_argument("--title", required=True, help="Display name (Vietnamese)")
    parser.add_argument("--description", default="", help="One sentence shown on the Home card")
    parser.add_argument("--icon", default="🧩")
    parser.add_argument("--group", default="Chức năng")
    parser.add_argument("--owner", default="")
    args = parser.parse_args()

    key = args.key.strip()
    if not is_valid_feature_key(key):
        print(f"ERROR: invalid feature key {key!r}. Use snake_case (a-z, 0-9, _), 3-50 chars, not reserved.")
        return 1
    backend_dir = ROOT / "backend" / "features" / key
    frontend_dir = ROOT / "frontend" / "features" / key
    for existing in (backend_dir, frontend_dir):
        if existing.exists():
            print(f"ERROR: {existing.relative_to(ROOT)} already exists. Choose another key or edit the feature.")
            return 1

    def quote(text: str) -> str:
        return text.replace("\\", "\\\\").replace('"', '\\"')

    values = {
        "key": key,
        "key_upper": key.upper(),
        "pascal": to_pascal_case(key),
        "slug": feature_url_slug(key),
        "title": quote(args.title.strip()),
        "description": quote(args.description.strip() or f"Chức năng {args.title.strip()}."),
        "icon": quote(args.icon.strip() or "🧩"),
        "group": quote(args.group.strip() or "Chức năng"),
        "owner": quote(args.owner.strip()),
    }
    created = write_tree(backend_dir, BACKEND_FILES, values)
    created += write_tree(frontend_dir, FRONTEND_FILES, values)

    doc_path = ROOT / "docs" / "business" / f"{key}.md"
    if not doc_path.exists():
        template = (ROOT / "docs" / "business" / "_TEMPLATE.md").read_text(encoding="utf-8")
        doc = template.replace("<feature_key>", key).replace("<Feature title>", args.title.strip())
        doc = doc.replace("<Home group, e.g. Kế hoạch sản xuất>", args.group.strip() or "Chức năng")
        doc = doc.replace("<one emoji, e.g. 📋>", args.icon.strip() or "🧩")
        doc_path.write_text(doc.replace("<Owner>", args.owner.strip() or "TBD"), encoding="utf-8", newline="\n")
        created.append(doc_path)

    print(f"Created feature '{key}' ({len(created)} files):")
    for path in created:
        print(f"  + {path.relative_to(ROOT).as_posix()}")
    print("\nNext steps (docs/rules/05-feature-workflow.md):")
    print(f"  1. Complete docs/business/{key}.md")
    print("  2. Implement models -> business -> repositories -> builders -> dto -> services -> controller -> pages")
    print("  3. python scripts/check.py      4. powershell -ExecutionPolicy Bypass -File .\\run.ps1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
