"""What the catalogs are still missing (UC-21) and the warnings of the data file (BR-08)."""

from collections import Counter, defaultdict
from datetime import date

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.constants import (
    TARGET_SYSTEM_START,
    UNCLASSIFIED_GROUP,
    WARNING_DUPLICATES,
    WARNING_MISSING_SMV,
    WARNING_MISSING_TARGET_B,
    WARNING_NO_PRODUCT_NAME,
    WARNING_NO_TARGET_SYSTEM,
    WARNING_NO_WORKERS,
    WARNING_UNCLASSIFIED,
)
from backend.features.sewing_productivity.models.clean_values import CleanRow
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.source_records import TargetRecord, WorkerRecord
from backend.features.sewing_productivity.models.upload_values import UploadWarning


class CatalogBusiness(BaseBusiness[CleanRow]):
    def unclassified_names(self, rows: list[CleanRow]) -> dict[str, int]:
        """BR-14 product names not in the catalog, with their number of rows."""
        counts = Counter(
            row.product_name for row in rows if row.product_name and row.product_group == UNCLASSIFIED_GROUP
        )
        return dict(sorted(counts.items()))

    def customer_names(self, rows: list[CleanRow]) -> list[tuple[str, str, int]]:
        """BR-15 every customer name with its current group and number of rows."""
        counts = Counter((row.customer_name, row.customer_group) for row in rows)
        return [(name, group, count) for (name, group), count in sorted(counts.items())]

    def styles_without_name(self, rows: list[CleanRow]) -> list[tuple[str, str, int]]:
        """BR-13 styles whose name could not be found: style, most frequent customer, number of rows."""
        customers: defaultdict[str, Counter[str]] = defaultdict(Counter)
        for row in rows:
            if not row.product_name:
                customers[row.style][row.customer_name] += 1
        result = []
        for style in sorted(customers):
            top = min(customers[style].items(), key=lambda item: (-item[1], item[0]))[0]
            result.append((style, top, sum(customers[style].values())))
        return result

    def warnings(
        self, file_rows: list[CleanRow], workers: list[WorkerRecord], targets: list[TargetRecord]
    ) -> list[UploadWarning]:
        """BR-08 what does not block saving; `workers` and `targets` are the tables as they will be after saving."""
        missing_smv = Counter(row.production_date for row in file_rows if row.smv is None)
        missing_b = Counter(row.production_date for row in file_rows if row.standard_output is None)
        warnings = [
            *self._per_day(WARNING_MISSING_SMV, missing_smv),
            *self._per_day(WARNING_MISSING_TARGET_B, missing_b),
            *self._days_without(file_rows, workers, targets),
            *self._per_day(WARNING_DUPLICATES, self._duplicates(file_rows)),
        ]
        unclassified = len(self.unclassified_names(file_rows))
        if unclassified:
            warnings.append(UploadWarning(kind=WARNING_UNCLASSIFIED, count=unclassified))
        no_name = len({row.style for row in file_rows if not row.product_name})
        if no_name:
            warnings.append(UploadWarning(kind=WARNING_NO_PRODUCT_NAME, count=no_name))
        return warnings

    @staticmethod
    def _per_day(kind: str, counts: Counter[date]) -> list[UploadWarning]:
        return [UploadWarning(kind=kind, warning_date=day, count=count) for day, count in sorted(counts.items())]

    @staticmethod
    def _duplicates(rows: list[CleanRow]) -> Counter[date]:
        """Rows repeating the same day, factory, line, order and colour; each repeat after the first is counted."""
        seen: Counter[tuple[object, ...]] = Counter()
        extra: Counter[date] = Counter()
        for row in rows:
            key = (row.production_date, row.factory, row.line, row.po_number, row.color)
            seen[key] += 1
            if seen[key] > 1:
                extra[row.production_date] += 1
        return extra

    @staticmethod
    def _days_without(
        rows: list[CleanRow], workers: list[WorkerRecord], targets: list[TargetRecord]
    ) -> list[UploadWarning]:
        worker_days = {(worker.factory, worker.work_date) for worker in workers}
        target_days = {(target.factory, target.target_date) for target in targets}
        produced: defaultdict[date, set[Factory]] = defaultdict(set)
        for row in rows:
            produced[row.production_date].add(row.factory)
        warnings: list[UploadWarning] = []
        for day in sorted(produced):
            no_workers = sorted(factory for factory in produced[day] if (factory, day) not in worker_days)
            if no_workers:
                detail = ", ".join(no_workers)
                warnings.append(
                    UploadWarning(kind=WARNING_NO_WORKERS, warning_date=day, count=len(no_workers), detail=detail)
                )
            no_target = sorted(factory for factory in produced[day] if (factory, day) not in target_days)
            if day >= TARGET_SYSTEM_START and no_target:
                detail = ", ".join(no_target)
                warnings.append(
                    UploadWarning(kind=WARNING_NO_TARGET_SYSTEM, warning_date=day, count=len(no_target), detail=detail)
                )
        return warnings
