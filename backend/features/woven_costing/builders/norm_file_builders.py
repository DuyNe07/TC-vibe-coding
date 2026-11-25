"""F-05 norm workbook: upload -> NormWorkbook, NormTables <-> NormWorkbook, NormWorkbook -> .xlsx template."""

from decimal import Decimal, InvalidOperation
from typing import Any

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType, UploadedFileDTO
from backend.features.woven_costing.builders.file_readers import read_raw_rows, text
from backend.features.woven_costing.constants import (
    NORM_SHEETS,
    SPANDEX_SHEET,
    TWIST_HOURS_NAME,
    TWIST_PARAM_NAMES,
    TWIST_STAFF_NAME,
    WARP_CHECK_NAMES,
)
from backend.features.woven_costing.exceptions import WovenFileError
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.norm_file import NormSheet, NormWorkbook
from backend.features.woven_costing.models.norm_set import (
    HcmFeatureNorm,
    HcmStageNorm,
    HcmStandardNorm,
    ListItem,
    MinuteRate,
    NormTables,
    SizeNorm,
    SpandexAddition,
    TcdnChemical,
    TcdnProcess,
    TwistParams,
    TwistSystemParams,
    WarpCheckParams,
    WeaveNorm,
    YarnCount,
    seed_spandex,
)
from backend.shared.file_io import ExcelReader, ExcelWriter

ZERO = Decimal(0)
SIX = ("labor", "depreciation", "power", "material", "fuel", "overhead")  # NC, KH, Điện, VT, NL, CPQL
HCM7 = (
    "chemical",
    "labor",
    "depreciation",
    "power",
    "fuel",
    "material",
    "overhead",
)  # HCTN, Lương, KH, Điện, NL, VT, QL
TCDN7 = ("chemical", "labor", "depreciation", "power", "fuel", "material", "overhead")  # HC, NC, KH, Điện, NL, VT, CPQL


def _s(value: Decimal) -> str:
    return f"{value.normalize():f}" if value else "0"


def _d(value: str) -> Decimal:
    try:
        return Decimal((value or "0").replace(",", ""))
    except InvalidOperation:
        return ZERO


def _items(values: list[str], names: tuple[str, ...]) -> CostItems:
    return CostItems(**{name: _d(v) for name, v in zip(names, values, strict=False)})


def _cells(items: CostItems, names: tuple[str, ...]) -> list[str]:
    return [_s(getattr(items, n)) for n in names]


class NormWorkbookReaderBuilder(BaseBuilder[NormWorkbook]):
    """Uploaded F-05 -> text cells of every sheet (row 1 = headers)."""

    def __init__(self, file: UploadedFileDTO) -> None:
        self.file = file

    def build(self) -> NormWorkbook:
        try:
            names = ExcelReader().sheet_names(self.file)
        except Exception as exc:
            raise WovenFileError(f"File {self.file.filename} không đọc được. Hãy dùng file mẫu bộ định mức.") from exc
        sheets = []
        for name in names:
            if name not in NORM_SHEETS:
                continue
            rows = read_raw_rows(self.file, name)
            header = [text(c) if not text(c).startswith("Unnamed") else "" for c in (rows[0] if rows else [])]
            width = len(header)
            body = [[text(row[i]) if i < len(row) else "" for i in range(width)] for row in rows[1:]]
            sheets.append(NormSheet(name=name, columns=header, rows=[r for r in body if any(r)]))
        return NormWorkbook(sheets=sheets)


