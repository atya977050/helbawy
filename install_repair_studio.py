from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
STUDIO = ROOT / "studio"
STUDIO.mkdir(exist_ok=True)

# --------------------------------------------------
# Repair Studio UI
# --------------------------------------------------

html = """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>عبقرينو — استوديو إصلاح البرامج</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;
 font-family:Arial,sans-serif;
 background:#07111f;
 color:#eef4ff;
}
header{
 padding:24px;
 text-align:center;
 background:#0b1b31;
 border-bottom:1px solid #203957;
}
h1{margin:0 0 8px}
.sub{color:#9eb3cc}
main{max-width:1100px;margin:auto;padding:22px}
.panel{
 background:#0d1d32;
 border:1px solid #23405f;
 border-radius:18px;
 padding:20px;
 margin-bottom:18px;
}
input{
 width:100%;
 padding:14px;
 border-radius:12px;
 border:1px solid #31506f;
 background:#081523;
 color:white;
 font-size:16px;
}
button{
 border:0;
 border-radius:12px;
 padding:12px 18px;
 margin:6px;
 cursor:pointer;
 font-weight:bold;
}
.primary{background:#d7ad45;color:#111}
.secondary{background:#244767;color:white}
.danger{background:#7e2934;color:white}
.card{
 background:#091727;
 border:1px solid #294662;
 border-radius:15px;
 padding:16px;
 margin-top:12px;
}
.status{
 display:inline-block;
 padding:6px 10px;
 border-radius:20px;
 background:#183958;
 color:#bcd7f2;
}
pre{
 white-space:pre-wrap;
 background:#050d16;
 padding:15px;
 border-radius:12px;
 overflow:auto;
}
.hidden{display:none}
</style>
</head>

<body>

<header>
<h1>🤖 عبقرينو</h1>
<div class="sub">استوديو إصلاح البرامج</div>
</header>

<main>

<section class="panel">
<h2>🔧 البرنامج المراد إصلاحه</h2>
<p>اكتب مسار البرنامج الموجود على الجهاز.</p>

<input
 id="projectPath"
 placeholder="/data/data/com.termux/files/home/my-project">

<br><br>

<button class="primary" onclick="scanProject()">
🔍 فحص البرنامج
</button>

<button class="secondary" onclick="location.href='/'">
🆕 إنشاء برنامج جديد
</button>
</section>

<section id="scanPanel" class="panel hidden">
<h2>📊 نتيجة الفحص</h2>
<div id="scanResult"></div>

<button class="primary" onclick="analyzeRootCause()">
🧠 تحليل السبب الجذري
</button>
</section>

<section id="causePanel" class="panel hidden">
<h2>🧠 تحليل المشاكل</h2>
<div id="causeResult"></div>

<button class="primary" onclick="buildRepairPlan()">
📋 إنشاء خطة الإصلاح
</button>
</section>

<section id="planPanel" class="panel hidden">
<h2>📋 خطة الإصلاح</h2>
<div id="planResult"></div>

<button class="primary" onclick="approveRepairs()">
✅ اعتماد الإصلاحات
</button>

<button class="danger" onclick="rejectRepairs()">
✕ رفض
</button>
</section>

<section id="repairPanel" class="panel hidden">
<h2>🛠️ تنفيذ الإصلاح</h2>
<div id="repairResult"></div>

<button class="primary" onclick="executeRepair()">
🚀 تنفيذ الإصلاح
</button>
</section>

<section id="verifyPanel" class="panel hidden">
<h2>🔎 التحقق النهائي</h2>
<div id="verifyResult"></div>

<button class="primary" onclick="verifyRepair()">
♻️ إعادة الفحص والتحقق
</button>
</section>

<section id="reportPanel" class="panel hidden">
<h2>📄 التقرير النهائي</h2>
<div id="reportResult"></div>
</section>

</main>

<script>

let state = {
 projectPath:"",
 scan:null,
 cause:null,
 plan:null,
 approved:false,
 repair:null,
 verification:null
};

function show(id){
 document.getElementById(id).classList.remove("hidden");
}

function esc(value){
 return String(value ?? "").replace(/[&<>"']/g,function(m){
  return {
   "&":"&amp;",
   "<":"&lt;",
   ">":"&gt;",
   '"':"&quot;",
   "'":"&#039;"
  }[m];
 });
}

async function api(url,data){
 const response = await fetch(url,{
  method:"POST",
  headers:{
   "Content-Type":"application/json"
  },
  body:JSON.stringify(data)
 });

 return await response.json();
}

async function scanProject(){

 state.projectPath =
  document.getElementById("projectPath").value.trim();

 if(!state.projectPath){
  alert("اكتب مسار البرنامج أولًا");
  return;
 }

 const data = await api(
  "/api/repair/scan",
  {project_path:state.projectPath}
 );

 state.scan=data;

 show("scanPanel");

 document.getElementById("scanResult").innerHTML =
  '<div class="card">' +
  '<span class="status">' +
  esc(data.status || "تم الفحص") +
  '</span>' +
  '<pre>' +
  esc(JSON.stringify(data,null,2)) +
  '</pre>' +
  '</div>';
}

async function analyzeRootCause(){

 const data = await api(
  "/api/repair/root-cause",
  {
   project_path:state.projectPath,
   scan:state.scan
  }
 );

 state.cause=data;
 show("causePanel");

 document.getElementById("causeResult").innerHTML =
  '<div class="card"><pre>' +
  esc(JSON.stringify(data,null,2)) +
  '</pre></div>';
}

async function buildRepairPlan(){

 const data = await api(
  "/api/repair/plan",
  {
   project_path:state.projectPath,
   scan:state.scan,
   cause:state.cause
  }
 );

 state.plan=data;
 show("planPanel");

 document.getElementById("planResult").innerHTML =
  '<div class="card"><pre>' +
  esc(JSON.stringify(data,null,2)) +
  '</pre></div>';
}

function approveRepairs(){

 state.approved=true;
 show("repairPanel");

 document.getElementById("repairResult").innerHTML =
  '<div class="card">' +
  '<span class="status">الإصلاحات معتمدة</span>' +
  '<p>تم اعتماد خطة الإصلاح بواسطة المستخدم.</p>' +
  '</div>';
}

function rejectRepairs(){
 alert("تم رفض خطة الإصلاح. لم يتم تنفيذ أي تعديل.");
}

async function executeRepair(){

 if(!state.approved){
  alert("يجب اعتماد الإصلاح أولًا");
  return;
 }

 const data = await api(
  "/api/repair/execute",
  {
   project_path:state.projectPath,
   scan:state.scan,
   cause:state.cause,
   plan:state.plan
  }
 );

 state.repair=data;
 show("verifyPanel");

 document.getElementById("repairResult").innerHTML =
  '<div class="card"><pre>' +
  esc(JSON.stringify(data,null,2)) +
  '</pre></div>';
}

async function verifyRepair(){

 const data = await api(
  "/api/repair/verify",
  {
   project_path:state.projectPath,
   previous_scan:state.scan,
   repair:state.repair
  }
 );

 state.verification=data;

 show("reportPanel");

 document.getElementById("verifyResult").innerHTML =
  '<div class="card"><pre>' +
  esc(JSON.stringify(data,null,2)) +
  '</pre></div>';

 document.getElementById("reportResult").innerHTML =
  '<div class="card">' +
  '<span class="status">اكتمل مسار الإصلاح</span>' +
  '<pre>' +
  esc(JSON.stringify(state,null,2)) +
  '</pre>' +
  '</div>';
}

</script>

</body>
</html>
"""

