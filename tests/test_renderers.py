from pathlib import Path
from zipfile import ZipFile

from export_service.doc_renderer import DocRenderer
from export_service.excel_renderer import ExcelRenderer
from export_service.models import ExportRequest, ExportOptions, Section, Table, TableRow


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
