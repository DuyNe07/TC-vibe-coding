"""UC-26 In nhãn thông số vải."""

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.woven_costing.builders.document_builders import LabelDocumentBuilder
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.business.label_business import LabelBusiness
from backend.features.woven_costing.constants import MAX_LABELS
from backend.features.woven_costing.dto.fabric_dto import PrintLabelRequest
from backend.features.woven_costing.exceptions import WovenCostingError
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository


class PrintLabelService(BaseService[PrintLabelRequest, FileDownloadDTO]):
    def __init__(self, repository: FabricRepository | None = None) -> None:
        self.repository = repository or FabricRepository()

    def execute(self, request: PrintLabelRequest) -> FileDownloadDTO:
        AccessBusiness().ensure_use_case(self.current_user, "UC-26")
        wanted = [label for label in request.labels if label.tcfno.strip()]
        if not wanted or len(wanted) > MAX_LABELS:
            raise WovenCostingError("Hãy nhập 1-4 mã vải để in nhãn.")
        fabric_biz, labels = FabricBusiness(), LabelBusiness()
        result = []
        for label in wanted:
            code = fabric_biz.clean_code(label.tcfno)[0]
            fabric = self.repository.by_tcfno(code)
            if fabric is None:
                raise WovenCostingError(f"Mã vải {code} chưa có trong dữ liệu gốc.")
            result.append(labels.build(fabric, label.remark))
        self.logger.info("UC-26 %s labels printed: %s", len(result), [r.tcfno for r in result])
        return LabelDocumentBuilder(result).build()
