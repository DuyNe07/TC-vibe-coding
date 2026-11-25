"""Fix 2026-11-25 (Prompt 03): on Screen 8 a line where only g/m (or only a dyeing choice) was typed disappeared."""

from datetime import date
from decimal import Decimal

from backend.features.woven_costing.builders.dyeing_job_builders import apply_input
from backend.features.woven_costing.dto.costsheet_dto import TcdnDyeingInputDTO
from backend.features.woven_costing.dto.dyeing_job_dto import DyeingJobInputDTO, DyeingJobLineDTO
from backend.features.woven_costing.models.dyeing_job import DyeingJob

D = Decimal
JOB = DyeingJob(job_no="GC-X-2026-00001", costing_date=date(2026, 11, 25))


def _apply(*lines: DyeingJobLineDTO) -> DyeingJob:
    return apply_input(JOB, DyeingJobInputDTO(customer_name="X", lines=list(lines)))


def test_line_with_only_weight_is_kept() -> None:
    job = _apply(DyeingJobLineDTO(g_per_m=D(245)))
    assert len(job.lines) == 1 and job.lines[0].g_per_m == 245


def test_line_with_only_a_dyeing_choice_is_kept() -> None:
    job = _apply(DyeingJobLineDTO(tcdn_dyeing=TcdnDyeingInputDTO(wr_chemical="D.W/R")))
    assert len(job.lines) == 1 and job.lines[0].tcdn_dyeing.wr_chemical == "D.W/R"


def test_blank_line_is_dropped() -> None:
    assert _apply(DyeingJobLineDTO()).lines == []
