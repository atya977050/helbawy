#!/usr/bin/env python3
"""
P45 Root Cause Engine

يحوّل Contract Graph + المصدر الفعلي إلى أسباب جذرية
قابلة للتتبع، مع الفصل بين:
CONFIRMED / DERIVED / INFERRED / EVIDENCE_LIMITED
"""

import json
import re
from pathlib import Path


class RootCauseError(RuntimeError):
    pass


class RootCauseEngine:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.reports_dir = self.project_path / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _load_json(self, path):
        if not path.exists():
            raise RootCauseError(f"Required file does not exist: {path}")
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RootCauseError(f"Invalid JSON: {path}") from exc

    def _read(self, relative):
        path = self.project_path / relative
        if path.is_file():
            return path.read_text(encoding="utf-8"), path

        # Resolve the expected source file from the actual project tree.
        # Never guess between multiple matches.
        candidates = []
        expected_parts = Path(relative).parts

        for candidate in self.project_path.rglob(Path(relative).name):
            try:
                rel = candidate.relative_to(self.project_path)
            except ValueError:
                continue

            parts = set(rel.parts)
            if not candidate.is_file():
                continue
            if {".git", "node_modules", "__pycache__", "reports"} & parts:
                continue

            rel_parts = rel.parts
            if len(rel_parts) < len(expected_parts):
                continue
            if rel_parts[-len(expected_parts):] != expected_parts:
                continue

            candidates.append(candidate)

        if len(candidates) == 1:
            path = candidates[0]
            return path.read_text(encoding="utf-8"), path

        if len(candidates) > 1:
            raise RootCauseError(
                "Ambiguous source file resolution for "
                f"{relative}: {len(candidates)} matches found."
            )

        return "", path

    @staticmethod
    def _has_any(text, patterns):
        return any(pattern in text for pattern in patterns)

    @staticmethod
    def _repair_context(project_root, evidence, design_type=None):
        """
        Derive repair context from actual project evidence.

        No project-specific filenames or hardcoded source anchors are used.
        The selected anchor must exist exactly once in the actual source.
        """
        for item in evidence or []:
            relative = item.get("file")
            if not relative:
                continue

            path = Path(project_root) / relative
            if not path.is_file():
                continue

            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            finding = str(item.get("finding", "")).strip()

            # Prefer an exact source fragment explicitly supplied by evidence.
            explicit = item.get("anchor")
            if explicit and source.count(explicit) == 1:
                return {
                    "target": relative,
                    "anchor": explicit,
                    "anchor_occurrences": 1,
                    "design_type": design_type,
                    "source": "evidence",
                }

            # Otherwise select an actual non-empty source line related to
            # the finding. Never invent source text.
            keywords = [
                token for token in re.findall(r"[A-Za-z_$][A-Za-z0-9_$.-]*", finding)
                if len(token) >= 4
            ]

            lines = source.splitlines()
            candidates = []

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    continue
                score = sum(1 for token in keywords if token in stripped)
                if score:
                    candidates.append((score, stripped))

            if candidates:
                candidates.sort(key=lambda x: (-x[0], len(x[1])))
                anchor = candidates[0][1]
                if source.count(anchor) == 1:
                    return {
                        "target": relative,
                        "anchor": anchor,
                        "anchor_occurrences": 1,
                        "design_type": design_type,
                        "source": "evidence-derived",
                    }

        return None

    def build(self):
        graph_path = self.reports_dir / "contract-graph.json"
        graph = self._load_json(graph_path)

        scan_path = self.reports_dir / "scan-report.json"
        scan = self._load_json(scan_path)
        classification = scan.get("classification", {})

        server_files = list(classification.get("server", []))
        client_files = list(classification.get("client", []))

        def read_first(paths):
            for relative in paths:
                text, path = self._read(relative)
                if text:
                    return text, path
            return "", self.project_path

        server, server_path = read_first(server_files)

        script_files = [
            item for item in client_files
            if Path(item).suffix.lower() in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".py"}
        ]
        html_files = [
            item for item in client_files
            if Path(item).suffix.lower() in {".html", ".htm"}
        ]

        client, client_path = read_first(script_files)
        html, html_path = read_first(html_files)

        causes = []

        # ---------------------------------------------------------
        # RC-CONNECTION-001
        # ---------------------------------------------------------
        if client:
            peer_exists = "RTCPeerConnection" in client

            if not peer_exists:
                causes.append({
                    "id": "RC-CONNECTION-001",
                    "title": "PeerConnection construction is absent",
                    "classification": "CONFIRMED",
                    "severity": "HIGH",
                    "evidence": [
                        {
                            "file": str(client_path.relative_to(self.project_path)),
                            "finding": (
                                "No RTCPeerConnection construction exists "
                                "in the detected client source."
                            ),
                        },
                        {
                            "source": "contract-graph.json",
                            "finding": "webrtc:peer-connection => MISSING",
                        },
                    ],
                    "effect": (
                        "The application has no constructed WebRTC peer "
                        "connection to carry media or signaling state."
                    ),
                })

        # ---------------------------------------------------------
        # RC-MESSAGE-001
        # ---------------------------------------------------------
        server_signaling = self._has_any(
            server,
            [
                "io.on(",
                "socket.on(",
                ".emit(",
                "socket.emit(",
            ],
        )

        client_signaling = self._has_any(
            client,
            [
                "socket.on(",
                "socket.emit(",
                ".on(",
                ".emit(",
            ],
        )

        if not server_signaling and not client_signaling:
            causes.append({
                "id": "RC-MESSAGE-001",
                "title": "Application communication contract is absent",
                "classification": "CONFIRMED",
                "severity": "HIGH",
                "evidence": [
                    {
                        "file": str(server_path.relative_to(self.project_path)),
                        "finding": (
                            "Socket.IO server is initialized, but no "
                            "connection, handler, or emit contract exists."
                        ),
                    },
                    {
                        "file": str(client_path.relative_to(self.project_path)),
                        "finding": (
                            "Detected client source is initialized for "
                            "application communication, but no signaling event contract exists."
                        ),
                    },
                    {
                        "source": "contract-graph.json",
                        "finding": "socketio:signaling => MISSING",
                    },
                ],
                "effect": (
                    "There is no implemented application-level signaling "
                    "path for WebRTC offer, answer, or ICE exchange."
                ),
            })

        # ---------------------------------------------------------
        # RC-MEDIA-UI-001
        # ---------------------------------------------------------
        remote_reference = (
            "remoteVideo" in client
            or "remote-video" in client
        )
        remote_element = bool(re.search(
            r'id\s*=\s*["\']remoteVideo["\']',
            html,
        ))

        if remote_reference and not remote_element:
            causes.append({
                "id": "RC-MEDIA-UI-001",
                "title": "Remote video DOM target is absent",
                "classification": "CONFIRMED",
                "severity": "HIGH",
                "evidence": [
                    {
                        "file": str(client_path.relative_to(self.project_path)),
                        "finding": (
                            "Detected client source references remoteVideo as "
                            "the target for the received media stream."
                        ),
                    },
                    {
                        "file": str(html_path.relative_to(self.project_path)),
                        "finding": (
                            "No element with the required remote media "
                            "target exists in the detected HTML source."
                        ),
                    },
                ],
                "effect": (
                    "The remote media target required by the client code "
                    "is not present in the supplied HTML."
                ),
            })

        # ---------------------------------------------------------
        # RC-MEDIA-LIFECYCLE-001
        # ---------------------------------------------------------
        captures_media = (
            "getUserMedia" in client
            and "localStream" in client
        )
        adds_tracks = (
            ".addTrack(" in client
            or "addTrack(" in client
        )

        if captures_media and not adds_tracks:
            causes.append({
                "id": "RC-MEDIA-LIFECYCLE-001",
                "title": "Captured local media is not attached to a peer",
                "classification": "DERIVED",
                "severity": "HIGH",
                "evidence": [
                    {
                        "file": str(client_path.relative_to(self.project_path)),
                        "finding": "getUserMedia() stores the result in localStream.",
                    },
                    {
                        "file": str(client_path.relative_to(self.project_path)),
                        "finding": "No addTrack() call was detected.",
                    },
                    {
                        "source": "contract-graph.json",
                        "finding": (
                            "webrtc:media-capture -> "
                            "webrtc:peer-connection => BROKEN"
                        ),
                    },
                ],
                "effect": (
                    "Based on the static source, captured media has no "
                    "detected path into a WebRTC peer connection."
                ),
                "limitation": (
                    "This is derived from source evidence and was not "
                    "runtime-tested."
                ),
            })

        # ---------------------------------------------------------
        # RC-CONNECTION-002
        # ---------------------------------------------------------
        signaling_apis = [
            "createOffer",
            "createAnswer",
            "setLocalDescription",
            "setRemoteDescription",
            "addIceCandidate",
            "onicecandidate",
        ]

        missing_signaling = [
            api for api in signaling_apis
            if api not in client
        ]

        if missing_signaling:
            causes.append({
                "id": "RC-CONNECTION-002",
                "title": "Connection negotiation and candidate lifecycle is absent",
                "classification": "CONFIRMED",
                "severity": "HIGH",
                "evidence": [
                    {
                        "file": str(client_path.relative_to(self.project_path)),
                        "finding": (
                            "The following connection APIs are absent: "
                            + ", ".join(missing_signaling)
                        ),
                    },
                    {
                        "source": "contract-graph.json",
                        "finding": (
                            "peer-connection node is MISSING with the "
                            "same API set unresolved."
                        ),
                    },
                ],
                "effect": (
                    "The source contains no implemented offer/answer "
                    "negotiation or ICE candidate lifecycle."
                ),
            })

        # ---------------------------------------------------------
        # Runtime consequence is deliberately NOT claimed confirmed.
        # ---------------------------------------------------------
        if "peerConnection.ontrack" in client and "RTCPeerConnection" not in client:
            causes.append({
                "id": "RC-RUNTIME-001",
                "title": "ontrack is assigned to an unconstructed peer reference",
                "classification": "INFERRED",
                "severity": "HIGH",
                "evidence": [
                    {
                        "file": str(client_path.relative_to(self.project_path)),
                        "finding": (
                            "A remote-track handler is assigned while "
                            "no peer-connection construction exists."
                        ),
                    },
                ],
                "effect": (
                    "Static analysis indicates that peerConnection has "
                    "no construction path before the ontrack assignment."
                ),
                "limitation": (
                    "A runtime browser test is required before claiming "
                    "the exact runtime exception and its timing."
                ),
            })

        # ---------------------------------------------------------
        # Attach repair context derived from actual project evidence.
        # Planner must consume this instead of fixed target/anchor maps.
        # ---------------------------------------------------------
        design_types = {
            "RC-CONNECTION-001": "code_insertion",
            "RC-MESSAGE-001": "multi_file_event_contract",
            "RC-MEDIA-UI-001": "dom_target_insertion",
            "RC-MEDIA-LIFECYCLE-001": "media_track_binding",
            "RC-CONNECTION-002": "connection_negotiation_lifecycle",
            "RC-RUNTIME-001": "runtime_consistency_verification",
        }

        for cause in causes:
            context = self._repair_context(
                self.project_path,
                cause.get("evidence", []),
                design_types.get(cause.get("id")),
            )
            if context:
                cause["repair_context"] = context

        report = {
            "project": str(self.project_path),
            "status": "EVIDENCED",
            "root_causes": causes,
            "summary": {
                "total": len(causes),
                "confirmed": sum(
                    item["classification"] == "CONFIRMED"
                    for item in causes
                ),
                "derived": sum(
                    item["classification"] == "DERIVED"
                    for item in causes
                ),
                "inferred": sum(
                    item["classification"] == "INFERRED"
                    for item in causes
                ),
                "evidence_limited": sum(
                    item["classification"] == "EVIDENCE_LIMITED"
                    for item in causes
                ),
            },
            "sources": {
                "contract_graph": str(graph_path),
                "scan_report": str(scan_path),
                "detected_server": (
                    str(server_path.relative_to(self.project_path))
                    if server_path.is_file() else None
                ),
                "detected_client": (
                    str(client_path.relative_to(self.project_path))
                    if client_path.is_file() else None
                ),
                "detected_html": (
                    str(html_path.relative_to(self.project_path))
                    if html_path.is_file() else None
                ),
            },
        }

        output = self.reports_dir / "root-cause-report.json"
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return report, output


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "."

    try:
        report, output = RootCauseEngine(path).build()

        print(
            f"[✓] Root Cause analysis completed: "
            f"{report['summary']['total']} causes."
        )
        print(
            f"[+] CONFIRMED: "
            f"{report['summary']['confirmed']}"
        )
        print(
            f"[+] DERIVED: "
            f"{report['summary']['derived']}"
        )
        print(
            f"[+] INFERRED: "
            f"{report['summary']['inferred']}"
        )
        print(f"[+] Saved to: {output}")

    except RootCauseError as exc:
        print(f"[!] ROOT CAUSE FAILED: {exc}")
        raise SystemExit(1)