class NormSheetsBuilder(BaseBuilder[NormWorkbook]):
    """NormTables of a set -> the 12 sheets of F-05 + sheet `Spandex` (template, view, comparison)."""

    def __init__(self, tables: NormTables) -> None:
        self.t = tables

    def build(self) -> NormWorkbook:
        t = self.t
        f, sp = t.twist.filament, t.twist.spun
        twist_rows = [
            [name, _s(getattr(f, field)), _s(getattr(sp, field))]
            for name, field in zip(TWIST_PARAM_NAMES, TwistSystemParams.model_fields, strict=False)
        ]
        twist_rows += [
            [TWIST_STAFF_NAME, _s(t.twist.staff_total), ""],
            [TWIST_HOURS_NAME, _s(t.twist.hours_per_day), ""],
        ]
        wc = t.warp_check
        warp_values = (wc.standard_ends, wc.standard_beats, wc.twist_factor, wc.check_speed_greige, wc.check_speed_dye)
        count_rows = [[c.fiber_system, c.count, _s(c.converted), "", ""] for c in t.yarn_counts]
        for i, level in enumerate(t.twist_levels):
            if i < len(count_rows):
                count_rows[i][4] = str(level)
            else:
                count_rows.append(["", "", "", "", str(level)])
        sheets = {
            "DonGiaPhut": [[r.stage, _s(r.speed), _s(r.spindles), _s(r.reel), _s(r.minutes), *_cells(r.rates, SIX)]
                           for r in t.minute_rates],
            "ThamSoSe": twist_rows,
            "ThamSoMacKiem": [[n, _s(v)] for n, v in zip(WARP_CHECK_NAMES, warp_values, strict=False)],
            "DinhMucHo": [[n.material, n.group, *_cells(n.items, SIX), _s(n.items.chemical)] for n in t.size_norms],
            "DinhMucDet": [[str(n.density), *_cells(n.items, SIX)] for n in t.weave_norms],
            "ChiSo": count_rows,
            "NhuomHCM_TieuChuan": [[n.fabric_type, n.color, *_cells(n.items, HCM7)] for n in t.hcm_standard],
            "NhuomHCM_CongDoan": [[n.name, *_cells(n.items, HCM7), _s(n.loss_rate)] for n in t.hcm_stages],
            "NhuomHCM_TinhNang": [[n.feature, n.fabric_type, n.chemical_note, *_cells(n.items, HCM7)]
                                  for n in t.hcm_features],
            "NhuomTCDN_QuyTrinh": [[p.code, p.component, p.material, p.color, p.process, *_cells(p.items, TCDN7),
                                    p.workshop, _s(p.loss_rate)] for p in t.tcdn_processes],
            "NhuomTCDN_HoaChat": [[c.key, c.weight_group, _s(c.cost)] for c in t.tcdn_chemicals],
            "DanhMuc": [[i.category, i.value] for i in t.lists],
            "Spandex": [[_s(s.spandex), _s(s.addition)] for s in t.spandex],
        }  # fmt: skip
        return NormWorkbook(
            sheets=[NormSheet(name=name, columns=list(NORM_SHEETS[name]), rows=rows) for name, rows in sheets.items()]
        )


