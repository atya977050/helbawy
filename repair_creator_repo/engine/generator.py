#!/usr/bin/env python3
import os
from pathlib import Path

class CodeGeneratorEngine:
    def __init__(self, project_name, project_type="webrtc_app"):
        self.project_name = project_name
        self.target_dir = Path(project_name).resolve()

    def scaffold(self):
        print(f"[+] Scaffolding new project '{self.project_name}'...")
        self.target_dir.mkdir(exist_ok=True, parents=True)
        public_dir = self.target_dir / "public"
        server_dir = self.target_dir / "server"
        public_dir.mkdir(exist_ok=True)
        server_dir.mkdir(exist_ok=True)

        (public_dir / "index.html").write_text("""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head><meta charset="UTF-8"><title>بلبل</title></head>
<body><h1>غرفة المكالمة</h1><script src="/socket.io/socket.io.js"></script><script src="app.js"></script></body>
</html>""", encoding="utf-8")

        (public_dir / "app.js").write_text("""
const socket = io();
let localStream, remoteStream, peerConnection;
const servers = { iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] };
async function init() {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
}
init();
""", encoding="utf-8")

        (self.target_dir / "server.js").write_text("""
const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const app = express();
const server = http.createServer(app);
const io = new Server(server);
app.use(express.static('public'));
server.listen(3000, () => console.log('Server running on port 3000'));
""", encoding="utf-8")

        print("[✓] Project scaffolded successfully.")
        return {"status": "success"}
