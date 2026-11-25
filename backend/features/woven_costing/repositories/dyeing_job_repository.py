"""Persistence of the 4.21 dyeing job orders (lines and result inside the document)."""

from backend.core.base import SqlRepository
from backend.features.woven_costing.models.dyeing_job import DyeingJob


class DyeingJobRepository(SqlRepository[DyeingJob]):
    def numbers(self) -> list[str]:
        return [j.job_no for j in self.list_all()]
