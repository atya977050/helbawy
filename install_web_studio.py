from pathlib import Path
import json
import re
import html
import ast
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
STUDIO = ROOT / "studio"
ENGINE = ROOT / "engine"
REPORTS = ROOT / "reports"

STUDIO.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# Web Studio
# ------------------------------------------------------------

INDEX = r'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>عبقرينو — استوديو إنشاء البرامج</title>

<style>
*{box-sizing:border-box}

body{
    margin:0;
    min-height:100vh;
    background:#0b0b0b;
    color:#f4d66d;
    font-family:Tahoma,Arial,sans-serif;
}

header{
    padding:24px 18px;
    text-align:center;
    border-bottom:1px solid #594a1c;
    background:#101010;
}

header h1{
    margin:0 0 8px;
    font-size:30px;
}

header p{
    margin:0;
    color:#c8bd91;
}

.container{
    width:min(1180px,94%);
    margin:auto;
    padding:25px 0 50px;
}

.panel{
    background:#141414;
    border:1px solid #5f4d1a;
    border-radius:20px;
    padding:24px;
    margin-bottom:22px;
    box-shadow:0 12px 35px rgba(0,0,0,.25);
}

h2,h3{
    margin-top:0;
}

label{
    display:block;
    margin-bottom:9px;
    color:#d9ca91;
}

textarea,input{
    width:100%;
    border:1px solid #65551f;
    border-radius:14px;
    background:#090909;
    color:#fff;
    padding:15px;
    font:inherit;
    outline:none;
}

textarea{
    min-height:120px;
    resize:vertical;
}

button{
    border:1px solid #826c25;
    border-radius:13px;
    padding:12px 18px;
    margin:7px 4px;
    background:#1d1d1d;
    color:#f4d66d;
    cursor:pointer;
    font:inherit;
}

button:hover{
    background:#29250f;
}

button.primary{
    background:#806b24;
    color:#fff;
}

button.danger{
    color:#ffb0b0;
}

.hidden{
    display:none!important;
}

.screen-list{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
    gap:14px;
}

.screen-card{
    padding:18px;
    border:1px solid #4e431f;
    border-radius:16px;
    background:#101010;
}

.designs{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(280px,1fr));
    gap:18px;
}

.design{
    border:1px solid #62521d;
    border-radius:20px;
    overflow:hidden;
    background:#111;
}

.design-head{
    padding:15px;
}

.preview{
    min-height:270px;
    margin:0 14px 14px;
    border:1px solid #413817;
    border-radius:15px;
    background:#181818;
    padding:16px;
}

.preview-title{
    height:25px;
    width:55%;
    border-radius:8px;
    background:#806b24;
    margin-bottom:18px;
}

.preview-grid{
    display:grid;
    grid-template-columns:repeat(2,1fr);
    gap:10px;
}

.preview-box{
    min-height:65px;
    border:1px solid #675720;
    border-radius:10px;
    padding:9px;
    color:#c9bd8d;
}

.preview-sidebar{
    display:grid;
    grid-template-columns:80px 1fr;
    gap:12px;
}

.preview-side{
    min-height:200px;
    border-radius:10px;
    border:1px solid #675720;
}

.preview-content{
    min-height:200px;
}

.big-action{
    height:70px;
    border-radius:12px;
    background:#806b24;
    margin-bottom:12px;
}

.status{
    padding:13px;
    border-radius:12px;
    background:#101010;
    color:#c9bd8d;
    margin-top:12px;
}

.badge{
    display:inline-block;
    border:1px solid #675720;
    border-radius:20px;
    padding:5px 10px;
    margin:3px;
    font-size:12px;
}

.notice{
    color:#bdb28b;
    line-height:1.8;
}

#modifyBox{
    margin-top:15px;
}
</style>
</head>

<body>

<header>
<h1>🤖 عبقرينو</h1>
<p>استوديو إنشاء البرامج وتصميم الشاشات</p>
</header>

<div class="container">

<section class="panel" id="ideaPanel">
<h2>فكرة البرنامج</h2>
<p class="notice">
اكتب فكرة البرنامج، وعبقرينو سيحللها ويقترح الشاشات المطلوبة.
</p>

<textarea id="idea"
placeholder="مثال: برنامج إدارة مكتب محاماة أون لاين"></textarea>

<button class="primary" onclick="analyzeIdea()">
تحليل الفكرة
</button>

