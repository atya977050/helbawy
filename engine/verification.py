#!/usr/bin/env python3
"""
P45 Verification Engine

لا يعتبر الإصلاح ناجحًا لمجرد أنه APPLIED.
VERIFIED يتطلب دليلًا فعليًا على الحالة النهائية.
"""

from pathlib import Path

from engine.execution_log import ExecutionLog


class VerificationError(RuntimeError):
    pass


class VerificationEngine:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.execution_log = ExecutionLog(self.project_path)

    def _target(self, target):
        path = (self.project_path / target).resolve()

        try:
            path.relative_to(self.project_path)
        except ValueError as exc:
            raise VerificationError(
                f"Verification target is outside project: {target}"
            ) from exc

        if not path.exists():
            raise VerificationError(
                f"Verification target does not exist: {target}"
            )

        if not path.is_file():
            raise VerificationError(
                f"Verification target is not a file: {target}"
            )

        return path

    def verify_exact_change(
        self,
        action_id,
        target,
        old_text,
        new_text,
    ):
        path = self._target(target)
        relative = str(path.relative_to(self.project_path))

        content = path.read_text(encoding="utf-8")

        checks = {
            "target_exists": True,
            "old_text_absent": old_text not in content,
            "new_text_present": new_text in content,
        }

        failed = [
            name for name, passed in checks.items()
            if not passed
        ]

        if failed:
            self.execution_log.record(
                "VERIFY",
                action_id,
                "FAILED",
                target=relative,
                checks=checks,
                failed_checks=failed,
            )

            raise VerificationError(
                f"Verification failed for {relative}: "
                + ", ".join(failed)
            )

        self.execution_log.record(
            "VERIFY",
            action_id,
            "VERIFIED",
            target=relative,
            checks=checks,
        )

        return {
            "action_id": action_id,
            "target": relative,
            "status": "VERIFIED",
            "checks": checks,
        }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print(
            "Usage: python engine/verification.py "
            "<target> <old_text> <new_text>"
        )
        raise SystemExit(2)

    engine = VerificationEngine(".")

    try:
        result = engine.verify_exact_change(
            action_id="CLI-VERIFY",
            target=sys.argv[1],
            old_text=sys.argv[2],
            new_text=sys.argv[3],
        )
        print(result)
    except VerificationError as exc:
        print(f"[!] VERIFICATION FAILED: {exc}")
        raise SystemExit(1)
