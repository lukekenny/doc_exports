# Template Authoring Guide

Sample templates are generated dynamically the first time the app runs (or whenever you execute `python -m export_service.template_setup`). They live under `templates/` but are ignored by git so you can safely modify them per deployment.

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
