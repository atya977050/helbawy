from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path


class RealScreenGenerator:
    """
    Real Screen Generator

    يحول Screen Contracts إلى ملفات شاشات فعلية.

    الناتج:
      public/screens/<screen-id>.html

    بالإضافة إلى:
      public/screens/manifest.json

    كل شاشة تحتوي:
      - بيانات العقد
      - الحقول
      - validation
      - actions
      - API wiring
      - loading/error/success states
    """

    VERSION = 1

    def __init__(self, project_dir, contracts):
        self.project_dir = Path(project_dir)
        self.public_dir = self.project_dir / "public"
        self.screens_dir = self.public_dir / "screens"
        self.contracts = contracts or []

    @staticmethod
    def _safe_id(value, fallback):
        value = str(value or "").strip().lower()

        value = re.sub(
            r"[^a-z0-9_-]+",
            "-",
            value,
        )

        value = re.sub(
            r"-+",
            "-",
            value,
        ).strip("-")

        return value or fallback

    @staticmethod
    def _json(value):
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _field_html(self, field):
        if isinstance(field, dict):
            field_id = self._safe_id(
                field.get("id"),
                "field",
            )

            name = str(
                field.get("name")
                or field_id
            )

            field_type = str(
                field.get("type")
                or "text"
            ).lower()

            required = (
                " required"
                if field.get("required")
                else ""
            )
        else:
            name = str(field).strip()
            field_id = self._safe_id(
                name,
                "field",
            )
            field_type = "text"
            required = ""

        input_type = {
            "email": "email",
            "number": "number",
            "date": "date",
            "datetime": "datetime-local",
            "password": "password",
            "tel": "tel",
            "url": "url",
        }.get(field_type, "text")

        if field_type in {
            "textarea",
            "longtext",
        }:
            control = (
                f'<textarea id="{field_id}" '
                f'name="{name}"{required}></textarea>'
            )
        else:
            control = (
                f'<input id="{field_id}" '
                f'name="{name}" '
                f'type="{input_type}"{required}>'
            )

        return f"""
        <label class="field">
            <span>{name}</span>
            {control}
        </label>
        """

    def _actions_html(self, actions):
        parts = []

        for action in actions:
            if isinstance(action, dict):
                action_id = self._safe_id(
                    action.get("id"),
                    "action",
                )
                label = (
                    action.get("label")
                    or action_id
                )
            else:
                label = str(action).strip()
                action_id = self._safe_id(
                    label,
                    "action",
                )

            parts.append(
                f"""
                <button
                    type="button"
                    class="action"
                    data-action="{action_id}">{label}
                </button>
                """
            )

        return "\n".join(parts)

    def _screen_html(self, contract):
        screen_id = self._safe_id(
            contract.get("id"),
            "screen",
        )

        title = contract.get(
            "title",
            screen_id,
        )

        purpose = contract.get(
            "purpose",
            "",
        )

        fields = contract.get(
            "fields",
            [],
        )

        actions = contract.get(
            "actions",
            [],
        )

        contract_json = self._json(contract)

        fields_html = "\n".join(
            self._field_html(field)
            for field in fields
        )

        actions_html = self._actions_html(
            actions
        )

        return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport"
      content="width=device-width,initial-scale=1">
<title>{title}</title>

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    font-family: Arial, sans-serif;
    background: #f5f6f8;
    color: #222;
}}

.page {{
    max-width: 900px;
    margin: 30px auto;
    padding: 20px;
}}

.card {{
    background: white;
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 8px 30px rgba(0,0,0,.08);
}}

h1 {{
    margin-top: 0;
}}

.purpose {{
    color: #666;
    margin-bottom: 25px;
}}

.form {{
    display: grid;
    gap: 16px;
}}

.field {{
    display: grid;
    gap: 7px;
}}

.field span {{
    font-weight: 700;
}}

.field input,
.field textarea {{
    width: 100%;
    padding: 12px;
    border: 1px solid #ccd0d5;
    border-radius: 10px;
    font-size: 16px;
}}

.field textarea {{
    min-height: 120px;
}}

.actions {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-top: 20px;
}}

