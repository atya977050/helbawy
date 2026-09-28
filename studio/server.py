#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sys
import os

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
                STUDIO / "ui" / "index.html"
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

                idea = data["idea"]

                approved = data[
                    "approved"
                ]

                options = data.get(
                    "options",
                    []
                )

                options = OptionsEngine().validate(
                    options
                )

                requirements = (
                    RequirementsEngine()
                    .analyze(idea)
                )

                generator = ProjectGenerator(
                    ROOT
                )

                target, manifest = (
                    generator.generate(
                        idea,
                        requirements,
                        approved,
                        options
                    )
                )

                self.send_json({
                    "ok":True,
                    "path":str(target),
                    "manifest":manifest
                })

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
