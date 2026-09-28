#!/usr/bin/env python3
"""
P45 Contract Graph

يبني خريطة قابلة للتتبع للعقود الموجودة والمفقودة والمكسورة
اعتماداً على تقارير Scanner و Contract Analyzer فقط.
"""

import json
from pathlib import Path


class ContractGraphError(RuntimeError):
    pass


class ContractGraphEngine:
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.reports_dir = self.project_path / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _load(self, name):
        path = self.reports_dir / name
        if not path.exists():
            raise ContractGraphError(f"Required report does not exist: {path}")

        try:
            return json.loads(path.read_text(encoding="utf-8")), path
        except json.JSONDecodeError as exc:
            raise ContractGraphError(f"Invalid JSON report: {path}") from exc

    @staticmethod
    def _node(node_id, kind, status, evidence=None, details=None):
        return {
            "id": node_id,
            "kind": kind,
            "status": status,
            "evidence": evidence or [],
            "details": details or {},
        }

    @staticmethod
    def _edge(source, target, relation, status, evidence=None, details=None):
        return {
            "source": source,
            "target": target,
            "relation": relation,
            "status": status,
            "evidence": evidence or [],
            "details": details or {},
        }

    def build(self):
        scan, scan_path = self._load("scan-report.json")
        contracts, contracts_path = self._load("contracts-report.json")

        classification = scan.get("classification", {})
        server_files = list(classification.get("server", []))
        client_files = list(classification.get("client", []))

        server_file = server_files[0] if server_files else None

        script_clients = [
            item for item in client_files
            if Path(item).suffix.lower() in {
                ".js", ".mjs", ".cjs", ".ts",
                ".tsx", ".jsx", ".py"
            }
        ]

        html_clients = [
            item for item in client_files
            if Path(item).suffix.lower() in {".html", ".htm"}
        ]

        client_file = script_clients[0] if script_clients else None
        html_file = html_clients[0] if html_clients else None

        emits = contracts.get("emits", [])
        handlers = contracts.get("handlers", [])
        socketio = contracts.get("socketio_initialization", [])
        webrtc = contracts.get("webrtc", [])
        nodes = []
        edges = []

        if server_file:
            nodes.append(self._node(
                "server:socketio",
                "socketio-server",
                "EXISTS",
                [server_file],
                {"initialization": socketio},
            ))

        if client_file:
            nodes.append(self._node(
                "client:socketio",
                "socketio-client",
                "EXISTS",
                [client_file],
            ))

        if emits or handlers:
            nodes.append(self._node(
                "socketio:signaling",
                "signaling-contract",
                "EXISTS",
                [str(contracts_path)],
                {
                    "emits": emits,
                    "handlers": handlers,
                },
            ))
        else:
            nodes.append(self._node(
                "socketio:signaling",
                "signaling-contract",
                "MISSING",
                [str(contracts_path)],
                {
                    "limitation": (
                        "No direct Socket.IO emit/on contracts were detected."
                    )
                },
            ))

        media_apis = {
            item.get("api")
            for item in webrtc
            if isinstance(item, dict)
        }

        if "getUserMedia" in media_apis:
            nodes.append(self._node(
                "webrtc:media-capture",
                "media-capture",
                "EXISTS",
                [str(contracts_path)],
                {"apis": sorted(media_apis)},
            ))
        else:
            nodes.append(self._node(
                "webrtc:media-capture",
                "media-capture",
                "MISSING",
                [str(contracts_path)],
            ))

        peer_apis = {
            "RTCPeerConnection",
            "createOffer",
            "createAnswer",
            "setLocalDescription",
            "setRemoteDescription",
            "addIceCandidate",
            "onicecandidate",
        }

        missing_peer_apis = sorted(peer_apis - media_apis)

        if "RTCPeerConnection" in media_apis:
            peer_status = "EXISTS"
        else:
            peer_status = "MISSING"

        nodes.append(self._node(
            "webrtc:peer-connection",
            "peer-connection",
            peer_status,
            [str(contracts_path)],
            {
                "detected_apis": sorted(peer_apis & media_apis),
                "missing_apis": missing_peer_apis,
            },
        ))

        if "ontrack" in media_apis:
            nodes.append(self._node(
                "webrtc:remote-track",
                "remote-track",
                "EXISTS",
                [str(contracts_path)],
            ))
        else:
            nodes.append(self._node(
                "webrtc:remote-track",
                "remote-track",
                "MISSING",
                [str(contracts_path)],
            ))

        if html_file:
            nodes.append(self._node(
                "dom:remote-video",
                "dom-target",
                "EVIDENCE_LIMITED",
                [html_file],
                {
                    "reason": (
                        "Static graph requires source inspection to resolve "
                        "the remoteVideo DOM target."
                    )
                },
            ))

        if server_file and client_file:
            edges.append(self._edge(
                "client:socketio",
                "server:socketio",
                "socketio-transport",
                "EXISTS",
                [client_file, server_file],
            ))

        if client_file:
            edges.append(self._edge(
                "client:socketio",
                "socketio:signaling",
                "signaling-contract",
                "BROKEN" if not (emits or handlers) else "EXISTS",
                [str(contracts_path)],
            ))

            edges.append(self._edge(
                "webrtc:media-capture",
                "webrtc:peer-connection",
                "media-to-peer",
                "BROKEN" if "RTCPeerConnection" not in media_apis else "EXISTS",
                [str(contracts_path)],
            ))

            edges.append(self._edge(
                "webrtc:peer-connection",
                "webrtc:remote-track",
                "peer-to-remote-track",
                "BROKEN" if "RTCPeerConnection" not in media_apis else "EXISTS",
                [str(contracts_path)],
            ))

            edges.append(self._edge(
                "webrtc:remote-track",
                "dom:remote-video",
                "remote-track-to-dom",
                "EVIDENCE_LIMITED",
                [client_file, html_file] if html_file else [client_file],
            ))

        graph = {
            "project": str(self.project_path),
            "status": "EVIDENCED",
            "nodes": nodes,
            "edges": edges,
            "summary": {
                "nodes": len(nodes),
                "edges": len(edges),
                "exists": sum(
                    item["status"] == "EXISTS" for item in nodes
                ),
                "missing": sum(
                    item["status"] == "MISSING" for item in nodes
                ),
                "broken": sum(
                    item["status"] == "BROKEN" for item in edges
                ),
                "evidence_limited": (
                    sum(item["status"] == "EVIDENCE_LIMITED" for item in nodes)
                    + sum(item["status"] == "EVIDENCE_LIMITED" for item in edges)
                ),
            },
            "sources": {
                "scan_report": str(scan_path),
                "contracts_report": str(contracts_path),
            },
        }

        output = self.reports_dir / "contract-graph.json"
        output.write_text(
            json.dumps(graph, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return graph, output


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "."

    try:
        graph, output = ContractGraphEngine(path).build()
        print(
            f"[✓] Contract Graph built: "
            f"{len(graph['nodes'])} nodes, "
            f"{len(graph['edges'])} edges."
        )
        print(f"[+] Saved to: {output}")
    except ContractGraphError as exc:
        print(f"[!] CONTRACT GRAPH FAILED: {exc}")
        raise SystemExit(1)
