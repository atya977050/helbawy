from pathlib import Path
from datetime import datetime, timezone
import json
import py_compile

ROOT = Path(__file__).resolve().parent
ENGINE = ROOT / "engine"

REQUIRED = [
    ENGINE / "contracts.py",
    ENGINE / "repair.py",
    ENGINE / "repair_design.py",
]

print("=== P45 ADD REPAIR DESIGN COMPILER + REPAIR GENERATOR ===")

ENGINE.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# 1. Repair Design Compiler
# ------------------------------------------------------------

design_compiler = '''from dataclasses import dataclass, asdict
from datetime import datetime, timezone


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CompiledRepairDesign:
    design_id: str
    candidate_id: str
    action_id: str
    target: str | None
    targets: list[str]
    repair_type: str
    intent: str
    depends_on: list[str]
    requires_exact_source_anchor: bool
    status: str = "COMPILED"
    execution_allowed: bool = False
    compiled_at: str = ""


class RepairDesignCompiler:
    """
    Converts an approved/design-only repair description into a
    deterministic intermediate representation.

    This component does NOT modify target files and does NOT
    generate executable source by itself.
    """

    def compile(self, action):
        design = action.get("design") or {}

        if not action.get("candidate_id"):
            raise ValueError("candidate_id is required")

        if not design.get("design_id"):
            raise ValueError("design_id is required")

        targets = []

        if design.get("target"):
            targets.append(design["target"])

        for target in design.get("targets", []):
            if target not in targets:
                targets.append(target)

        if not targets:
            raise ValueError("No repair target declared")

        return CompiledRepairDesign(
            design_id=design["design_id"],
            candidate_id=action["candidate_id"],
            action_id=action["action_id"],
            target=design.get("target"),
            targets=targets,
            repair_type=design.get("type", ""),
            intent=design.get("intent", ""),
            depends_on=list(design.get("depends_on", [])),
            requires_exact_source_anchor=bool(
                design.get("requires_exact_source_anchor", True)
            ),
            compiled_at=utc_now(),
        )

    def to_dict(self, compiled):
        return asdict(compiled)
'''


# ------------------------------------------------------------
# 2. Repair Generator
# ------------------------------------------------------------

repair_generator = '''from dataclasses import dataclass, asdict
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
            generator=f"RepairGenerator:{repair_type}",
            status="GENERATED",
            execution_allowed=False,
            generated_at=utc_now(),
        )

    def _generate_new_text(self, repair_type, old_text, action):
        """
        Deterministic repair templates.

        These templates are deliberately conservative. They do not
        invent protocol semantics when the evidence/design does not
        define them.
        """

        if repair_type == "exact_code_insertion":
            return self._generate_peer_connection(old_text)

        if repair_type == "dom_target_insertion":
            return self._generate_remote_video_dom(old_text)

        if repair_type == "media_track_binding":
            return self._generate_media_track_binding(old_text)

        if repair_type == "runtime_consistency_verification":
            raise RepairGenerationError(
                "Runtime verification is not a source-code generation action."
            )

        if repair_type in (
            "webrtc_negotiation_lifecycle",
            "multi_file_signaling_contract",
        ):
            raise RepairGenerationError(
                "This repair type requires an explicit protocol template "
                "before source generation is permitted."
            )

        raise RepairGenerationError(
            f"Unsupported repair type: {repair_type}"
        )

    @staticmethod
    def _generate_peer_connection(old_text):
        marker = "const servers = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };"

        if marker not in old_text:
            raise RepairGenerationError(
                "PeerConnection generator requires the exact servers declaration."
            )

        return (
            old_text
            + "\\n"
            + "peerConnection = new RTCPeerConnection(servers);"
        )

    @staticmethod
    def _generate_remote_video_dom(old_text):
        if "</body>" not in old_text:
            raise RepairGenerationError(
                "DOM generator requires an exact </body> anchor."
            )

        return (
            '<video id="remoteVideo" autoplay playsinline></video>\\n'
            "</body>"
        )

    @staticmethod
    def _generate_media_track_binding(old_text):
        if "localStream = await navigator.mediaDevices.getUserMedia" not in old_text:
            raise RepairGenerationError(
                "Media generator requires the getUserMedia statement."
            )

        return (
            old_text
            + "\\n"
            + "localStream.getTracks().forEach(track => "
              "peerConnection.addTrack(track, localStream));"
        )

    @staticmethod
    def to_dict(generated):
        return asdict(generated)
'''


# ------------------------------------------------------------
# 3. Do not overwrite existing implementations
# ------------------------------------------------------------

targets = {
    ENGINE / "repair_design.py": design_compiler,
    ENGINE / "repair_generator.py": repair_generator,
}

for path, content in targets.items():
    if path.exists():
        print("[!] STOP: file already exists:", path)
        print("    No files were modified.")
        raise SystemExit(2)

# Write only new engine modules.
for path, content in targets.items():
    path.write_text(content, encoding="utf-8")

# Compile before declaring success.
for path in targets:
    py_compile.compile(str(path), doraise=True)

report = {
    "report": "P45-REPAIR-GENERATOR-001",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "status": "ADDED_AND_COMPILED",
    "execution_allowed": False,
    "components": [
        "engine/repair_design.py",
        "engine/repair_generator.py",
    ],
    "capabilities": [
        "compile repair designs",
        "read exact current source",
        "derive old_text from unique anchors",
        "generate deterministic new_text where an explicit template exists",
        "preserve before SHA-256",
        "never modify target files",
        "never approve repairs",
        "never execute repairs",
    ],
    "explicit_limits": [
        "WebRTC negotiation generation is not guessed.",
        "Multi-file Socket.IO signaling generation requires an explicit protocol template.",
        "Runtime verification does not generate source code.",
    ],
}

report_path = ROOT / "reports" / "p45-repair-generator-report.json"
report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("STATUS: ADDED_AND_COMPILED")
print("ENGINE: engine/repair_design.py")
print("ENGINE: engine/repair_generator.py")
print("REPORT:", report_path)
print("EXECUTION_ALLOWED: False")
