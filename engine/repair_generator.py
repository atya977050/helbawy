from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime, timezone
import hashlib


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class GeneratedRepair:
    action_id: str
    candidate_id: str
    target: str
    old_text: str
    new_text: str
    before_sha256: str
    generator: str
    status: str
    execution_allowed: bool
    generated_at: str


class RepairGenerationError(Exception):
    pass


class RepairGenerator:
    """
    Generates evidence-backed old_text/new_text proposals.

    IMPORTANT:
    - Reads the current target source.
    - Requires an exact source anchor.
    - Never writes the target file.
    - Never approves a repair.
    - Never executes a repair.

    The generator currently provides deterministic generators for
    safe structural repairs. Complex protocol changes must have
    an explicit generator/template rather than being guessed.
    """

    def __init__(self, project_root):
        self.project_root = Path(project_root).resolve()

    def _target(self, target):
        path = (self.project_root / target).resolve()

        if self.project_root not in path.parents:
            raise RepairGenerationError(
                f"Target escapes project root: {target}"
            )

        if not path.exists():
            raise RepairGenerationError(
                f"Target does not exist: {target}"
            )

        if not path.is_file():
            raise RepairGenerationError(
                f"Target is not a file: {target}"
            )

        return path

    def _read(self, target):
        path = self._target(target)
        return path, path.read_text(encoding="utf-8")

    def _unique_anchor(self, source, anchor):
        if not anchor:
            raise RepairGenerationError(
                "Exact source anchor is required."
            )

        count = source.count(anchor)

        if count == 0:
            raise RepairGenerationError(
                "Exact source anchor was not found."
            )

        if count != 1:
            raise RepairGenerationError(
                f"Exact source anchor is ambiguous: {count} matches."
            )

    def generate(
        self,
        action,
        anchor,
    ):
        """
        Generate old_text/new_text from an approved design/action.

        `anchor` must be an exact source fragment from the current file.
        """

        target = action.get("target")
        if not target:
            raise RepairGenerationError("Repair action has no target.")

        design = action.get("design") or {}
        repair_type = design.get("type")

        path, source = self._read(target)

        self._unique_anchor(source, anchor)

        old_text = anchor
        new_text = self._generate_new_text(
            repair_type=repair_type,
            old_text=old_text,
            action=action,
        )

        if not new_text:
            raise RepairGenerationError(
                f"No generator exists for repair type: {repair_type}"
            )

        if new_text == old_text:
            raise RepairGenerationError(
                "Generated new_text is identical to old_text."
            )

        return GeneratedRepair(
            action_id=action["action_id"],
            candidate_id=action["candidate_id"],
            target=str(path.relative_to(self.project_root)),
            old_text=old_text,
            new_text=new_text,
            before_sha256=sha256_text(source),
            generator=f"RepairGenerator:{repair_type or "generic"}",
            status="GENERATED",
            execution_allowed=False,
            generated_at=utc_now(),
        )

    @staticmethod
    def _safe_transformation_from_design(design, old_text):
        """
        Resolve only transformations explicitly grounded in the repair design.

        The generator may normalize a complete replacement/insertion operation,
        but it never invents project-specific source code.
        """
        if not isinstance(design, dict):
            return None

        for key in ("replacement", "insertion", "prefix", "suffix"):
            if key in design and design[key] is not None:
                return True

        return False

    def _generate_new_text(self, repair_type, old_text, action):
        """
        Generic deterministic repair generation.

        Priority:
        1. Explicit safe transformation supplied by the repair design.
        2. A deterministic transformation strategy derived from actual
           source evidence when the design explicitly declares it.
        3. Block generation rather than guessing source code.
        """
        design = action.get("design") or {}

        if not self._safe_transformation_from_design(design, old_text):
            strategy = design.get("strategy")

            if strategy == "remove_anchor":
                if not old_text:
                    raise RepairGenerationError(
                        "Cannot remove an empty anchor."
                    )
                return ""

            if strategy == "comment_anchor":
                language = str(design.get("language") or "").lower()

                if language in {"python", "py", "shell", "bash", "yaml", "yml"}:
                    prefix = "# "
                elif language in {"html", "xml"}:
                    prefix = "<!-- "
                else:
                    prefix = "// "

                return prefix + old_text

            if strategy == "disable_anchor":
                language = str(design.get("language") or "").lower()

                if language in {"python", "py"}:
                    return "if False:\n    " + old_text.replace(
                        "\n", "\n    "
                    )

                if language in {"html", "xml"}:
                    return "<!-- " + old_text + " -->"

                return "/* " + old_text + " */"

            raise RepairGenerationError(
                "No safe generic transformation strategy was supplied "
                "by the repair design. Generation blocked; no source "
                "code was guessed."
            )

        replacement = design.get("replacement")
        if replacement is not None:
            if not isinstance(replacement, str):
                raise RepairGenerationError(
                    "Repair replacement must be text."
                )
            if replacement == old_text:
                raise RepairGenerationError(
                    "Generated new_text is identical to old_text."
                )
            return replacement

        insertion = design.get("insertion")
        if insertion is not None:
            if not isinstance(insertion, str):
                raise RepairGenerationError(
                    "Repair insertion must be text."
                )
            new_text = old_text + "\n" + insertion
            if new_text == old_text:
                raise RepairGenerationError(
                    "Generated new_text is identical to old_text."
                )
            return new_text

        prefix = design.get("prefix")
        suffix = design.get("suffix")

        if prefix is not None or suffix is not None:
            if prefix is not None and not isinstance(prefix, str):
                raise RepairGenerationError(
                    "Repair prefix must be text."
                )
            if suffix is not None and not isinstance(suffix, str):
                raise RepairGenerationError(
                    "Repair suffix must be text."
                )

            new_text = (
                (prefix or "")
                + old_text
                + (suffix or "")
            )

            if new_text == old_text:
                raise RepairGenerationError(
                    "Generated new_text is identical to old_text."
                )

            return new_text

        raise RepairGenerationError(
            "Repair design declared a transformation but supplied no "
            "usable transformation text."
        )






    @staticmethod
    def to_dict(generated):
        return asdict(generated)
