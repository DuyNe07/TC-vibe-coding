"""Persistence of 4.1 / 4.2 fabrics and 4.3 import logs."""

from backend.core.base import SqlRepository
from backend.features.woven_costing.models.fabric import Fabric, FabricImportLog


class FabricRepository(SqlRepository[Fabric]):
    """Table <developer>__woven_costing__fabric (one document per TCFNO, yarns inside)."""

    def by_tcfno(self, tcfno: str) -> Fabric | None:
        found = self.find_by(tcfno=tcfno.strip().upper())
        return found[0] if found else None

    def index_by_tcfno(self) -> dict[str, Fabric]:
        return {f.tcfno: f for f in self.list_all()}


class FabricImportLogRepository(SqlRepository[FabricImportLog]):
    def latest(self, limit: int) -> list[FabricImportLog]:
        return sorted(self.list_all(), key=lambda log: log.created_at, reverse=True)[:limit]
