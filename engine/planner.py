#!/usr/bin/env python3
"""
P45 Evidence-Based Engineering Planner

Discovery -> Evidence -> Diagnosis -> Repair Plan

The planner does not modify project files.
It consumes project-local reports and produces a traceable plan.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

try:
    from engine.contracts import Evidence, RepairAction, RepairPlan
except ModuleNotFoundError:
    from contracts import Evidence, RepairAction, RepairPlan


class PlanningError(RuntimeError):
    pass


class EngineeringPlanner:
    def __init__(self, project_path, goal="general_repair"):
        self.project_path = Path(project_path).resolve()
        self.goal = goal
        self.reports_dir = self.project_path / "reports"
        self.plans_dir = self.project_path / "plans"

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat()

    def _load_report(self, name, required=True):
        path = self.reports_dir / name

        if not path.exists():
            if required:
                raise PlanningError(
                    f"Required report is MISSING: {path}"
                )
            return {}, path

        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PlanningError(
                f"Report is INVALID JSON: {path}"
            ) from exc

        if not isinstance(report, dict):
            raise PlanningError(
                f"Report is INVALID: expected JSON object: {path}"
            )

        return report, path

    @staticmethod
    def _report_status(report, path):
        status = report.get("status")

        if not status:
            raise PlanningError(
                f"Report has no explicit status: {path}"
            )

        return str(status).upper()

    @staticmethod
    def _assert_report_current(report_name, report_path, input_paths):
        report_mtime = report_path.stat().st_mtime_ns

        stale_inputs = []
        for input_path in input_paths:
            if input_path.exists() and input_path.stat().st_mtime_ns > report_mtime:
                stale_inputs.append(str(input_path))

        if stale_inputs:
            raise PlanningError(
                f"Report is STALE: {report_name}; "
                f"newer inputs detected: {', '.join(stale_inputs)}"
            )

    def _require_valid_report(self, name, input_paths=None):
        report, path = self._load_report(name, required=True)
        status = self._report_status(report, path)

        forbidden = {
            "MISSING",
            "INVALID",
            "STALE",
            "EVIDENCE_LIMITED",
            "FAILED",
            "INCOMPLETE",
        }

        if status in forbidden:
            raise PlanningError(
                f"Report cannot be consumed as valid evidence: "
                f"{name} status={status}"
            )

        if input_paths:
            self._assert_report_current(
                name,
                path,
                input_paths,
            )

        return report, path

    def _evidence_dict(self, evidence):
        return {
            "source": evidence.source,
            "finding": evidence.finding,
            "status": evidence.status,
            "file": evidence.file,
            "line": evidence.line,
            "details": evidence.details,
        }

    def _action_dict(self, action):
        return {
            "action_id": action.action_id,
            "target": action.target,
            "reason": action.reason,
            "status": action.status,
            "before_sha256": action.before_sha256,
            "after_sha256": action.after_sha256,
            "snapshot": action.snapshot,
            "verification": action.verification,
            "evidence": [
                self._evidence_dict(item)
                for item in action.evidence
            ],
        }

    def diagnose_and_plan(self):
        print(f"[*] Starting evidence-based diagnosis for goal: '{self.goal}'")

        scan_report, scan_path = self._require_valid_report(
            "scan-report.json"
        )

        contracts_report, contracts_path = self._require_valid_report(
            "contracts-report.json",
            input_paths=[scan_path],
        )

        contract_graph, graph_path = self._require_valid_report(
            "contract-graph.json",
            input_paths=[scan_path, contracts_path],
        )

        root_cause_report, root_cause_path = self._require_valid_report(
            "root-cause-report.json",
            input_paths=[graph_path, contracts_path],
        )

        findings = []
        evidence_items = []
        actions = []
        repair_candidates = []

        # ---------------------------------------------------------
        # 1. Validate project identity against the fresh scan report
        # ---------------------------------------------------------
        scan_root = scan_report.get("root")

        if scan_root:
            resolved_scan_root = str(Path(scan_root).resolve())
            if resolved_scan_root != str(self.project_path):
                raise PlanningError(
                    "Scan report belongs to a different project: "
                    f"{resolved_scan_root}"
                )
        else:
            evidence_items.append(
                Evidence(
                    source=str(scan_path),
                    finding="Scan report has no project root.",
                    status="EVIDENCE_INCOMPLETE",
                    details={"limitation": "Project identity could not be independently confirmed."},
                )
            )

        # ---------------------------------------------------------
        # 2. Project structure evidence
        # ---------------------------------------------------------
        files = scan_report.get("files", [])
        classification = scan_report.get("classification", {})

        evidence_items.append(
            Evidence(
                source=str(scan_path),
                finding=f"Scanner identified {len(files)} project files.",
                status="EVIDENCED",
                details={
                    "file_count": len(files),
                    "directory_count": len(scan_report.get("directories", [])),
                },
            )
        )

        client_files = classification.get("client", [])
        server_files = classification.get("server", [])
        config_files = classification.get("config", [])
        test_files = classification.get("tests", [])

        if client_files:
            evidence_items.append(
                Evidence(
                    source=str(scan_path),
                    finding=f"Client classification contains {len(client_files)} file(s).",
                    status="EVIDENCED",
                    file=client_files[0],
                    details={"files": client_files},
                )
            )
        else:
            findings.append({
                "severity": "WARNING",
                "issue": "No client files were classified by the scanner.",
                "evidence": str(scan_path),
            })

        if server_files:
            evidence_items.append(
                Evidence(
                    source=str(scan_path),
                    finding=f"Server classification contains {len(server_files)} file(s).",
                    status="EVIDENCED",
                    file=server_files[0],
                    details={"files": server_files},
                )
            )
        else:
            findings.append({
                "severity": "WARNING",
                "issue": "No server files were classified by the scanner.",
                "evidence": str(scan_path),
            })

        if config_files:
            evidence_items.append(
                Evidence(
                    source=str(scan_path),
                    finding=f"Configuration classification contains {len(config_files)} file(s).",
                    status="EVIDENCED",
                    file=config_files[0],
                    details={"files": config_files},
                )
            )

        if not test_files:
            findings.append({
                "severity": "WARNING",
                "issue": "No test files were classified by the scanner.",
                "evidence": str(scan_path),
            })
            evidence_items.append(
                Evidence(
                    source=str(scan_path),
                    finding="No test files were classified.",
                    status="EVIDENCED",
                    details={"classification": "tests", "count": 0},
                )
            )

        # ---------------------------------------------------------
        # 3. Communication / WebRTC contract evidence
        # ---------------------------------------------------------
        emits = contracts_report.get("emits", [])
        handlers = contracts_report.get("handlers", [])
        socketio_initialization = contracts_report.get(
            "socketio_initialization", []
        )
        webrtc = contracts_report.get("webrtc", [])
        analyzer_findings = contracts_report.get("findings", [])

        evidence_items.append(
            Evidence(
                source=str(contracts_path),
                finding=(
                    f"Contract analyzer inspected "
                    f"{contracts_report.get('files_analyzed', 0)} file(s)."
                ),
                status="EVIDENCED",
                details={
                    "emits": len(emits),
                    "handlers": len(handlers),
                    "socketio_initialization": len(socketio_initialization),
                    "webrtc_apis": len(webrtc),
                    "analyzer_findings": len(analyzer_findings),
                },
            )
        )

        if socketio_initialization:
            evidence_items.append(
                Evidence(
                    source=str(contracts_path),
                    finding=(
                        "Socket.IO initialization evidence was detected "
                        f"in {len(socketio_initialization)} location(s)."
                    ),
                    status="EVIDENCED",
                    details={
                        "initialization": socketio_initialization,
                    },
                )
            )

        if emits or handlers:
            evidence_items.append(
                Evidence(
                    source=str(contracts_path),
                    finding=(
                        f"Direct Socket.IO contracts detected: "
                        f"{len(emits)} emit(s), {len(handlers)} handler(s)."
                    ),
                    status="EVIDENCED",
                    details={
                        "emits": emits,
                        "handlers": handlers,
                    },
                )
            )
        else:
            evidence_items.append(
                Evidence(
                    source=str(contracts_path),
                    finding=(
                        "No direct Socket.IO emit/on contracts were detected "
                        "by the current static analyzer."
                    ),
                    status="EVIDENCE_LIMITED",
                    details={
                        "limitation": (
                            "Absence of direct regex matches is not proof "
                            "that no indirect or dynamic contract exists."
                        ),
                    },
                )
            )

        if webrtc:
            evidence_items.append(
                Evidence(
                    source=str(contracts_path),
                    finding=(
                        f"WebRTC API evidence detected across "
                        f"{len(webrtc)} API occurrence group(s)."
                    ),
                    status="EVIDENCED",
                    details={
                        "webrtc": webrtc,
                    },
                )
            )

        # Preserve analyzer findings as traceable diagnosis evidence.
        for item in analyzer_findings:
            code = item.get("code", "UNKNOWN")
            severity = item.get("severity", "INFO")
            status = item.get("status", "EVIDENCED")
            message = item.get("message", code)

            findings.append({
                "severity": severity,
                "issue": message,
                "code": code,
                "evidence": str(contracts_path),
                "status": status,
                "details": {
                    key: value
                    for key, value in item.items()
                    if key not in {"code", "severity", "status", "message"}
                },
            })

            evidence_items.append(
                Evidence(
                    source=str(contracts_path),
                    finding=f"{code}: {message}",
                    status=status,
                    details=item,
                )
            )

        # ---------------------------------------------------------
        # 4. Build only evidence-backed repair actions
        # ---------------------------------------------------------
        if not test_files:
            action_evidence = [
                item for item in evidence_items
                if "test files" in item.finding.lower()
            ]

            actions.append(
                RepairAction(
                    action_id="P45-PLAN-TEST-COVERAGE-001",
                    target="",
                    reason=(
                        "Establish project verification coverage before "
                        "claiming behavioral repair success."
                    ),
                    evidence=action_evidence,
                    status="PLANNED",
                    verification=[
                        "Add or identify executable project tests.",
                        "Run tests after any repair.",
                    ],
                )
            )

        # ---------------------------------------------------------
        # 5. Root Cause -> Repair Candidates
        # ---------------------------------------------------------
        # Candidates are proposals only.
        # They NEVER modify project files and ALWAYS require approval.
        root_causes = root_cause_report.get("root_causes", [])

        evidence_items.append(
            Evidence(
                source=str(root_cause_path),
                finding=(
                    f"Root Cause Engine produced "
                    f"{len(root_causes)} traceable root cause(s)."
                ),
                status="EVIDENCED",
                details={
                    "summary": root_cause_report.get("summary", {}),
                },
            )
        )

        # ---------------------------------------------------------
        # 5. Root Cause -> Repair Candidates
        #
        # IMPORTANT:
        # target/anchor come from the actual root-cause evidence.
        # No project-specific target map is used.
        # ---------------------------------------------------------
        for cause in root_causes:
            cause_id = cause.get("id", "UNKNOWN")
            context = cause.get("repair_context") or {}

            target = context.get("target", "")
            anchor = context.get("anchor", "")
            design_type = context.get("design_type")

            design = {
                "type": design_type,
                "anchor": anchor,
                "anchor_source": context.get("source"),
            }

            if not target or not anchor:
                design["generation_status"] = "BLOCKED"
                design["generation_reason"] = (
                    "No unique source anchor was discovered from actual project evidence."
                )

            repair_candidates.append({
                "candidate_id": f"P45-REPAIR-CANDIDATE-{cause_id}",
                "reason": cause_id,
                "title": cause.get(
                    "title",
                    "Unspecified root cause",
                ),
                "classification": cause.get(
                    "classification",
                    "EVIDENCE_LIMITED",
                ),
                "severity": cause.get("severity", "INFO"),
                "target": target,
                "status": "PROPOSED",
                "requires": "APPROVAL",
                "evidence": cause.get("evidence", []),
                "repair_context": context,
                "verification": [
                    "Re-read the actual target source before generation.",
                    "Require the discovered anchor to occur exactly once.",
                    "Verify the generated change after approval and execution.",
                ],
                "design": design,
            })

        # ---------------------------------------------------------
        # 6. Legacy-compatible execution steps
        # ---------------------------------------------------------
        steps = [
            {
                "step": 1,
                "action": "Verify environmental prerequisites and dependencies.",
                "status": "pending",
            },
            {
                "step": 2,
                "action": f"Address evidence-backed diagnostic findings for goal: {self.goal}",
                "status": "pending",
                "findings_count": len(findings),
            },
            {
                "step": 3,
                "action": "Execute only approved repair actions after snapshot creation.",
                "status": "pending",
            },
            {
                "step": 4,
                "action": "Run verification and re-analyze the project.",
                "status": "pending",
            },
        ]

        # ---------------------------------------------------------
        # 6. Structured P45 plan
        # ---------------------------------------------------------
        plan_model = RepairPlan(
            project=str(self.project_path),
            goal=self.goal,
            actions=actions,
            status="PLANNED",
        )

        plan = {
            "project": plan_model.project,
            "goal": plan_model.goal,
            "status": plan_model.status,
            "created_at": plan_model.created_at,
            "findings": findings,
            "evidence": [
                self._evidence_dict(item)
                for item in evidence_items
            ],
            "actions": [
                self._action_dict(item)
                for item in plan_model.actions
            ],
            "repair_candidates": repair_candidates,

            # Legacy-compatible fields
            "diagnosis_findings": findings,
            "execution_steps": steps,

            "sources": {
                "scan_report": str(scan_path),
                "contracts_report": str(contracts_path),
                "contract_graph": str(graph_path),
                "root_cause_report": str(root_cause_path),
            },
        }

        self.plans_dir.mkdir(exist_ok=True, parents=True)
        plan_path = self.plans_dir / "execution-plan.json"
        plan_path.write_text(
            json.dumps(plan, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(
            f"[✓] Evidence-based diagnosis completed: "
            f"{len(findings)} findings, "
            f"{len(evidence_items)} evidence items, "
            f"{len(actions)} planned actions."
        )
        print(f"[+] Execution plan saved to: {plan_path}")

        return plan


if __name__ == "__main__":
    import sys

    args = sys.argv[1:]

    if not args:
        path = "."
        goal = "general_repair"
    elif len(args) == 1:
        candidate = Path(args[0])
        if candidate.exists() and candidate.is_dir():
            path = args[0]
            goal = "general_repair"
        else:
            path = "."
            goal = args[0]
    else:
        path = args[0]
        goal = args[1]

    planner = EngineeringPlanner(path, goal)

    try:
        planner.diagnose_and_plan()
    except PlanningError as exc:
        print(f"[!] PLANNING FAILED: {exc}")
        raise SystemExit(1)