(STUDIO / "repair.html").write_text(
    html,
    encoding="utf-8"
)

# --------------------------------------------------
# Temporary API adapter
# سيتم ربطه بمحركات P45 الحقيقية لاحقًا
# --------------------------------------------------

api = """from pathlib import Path

def scan(project_path):
    p = Path(project_path).expanduser()

    if not p.exists():
        return {
            "status": "error",
            "error": "المسار غير موجود",
            "project_path": str(p)
        }

    files = []

    for item in p.rglob("*"):
        if not item.is_file():
            continue

        if ".git" in item.parts:
            continue

        if "node_modules" in item.parts:
            continue

        files.append(str(item.relative_to(p)))

    return {
        "status": "scanned",
        "project_path": str(p),
        "file_count": len(files),
        "files": files[:500]
    }


def root_cause(project_path, scan_data):
    return {
        "status": "analysis_ready",
        "project_path": project_path,
        "message": "مرحلة تحليل السبب الجذري جاهزة للربط بمحرك P45."
    }


def plan(project_path, scan_data, cause):
    return {
        "status": "plan_ready",
        "project_path": project_path,
        "actions": [],
        "message": "مرحلة خطة الإصلاح جاهزة للربط بمحرك P45."
    }


def execute(project_path, scan_data, cause, plan_data):
    return {
        "status": "awaiting_engine",
        "project_path": project_path,
        "changed": [],
        "message": "لم يتم تعديل الملفات. سيتم ربط DeepRepairEngine."
    }


def verify(project_path, previous_scan, repair):
    return {
        "status": "verification_ready",
        "project_path": project_path,
        "message": "سيتم ربط VerificationEngine وإعادة الفحص."
    }
"""

(STUDIO / "repair_api.py").write_text(
    api,
    encoding="utf-8"
)

report = {
    "name": "عبقرينو — Repair Studio",
    "status": "installed",
    "ui": "studio/repair.html",
    "api": "studio/repair_api.py",
    "next": "connect_real_p45_engines"
}

(ROOT / "reports" / "repair-studio-install-report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("==============================================")
print("[+] تم إنشاء استوديو إصلاح البرامج")
print("[+] studio/repair.html")
print("[+] studio/repair_api.py")
print("[+] reports/repair-studio-install-report.json")
print("==============================================")
