# Template Authoring Guide

Sample templates (DOCX, XLSX, PPTX, and TXT) are generated dynamically the first time the app runs (or whenever you execute `python -m export_service.template_setup`). They live under `templates/` but are ignored by git so you can safely modify them per deployment; when using Docker, keep that directory mounted as a volume so the files persist between container recreations.

1. `summary_template.docx`
   - Title placeholder: `{{ title }}`
   - Summary paragraph: `{{ summary }}`
   - Section loop:
     ```
     {% for section in sections %}
     {{ section.heading }}
     {{ section.body }}
     {% endfor %}
     ```
   - Table placeholder: create a Word table with a header row, then in the next row insert `{{ row.region }}`, `{{ row.sales }}`, etc., wrapped by `{% for row in tables[0].rows %} ... {% endfor %}`.

2. `full_report_template.docx`
   - Adds header/footer with page numbers and iterates over all tables by name using `{% for table in tables %}`.

3. `summary_template.xlsx`
   - Pre-populated workbook showing where `{{ title }}`, `{{ summary }}`, and table names are inserted.
   - Meant as a starting point for spreadsheet-only exports or to be zipped with other artifacts.

4. `summary_template.pptx`
   - Simple deck with a title slide, a bullet slide for sections, and a table slide summarizing row counts.
   - Customize slide layouts, backgrounds, or logos directly in PowerPoint.

5. `summary_template.txt`
   - Plain text skeleton that mirrors the DOCX layout using Markdown-like headings.

## Editing Steps
1. Run `python -m export_service.template_setup --force` to regenerate the latest base templates if needed.
2. Open the `.docx` template in Word.
3. Use built-in styles (Heading 1/2, Normal, Table Grid) to keep formatting consistent.
4. Insert logos via `Insert -> Pictures` and save under `templates/assets`. Reference with `{{ logo }}` in the document.
5. Save the document; no compilation needed. The service loads templates dynamically.

## Mapping Tables
- `tables` is a list where each item has `name`, `columns`, and `rows`.
- Access by index: `tables[0].rows`.
- Access by name:
  ```
  {% for table in tables %}
  {{ table.name }}
  {% endfor %}
  ```
  Then inside: `{% for row in table.rows %}` to render each row.

## Conditional Blocks
Use Jinja2 syntax for conditional content:
```
{% if sections %}
{{ sections|length }} sections included.
{% endif %}
```

Refer to [docxtpl documentation](https://docxtpl.readthedocs.io/) for advanced constructs (loops, filters, InlineImage).
