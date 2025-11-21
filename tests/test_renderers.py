from pathlib import Path
from zipfile import ZipFile

from export_service.doc_renderer import DocRenderer
from export_service.excel_renderer import ExcelRenderer
from export_service.models import ExportRequest, ExportOptions, Section, Table, TableRow
from export_service.text_renderer import TextRenderer


def sample_request() -> ExportRequest:
    return ExportRequest(
        title="Monthly Sales",
        summary="Summary",
        session_id="abc",
        sections=[Section(heading="Overview", body="Details")],
        tables=[
            Table(
                name="SalesByRegion",
                columns=["region", "sales"],
                rows=[TableRow(__root__={"region": "East", "sales": 10})],
            )
        ],
        options=ExportOptions(include_xlsx=True, zip_all=True),
    )


def sample_request_with_list_rows() -> ExportRequest:
    return ExportRequest(
        title="Members",
        summary="Details",
        session_id="xyz",
        tables=[
            {
                "name": "Members",
                "columns": ["name", "region", "phone"],
                "rows": [
                    ["Member A", "Metro", "123"],
                    ["Member B", "Rural"],
                    ["Member C", "Coastal", "999", "extra"],
                ],
            }
        ],
        options=ExportOptions(include_xlsx=True, zip_all=True),
    )


def test_doc_renderer_creates_doc(tmp_path):
    renderer = DocRenderer()
    request = sample_request()
    output = renderer.render(request, tmp_path)
    assert output.exists()
    with ZipFile(output) as archive:
        xml = archive.read("word/document.xml").decode()
    assert "Monthly Sales" in xml
    assert "Overview" in xml


def test_excel_renderer_creates_sheet(tmp_path):
    renderer = ExcelRenderer()
    request = sample_request()
    output = renderer.render(request, tmp_path)
    assert output.exists()


def test_excel_renderer_accepts_list_rows(tmp_path):
    renderer = ExcelRenderer()
    request = sample_request_with_list_rows()
    output = renderer.render(request, tmp_path)
    assert output.exists()
    table = request.tables[0]
    assert table.rows[0].root == {"name": "Member A", "region": "Metro", "phone": "123"}
    assert table.rows[1].root == {"name": "Member B", "region": "Rural", "phone": None}
    assert table.rows[2].root == {
        "name": "Member C",
        "region": "Coastal",
        "phone": "999",
        "column_4": "extra",
    }


def test_text_renderer_outputs_plain_text(tmp_path):
    renderer = TextRenderer()
    request = sample_request()
    request.options.include_txt = True
    output = renderer.render(request, tmp_path)
    assert output.exists()
    content = output.read_text()
    assert "Monthly Sales" in content
    assert "Overview" in content
    assert "East" in content
