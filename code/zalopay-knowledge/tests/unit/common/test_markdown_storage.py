"""Unit tests for the Markdown → Confluence storage converter."""

from __future__ import annotations

from app.common.markdown_storage import md_to_storage


def test_headings():
    out = md_to_storage("# Title\n## Sub\n### Deep")
    assert "<h1>Title</h1>" in out
    assert "<h2>Sub</h2>" in out
    assert "<h3>Deep</h3>" in out


def test_table_header_and_rows():
    md = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
    out = md_to_storage(md)
    assert "<table><tbody>" in out and "</tbody></table>" in out
    assert "<tr><th>A</th><th>B</th></tr>" in out
    assert "<tr><td>1</td><td>2</td></tr>" in out
    assert "<tr><td>3</td><td>4</td></tr>" in out
    # the separator row must NOT render
    assert "---" not in out


def test_bullet_list():
    out = md_to_storage("- one\n- two\n- three")
    assert out == "<ul><li>one</li><li>two</li><li>three</li></ul>"


def test_bold_and_paragraph():
    out = md_to_storage("This is **bold** text.")
    assert out == "<p>This is <strong>bold</strong> text.</p>"


def test_horizontal_rule():
    assert "<hr/>" in md_to_storage("a\n\n---\n\nb")


def test_escapes_html_but_keeps_br():
    out = md_to_storage("x < y & z<br>next")
    assert "&lt; y &amp; z" in out
    assert "<br/>" in out
    assert "<script" not in md_to_storage("<script>alert(1)</script>")


def test_table_cell_keeps_bold_and_br():
    md = "| K | V |\n|---|---|\n| KPI | a<br>b |\n| Flag | **PASS** |"
    out = md_to_storage(md)
    assert "<td>a<br/>b</td>" in out
    assert "<td><strong>PASS</strong></td>" in out


def test_empty_input():
    assert md_to_storage("") == ""
    assert md_to_storage("\n\n") == ""