<div id="ideaStatus" class="status hidden"></div>
</section>

<section class="panel hidden" id="requirementsPanel">
<h2>الشاشات المقترحة</h2>

<div id="screenList" class="screen-list"></div>

<div class="status">
بعد اعتماد الشاشة سيتم عرض 3 تصميمات مرئية لها.
</div>
</section>

<section class="panel hidden" id="designPanel">

<h2 id="designTitle">تصميم الشاشة</h2>
<p id="designPurpose" class="notice"></p>

<div id="designs" class="designs"></div>

<div>
<button onclick="moreDesigns()">🔄 تصميمات أخرى</button>
<button onclick="showModify()">✏️ تعديل</button>
<button class="danger" onclick="rejectScreen()">✕ رفض الشاشة</button>
</div>

<div id="modifyBox" class="hidden">
<label>ما التعديل المطلوب؟</label>
<textarea id="modification"
placeholder="مثال: أريد القائمة الجانبية على اليمين وزر بحث واضح"></textarea>
<button class="primary" onclick="applyModification()">
عرض التصميم المعدل
</button>
</div>

</section>

<section class="panel hidden" id="approvedPanel">
<h2>الشاشات المعتمدة</h2>

<div id="approvedList"></div>

<button class="primary" onclick="finishCreation()">
🚀 إنشاء البرنامج
</button>

<div id="finishStatus" class="status hidden"></div>
</section>

</div>

<script>
let state = {
    idea:"",
    screens:[],
    approved:[],
    currentIndex:0,
    offset:0
};

async function api(url, options={}){
    const response = await fetch(url, {
        headers:{"Content-Type":"application/json"},
        ...options
    });

    const data = await response.json();

    if(!response.ok || data.ok === false){
        throw new Error(data.error || "حدث خطأ");
    }

    return data;
}

function show(id){
    document.getElementById(id).classList.remove("hidden");
}

function hide(id){
    document.getElementById(id).classList.add("hidden");
}

async function analyzeIdea(){

    const idea = document.getElementById("idea").value.trim();

    if(!idea){
        alert("اكتب فكرة البرنامج أولاً");
        return;
    }

    state.idea = idea;

    const status = document.getElementById("ideaStatus");
    show("ideaStatus");
    status.textContent = "عبقرينو يحلل الفكرة...";

    try{
        const data = await api("/api/analyze", {
            method:"POST",
            body:JSON.stringify({idea})
        });

        state.screens = data.screens;
        state.approved = [];

        renderScreens();
        show("requirementsPanel");
        renderApproved();

        status.textContent =
            "تم تحليل الفكرة. اختر الشاشة التي تريد تصميمها.";

    }catch(error){
        status.textContent = error.message;
    }
}

function renderScreens(){

    const box = document.getElementById("screenList");

    box.innerHTML = state.screens.map((screen,index)=>`
        <div class="screen-card">
            <h3>${escapeHtml(screen.title)}</h3>
            <p>${escapeHtml(screen.purpose)}</p>
            <button class="primary"
                onclick="openScreen(${index})">
                تصميم هذه الشاشة
            </button>
        </div>
    `).join("");
}

async function openScreen(index){

    state.currentIndex = index;
    state.offset = 0;

    const screen = state.screens[index];

    document.getElementById("designTitle").textContent =
        "تصميم: " + screen.title;

    document.getElementById("designPurpose").textContent =
        screen.purpose;

    hide("modifyBox");
    show("designPanel");

    await loadDesigns();
}

async function loadDesigns(){

    const screen = state.screens[state.currentIndex];

    const data = await api("/api/proposals", {
        method:"POST",
        body:JSON.stringify({
            screen,
            offset:state.offset
        })
    });

    renderDesigns(data.proposals);
}

function renderDesigns(proposals){

    const box = document.getElementById("designs");

    box.innerHTML = proposals.map((p,index)=>`
        <article class="design">

            <div class="design-head">
                <h3>التصميم ${index+1}</h3>
                <span class="badge">${escapeHtml(p.layout)}</span>
            </div>

            <div class="preview">
                ${previewHtml(p, index)}
            </div>

            <div class="design-head">
                <p>${escapeHtml(p.purpose)}</p>

                <button class="primary"
                    onclick='approveDesign(${JSON.stringify(p)})'>
                    ✓ اختيار هذا التصميم
                </button>
            </div>

        </article>
    `).join("");
}