.action {{
    border: 0;
    border-radius: 10px;
    padding: 12px 20px;
    cursor: pointer;
    font-weight: 700;
}}

.status {{
    margin-top: 20px;
    padding: 12px;
    border-radius: 10px;
    background: #f0f2f5;
    white-space: pre-wrap;
}}
</style>
</head>

<body>

<main class="page">
<section class="card">

<h1>{title}</h1>

<div class="purpose">
{purpose}
</div>

<form id="screenForm" class="form">
{fields_html}
</form>

<div class="actions">
{actions_html}
</div>

<div id="status" class="status">
جاهز.
</div>

</section>
</main>

<script>
"use strict";

const SCREEN_CONTRACT = {contract_json};

const form = document.getElementById("screenForm");
const statusBox = document.getElementById("status");

function setStatus(message) {{
    statusBox.textContent = String(message);
}}

function collectFormData() {{
    const data = {{}};

    if (!form) {{
        return data;
    }}

    const elements = form.querySelectorAll(
        "input, textarea, select"
    );

    elements.forEach((element) => {{
        data[element.name || element.id] =
            element.value;
    }});

    return data;
}}

function validateForm() {{
    if (!form) {{
        return true;
    }}

    if (!form.reportValidity()) {{
        setStatus(
            "يرجى استكمال البيانات المطلوبة."
        );
        return false;
    }}

    return true;
}}

async function executeAction(action) {{

    if (!validateForm()) {{
        return;
    }}

    const data = collectFormData();

    const method = String(
        action.method || "POST"
    ).toUpperCase();

    const api = action.api;

    if (!api) {{
        setStatus(
            "تم تنفيذ التحقق محليًا. " +
            "هذه الشاشة لا تحتوي على API محدد " +
            "داخل العقد بعد."
        );

        console.log(
            "SCREEN_ACTION",
            {{
                screen: SCREEN_CONTRACT.id,
                action,
                data
            }}
        );

        return;
    }}

    setStatus("جارٍ التنفيذ...");

    try {{

        const response = await fetch(
            api,
            {{
                method,
                headers: {{
                    "Content-Type":
                        "application/json"
                }},
                body:
                    method === "GET"
                        ? undefined
                        : JSON.stringify(data)
            }}
        );

        const text =
            await response.text();

        if (!response.ok) {{
            throw new Error(
                "HTTP " +
                response.status +
                ": " +
                text
            );
        }}

        setStatus(
            "تم التنفيذ بنجاح.\\n" +
            text
        );

    }} catch (error) {{

        setStatus(
            "فشل تنفيذ العملية:\\n" +
            error.message
        );

        console.error(error);
    }}
}}

document
    .querySelectorAll("[data-action]")
    .forEach((button) => {{

        button.addEventListener(
            "click",
            () => {{

                const id =
                    button.dataset.action;

                const action =
                    SCREEN_CONTRACT.actions
                        .find(
                            item =>
                                item.id === id
                        );

                if (!action) {{
                    setStatus(
                        "Action غير موجودة في العقد."
                    );
                    return;
                }}

                executeAction(action);
            }}
        );
    }});
</script>

</body>
</html>
"""

    def generate(self):
        self.screens_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        generated = []

        for index, contract in enumerate(
            self.contracts
        ):
            screen_id = self._safe_id(
                contract.get("id"),
                f"screen-{index + 1}",
            )

            path = (
                self.screens_dir
                / f"{screen_id}.html"
            )

            path.write_text(
                self._screen_html(contract),
                encoding="utf-8",
            )

            generated.append(
                {
                    "id": contract.get(
                        "id",
                        screen_id,
                    ),
                    "title": contract.get(
                        "title",
                        screen_id,
                    ),
                    "file": str(
                        path.relative_to(
                            self.public_dir
                        )
                    ),
                    "status": "generated",
                }
            )

        manifest = {
            "version": self.VERSION,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "total": len(generated),
            "screens": generated,
        }

        manifest_path = (
            self.screens_dir
            / "manifest.json"
        )

        manifest_path.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        return {
            "version": self.VERSION,
            "status": "PASSED",
            "total": len(generated),
            "screens": generated,
            "manifest": str(
                manifest_path
            ),
        }
