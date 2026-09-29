import urllib.parse
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sys
import os
import hmac
import secrets
import time

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "studio"

sys.path.insert(0, str(ROOT))

from engine.creation import (
    RequirementsEngine,
    ScreenProposalEngine,
    ProjectGenerator,
    ConversationState
)
from engine.ai_core import (
    AssistantEngine,
    AssistantAction,
)
from engine.options import OptionsEngine
from engine.abqaryno_master_factory import MasterAbqarynoFactory

from studio.repair_api import (
    scan as repair_scan,
    root_cause as repair_root_cause,
    plan as repair_plan,
    approve as repair_approve,
    generate as repair_generate,
    execute as repair_execute,
    verify as repair_verify,
)

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8787"))

OWNER_SESSION_TTL = 3600
OWNER_SESSIONS = {}
ZIP_ARTIFACTS = {}


class Handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):

        raw = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(raw))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.end_headers()

        self.wfile.write(raw)


    def _owner_session_token(self):
        cookie = self.headers.get("Cookie", "")
        for part in cookie.split(";"):
            part = part.strip()
            if part.startswith("abqaryno_owner_session="):
                return part.split("=", 1)[1]
        return None


    def _owner_authenticated(self):
        token = self._owner_session_token()
        if not token:
            return False

        expires = OWNER_SESSIONS.get(token)
        if not expires:
            return False

        if expires < time.time():
            OWNER_SESSIONS.pop(token, None)
            return False

        OWNER_SESSIONS[token] = time.time() + OWNER_SESSION_TTL
        return True


    def _owner_required(self):
        if self._owner_authenticated():
            return True

        self.send_json({
            "ok": False,
            "error": "يتطلب هذا الإجراء دخول المالك."
        }, status=401)
        return False


    def _send_json_cookie(self, data, cookie, status=200):
        raw = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(raw))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Set-Cookie",
            cookie
        )

        self.end_headers()
        self.wfile.write(raw)


    def read_json(self):

        length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )

        raw = self.rfile.read(length)

        return json.loads(
            raw.decode("utf-8")
        )


    def do_GET(self):



        # ALHELAWBY_PORTAL_ROUTE


        if self.path == "/portal":


            portal = STUDIO / "ui" / "portal.html"


            if portal.exists():


                self.send_response(200)


                self.send_header("Content-Type", "text/html; charset=utf-8")


                self.end_headers()


                self.wfile.write(portal.read_bytes())


            else:


                self.send_error(404)


            return


        if self.path == "/":

            raw = (
                STUDIO / "ui" / "portal.html"
            ).read_bytes()

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(raw))
            )

            self.end_headers()

            self.wfile.write(raw)

            return


        if self.path == "/create/understanding":
            raw=(STUDIO / "ui" / "create-understanding.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if self.path == "/create/requirements":
            raw=(STUDIO / "ui" / "create-requirements.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if self.path == "/create/plan":
            raw=(STUDIO / "ui" / "create-plan.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if self.path == "/create/build":
            raw=(STUDIO / "ui" / "create-build.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return

        if self.path == "/api/options":
            self.send_json({
                "ok": True,
                "options": OptionsEngine().catalog()
            })
            return

        if self.path == "/repair.html":

            raw = (
                STUDIO / "repair.html"
            ).read_bytes()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )
            self.send_header(
                "Content-Length",
                str(len(raw))
            )
            self.end_headers()
            self.wfile.write(raw)

            return


        if self.path == "/create":

            raw = (
                STUDIO / "ui" / "create-idea.html"
            ).read_bytes()

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(raw))
            )

            self.end_headers()

            self.wfile.write(raw)

            return


        if self.path == "/repair":

            raw = (
                STUDIO / "repair.html"
            ).read_bytes()

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(raw))
            )

            self.end_headers()

            self.wfile.write(raw)

            return

        if self.path.startswith("/api/project/download"):
            if not self._owner_required():
                return

            parsed = urllib.parse.urlparse(self.path)
            query = urllib.parse.parse_qs(parsed.query)
            artifact_id = query.get("id", [""])[0]

            artifact = ZIP_ARTIFACTS.get(artifact_id)

            if not artifact:
                self.send_error(404, "ZIP artifact not found")
                return

            if artifact["expires_at"] < time.time():
                ZIP_ARTIFACTS.pop(artifact_id, None)
                self.send_error(410, "ZIP artifact expired")
                return

            project_zip = Path(artifact["path"]).resolve()

            root = Path(ROOT).resolve()
            artifact_root = (
                root.parent / ".abqaryno_artifacts"
            ).resolve()

            try:
                project_zip.relative_to(root)
            except ValueError:
                try:
                    project_zip.relative_to(artifact_root)
                except ValueError:
                    self.send_error(403, "Forbidden")
                    return

            if project_zip.suffix.lower() != ".zip":
                self.send_error(400, "ZIP required")
                return

            if not project_zip.exists() or not project_zip.is_file():
                self.send_error(404, "ZIP not found")
                return

            data = project_zip.read_bytes()

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/zip"
            )
            from urllib.parse import quote

            download_name = project_zip.name
            encoded_name = quote(download_name, safe="")

            self.send_header(
                "Content-Disposition",
                'attachment; filename="abqaryno-project.zip"; '
                "filename*=UTF-8''"
                + encoded_name
            )
            self.send_header(
                "Content-Length",
                str(len(data))
            )
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_json(
            {"ok":False,"error":"Not found"},
            404
        )


    def do_POST(self):

        try:

            data = self.read_json()

            if self.path == "/api/analyze":

                idea = data.get(
                    "idea",
                    ""
                ).strip()

                if not idea:
                    raise ValueError(
                        "فكرة البرنامج مطلوبة"
                    )

                result = (
                    RequirementsEngine()
                    .analyze(idea)
                )

                self.send_json({
                    "ok":True,
                    "screens":
                        result["screens"],
                    "requirements":
                        result
                })

                return


            if self.path == "/api/proposals":

                screen = data["screen"]

                offset = int(
                    data.get(
                        "offset",
                        0
                    )
                )

                idea = data.get("idea", "").strip()

                requirements = (
                    RequirementsEngine()
                    .analyze(idea)
                    if idea
                    else data.get("requirements", {})
                )

                proposals = (
                    ScreenProposalEngine(requirements)
                    .proposals(
                        screen,
                        offset
                    )
                )

                self.send_json({
                    "ok": True,
                    "proposals": proposals
                })

                return

            if self.path == "/api/assistant":

                prompt = data.get("prompt", "").strip()

                if not prompt:
                    raise ValueError("طلب المساعد مطلوب")

                idea = data.get("idea", "").strip()

                requirements = data.get("requirements", {})

                if idea and not requirements:
                    requirements = (
                        RequirementsEngine()
                        .analyze(idea)
                    )

                screen = data.get("screen", {})
                user = data.get("user", {})

                result = AssistantEngine().handle(
                    prompt=prompt,
                    idea=idea,
                    requirements=requirements,
                    screen=screen,
                    user=user,
                )

                self.send_json(result)
                return

            if self.path == "/api/assistant/confirm":

                action_data = data.get("action", {})
                confirmed = bool(
                    data.get("confirmed", False)
                )

                if not isinstance(action_data, dict):
                    raise ValueError("بيانات الإجراء غير صالحة")

                action_id = str(
                    action_data.get("action_id", "")
                ).strip()

                if not action_id:
                    raise ValueError("معرّف الإجراء مطلوب")

                action = AssistantAction(
                    action_id=action_id,
                    title=str(
                        action_data.get("title", "")
                    ),
                    description=str(
                        action_data.get("description", "")
                    ),
                    requires_confirmation=bool(
                        action_data.get(
                            "requires_confirmation",
                            True
                        )
                    ),
                    status=str(
                        action_data.get(
                            "status",
                            "proposed"
                        )
                    ),
                )

                engine = AssistantEngine()

                if action.status != "proposed":
                    raise ValueError(
                        "الإجراء يجب أن يكون في حالة proposed قبل التأكيد"
                    )

                action = engine.actions.confirm(
                    action,
                    confirmed=confirmed,
                )

                if confirmed:
                    action = engine.actions.approve(
                        action
                    )

                self.send_json({
                    "ok": True,
                    "action": {
                        "action_id": action.action_id,
                        "title": action.title,
                        "description": action.description,
                        "requires_confirmation": (
                            action.requires_confirmation
                        ),
                        "status": action.status,
                    }
                })

                return


            if self.path == "/api/owner/status":
                self.send_json({
                    "ok": True,
                    "authenticated": self._owner_authenticated()
                })
                return


            if self.path == "/api/owner/login":
                password = str(data.get("password", ""))

                configured_password = os.environ.get(
                    "ABQARYNO_OWNER_PASSWORD",
                    ""
                )

                if not configured_password:
                    self.send_json({
                        "ok": False,
                        "error": "كلمة سر المالك غير مهيأة على السيرفر."
                    }, status=503)
                    return

                if not hmac.compare_digest(
                    password,
                    configured_password
                ):
                    self.send_json({
                        "ok": False,
                        "error": "كلمة سر المالك غير صحيحة."
                    }, status=401)
                    return

                token = secrets.token_urlsafe(32)

                OWNER_SESSIONS[token] = (
                    time.time() + OWNER_SESSION_TTL
                )

                self._send_json_cookie(
                    {
                        "ok": True,
                        "authenticated": True,
                        "expires_in": OWNER_SESSION_TTL
                    },
                    "abqaryno_owner_session="
                    + token
                    + "; Path=/; HttpOnly; SameSite=Lax; Max-Age="
                    + str(OWNER_SESSION_TTL)
                )
                return


            if self.path == "/api/project/zip":

                if not self._owner_required():
                    return

                project_path = str(
                    Path(data.get("project_path", "")).expanduser().resolve()
                )

                root = Path(ROOT).resolve()
                project = Path(project_path)

                try:
                    project.relative_to(root)
                except ValueError:
                    self.send_json({
                        "ok": False,
                        "error": "مسار المشروع غير مسموح."
                    }, status=403)
                    return

                if not project.exists() or not project.is_dir():
                    self.send_json({
                        "ok": False,
                        "error": "المشروع غير موجود."
                    }, status=404)
                    return

                artifact_root = (
                    Path(ROOT).resolve().parent
                    / ".abqaryno_artifacts"
                )
                artifact_root.mkdir(
                    parents=True,
                    exist_ok=True
                )

                generator = ProjectGenerator(ROOT)
                zip_path = generator.create_zip(
                    project,
                    output_dir=artifact_root
                )

                artifact_id = secrets.token_urlsafe(24)

                ZIP_ARTIFACTS[artifact_id] = {
                    "path": str(zip_path),
                    "expires_at": time.time() + OWNER_SESSION_TTL
                }

                self.send_json({
                    "ok": True,
                    "project_path": str(project),
                    "artifact_id": artifact_id,
                    "download": "/api/project/download?id="
                                + urllib.parse.quote(
                                    artifact_id,
                                    safe=""
                                )
                })

                return


            if self.path == "/api/state":

                state = ConversationState(
                    ROOT
                )

                state.save(data)

                self.send_json({
                    "ok":True
                })

                return


            if self.path == "/api/create":
                idea = str(
                    data.get("idea", "")
                ).strip()

                approved = data.get(
                    "approved",
                    []
                )

                options = OptionsEngine().validate(
                    data.get("options", [])
                )

                if not idea:
                    raise ValueError(
                        "فكرة البرنامج مطلوبة"
                    )

                if not approved:
                    raise ValueError(
                        "يجب اعتماد شاشة واحدة على الأقل قبل الإنشاء"
                    )

                specification = json.dumps(
                    {
                        "idea": idea,
                        "approved_screens": approved,
                        "options": options,
                    },
                    ensure_ascii=False,
                    indent=2,
                )

                project_name = idea[:80]

                factory = MasterAbqarynoFactory(
                    project_name,
                    specification,
                    root_dir=ROOT,
                )

                factory.build()

                target = factory.target_dir
                evidence_path = (
                    target / ".abqaryno-evidence.json"
                )

                evidence = {}

                if evidence_path.exists():
                    evidence = json.loads(
                        evidence_path.read_text(
                            encoding="utf-8"
                        )
                    )

                status = evidence.get(
                    "status",
                    "FAILED",
                )

                if status != "PASS":
                    self.send_json(
                        {
                            "ok": False,
                            "status": status,
                            "path": str(target),
                            "verification": evidence,
                        },
                        500,
                    )
                    return

                self.send_json(
                    {
                        "ok": True,
                        "status": "VERIFIED",
                        "path": str(target),
                        "verification": evidence,
                        "manifest": {
                            "idea": idea,
                            "approved_screens": approved,
                            "options": options,
                            "creation_engine":
                                "MasterAbqarynoFactory",
                        },
                    }
                )

                return


            # =====================================================
            # P45 Repair Studio
            # =====================================================

            if self.path == "/api/repair/scan":

                result = repair_scan(
                    data["project_path"]
                )

                self.send_json({
                    "ok": True,
                    **result,
                })

                return


            if self.path == "/api/repair/root-cause":

                result = repair_root_cause(
                    data["project_path"],
                    data.get("scan")
                )

                self.send_json({
                    "ok": True,
                    **result,
                })

                return


            if self.path == "/api/repair/plan":

                result = repair_plan(
                    data["project_path"],
                    data.get("scan"),
                    data.get("cause")
                )

                self.send_json({
                    "ok": True,
                    **result,
                })

                return


            if self.path == "/api/repair/generate":
                result = repair_generate(
                    data.get("project_path", ""),
                    data.get("candidate"),
                )
                self.send_json(result)
                return

            if self.path == "/api/repair/approve":

                result = repair_approve(
                    data["project_path"],
                    data["candidate_id"]
                )

                self.send_json({
                    "ok": True,
                    **result,
                })

                return


            if self.path == "/api/repair/execute":

                result = repair_execute(
                    project_path=data["project_path"],
                    scan_data=data.get("scan"),
                    cause=data.get("cause"),
                    plan_data=data.get("plan"),
                    candidate_id=data.get("candidate_id"),
                    target=data.get("target"),
                    reason=data.get("reason"),
                    old_text=data.get("old_text"),
                    new_text=data.get("new_text"),
                )

                self.send_json({
                    "ok": True,
                    **result,
                })

                return


            if self.path == "/api/repair/verify":

                result = repair_verify(
                    project_path=data["project_path"],
                    previous_scan=data.get("previous_scan"),
                    repair=data.get("repair"),
                    old_text=data.get("old_text"),
                    new_text=data.get("new_text"),
                )

                self.send_json({
                    "ok": True,
                    **result,
                })

                return


            self.send_json(
                {
                    "ok":False,
                    "error":"مسار غير معروف"
                },
                404
            )

        except Exception as exc:

            self.send_json(
                {
                    "ok":False,
                    "error":str(exc)
                },
                400
            )


def main():

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler
    )

    print(
        f"عبقرينو Web Studio يعمل على "
        f"http://{HOST}:{PORT}"
    )

    print(
        "أوقفه بـ Ctrl+C"
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
