from pathlib import Path
import json
import re


class PostBuildFinalizer:
    """
    Final gate executed immediately after project generation.

    Responsibilities:
    - inspect generated output
    - detect obvious cross-project contamination
    - preserve valid generated content
    - write a finalization report
    - block release on contamination
    """

    SOURCE_EXTENSIONS = {
        ".html",
        ".htm",
        ".js",
        ".mjs",
        ".cjs",
        ".css",
        ".json",
        ".py",
        ".md",
        ".txt",
        ".sql",
        ".xml",
        ".yaml",
        ".yml",
    }

    IGNORE_DIRS = {
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        "venv",
    }

    def __init__(self, target_dir, project_name, specification=None):
        self.target_dir = Path(target_dir)
        self.project_name = str(project_name or "").strip()
        self.specification = str(specification or "").strip()

    def run(self):
        if not self.target_dir.exists():
            return self._blocked(
                "TARGET_DIR_NOT_FOUND",
                "Generated project directory does not exist.",
            )

        contamination = self._scan_contamination()
        source_candidates = self._trace_source_candidates(contamination)

        result = {
            "engine": "PostBuildFinalizer",
            "version": 2,
            "status": "BLOCKED" if contamination else "PASSED",
            "project_name": self.project_name,
            "target_dir": str(self.target_dir),
            "contamination": contamination,
            "source_candidates": source_candidates,
            "cleaned": [],
        }

        report = self.target_dir / ".abqaryno-post-build.json"
        report.write_text(
            json.dumps(
                result,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        if contamination:
            return result

        return result

    def _scan_contamination(self):
        """
        Conservative scan.

        We do NOT delete suspicious content automatically.
        Suspicious cross-project content blocks release instead.
        """
        suspicious = []

        # Known contamination signatures observed in generated output.
        forbidden_foreign_content = (
            "منصة الاستشارات القانونية أون لاين",
            "اختيار نوع الاستشارة",
            "بوابة الاستشارات القانونية أون لاين",
        )

        for path in self._source_files():
            try:
                text = path.read_text(
                    encoding="utf-8",
                    errors="ignore",
                )
            except Exception:
                continue

            for signature in forbidden_foreign_content:
                if signature not in text:
                    continue

                # Legal consultation content is valid only when the
                # current project itself is clearly that project.
                project_text = (
                    self.project_name + " " + self.specification
                )

                legal_project = any(
                    marker in project_text
                    for marker in (
                        "استشارات قانونية",
                        "محام",
                        "المحامي",
                        "الموكل",
                        "قانون",
                        "legal",
                        "lawyer",
                        "consultation",
                    )
                )

                if not legal_project:
                    suspicious.append(
                        {
                            "file": str(path.relative_to(self.target_dir)),
                            "signature": signature,
                            "type": "CROSS_PROJECT_CONTAMINATION",
                        }
                    )

        return suspicious

    def _trace_source_candidates(self, contamination):
        """
        Trace suspicious generated signatures back to Studio source files.
        This is diagnostic only: it never modifies source or generated files.
        """
        if not contamination:
            return []

        signatures = {
            item.get("signature")
            for item in contamination
            if item.get("signature")
        }

        roots = (
            Path(__file__).resolve().parent,
            Path(__file__).resolve().parent.parent / "studio",
        )

        candidates = []

        for root in roots:
            if not root.exists():
                continue

            for path in root.rglob("*"):
                if not path.is_file():
                    continue

                if any(
                    part in self.IGNORE_DIRS
                    for part in path.parts
                ):
                    continue

                if path.suffix.lower() not in self.SOURCE_EXTENSIONS:
                    continue

                try:
                    text = path.read_text(
                        encoding="utf-8",
                        errors="ignore",
                    )
                except Exception:
                    continue

                matched = [
                    signature
                    for signature in signatures
                    if signature in text
                ]

                if matched:
                    candidates.append(
                        {
                            "file": str(
                                path.relative_to(
                                    Path(__file__).resolve().parent.parent
                                )
                            ),
                            "signatures": matched,
                        }
                    )

        return candidates

    def _source_files(self):
        for path in self.target_dir.rglob("*"):
            if not path.is_file():
                continue

            if any(
                part in self.IGNORE_DIRS
                for part in path.parts
            ):
                continue

            if path.suffix.lower() in self.SOURCE_EXTENSIONS:
                yield path

    def _blocked(self, code, message):
        result = {
            "engine": "PostBuildFinalizer",
            "version": 1,
            "status": "BLOCKED",
            "project_name": self.project_name,
            "target_dir": str(self.target_dir),
            "contamination": [
                {
                    "code": code,
                    "message": message,
                }
            ],
            "cleaned": [],
        }

        if self.target_dir.exists():
            (
                self.target_dir / ".abqaryno-post-build.json"
            ).write_text(
                json.dumps(
                    result,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

        return result