function previewHtml(p,index){

    if(index === 1){
        return `
            <div class="preview-title"></div>
            <div class="preview-box">إحصائيات</div>
            <br>
            <div class="preview-grid">
                <div class="preview-box">قضايا</div>
                <div class="preview-box">موكلون</div>
                <div class="preview-box">جلسات</div>
                <div class="preview-box">مستندات</div>
            </div>
        `;
    }

    if(index === 2){
        return `
            <div class="preview-title"></div>
            <div class="big-action"></div>
            <div class="preview-box">الوظائف الرئيسية</div>
            <br>
            <div class="preview-box">معلومات البرنامج</div>
        `;
    }

    return `
        <div class="preview-title"></div>
        <div class="preview-grid">
            <div class="preview-box">وظيفة 1</div>
            <div class="preview-box">وظيفة 2</div>
            <div class="preview-box">وظيفة 3</div>
            <div class="preview-box">وظيفة 4</div>
        </div>
        <br>
        <div class="preview-box">شريط التنقل</div>
    `;
}

async function approveDesign(proposal){

    proposal.approved = true;

    const screen = state.screens[state.currentIndex];

    state.approved =
        state.approved.filter(
            x => x.screen_id !== screen.id
        );

    state.approved.push(proposal);

    await api("/api/state", {
        method:"POST",
        body:JSON.stringify({
            phase:"screen_approved",
            idea:state.idea,
            screens:state.screens,
            approved:state.approved
        })
    });

    renderApproved();
    hide("designPanel");

    document.getElementById("approvedPanel")
        .scrollIntoView({behavior:"smooth"});
}

function moreDesigns(){

    state.offset += 3;
    loadDesigns();
}

function showModify(){
    show("modifyBox");
    document.getElementById("modification").focus();
}

async function applyModification(){

    const modification =
        document.getElementById("modification").value.trim();

    if(!modification){
        alert("اكتب التعديل المطلوب");
        return;
    }

    const screen =
        {...state.screens[state.currentIndex]};

    screen.purpose += " — تعديل المستخدم: " + modification;

    state.screens[state.currentIndex] = screen;
    state.offset = 0;

    document.getElementById("designPurpose").textContent =
        screen.purpose;

    hide("modifyBox");

    await loadDesigns();
}

function rejectScreen(){

    const screen =
        state.screens[state.currentIndex];

    state.approved =
        state.approved.filter(
            x => x.screen_id !== screen.id
        );

    hide("designPanel");
    renderApproved();
}

function renderApproved(){

    const box = document.getElementById("approvedList");

    if(!state.approved.length){
        box.innerHTML =
            "<p class='notice'>لم يتم اعتماد أي شاشة بعد.</p>";
        return;
    }

    box.innerHTML = state.approved.map(x=>`
        <div class="screen-card">
            <h3>✓ ${escapeHtml(x.title)}</h3>
            <p>${escapeHtml(x.purpose)}</p>
            <span class="badge">${escapeHtml(x.layout)}</span>
        </div>
    `).join("");
}

async function finishCreation(){

    if(!state.approved.length){
        alert("اعتمد شاشة واحدة على الأقل");
        return;
    }

    const box = document.getElementById("finishStatus");

    show("finishStatus");
    box.textContent =
        "عبقرينو ينشئ البرنامج...";

    try{

        const data = await api("/api/create", {
            method:"POST",
            body:JSON.stringify({
                idea:state.idea,
                approved:state.approved
            })
        });

        box.textContent =
            "تم إنشاء البرنامج بنجاح: " +
            data.path;

    }catch(error){
        box.textContent = error.message;
    }
}

function escapeHtml(value){
    return String(value)
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}
</script>