class NormTablesBuilder(BaseBuilder[NormTables]):
    """Validated F-05 workbook (BR-63 passed) -> NormTables. Without sheet `Spandex` the table keeps its initial
    values (the service then copies the table of the set in force, 4.5.13)."""

    def __init__(self, book: NormWorkbook) -> None:
        self.book = book

    def _rows(self, name: str) -> list[list[str]]:
        sheet = self.book.sheet(name)
        if sheet is None:
            return []
        wanted = [c for c in NORM_SHEETS[name]]
        position = {c.strip(): i for i, c in enumerate(sheet.columns)}
        return [[(row[position[c]] if c in position and position[c] < len(row) else "") for c in wanted]
                for row in sheet.rows]  # fmt: skip

    def _by_name(self, name: str) -> dict[str, list[str]]:
        return {row[0].strip().casefold(): row for row in self._rows(name) if row and row[0].strip()}

    def build(self) -> NormTables:
        twist = self._by_name("ThamSoSe")

        def system(col: int) -> TwistSystemParams:
            values = [_d(twist.get(n.casefold(), ["", "", ""])[col]) for n in TWIST_PARAM_NAMES]
            return TwistSystemParams(**dict(zip(TwistSystemParams.model_fields, values, strict=False)))

        warp = self._by_name("ThamSoMacKiem")
        wv = [_d(warp.get(n.casefold(), ["", ""])[1]) for n in WARP_CHECK_NAMES]
        counts = self._rows("ChiSo")
        return NormTables(
            minute_rates=[MinuteRate(stage=r[0], speed=_d(r[1]), spindles=_d(r[2]), reel=_d(r[3]), minutes=_d(r[4]),
                                     rates=_items(r[5:11], SIX)) for r in self._rows("DonGiaPhut") if r[0]],
            twist=TwistParams(filament=system(1), spun=system(2),
                              staff_total=_d(twist.get(TWIST_STAFF_NAME.casefold(), ["", ""])[1]),
                              hours_per_day=_d(twist.get(TWIST_HOURS_NAME.casefold(), ["", ""])[1])),
            warp_check=WarpCheckParams(standard_ends=wv[0], standard_beats=wv[1], twist_factor=wv[2],
                                       check_speed_greige=wv[3], check_speed_dye=wv[4]),
            size_norms=[SizeNorm(material=r[0], group=r[1],
                                 items=_items(r[2:8], SIX).model_copy(update={"chemical": _d(r[8])}))
                        for r in self._rows("DinhMucHo") if r[0]],
            weave_norms=[WeaveNorm(density=int(_d(r[0])), items=_items(r[1:7], SIX)) for r in self._rows("DinhMucDet") if r[0]],
            yarn_counts=[YarnCount(fiber_system=r[0], count=r[1], converted=_d(r[2])) for r in counts if r[1]],
            twist_levels=[int(_d(r[4])) for r in counts if len(r) > 4 and r[4]],
            hcm_standard=[HcmStandardNorm(fabric_type=r[0], color=r[1], items=_items(r[2:9], HCM7))
                          for r in self._rows("NhuomHCM_TieuChuan") if r[0]],
            hcm_stages=[HcmStageNorm(name=r[0], items=_items(r[1:8], HCM7), loss_rate=_d(r[8]))
                        for r in self._rows("NhuomHCM_CongDoan") if r[0]],
            hcm_features=[HcmFeatureNorm(feature=r[0], fabric_type=r[1], chemical_note=r[2], items=_items(r[3:10], HCM7))
                          for r in self._rows("NhuomHCM_TinhNang") if r[0]],
            tcdn_processes=[TcdnProcess(code=r[0], component=r[1], material=r[2], color=r[3], process=r[4],
                                        items=_items(r[5:12], TCDN7), workshop=r[12], loss_rate=_d(r[13]))
                            for r in self._rows("NhuomTCDN_QuyTrinh") if r[0]],
            tcdn_chemicals=[TcdnChemical(key=r[0], weight_group=r[1], cost=_d(r[2]))
                            for r in self._rows("NhuomTCDN_HoaChat") if r[0]],
            lists=[ListItem(category=r[0], value=r[1]) for r in self._rows("DanhMuc") if r[0] and r[1]],
            spandex=self._spandex(),
        )  # fmt: skip

    def _spandex(self) -> list[SpandexAddition]:
        if self.book.sheet(SPANDEX_SHEET) is None:
            return seed_spandex()
        return [SpandexAddition(spandex=_d(r[0]), addition=_d(r[1])) for r in self._rows(SPANDEX_SHEET) if r[0]]


def _cell_value(column: str, value: str) -> Any:
    """Numbers are written as numbers in the template."""
    if column in ("Công đoạn", "Tham số", "Nguyên liệu hồ", "Nhóm tổng canh", "Hệ sợi", "Chi số", "Loại vải",
                  "Cấp màu", "Tính năng", "Hóa chất sử dụng", "Mã quy trình", "Thành phần nhuộm", "Nguyên liệu nhuộm",
                  "Quy trình chuẩn", "Xưởng", "Khóa", "Nhóm trọng lượng", "Loại danh mục", "Giá trị_text"):  # fmt: skip
        return value
    if value == "":
        return None
    try:
        number = Decimal(value)
    except InvalidOperation:
        return value
    return int(number) if number == number.to_integral_value() else float(number)


class NormTemplateBuilder(BaseBuilder[FileDownloadDTO]):
    """UC-06: F-05 file filled with the set in force, named bo-dinh-muc-<YYYYMMDD>.xlsx."""

    def __init__(self, book: NormWorkbook, file_name: str) -> None:
        self.book = book
        self.file_name = file_name

    def build(self) -> FileDownloadDTO:
        data = {}
        for sheet in self.book.sheets:
            rows = []
            for row in sheet.rows:
                record = {}
                for column, value in zip(sheet.columns, row, strict=False):
                    keep_text = sheet.name == "DanhMuc"
                    record[column] = value if keep_text else _cell_value(column, value)
                rows.append(record)
            data[sheet.name] = rows or [dict.fromkeys(sheet.columns, None)]
        return FileDownloadDTO(filename=self.file_name, content=ExcelWriter().write(data), mime_type=MimeType.XLSX)
