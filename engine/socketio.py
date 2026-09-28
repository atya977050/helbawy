#!/usr/bin/env python3
import re
from pathlib import Path


class SocketIOAnalyzer:
    """
    P45 communication-contract analyzer.

    Detects Socket.IO wiring and WebRTC lifecycle evidence.
    It reports absence as a diagnostic limitation/finding, not as proof
    that a contract cannot exist through indirect/dynamic code.
    """

    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.ignored_dirs = {
            ".git", "node_modules", "__pycache__", ".repair-repository",
            "venv", "env", "plans", "reports", "snapshots", "logs"
        }

    def _files(self):
        for path in self.project_path.rglob("*"):
            if any(part in self.ignored_dirs for part in path.parts):
                continue
            if path.is_file() and path.suffix in {".js", ".ts", ".py"}:
                yield path

    @staticmethod
    def _read(path):
        try:
            return path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            return ""

    def analyze(self):
        emits = []
        handlers = []
        socketio_initialization = []
        webrtc = []
        files_analyzed = 0

        patterns = {
            "emit": re.compile(
                r'(?:(?:socket|io)\s*\.\s*(?:to\s*\(.*?\)\s*\.\s*)?'
                r'emit)\s*\(\s*["\']([^"\']+)["\']',
                re.DOTALL,
            ),
            "on": re.compile(
                r'(?:socket|io)\s*\.\s*on\s*\(\s*'
                r'["\']([^"\']+)["\']',
                re.DOTALL,
            ),
            "socketio_server": re.compile(
                r'new\s+Server\s*\('
            ),
            "socketio_client": re.compile(
                r'\bio\s*\(\s*\)'
            ),
        }

        webrtc_patterns = {
            "RTCPeerConnection": r'\bRTCPeerConnection\s*\(',
            "getUserMedia": r'\bnavigator\s*\.\s*mediaDevices\s*\.\s*getUserMedia\s*\(',
            "createOffer": r'\.\s*createOffer\s*\(',
            "createAnswer": r'\.\s*createAnswer\s*\(',
            "setLocalDescription": r'\.\s*setLocalDescription\s*\(',
            "setRemoteDescription": r'\.\s*setRemoteDescription\s*\(',
            "addIceCandidate": r'\.\s*addIceCandidate\s*\(',
            "onicecandidate": r'\.\s*onicecandidate\s*=',
            "ontrack": r'\.\s*ontrack\s*=',
            "srcObject": r'\.\s*srcObject\s*=',
        }

        compiled_webrtc = {
            name: re.compile(pattern)
            for name, pattern in webrtc_patterns.items()
        }

        for path in self._files():
            text = self._read(path)
            if not text:
                continue

            files_analyzed += 1
            relative = str(path.relative_to(self.project_path))

            for event in patterns["emit"].findall(text):
                emits.append({
                    "event": event,
                    "file": relative,
                })

            for event in patterns["on"].findall(text):
                handlers.append({
                    "event": event,
                    "file": relative,
                })

            if patterns["socketio_server"].search(text):
                socketio_initialization.append({
                    "type": "server",
                    "file": relative,
                    "evidence": "new Server(...)",
                })

            if patterns["socketio_client"].search(text):
                socketio_initialization.append({
                    "type": "client",
                    "file": relative,
                    "evidence": "io()",
                })

            for name, pattern in compiled_webrtc.items():
                matches = list(pattern.finditer(text))
                if matches:
                    webrtc.append({
                        "api": name,
                        "file": relative,
                        "count": len(matches),
                    })

        api_names = {item["api"] for item in webrtc}

        findings = []

        if socketio_initialization and not emits and not handlers:
            findings.append({
                "code": "SOCKETIO_INITIALIZED_NOT_WIRED",
                "severity": "HIGH",
                "status": "EVIDENCED",
                "message": (
                    "Socket.IO initialization was detected, but no direct "
                    "emit/on handlers were detected by the current analyzer."
                ),
            })

        if "RTCPeerConnection" not in api_names:
            findings.append({
                "code": "PEER_CONNECTION_NOT_INITIALIZED",
                "severity": "HIGH",
                "status": "EVIDENCED",
                "message": "No RTCPeerConnection(...) construction was detected.",
            })

        signaling = {
            "createOffer",
            "createAnswer",
            "setLocalDescription",
            "setRemoteDescription",
            "addIceCandidate",
            "onicecandidate",
        }
        missing_signaling = sorted(signaling - api_names)

        if missing_signaling:
            findings.append({
                "code": "SIGNALING_APIS_NOT_DETECTED",
                "severity": "HIGH",
                "status": "EVIDENCED",
                "missing": missing_signaling,
                "message": (
                    "Expected WebRTC signaling APIs were not detected "
                    "by direct source analysis."
                ),
            })

        if "getUserMedia" in api_names and "ontrack" in api_names:
            findings.append({
                "code": "WEBRTC_PARTIAL",
                "severity": "INFO",
                "status": "EVIDENCED",
                "message": (
                    "Media capture and remote-track handling are present, "
                    "but this does not prove a complete WebRTC connection."
                ),
            })

        if not emits and not handlers:
            findings.append({
                "code": "CONTRACT_EVIDENCE_LIMITED",
                "severity": "INFO",
                "status": "EVIDENCE_LIMITED",
                "message": (
                    "No direct Socket.IO emit/on contracts were found. "
                    "This is not proof that no dynamic or indirect contract exists."
                ),
            })

        return {
            "status": "EVIDENCED",
            "root": str(self.project_path),
            "files_analyzed": files_analyzed,
            "emits": emits,
            "handlers": handlers,
            "socketio_initialization": socketio_initialization,
            "webrtc": webrtc,
            "findings": findings,
        }


if __name__ == "__main__":
    import json
    import sys

    project = sys.argv[1] if len(sys.argv) > 1 else "."
    result = SocketIOAnalyzer(project).analyze()
    print(json.dumps(result, ensure_ascii=False, indent=2))
