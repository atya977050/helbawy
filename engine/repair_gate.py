#!/usr/bin/env python3

import json
from pathlib import Path

from engine.approval import ApprovalGate, ApprovalError


class RepairGateError(Exception):
    pass


class RepairGate:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.plan_path = self.project_path / "plans" / "execution-plan.json"

    def load_candidates(self):
        if not self.plan_path.exists():
            raise RepairGateError(
                f"Execution plan is missing: {self.plan_path}"
            )

        try:
            plan = json.loads(
                self.plan_path.read_text(encoding="utf-8")
            )
        except json.JSONDecodeError as exc:
            raise RepairGateError(
                f"Execution plan is invalid JSON: {self.plan_path}"
            ) from exc

        candidates = plan.get("repair_candidates", [])

        if not candidates:
            raise RepairGateError("No repair candidates found.")

        return candidates

    def show(self):
        candidates = self.load_candidates()

        print("\n" + "=" * 70)
        print(" P45 REPAIR GATE")
        print("=" * 70)
        print("اختر إصلاحًا واحدًا أو أكثر من المرشحات التالية:")
        print("مثال: 1 أو 1,3 أو 1,2,4,5,6")
        print("اكتب 0 للإلغاء.\n")

        for number, candidate in enumerate(candidates, 1):
            print(f"[{number}] {candidate.get('title', 'Untitled')}")
            print(f"    Candidate : {candidate.get('candidate_id')}")
            print(f"    Severity  : {candidate.get('severity')}")
            print(f"    Target    : {candidate.get('target')}")
            print(f"    Status    : {candidate.get('status')}")
            print()

        choice = input(
            "اختر أرقام الإصلاحات: "
        ).strip()

        if choice == "0":
            print("[!] Gate cancelled.")
            return None

        try:
            numbers = []
            for part in choice.split(","):
                number = int(part.strip())
                if number < 1 or number > len(candidates):
                    raise ValueError
                if number not in numbers:
                    numbers.append(number)
        except ValueError:
            print("[!] Invalid repair selection.")
            return None

        selected = [candidates[number - 1] for number in numbers]

        print("\n" + "-" * 70)
        print(" SELECTED REPAIRS")
        print("-" * 70)

        for number, candidate in zip(numbers, selected):
            print(f"\n[{number}] {candidate.get('title')}")
            print(f"Candidate : {candidate.get('candidate_id')}")
            print(f"Reason    : {candidate.get('reason')}")
            print(f"Class     : {candidate.get('classification')}")
            print(f"Severity  : {candidate.get('severity')}")
            print(f"Target    : {candidate.get('target')}")
            print(f"Status    : {candidate.get('status')}")
            print(f"Requires  : {candidate.get('requires')}")

            print("Evidence:")
            for item in candidate.get("evidence", []):
                print(f"  - {item}")

            print("Verification:")
            for item in candidate.get("verification", []):
                print(f"  - {item}")

            if str(candidate.get("status", "")).upper() != "PROPOSED":
                print(
                    f"\n[!] Candidate is not awaiting approval: "
                    f"{candidate.get('candidate_id')}"
                )
                return None

        approval = input(
            "\nهل توافق على اعتماد الإصلاحات المختارة للتنفيذ؟ (yes/no): "
        ).strip().lower()

        if approval not in ("yes", "y"):
            print("[!] Selected repair candidates were not approved.")
            return None

        results = []

        for candidate in selected:
            try:
                result = ApprovalGate(
                    self.project_path
                ).approve(candidate["candidate_id"])
            except ApprovalError as exc:
                raise RepairGateError(str(exc)) from exc

            results.append(result)

        print("\n" + "=" * 70)
        print(" REPAIR CANDIDATES APPROVED")
        print("=" * 70)

        for result in results:
            print(f"Candidate : {result['candidate_id']}")
            print(f"Target    : {result.get('target')}")
            print(f"Reason    : {result.get('reason')}")
            print(f"Approved  : {result['approved']}")
            print(f"At        : {result['approved_at']}")
            print()

        print("[+] Approval recorded for all selected candidates.")
        print("[+] No repair was executed by the gate.")

        return results
