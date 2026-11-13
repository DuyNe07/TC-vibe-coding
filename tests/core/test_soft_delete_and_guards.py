"""Soft delete in every repository, find_by index, and the volume guards (Excel rows, charts)."""

from io import BytesIO

import pandas as pd
import pytest
from openpyxl import Workbook

from backend.core import db
from backend.core.base import BaseEntity, InMemoryRepository, JsonFileRepository, SqlRepository
from backend.core.current_user import CurrentUser, set_current_user
from backend.core.exceptions import ConflictError, FileProcessingError, NotFoundError
from backend.shared.file_io import ExcelReader
from frontend.core.components.charts import (
    BIN,
    LABEL_MAX_MARKS,
    OTHER,
    SERIES,
    VALUE,
    headroom,
    keep_top,
    prepare_bars,
    prepare_histogram,
    prepare_lines,
    sample_rows,
    show_labels,
    to_long,
)


class Item(BaseEntity):
    code: str
    qty: int = 0


class ItemSqlRepository(SqlRepository[Item]):
    table_name = "core__soft_item"


class ItemMemoryRepository(InMemoryRepository[Item]):
    pass


class ItemFileRepository(JsonFileRepository[Item]):
    storage_file = "items.json"


@pytest.mark.parametrize("make", [ItemSqlRepository, ItemMemoryRepository, ItemFileRepository])
def test_delete_only_flags_the_row(make) -> None:  # type: ignore[no-untyped-def]
    set_current_user(CurrentUser("an", "An", False, frozenset()))
    try:
        repo = make()
        a, b = repo.add(Item(code="A")), repo.add(Item(code="B"))
        repo.delete(a.id)
        assert repo.get(a.id) is None and not repo.exists(a.id) and repo.count() == 1
        assert [i.code for i in repo.list_all()] == ["B"] and repo.find_by(code="A") == []
        with pytest.raises(NotFoundError):
            repo.delete(a.id)  # already deleted
        with pytest.raises(NotFoundError):
            repo.update(a)
        with pytest.raises(ConflictError):
            repo.add(Item(id=a.id, code="A"))  # the id is still stored
        deleted = repo.list_deleted()
        assert [(i.code, i.is_deleted, i.deleted_by) for i in deleted] == [("A", True, "an")]
        assert deleted[0].deleted_at is not None
        assert repo.restore(a.id).code == "A" and repo.get(a.id) is not None
        repo.clear()
        assert repo.count() == 0 and len(repo.list_deleted()) == 2 and b.id in {i.id for i in repo.list_deleted()}
    finally:
        set_current_user(None)


def test_sql_rows_keep_the_flag_in_the_document_and_dtos_never_see_it() -> None:
    repo = ItemSqlRepository()
    item = repo.add(Item(code="A"))
    assert "is_deleted" not in item.model_dump(), "XxxDTO(**entity.model_dump()) must keep working"
    repo.delete(item.id)

    async def stored() -> dict:
        async with db.engine().connect() as connection:
            return (await connection.execute(repo.table.select())).one().data

    document = db.run(stored())
    assert document["is_deleted"] is True and document["code"] == "A", "the row stays, flagged"


def test_find_by_uses_an_index_that_follows_writes() -> None:
    repo = ItemSqlRepository()
    repo.save_many([Item(code=f"C{i % 10}", qty=i) for i in range(100)])
    assert len(repo.find_by(code="C3")) == 10
    assert len(repo.find_by(code="C3", qty=13)) == 1
    repo.add(Item(code="C3", qty=999))
    assert len(repo.find_by(code="C3")) == 11, "a write drops the cached table and its indexes"
    with pytest.raises(Exception, match="unknown"):
        repo.find_by(colour="red")


def _xlsx(rows: int) -> bytes:
    book = Workbook()
    sheet = book.active
    sheet.append(["Mã", "SL"])
    for i in range(rows):
        sheet.append([f"A{i}", i])
    buffer = BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def test_excel_reader_refuses_sheets_over_the_row_limit() -> None:
    assert len(ExcelReader(max_rows=5).read(_xlsx(5))) == 5
    with pytest.raises(FileProcessingError, match="more than 5 rows"):
        ExcelReader(max_rows=5).read(_xlsx(6))


def test_bar_preparation_sums_and_groups_small_categories() -> None:
    rows = pd.DataFrame({"k": [f"c{i}" for i in range(50)] * 2, "v": list(range(50)) * 2})
    data, note = prepare_bars(to_long(rows, "k", "v"), "k", max_categories=10)
    assert len(data) == 10 and OTHER in set(data["k"]) and note
    assert data[VALUE].sum() == rows["v"].sum(), "grouping never loses value"


def test_line_preparation_thins_long_series_and_keeps_the_last_point() -> None:
    rows = pd.DataFrame({"x": range(20_000), "a": range(20_000), "b": range(20_000)})
    data, note = prepare_lines(to_long(rows, "x", ["a", "b"]), "x", max_points=1_000)
    for _, part in data.groupby(SERIES):
        assert len(part) <= 1_001 and part["x"].iloc[-1] == 19_999
    assert note


def test_histogram_bins_every_value_once_with_shared_edges() -> None:
    rows = pd.DataFrame({"v": list(range(1_000)), "g": ["a", "b"] * 500})
    data = prepare_histogram(to_long(rows, "v", "v", "g"), bins=10)
    assert len(data) == 20 and data[VALUE].sum() == 1_000, "two series x 10 bins, no value lost"
    assert list(data[data[SERIES] == "a"][BIN]) == list(data[data[SERIES] == "b"][BIN])


def test_keep_top_groups_the_rest_and_sample_rows_caps_without_reordering() -> None:
    frame = pd.DataFrame({"k": [f"c{i}" for i in range(40)], "v": range(40)})
    kept, note = keep_top(frame, "k", frame["v"], 10)
    assert kept["k"].nunique() == 10 and OTHER in set(kept["k"]) and note
    sampled, note = sample_rows(pd.DataFrame({"i": range(10_000)}), 500)
    assert len(sampled) == 500 and sampled["i"].is_monotonic_increasing and note


def test_labels_are_hidden_past_the_readable_limit() -> None:
    assert show_labels(True, LABEL_MAX_MARKS) == (True, "")
    shown, note = show_labels(True, LABEL_MAX_MARKS + 1)
    assert not shown and note
    assert show_labels(False, 5) == (False, "")


def test_headroom_leaves_space_above_and_below_printed_values() -> None:
    assert headroom(pd.Series([0, 100])) == [0.0, 120.0]
    low, high = headroom(pd.Series([-50, 50]))
    assert low < -50 and high > 50