</body>
</html>
'''

(STUDIO / "index.html").write_text(INDEX, encoding="utf-8")

# ------------------------------------------------------------
# Local web server
# ------------------------------------------------------------

SERVER = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
STUDIO = ROOT / "studio"

sys.path.insert(0, str(ROOT))

from engine.creation import (
    RequirementsEngine,
    ScreenProposalEngine,
    ProjectGenerator,
    ConversationState
)

HOST = "127.0.0.1"
PORT = 8787


class Handler(BaseHTTPRequestHandler):

    def send_json(self, data, status=200):

        raw = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(raw))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.end_headers()

        self.wfile.write(raw)


    def read_json(self):

        length = int(
            self.headers.get(
                "Content-Length",
                0
            )
        )

        raw = self.rfile.read(length)

        return json.loads(
            raw.decode("utf-8")
        )


    def do_GET(self):

        if self.path in ("/", "/index.html"):

            raw = (
                STUDIO / "index.html"
            ).read_bytes()

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/html; charset=utf-8"
            )

            self.send_header(
                "Content-Length",
                str(len(raw))
            )

            self.end_headers()

            self.wfile.write(raw)

            return

        self.send_json(
            {"ok":False,"error":"Not found"},
            404
        )


    def do_POST(self):

        try:

            data = self.read_json()

            if self.path == "/api/analyze":

                idea = data.get(
                    "idea",
                    ""
                ).strip()

                if not idea:
                    raise ValueError(
                        "فكرة البرنامج مطلوبة"
                    )

                result = (
                    RequirementsEngine()
                    .analyze(idea)
                )

                self.send_json({
                    "ok":True,
                    "screens":
                        result["screens"],
                    "requirements":
                        result
                })

                return


            if self.path == "/api/proposals":

                screen = data["screen"]

                offset = int(
                    data.get(
                        "offset",
                        0
                    )
                )

                proposals = (
                    ScreenProposalEngine()
                    .proposals(
                        screen,
                        offset
                    )
                )

                self.send_json({
                    "ok":True,
                    "proposals":[
                        p.__dict__
                        for p in proposals
                    ]
                })

                return


            if self.path == "/api/state":

                state = ConversationState(
                    ROOT
                )

                state.save(data)

                self.send_json({
                    "ok":True
                })

                return


            if self.path == "/api/create":

                idea = data["idea"]

                approved = data[
                    "approved"
                ]

                requirements = (
                    RequirementsEngine()
                    .analyze(idea)
                )

                generator = ProjectGenerator(
                    ROOT
                )

                target, manifest = (
                    generator.generate(
                        idea,
                        requirements,
                        approved
                    )
                )

                self.send_json({
                    "ok":True,
                    "path":str(target),
                    "manifest":manifest
                })

                return


            self.send_json(
                {
                    "ok":False,
                    "error":"مسار غير معروف"
                },
                404
            )

        except Exception as exc:

            self.send_json(
                {
                    "ok":False,
                    "error":str(exc)
                },
                400
            )


def main():

    server = ThreadingHTTPServer(
        (HOST, PORT),
        Handler
    )

    print(
        f"عبقرينو Web Studio يعمل على "
        f"http://{HOST}:{PORT}"
    )

    print(
        "أوقفه بـ Ctrl+C"
    )

    server.serve_forever()


if __name__ == "__main__":
    main()
'''

(STUDIO / "server.py").write_text(
    SERVER,
    encoding="utf-8"
)

# ------------------------------------------------------------
# launcher
# ------------------------------------------------------------

LAUNCHER = r'''#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=============================================="
echo " عبقرينو — Web Studio"
echo "=============================================="
echo
echo "افتح في المتصفح:"
echo "http://127.0.0.1:8787"
echo
echo "Termux يعمل كمحرك خلفي فقط."
echo "=============================================="
echo

python3 studio/server.py
'''

launcher = ROOT / "run_web_studio.sh"
launcher.write_text(LAUNCHER, encoding="utf-8")
launcher.chmod(0o755)

# ------------------------------------------------------------
# Syntax checks
# ------------------------------------------------------------

for path in ENGINE.glob("*.py"):
    ast.parse(path.read_text(encoding="utf-8"))

ast.parse(
    (STUDIO / "server.py").read_text(
        encoding="utf-8"
    )
)

report = {
    "status":"WEB_STUDIO_INSTALLED",
    "studio":"studio/index.html",
    "server":"studio/server.py",
    "launcher":"run_web_studio.sh",
    "port":8787,
    "features":[
        "browser idea input",
        "requirements screens",
        "three visual designs",
        "more designs",
        "screen modification",
        "screen rejection",
        "screen approval",
        "creation state",
        "project generation"
    ]
}

(REPORTS / "web-studio-install-report.json").write_text(
    json.dumps(
        report,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("=" * 70)
print("[+] تم تركيب Web Studio لعبقرينو")
print("[+] الواجهة: studio/index.html")
print("[+] الخادم: studio/server.py")
print("[+] المشغل: run_web_studio.sh")
print("[+] تم فحص Python syntax")
print("[+] التقرير: reports/web-studio-install-report.json")
print("=" * 70)
