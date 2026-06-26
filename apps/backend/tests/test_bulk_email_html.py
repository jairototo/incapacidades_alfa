"""Unit tests for _build_bulk_email_html() — verifies HTML structure and brand content."""
from app.tasks.email_tasks import _build_bulk_email_html


def test_html_contains_table_structure():
    items = [
        {"numero": "ARL-2026-001", "numero_documento": "10000001", "dias_totales": 7},
        {"numero": "ARL-2026-002", "numero_documento": "20000002", "dias_totales": 14},
    ]
    html = _build_bulk_email_html("TechCorp S.A.", "25/06/2026", items)

    # Valid HTML5 skeleton
    assert "<!DOCTYPE html>" in html
    assert 'lang="es"' in html

    # Header section
    assert "Seguros Alfa" in html
    assert "Confirmación de Radicación de Incapacidades" in html

    # Summary body line
    assert "TechCorp S.A." in html
    assert "25/06/2026" in html

    # Table structure with both rows
    assert "<table" in html
    assert "<thead" in html
    assert "<tbody" in html
    assert "ARL-2026-001" in html
    assert "10000001" in html
    assert ">7<" in html
    assert "ARL-2026-002" in html
    assert "20000002" in html
    assert ">14<" in html

    # Footer
    assert "generado automáticamente" in html

    # Inline styles required (no external CSS)
    assert 'style="' in html


def test_html_item_count_in_summary_line():
    items = [
        {"numero": "ARL-X", "numero_documento": "99", "dias_totales": 3},
        {"numero": "ARL-Y", "numero_documento": "88", "dias_totales": 5},
        {"numero": "ARL-Z", "numero_documento": "77", "dias_totales": 2},
    ]
    html = _build_bulk_email_html("Empresa Test", "01/01/2026", items)
    # The summary line mentions the count of items
    assert "<strong>3</strong>" in html


def test_html_single_item():
    items = [{"numero": "SALUD-001", "numero_documento": "55555", "dias_totales": 10}]
    html = _build_bulk_email_html("Empresa Única", "15/03/2026", items)
    assert "SALUD-001" in html
    assert "55555" in html
    assert ">10<" in html
    assert "<strong>1</strong>" in html
