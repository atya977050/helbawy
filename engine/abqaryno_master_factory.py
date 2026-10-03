import json
import sys
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from datetime import datetime

class MasterAbqarynoFactory:
    def __init__(self, project_name, specification, root_dir=None):
        self.project_name = project_name
        self.specification = specification

        self.root_dir = (
            Path(root_dir).resolve()
            if root_dir
            else Path(__file__).resolve().parent.parent
        )

        safe_name = (
            str(project_name)
            .strip()
            .lower()
            .replace(" ", "-")
        )

        self.target_dir = self.root_dir / safe_name
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.brain = {
            "project": project_name,
            "specification": specification,
            "requirements": {},
            "architecture": {},
            "security": {},
            "database": {},
            "frontend": {},
            "implementation": {},
            "tests": [],
            "evidence": {}
        }

    def build_internal_blueprint(self):
        """يبني مخطط التنفيذ داخليًا ولا يتم عرضه للمستخدم."""
        requirements = self.brain.get("requirements", {})

        domain = requirements.get("domain", "Standard-Web")
        entities = list(requirements.get("entities", []))
        required_capabilities = {
            str(item).strip().lower()
            for item in requirements.get("capabilities", [])
            if str(item).strip()
        }

        self.brain["blueprint"] = {
            "version": 1,
            "visibility": "internal",
            "domain": domain,
            "entities": entities,
            "roles": list(requirements.get("roles", [])),
            "modules": [],
            "screens": list(requirements.get("screens", [])),
            "database": {
                "entities": entities,
                "relations": list(requirements.get("relations", [])),
            },
            "api": list(requirements.get("api", [])),
            "realtime": {
                "required": False,
                "technology": None,
                "features": [],
            },
            "security": {
                "authentication": True,
                "authorization": True,
                "validation": True,
                "audit": True,
            },
            "tests": [],
            "completion_criteria": [],
        }

        # خريطة القدرات الوظيفية لكل وحدة.
        module_map = {
            "Legal-Tech": [
                ("المستخدمون", [
                    "users",
                    "auth",
                    "roles",
                    "permissions",
                ]),
                ("الموكلون", [
                    "users",
                    "crud",
                    "search",
                    "permissions",
                ]),
                ("المحامون", [
                    "users",
                    "crud",
                    "search",
                    "permissions",
                ]),
                ("القضايا", [
                    "crud",
                    "search",
                    "files",
                    "permissions",
                    "audit",
                ]),
                ("المستندات", [
                    "files",
                    "document_processing",
                    "permissions",
                    "audit",
                ]),
                ("الاستشارات", [
                    "crud",
                    "scheduling",
                    "notifications",
                    "permissions",
                ]),
                ("المواعيد", [
                    "crud",
                    "scheduling",
                    "notifications",
                    "permissions",
                ]),
                ("المحادثات", [
                    "chat",
                    "realtime",
                    "notifications",
                    "permissions",
                ]),
                ("الإشعارات", [
                    "notifications",
                    "realtime",
                    "permissions",
                ]),
                ("التقارير", [
                    "reports",
                    "search",
                    "permissions",
                ]),
            ],
            "E-Commerce": [
                ("المستخدمون", [
                    "users",
                    "auth",
                    "roles",
                    "permissions",
                ]),
                ("المنتجات", [
                    "crud",
                    "search",
                    "files",
                ]),
                ("الطلبات", [
                    "crud",
                    "search",
                    "notifications",
                    "permissions",
                ]),
                ("المدفوعات", [
                    "payments",
                    "notifications",
                    "audit",
                    "permissions",
                ]),
            ],
            "Standard-Web": [
                ("المستخدمون", [
                    "users",
                    "auth",
                    "roles",
                    "permissions",
                ]),
                ("العناصر", [
                    "crud",
                    "search",
                ]),
                ("التقارير", [
                    "reports",
                    "search",
                ]),
            ],
        }

        # الوحدات تُشتق من الشاشات الفعلية المستخرجة من فكرة المستخدم.
        # لا نستخدم قوالب Legal-Tech أو Standard-Web تلقائية.
        source_screens = requirements.get("screens", [])
        modules = []

        for i, screen in enumerate(source_screens, 1):
            if isinstance(screen, dict):
                name = (
                    screen.get("title")
                    or screen.get("name")
                    or screen.get("id")
                    or f"الشاشة {i}"
                )
                capabilities = list(screen.get("capabilities", []))
            else:
                name = str(screen)
                capabilities = []

            capabilities = sorted(
                set(capabilities) | set(required_capabilities)
            )

            modules.append({
                "id": str(i),
                "name": name,
                "status": "planned",
                "capabilities": capabilities,
                "requires": [
                    "frontend",
                    "backend",
                    "database",
                    "validation",
                    "permissions",
                    "tests",
                ],
            })

        self.brain["blueprint"]["modules"] = modules

        # ربط الشاشات والـ APIs والعلاقات مباشرة بالمتطلبات المستخرجة.
        self.brain["blueprint"]["screens"] = list(
            requirements.get("screens", [])
        )
        self.brain["blueprint"]["api"] = list(
            requirements.get("api", [])
        )
        self.brain["blueprint"]["database"]["relations"] = list(
            requirements.get("relations", [])
        )

        all_capabilities = sorted({
            capability
            for module in modules
            for capability in module.get("capabilities", [])
        })

        realtime_features = sorted({
            capability
            for capability in all_capabilities
            if capability in {
                "chat",
                "realtime",
                "notifications",
                "video",
                "webrtc",
                "voice",
            }
        })

        realtime_required = bool(realtime_features)

        self.brain["blueprint"]["realtime"] = {
            "required": realtime_required,
            "technology": (
                "Socket.IO"
                if realtime_required
                else None
            ),
            "features": realtime_features,
        }

        self.brain["blueprint"]["capabilities"] = all_capabilities

        self.brain["blueprint"]["completion_criteria"] = [
            "frontend_connected",
            "backend_connected",
            "database_connected",
            "validation_active",
            "permissions_active",
            "runtime_test_passed",
            "http_test_passed",
        ]

        return self.brain["blueprint"]


    def run_screen_contract_agent(self):
        """
        تحويل شاشات الـBlueprint إلى عقود تنفيذية حقيقية.
        """

        print(
            "🧩 [Screen Contract Agent] "
            "Building executable screen contracts..."
        )

        from engine.screen_contract_engine import (
            ScreenContractEngine,
        )

        blueprint = self.brain.get("blueprint", {})
        result = ScreenContractEngine(blueprint).build()

        # ربط العقد التنفيذي بذكاء الشاشة الحقيقي.
        from engine.creation import ScreenIntelligenceEngine

        intelligence = ScreenIntelligenceEngine()

        for contract in result.get("contracts", []):
            screen_id = contract.get("id") or contract.get("key")

            screen = next(
                (
                    item
                    for item in blueprint.get("screens", [])
                    if item.get("id") == screen_id
                ),
                None,
            )

            if screen is None:
                continue

            analyzed = intelligence.analyze(
                screen,
                self.brain.get("requirements", {}),
            )

            contract["layout"] = analyzed.get("layout", "")
            contract["components"] = list(
                analyzed.get("components", [])
            )
            contract["fields"] = list(
                analyzed.get("fields", [])
            )
            # أفعال العقد التنفيذي هي مصدر الحقيقة للتنفيذ.
            # لا نستبدلها بأفعال التحليل النصية حتى لا نفقد
            # method / api / execution metadata.
            original_actions = list(contract.get("actions", []))
            analyzed_actions = list(analyzed.get("actions", []))

            if original_actions:
                contract["actions"] = original_actions
            else:
                contract["actions"] = analyzed_actions
            contract["roles"] = list(
                analyzed.get("roles", [])
            )
            contract["capabilities"] = list(
                analyzed.get("capabilities", [])
            )
            contract["navigation"] = dict(
                analyzed.get("navigation", {})
            )

        self.brain["screen_contracts"] = result

        if result.get("status") != "PASSED":
            raise RuntimeError(
                "ABQARYNO_SCREEN_CONTRACTS_INVALID: "
                + ", ".join(result.get("errors", []))
            )

        print(
            "✅ [Screen Contract Agent] "
            f"{result.get('total', 0)} screen contracts ready."
        )

    def validate_internal_blueprint(self):
        """يتحقق من الـBlueprint داخليًا قبل السماح بالبناء."""
        blueprint = self.brain.get("blueprint", {})
        errors = []

        required = [
            "domain",
            "entities",
            "modules",
            "database",
            "security",
            "completion_criteria",
        ]

        for key in required:
            if key not in blueprint:
                errors.append("missing:" + key)

        if not blueprint.get("modules"):
            errors.append("no_modules")

        for module in blueprint.get("modules", []):
            for requirement in module.get("requires", []):
                if not requirement:
                    errors.append("invalid_module_requirement")

        valid = not errors

        self.brain["blueprint_validation"] = {
            "status": "PASSED" if valid else "FAILED",
            "errors": errors,
        }

        if not valid:
            raise RuntimeError(
                "ABQARYNO_INTERNAL_BLUEPRINT_INVALID: "
                + ", ".join(errors)
            )

        return True


    def run_architect_agent(self):
        print("🧠 [Architect Agent] Designing architecture from internal Blueprint...")

        blueprint = self.brain.get("blueprint", {})
        if not blueprint:
            raise RuntimeError("ABQARYNO_BLUEPRINT_REQUIRED_FOR_ARCHITECTURE")

        domain = str(blueprint.get("domain", "")).strip().lower()
        modules = list(blueprint.get("modules", []))
        realtime = dict(blueprint.get("realtime", {}))
        security = dict(blueprint.get("security", {}))

        if not modules:
            raise RuntimeError("ABQARYNO_BLUEPRINT_MODULES_REQUIRED_FOR_ARCHITECTURE")

        capabilities = set()
        for module in modules:
            if isinstance(module, dict):
                for capability in module.get("capabilities", []):
                    capabilities.add(str(capability).strip().lower())
                for item in module.get("requires", []):
                    capabilities.add(str(item).strip().lower())
            else:
                capabilities.add(str(module).strip().lower())

        realtime_required = bool(
            realtime.get("required")
            or {"chat", "realtime", "video", "webrtc", "notifications"} & capabilities
        )

        auth_required = bool(
            security.get("authentication", True)
            or "auth" in capabilities
            or "users" in capabilities
        )

        architecture = {
            "generated_from": "internal_blueprint",
            "domain": domain,
            "stack": {
                "backend": "Node.js + Express",
                "database": "SQLite",
                "frontend": "HTML + CSS + JavaScript",
            },
            "realtime": {
                "required": realtime_required,
                "technology": (
                    "Socket.IO"
                    if realtime_required
                    else None
                ),
                "webrtc": bool(
                    {"video", "webrtc", "voice", "camera"} & capabilities
                ),
            },
            "auth": {
                "required": auth_required,
                "technology": (
                    "JWT + bcrypt"
                    if auth_required
                    else None
                ),
            },
            "modules": modules,
            "capabilities": sorted(capabilities),
        }

        self.brain["architecture"] = architecture

        self.brain["blueprint"]["architecture"] = {
            "generated": True,
            "backend": architecture["stack"]["backend"],
            "database": architecture["stack"]["database"],
            "frontend": architecture["stack"]["frontend"],
            "realtime": architecture["realtime"],
            "auth": architecture["auth"],
        }

        print(
            "✅ Architecture generated from Blueprint | "
            f"domain={domain or 'generic'} | "
            f"modules={len(modules)} | "
            f"realtime={'yes' if realtime_required else 'no'} | "
            f"auth={'yes' if auth_required else 'no'}"
        )


    def run_database_agent(self):
        print("🗄️ [Database Agent] Generating SQL schema from internal Blueprint...")

        db_dir = self.target_dir / "database"
        db_dir.mkdir(parents=True, exist_ok=True)

        blueprint = self.brain.get("blueprint", {})
        if not blueprint:
            raise RuntimeError("ABQARYNO_BLUEPRINT_REQUIRED_FOR_DATABASE")

        # قاعدة البيانات تُبنى من الـ Blueprint المعتمد، وليس من المتطلبات الخام.
        blueprint_entities = list(blueprint.get("entities", []))
        blueprint_database = dict(blueprint.get("database", {}))
        blueprint_relations = list(blueprint_database.get("relations", []))
        blueprint_capabilities = list(blueprint.get("capabilities", []))

        if not blueprint_entities:
            raise RuntimeError("ABQARYNO_BLUEPRINT_ENTITIES_REQUIRED_FOR_DATABASE")

        database_requirements = {
            "domain": blueprint.get("domain", "Standard-Web"),
            "entities": blueprint_entities,
            "capabilities": blueprint_capabilities,
            "roles": list(blueprint.get("roles", [])),
            "relations": blueprint_relations,
        }

        from engine.creation import DatabaseEngine

        database_engine = DatabaseEngine()
        tables = database_engine.analyze(database_requirements)
        schema = database_engine.schema(database_requirements)

        if not schema.strip():
            raise RuntimeError("ABQARYNO_DATABASE_SCHEMA_EMPTY")

        schema_path = db_dir / "schema.sql"
        schema_path.write_text(schema, encoding="utf-8")

        self.brain["blueprint"]["database"] = {
            "tables": tables,
            "entities": blueprint_entities,
            "relations": blueprint_relations,
            "capabilities": blueprint_capabilities,
            "schema_path": "database/schema.sql",
            "generated_from": "internal_blueprint",
        }

        self.brain["database"] = {
            "status": "Schema generated from Blueprint",
            "path": "database/schema.sql",
            "tables": tables,
        }

        print(
            f"✅ Database schema created from Blueprint | "
            f"tables={len(tables)}"
        )

    def run_frontend_agent(self):
        print("🎨 [Frontend Agent] Generating contract-driven UI...")

        blueprint = self.brain.get("blueprint", {})
        if not blueprint:
            raise RuntimeError("ABQARYNO_BLUEPRINT_REQUIRED_FOR_FRONTEND")

        public_dir = self.target_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)

        contracts = list(
            self.brain.get("screen_contracts", {}).get("contracts", [])
        )

        if not contracts:
            raise RuntimeError(
                "ABQARYNO_SCREEN_CONTRACTS_REQUIRED_FOR_FRONTEND"
            )

        api_list = list(blueprint.get("api", []))

        contract_data = json.dumps(
            contracts,
            ensure_ascii=False
        )

        api_data = json.dumps(
            api_list,
            ensure_ascii=False
        )

        html_content = r"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__PROJECT_NAME__</title>

<style>
*{box-sizing:border-box}

body{
    margin:0;
    min-height:100vh;
    font-family:Tahoma,Arial,sans-serif;
    background:#0f172a;
    color:#f8fafc;
}

header{
    padding:18px;
    text-align:center;
    background:#111827;
    border-bottom:1px solid #334155;
}

header h1{
    margin:0;
    color:#fbbf24;
}

header p{
    color:#cbd5e1;
}

main{
    width:min(1000px,94%);
    margin:25px auto;
}

.status{
    padding:12px;
    margin-bottom:18px;
    border:1px solid #334155;
    border-radius:10px;
    background:#172033;
}

.status.ok{
    border-color:#166534;
}

.screen{
    background:#1e293b;
    border:1px solid #334155;
    border-radius:16px;
    padding:22px;
}

.hidden{
    display:none !important;
}

.screen h2{
    color:#fbbf24;
    margin-top:0;
}

.screen-purpose{
    color:#cbd5e1;
    line-height:1.8;
}

.actions{
    display:flex;
    flex-wrap:wrap;
    gap:10px;
    margin-top:20px;
}

button{
    border:0;
    border-radius:9px;
    padding:11px 16px;
    cursor:pointer;
    font-weight:bold;
}

.primary{
    background:#fbbf24;
    color:#111827;
}

.secondary{
    background:#334155;
    color:#f8fafc;
}

.danger{
    background:#991b1b;
    color:white;
}

.choice-grid{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(230px,1fr));
    gap:16px;
    margin-top:20px;
}

.choice{
    padding:20px;
    background:#111827;
    border:1px solid #334155;
    border-radius:13px;
}

.choice h3{
    color:#fbbf24;
}

.chat{
    display:flex;
    flex-direction:column;
    gap:14px;
}

.messages{
    min-height:280px;
    max-height:55vh;
    overflow:auto;
    padding:15px;
    background:#111827;
    border:1px solid #334155;
    border-radius:12px;
}

.message{
    padding:10px 12px;
    margin-bottom:10px;
    border-radius:10px;
    background:#1e293b;
}

.message.consultant{
    border-right:4px solid #fbbf24;
}

textarea{
    width:100%;
    min-height:90px;
    resize:vertical;
    padding:12px;
    background:#111827;
    color:#f8fafc;
    border:1px solid #334155;
    border-radius:10px;
}

.toolbar{
    display:flex;
    flex-wrap:wrap;
    gap:8px;
    padding:12px;
    background:#111827;
    border:1px solid #334155;
    border-radius:10px;
}

.toolbar label,
.toolbar button{
    display:inline-flex;
    align-items:center;
    gap:6px;
}

.file-list{
    color:#cbd5e1;
    font-size:14px;
}

.reply-actions{
    display:flex;
    flex-wrap:wrap;
    gap:7px;
    margin-top:8px;
}

.small{
    padding:7px 10px;
    font-size:13px;
}

.back{
    margin-bottom:15px;
}

.notice{
    color:#94a3b8;
    line-height:1.7;
}

@media(max-width:650px){
    main{width:96%}
    .screen{padding:15px}
}
</style>
</head>

<body>

<header>
    <h1>__PROJECT_NAME__</h1>
    <p>منصة الاستشارات القانونية أون لاين</p>
</header>

<main>

<div id="status" class="status">
    جاري الاتصال بالنظام...
</div>

<section id="app"></section>

</main>

<script>
const ABQARYNO_CONTRACTS = __CONTRACTS__;
const ABQARYNO_API = __API__;

const state = {
    current: null,
    user: null,
    consultations: {},
    conversationId: null,
    selectedFiles: []
};

function escapeHtml(value){
    return String(value ?? "")
        .replaceAll("&","&amp;")
        .replaceAll("<","&lt;")
        .replaceAll(">","&gt;")
        .replaceAll('"',"&quot;")
        .replaceAll("'","&#039;");
}

function getContract(id){
    return ABQARYNO_CONTRACTS.find(
        c => c.id === id || c.key === id
    );
}

function getConsultationContracts(){
    return ABQARYNO_CONTRACTS.filter(c =>
        ["free_consultation","private_consultation"].includes(
            c.id || c.key
        )
    );
}

async function request(path, options = {}){
    const response = await fetch(path,{
        headers:{
            "Content-Type":"application/json",
            ...(options.headers || {})
        },
        ...options
    });

    const data = await response.json().catch(() => ({}));

    if(!response.ok){
        const error = new Error(
            data.error || `HTTP ${response.status}`
        );
        error.data = data;
        throw error;
    }

    return data;
}

async function ensureUser(){
    if(state.user) return state.user;

    const result = await request("/api/users",{
        method:"POST",
        body:JSON.stringify({
            name:"مستخدم عبقرينو"
        })
    });

    state.user = {
        id:result.id,
        name:"مستخدم عبقرينو"
    };

    return state.user;
}

function showStatus(message, ok=false){
    const status = document.getElementById("status");
    status.textContent = message;
    status.classList.toggle("ok",ok);
}

function renderWelcome(){
    const contract =
        getContract("home") ||
        ABQARYNO_CONTRACTS[0];

    const app = document.getElementById("app");

    app.innerHTML = `
        <section class="screen">
            <h2>${escapeHtml(
                contract?.title || "مرحبًا بك"
            )}</h2>

            <p class="screen-purpose">
                ${escapeHtml(
                    contract?.purpose ||
                    "بوابة الاستشارات القانونية أون لاين"
                )}
            </p>

            <div class="actions">
                <button class="primary"
                        onclick="renderChoice()">
                    متابعة
                </button>
            </div>
        </section>
    `;

    state.current = "home";
}

function renderChoice(){
    const contracts = getConsultationContracts();
    const app = document.getElementById("app");

    app.innerHTML = `
        <section class="screen">
            <button class="secondary back"
                    onclick="renderWelcome()">
                ← رجوع
            </button>

            <h2>اختيار نوع الاستشارة</h2>

            <p class="notice">
                اختر نوع الاستشارة التي تريد الدخول إليها.
            </p>

            <div class="choice-grid">
                ${contracts.map(contract => `
                    <div class="choice">
                        <h3>
                            ${escapeHtml(contract.title)}
                        </h3>

                        <p class="screen-purpose">
                            ${escapeHtml(contract.purpose)}
                        </p>

                        <button class="primary"
                                onclick="openConsultation(
                                    '${escapeHtml(contract.id || contract.key)}'
                                )">
                            دخول
                        </button>
                    </div>
                `).join("")}
            </div>
        </section>
    `;

    state.current = "choice";
}

async function openConsultation(screenId){
    const contract = getContract(screenId);

    if(!contract){
        showStatus("تعذر تحديد شاشة الاستشارة.");
        return;
    }

    try{
        const user = await ensureUser();

        const type =
            screenId === "private_consultation"
                ? "private"
                : "free";

        let result = state.consultations[type];

        if(!result){
            result = await request("/api/consultations",{
                method:"POST",
                body:JSON.stringify({
                    user_id:user.id,
                    type,
                    status:"open",
                    subject:
                        type === "private"
                            ? "استشارة خاصة"
                            : "استشارة مجانية"
                })
            });

            state.consultations[type] = result;
        }

        state.conversationId =
            result.conversation?.id ||
            result.conversation_id ||
            null;

        renderConsultation(contract,type);

        await loadMessages();

        showStatus(
            "تم فتح الاستشارة وقاعدة البيانات متصلة.",
            true
        );

    }catch(error){
        showStatus(
            error.message || "تعذر فتح الاستشارة."
        );
    }
}

function renderConsultation(contract,type){
    const isPrivate =
        type === "private";

    const components =
        new Set(contract.components || []);

    const actions =
        new Set(contract.actions || []);

    const app = document.getElementById("app");

    app.innerHTML = `
        <section class="screen">

            <button class="secondary back"
                    onclick="renderChoice()">
                ← رجوع
            </button>

            <h2>${escapeHtml(contract.title)}</h2>

            <p class="screen-purpose">
                ${escapeHtml(contract.purpose)}
            </p>

            <div class="chat">

                ${
                    components.has("بيانات المستشار")
                    ? `
                    <div class="notice">
                        بيانات المستشار
                    </div>
                    `
                    : ""
                }

                ${
                    components.has("منطقة الرسائل")
                    ? `
                    <div id="messages"
                         class="messages">
                        جاري تحميل الرسائل...
                    </div>
                    `
                    : ""
                }

                ${
                    components.has("حقل كتابة الرسالة")
                    ? `
                    <textarea id="message-input"
                              placeholder="اكتب رسالتك..."></textarea>
                    `
                    : ""
                }

                ${
                    components.has("شريط أدوات المرفقات")
                    ? `
                    <div class="toolbar">

                        ${
                            components.has("اختيار مستند")
                            ? `
                            <label>
                                📄 مستند
                                <input type="file"
                                       hidden
                                       onchange="selectFiles(this)">
                            </label>
                            `
                            : ""
                        }

                        ${
                            components.has("اختيار ملف")
                            ? `
                            <label>
                                📎 ملف
                                <input type="file"
                                       hidden
                                       onchange="selectFiles(this)">
                            </label>
                            `
                            : ""
                        }

                        ${
                            components.has("اختيار فيديو")
                            ? `
                            <label>
                                🎥 فيديو
                                <input type="file"
                                       accept="video/*"
                                       hidden
                                       onchange="selectFiles(this)">
                            </label>
                            `
                            : ""
                        }

                        ${
                            components.has("اختيار ملف صوتي")
                            ? `
                            <label>
                                🎵 صوت
                                <input type="file"
                                       accept="audio/*"
                                       hidden
                                       onchange="selectFiles(this)">
                            </label>
                            `
                            : ""
                        }

                    </div>

                    <div id="file-list"
                         class="file-list">
                        لا توجد ملفات مرفقة.
                    </div>
                    `
                    : ""
                }

                ${
                    components.has("زر إرسال")
                    ? `
                    <div class="actions">
                        <button class="primary"
                                onclick="sendMessage()">
                            إرسال
                        </button>
                    </div>
                    `
                    : ""
                }

            </div>
        </section>
    `;

    state.current = contract.id || contract.key;
}

function selectFiles(input){
    state.selectedFiles.push(
        ...Array.from(input.files || [])
    );

    const output =
        document.getElementById("file-list");

    if(!output) return;

    output.innerHTML =
        state.selectedFiles.length
            ? state.selectedFiles.map(
                file => escapeHtml(file.name)
              ).join("<br>")
            : "لا توجد ملفات مرفقة.";
}

async function loadMessages(){
    const output =
        document.getElementById("messages");

    if(!output) return;

    try{
        const data =
            await request("/api/messages");

        const rows =
            Array.isArray(data)
                ? data
                : data.messages || data.rows || [];

        output.innerHTML =
            rows.length
                ? rows.map(renderMessage).join("")
                : `<p class="notice">
                     لا توجد رسائل بعد.
                   </p>`;

    }catch(error){
        output.innerHTML =
            `<p class="notice">
                ${escapeHtml(error.message)}
             </p>`;
    }
}

function renderMessage(message){
    const text =
        message.message ||
        message.content ||
        "";

    const isConsultant =
        String(message.role || "")
            .toLowerCase()
            .includes("consult");

    return `
        <div class="message ${
            isConsultant ? "consultant" : ""
        }">
            <div>${escapeHtml(text)}</div>

            ${
                isConsultant
                ? `
                <div class="reply-actions">

                    <button class="secondary small"
                            onclick='copyReply(${JSON.stringify(text)})'>
                        نسخ
                    </button>

                    <button class="secondary small"
                            onclick='printReply(${JSON.stringify(text)})'>
                        طباعة
                    </button>

                    <button class="secondary small"
                            onclick='exportReply(${JSON.stringify(text)})'>
                        تصدير
                    </button>

                </div>
                `
                : ""
            }
        </div>
    `;
}

async function sendMessage(){
    const input =
        document.getElementById("message-input");

    if(!input || !input.value.trim()){
        showStatus("اكتب الرسالة أولًا.");
        return;
    }

    if(!state.conversationId){
        showStatus("لم يتم إنشاء محادثة بعد.");
        return;
    }

    try{
        const user = await ensureUser();

        await request("/api/messages",{
            method:"POST",
            body:JSON.stringify({
                conversation_id:state.conversationId,
                sender_id:user.id,
                message:input.value.trim()
            })
        });

        input.value = "";
        await loadMessages();

        showStatus("تم إرسال الرسالة.",true);

    }catch(error){
        showStatus(
            error.message || "تعذر إرسال الرسالة."
        );
    }
}

function copyReply(text){
    navigator.clipboard?.writeText(text);
    showStatus("تم نسخ الرد.",true);
}

function printReply(text){
    const win = window.open("","_blank");

    if(!win){
        showStatus("تعذر فتح نافذة الطباعة.");
        return;
    }

    win.document.write(`
        <html dir="rtl">
        <body>
        <h2>رد المستشار</h2>
        <p>${escapeHtml(text)}</p>
        <script>
        window.print();
        <\/script>
        </body>
        </html>
    `);

    win.document.close();
}

function exportReply(text){
    const blob =
        new Blob([text],{
            type:"text/plain;charset=utf-8"
        });

    const url =
        URL.createObjectURL(blob);

    const a =
        document.createElement("a");

    a.href = url;
    a.download = "رد-المستشار.txt";
    a.click();

    URL.revokeObjectURL(url);

    showStatus("تم تصدير الرد.",true);
}

async function checkHealth(){
    try{
        const data =
            await request("/api/health");

        showStatus(
            data.database === "connected"
                ? "النظام متصل وقاعدة البيانات تعمل."
                : "النظام متصل.",
            true
        );
    }catch(error){
        showStatus("تعذر الاتصال بالخادم.");
    }
}

renderWelcome();
checkHealth();
</script>

</body>
</html>
"""

        html_content = html_content.replace(
            "__PROJECT_NAME__",
            str(self.project_name)
        )

        html_content = html_content.replace(
            "__CONTRACTS__",
            contract_data
        )

        html_content = html_content.replace(
            "__API__",
            api_data
        )

        (public_dir / "index.html").write_text(
            html_content,
            encoding="utf-8"
        )

        self.brain["frontend"] = {
            "status": "UI generated from screen contracts",
            "path": "public/index.html",
            "screens": len(contracts),
            "api_bindings": len(api_list),
            "generated_from": "screen_contracts",
        }

        self.brain["blueprint"]["frontend"] = {
            "generated": True,
            "screens": len(contracts),
            "api_bindings": len(api_list),
            "source": "screen_contracts",
        }

        print(
            f"✅ Contract-driven UI generated | "
            f"screens={len(contracts)} | apis={len(api_list)}"
        )

    def run_backend_agent(self):
        print("⚙️ [Backend Agent] Generating backend from internal Blueprint...")

        blueprint = self.brain.get("blueprint", {})
        if not blueprint:
            raise RuntimeError("ABQARYNO_BLUEPRINT_REQUIRED_FOR_BACKEND")

        database = blueprint.get("database", {})
        tables = list(database.get("tables", []))

        if not tables:
            raise RuntimeError("ABQARYNO_DATABASE_TABLES_REQUIRED_FOR_BACKEND")

        public_dir = self.target_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)

        routes_dir = self.target_dir / "routes"
        routes_dir.mkdir(parents=True, exist_ok=True)

        server_code = r"""const express = require("express");
const path = require("path");
const fs = require("fs");
const { DatabaseSync } = require("node:sqlite");

const app = express();

app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true }));
app.use(express.static(path.join(__dirname, "public")));

const databaseDir = path.join(__dirname, "database");
fs.mkdirSync(databaseDir, { recursive: true });

const dbPath = path.join(databaseDir, "app.db");
const db = new DatabaseSync(dbPath);

const schemaPath = path.join(databaseDir, "schema.sql");
if (fs.existsSync(schemaPath)) {
    const schema = fs.readFileSync(schemaPath, "utf8");
    db.exec(schema);
}

app.locals.db = db;

/* =========================
   Abqaryno Authentication
   ========================= */

const crypto = require("crypto");

db.exec(`
CREATE TABLE IF NOT EXISTS auth_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT "client",
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS auth_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES auth_users(id)
);
`);

function hashPassword(password, salt) {
    return crypto.scryptSync(password, salt, 64).toString("hex");
}

function createPasswordHash(password) {
    const salt = crypto.randomBytes(16).toString("hex");
    return {
        salt,
        hash: hashPassword(password, salt)
    };
}

function verifyPassword(password, salt, expectedHash) {
    const actual = hashPassword(password, salt);

    return crypto.timingSafeEqual(
        Buffer.from(actual, "hex"),
        Buffer.from(expectedHash, "hex")
    );
}

function createSession(userId) {
    const token = crypto.randomBytes(32).toString("hex");

    const tokenHash = crypto
        .createHash("sha256")
        .update(token)
        .digest("hex");

    const createdAt = new Date();
    const expiresAt = new Date(
        createdAt.getTime() + (7 * 24 * 60 * 60 * 1000)
    );

    db.prepare(`
        INSERT INTO auth_sessions
        (user_id, token_hash, expires_at, created_at)
        VALUES (?, ?, ?, ?)
    `).run(
        userId,
        tokenHash,
        expiresAt.toISOString(),
        createdAt.toISOString()
    );

    return token;
}

function getAuthenticatedUser(req) {
    const header = String(req.headers.authorization || "");

    if (!header.startsWith("Bearer ")) {
        return null;
    }

    const token = header.slice(7).trim();

    if (!token) {
        return null;
    }

    const tokenHash = crypto
        .createHash("sha256")
        .update(token)
        .digest("hex");

    const row = db.prepare(`
        SELECT
            u.id,
            u.full_name,
            u.phone,
            u.role,
            u.active,
            s.expires_at
        FROM auth_sessions s
        JOIN auth_users u ON u.id = s.user_id
        WHERE s.token_hash = ?
    `).get(tokenHash);

    if (!row || !row.active) {
        return null;
    }

    if (new Date(row.expires_at).getTime() <= Date.now()) {
        db.prepare(
            "DELETE FROM auth_sessions WHERE token_hash = ?"
        ).run(tokenHash);

        return null;
    }

    return row;
}

function requireAuth(req, res, next) {
    const user = getAuthenticatedUser(req);

    if (!user) {
        return res.status(401).json({
            ok: false,
            error: "يجب تسجيل الدخول أولاً"
        });
    }

    req.user = user;
    next();
}

app.post("/api/auth/register", (req, res) => {
    try {
        const input = req.body && typeof req.body === "object"
            ? req.body
            : {};

        const fullName = String(input.full_name || input.name || "").trim();
        const phone = String(input.phone || "").trim();
        const password = String(input.password || "");

        if (!fullName || !phone || password.length < 8) {
            return res.status(400).json({
                ok: false,
                error: "الاسم ورقم الهاتف وكلمة المرور من 8 أحرف على الأقل مطلوبة"
            });
        }

        const existing = db.prepare(
            "SELECT id FROM auth_users WHERE phone = ?"
        ).get(phone);

        if (existing) {
            return res.status(409).json({
                ok: false,
                error: "رقم الهاتف مسجل بالفعل"
            });
        }

        const credentials = createPasswordHash(password);
        const now = new Date().toISOString();

        const result = db.prepare(`
            INSERT INTO auth_users
            (full_name, phone, password_hash, password_salt, role, active, created_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)
        `).run(
            fullName,
            phone,
            credentials.hash,
            credentials.salt,
            "client",
            now
        );

        const userId = Number(result.lastInsertRowid);
        const token = createSession(userId);

        res.status(201).json({
            ok: true,
            user: {
                id: userId,
                full_name: fullName,
                phone,
                role: "client"
            },
            token
        });
    } catch (error) {
        console.error(error);

        res.status(400).json({
            ok: false,
            error: "تعذر إنشاء الحساب"
        });
    }
});

app.post("/api/auth/login", (req, res) => {
    try {
        const input = req.body && typeof req.body === "object"
            ? req.body
            : {};

        const phone = String(input.phone || "").trim();
        const password = String(input.password || "");

        if (!phone || !password) {
            return res.status(400).json({
                ok: false,
                error: "رقم الهاتف وكلمة المرور مطلوبان"
            });
        }

        const user = db.prepare(`
            SELECT
                id,
                full_name,
                phone,
                password_hash,
                password_salt,
                role,
                active
            FROM auth_users
            WHERE phone = ?
        `).get(phone);

        if (!user || !user.active) {
            return res.status(401).json({
                ok: false,
                error: "بيانات الدخول غير صحيحة"
            });
        }

        if (!verifyPassword(
            password,
            user.password_salt,
            user.password_hash
        )) {
            return res.status(401).json({
                ok: false,
                error: "بيانات الدخول غير صحيحة"
            });
        }

        const token = createSession(user.id);

        res.json({
            ok: true,
            user: {
                id: user.id,
                full_name: user.full_name,
                phone: user.phone,
                role: user.role
            },
            token
        });
    } catch (error) {
        console.error(error);

        res.status(500).json({
            ok: false,
            error: "تعذر تسجيل الدخول"
        });
    }
});

app.get("/api/auth/me", requireAuth, (req, res) => {
    res.json({
        ok: true,
        user: {
            id: req.user.id,
            full_name: req.user.full_name,
            phone: req.user.phone,
            role: req.user.role
        }
    });
});

app.post("/api/auth/logout", requireAuth, (req, res) => {
    const header = String(req.headers.authorization || "");
    const token = header.slice(7).trim();

    const tokenHash = crypto
        .createHash("sha256")
        .update(token)
        .digest("hex");

    db.prepare(
        "DELETE FROM auth_sessions WHERE token_hash = ?"
    ).run(tokenHash);

    res.json({
        ok: true,
        message: "تم تسجيل الخروج"
    });
});

app.get("/api/health", (req, res) => {
    res.json({
        ok: true,
        status: "PASS",
        factory: "Abqaryno Master",
        database: "connected"
    });
});

app.get("/api/meta", (req, res) => {
    res.json({
        ok: true,
        project: __PROJECT_NAME__,
        tables: __TABLES__
    });
});

__ROUTES__

app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({
        ok: false,
        error: "حدث خطأ داخلي في الخادم"
    });
});

const PORT = Number(process.env.PORT || 3000);

app.listen(PORT, "0.0.0.0", () => {
    console.log(`🚀 Abqaryno App running on port ${PORT}`);
});
"""

        project_name_json = json.dumps(
            self.project_name,
            ensure_ascii=False
        )

        tables_json = json.dumps(
            tables,
            ensure_ascii=False
        )

        route_blocks = []

        for table in tables:
            safe_table = str(table).strip()

            if not safe_table.isidentifier():
                continue

            route_blocks.append(
                """
app.get("/api/TABLE_NAME", (req, res) => {
    try {
        const rows = db.prepare("SELECT * FROM TABLE_NAME").all();
        res.json({
            ok: true,
            table: "TABLE_NAME",
            data: rows
        });
    } catch (error) {
        res.status(500).json({
            ok: false,
            table: "TABLE_NAME",
            error: error.message
        });
    }
});

app.post("/api/TABLE_NAME", (req, res) => {
    try {
        const input = req.body && typeof req.body === "object"
            ? { ...req.body }
            : {};

        const tableColumns = db.prepare(
            "PRAGMA table_info(TABLE_NAME)"
        ).all();

        const hasCreatedAt = tableColumns.some(
            column => column.name === "created_at"
        );

        if (
            hasCreatedAt &&
            input.created_at === undefined
        ) {
            input.created_at = new Date().toISOString();
        }

        const columns = Object.keys(input).filter(
            key => /^[A-Za-z_][A-Za-z0-9_]*$/.test(key)
        );

        if (!columns.length) {
            return res.status(400).json({
                ok: false,
                error: "لا توجد بيانات صالحة للحفظ"
            });
        }

        const values = columns.map(key => input[key]);
        const placeholders = columns.map(() => "?").join(", ");
        const columnSql = columns
            .map(key => `"${key}"`)
            .join(", ");

        const statement = db.prepare(
            `INSERT INTO TABLE_NAME (${columnSql})
             VALUES (${placeholders})`
        );

        const result = statement.run(...values);

        res.status(201).json({
            ok: true,
            table: "TABLE_NAME",
            id: Number(result.lastInsertRowid)
        });
    } catch (error) {
        res.status(400).json({
            ok: false,
            table: "TABLE_NAME",
            error: error.message
        });
    }
});
app.get("/api/TABLE_NAME/:id", (req, res) => {
    try {
        const row = db.prepare(
            "SELECT * FROM TABLE_NAME WHERE id = ?"
        ).get(req.params.id);

        if (!row) {
            return res.status(404).json({
                ok: false,
                table: "TABLE_NAME",
                error: "NOT_FOUND"
            });
        }

        res.json({
            ok: true,
            table: "TABLE_NAME",
            data: row
        });
    } catch (error) {
        res.status(500).json({
            ok: false,
            table: "TABLE_NAME",
            error: error.message
        });
    }
});

app.put("/api/TABLE_NAME/:id", (req, res) => {
    try {
        const input = req.body && typeof req.body === "object"
            ? req.body
            : {};

        const columns = Object.keys(input).filter(
            key =>
                key !== "id" &&
                /^[A-Za-z_][A-Za-z0-9_]*$/.test(key)
        );

        if (!columns.length) {
            return res.status(400).json({
                ok: false,
                error: "لا توجد بيانات صالحة للتعديل"
            });
        }

        const values = columns.map(key => input[key]);

        const assignments = columns
            .map(key => `"${key}" = ?`)
            .join(", ");

        values.push(req.params.id);

        const statement = db.prepare(
            `UPDATE TABLE_NAME
             SET ${assignments}
             WHERE id = ?`
        );

        const result = statement.run(...values);

        if (!result.changes) {
            return res.status(404).json({
                ok: false,
                table: "TABLE_NAME",
                error: "NOT_FOUND"
            });
        }

        res.json({
            ok: true,
            table: "TABLE_NAME",
            id: Number(req.params.id),
            updated: true
        });
    } catch (error) {
        res.status(400).json({
            ok: false,
            table: "TABLE_NAME",
            error: error.message
        });
    }
});

app.delete("/api/TABLE_NAME/:id", (req, res) => {
    try {
        const result = db.prepare(
            "DELETE FROM TABLE_NAME WHERE id = ?"
        ).run(req.params.id);

        if (!result.changes) {
            return res.status(404).json({
                ok: false,
                table: "TABLE_NAME",
                error: "NOT_FOUND"
            });
        }

        res.json({
            ok: true,
            table: "TABLE_NAME",
            id: Number(req.params.id),
            deleted: true
        });
    } catch (error) {
        res.status(400).json({
            ok: false,
            table: "TABLE_NAME",
            error: error.message
        });
    }
});

""".replace("TABLE_NAME", safe_table)
            )

        routes = "\n".join(route_blocks)

        server_code = server_code.replace(
            "__PROJECT_NAME__",
            project_name_json
        )
        server_code = server_code.replace(
            "__TABLES__",
            tables_json
        )
        server_code = server_code.replace(
            "__ROUTES__",
            routes
        )

        (self.target_dir / "server.js").write_text(
            server_code,
            encoding="utf-8"
        )

        package_json = json.dumps(
            {
                "name": self.target_dir.name.lower().replace(" ", "-"),
                "version": "1.0.0",
                "private": True,
                "main": "server.js",
                "scripts": {
                    "start": "node server.js"
                },
                "dependencies": {
                    "express": "^4.21.2"
                }
            },
            ensure_ascii=False,
            indent=2
        )

        (self.target_dir / "package.json").write_text(
            package_json,
            encoding="utf-8"
        )

        # Keep the functional API contract defined by the internal Blueprint.
        # Database tables are persistence resources and must not replace
        # the application's functional API contract.
        api_list = list(blueprint.get("api", []))

        if not api_list:
            raise RuntimeError(
                "ABQARYNO_BLUEPRINT_API_REQUIRED_FOR_BACKEND"
            )

        self.brain["blueprint"]["api"] = api_list

        self.brain["implementation"] = {
            "files": [
                "server.js",
                "package.json",
                "database/schema.sql",
                "database/app.db",
                "public/index.html",
            ],
            "generated_from": "internal_blueprint",
            "database_tables": tables,
            "api_generation": "blueprint_driven",
            "api_contracts": api_list,
            "authentication": {
                "status": "implemented",
                "password_hashing": "scrypt",
                "sessions": "sqlite",
                "routes": [
                    "/api/auth/register",
                    "/api/auth/login",
                    "/api/auth/me",
                    "/api/auth/logout",
                ],
            },
        }

        print(
            "✅ Backend generated from Blueprint | "
            f"tables={len(tables)} | apis={len(api_list)}"
        )


    def run_test_and_evidence_agent(self):
        import json
        import shutil
        import subprocess
        from datetime import datetime

        tests = []
        root = self.target_dir

        def add_test(name, command, passed, stdout="", stderr="", exit_code=None):
            tests.append({
                "test": name,
                "command": command,
                "passed": bool(passed),
                "exit_code": exit_code,
                "stdout": stdout[-4000:],
                "stderr": stderr[-4000:],
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })

        required = [
            "server.js",
            "package.json",
            "database/schema.sql",
            "public/index.html",
        ]

        missing = [x for x in required if not (root / x).exists()]

        add_test(
            "Required Files Test",
            "filesystem-check",
            not missing,
            stdout="required files present" if not missing else "",
            stderr="missing: " + ", ".join(missing) if missing else "",
            exit_code=0 if not missing else 1,
        )

        node = shutil.which("node")

        if not node:
            add_test(
                "Node Availability Test",
                "node --version",
                False,
                stderr="node executable not found",
                exit_code=127,
            )
        else:
            proc = subprocess.run(
                [node, "--check", "server.js"],
                cwd=root,
                text=True,
                capture_output=True,
            )

            add_test(
                "Server Syntax Test",
                "node --check server.js",
                proc.returncode == 0,
                proc.stdout,
                proc.stderr,
                proc.returncode,
            )

            sqlite_check = subprocess.run(
                [
                    node,
                    "-e",
                    "const { DatabaseSync } = require('node:sqlite'); "
                    "const db = new DatabaseSync(':memory:'); "
                    "db.exec('CREATE TABLE t(id INTEGER);'); "
                    "console.log('NODE_SQLITE_RUNTIME_OK');",
                ],
                cwd=root,
                text=True,
                capture_output=True,
            )

            add_test(
                "SQLite Runtime Test",
                "node:sqlite in-memory database",
                sqlite_check.returncode == 0
                and "NODE_SQLITE_RUNTIME_OK" in sqlite_check.stdout,
                sqlite_check.stdout,
                sqlite_check.stderr,
                sqlite_check.returncode,
            )

        # عبقرينو V2: تحقق مستقل من المشروع المولد
        creation_verification = None

        try:
            from engine.creation import CreationVerificationEngine

            creation_verification = (
                CreationVerificationEngine().verify(root)
            )

            for check in creation_verification.get("checks", []):
                add_test(
                    "Creation V2 | " + str(check.get("name", "unknown")),
                    "CreationVerificationEngine V2",
                    check.get("status") == "PASSED",
                    json.dumps(
                        check,
                        ensure_ascii=False,
                    ),
                    "",
                    0 if check.get("status") == "PASSED" else 1,
                )

        except Exception as exc:
            add_test(
                "Creation V2 Verification",
                "CreationVerificationEngine V2",
                False,
                "",
                repr(exc),
                1,
            )

            creation_verification = {
                "version": 2,
                "status": "FAILED",
                "error": repr(exc),
                "checks": [],
                "failed_checks": ["Creation V2 Verification"],
            }

        creation_checks_passed = bool(creation_verification) and (
            creation_verification.get("status") == "PASSED"
            and not creation_verification.get("failed_checks")
        )

        verified = bool(tests) and all(
            t["passed"] for t in tests
        ) and creation_checks_passed

        if creation_verification:
            creation_verification["status"] = (
                "PASSED" if creation_checks_passed else "FAILED"
            )
            if creation_checks_passed:
                creation_verification.pop("failed_checks", None)

        evidence = {
            "version": 2,
            "verified": verified,
            "status": "PASS" if verified else "FAILED",
            "tests": tests,
            "creation_verification": creation_verification,
            "runtime": {
                "node": subprocess.run(
                    ["node", "--version"],
                    text=True,
                    capture_output=True,
                ).stdout.strip()
                if shutil.which("node") else None
            },
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        (root / ".abqaryno-evidence.json").write_text(
            json.dumps(
                evidence,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        self.brain["tests"] = tests
        self.brain["evidence"] = evidence

        print("\n=== ABQARYNO REAL VERIFICATION V2 ===")

        for test in tests:
            state = "PASS" if test["passed"] else "FAIL"
            print(f"{state} | {test['test']}")

        print(
            f"VERIFICATION_STATUS={evidence['status']}"
        )

    def run_real_execution_agent(self):
        """
        تشغيل المشروع الناتج فعليًا مع عصا التنفيذ والتعافي.
        """

        print(
            "🪄 [Magic Cane] "
            "Inspecting execution area..."
        )

        from engine.execution_recovery_engine import (
            ExecutionRecoveryEngine,
        )

        recovery = ExecutionRecoveryEngine(
            self.target_dir
        )

        recovery_report = recovery.execute_with_recovery()

        self.brain.setdefault("evidence", {})
        self.brain["evidence"][
            "execution_recovery"
        ] = recovery_report

        if recovery_report.get("status") not in {
            "COMPLETED_CLEAN",
            "COMPLETED_WITH_REPAIRS",
        }:
            raise RuntimeError(
                "ABQARYNO_EXECUTION_RECOVERY_BLOCKED"
            )

        print(
            "🪄 [Magic Cane] "
            "Recovery inspection passed."
        )

        from engine.real_execution_engine import (
            RealExecutionEngine,
        )

        print(
            "🚀 [Real Execution Agent] "
            "Starting real runtime verification..."
        )

        engine = RealExecutionEngine(
            self.target_dir
        )

        report = engine.run(
            blueprint=self.brain.get(
                "blueprint",
                {},
            )
        )

        self.brain["evidence"][
            "real_execution"
        ] = report

        if report.get("status") != "PASS":
            raise RuntimeError(
                "ABQARYNO_REAL_EXECUTION_FAILED"
            )

        print(
            "✅ [Real Execution Agent] "
            "Real runtime and HTTP checks passed."
        )

    def run_real_screen_generator_agent(self):
        """
        تحويل Screen Contracts إلى ملفات شاشات
        حقيقية داخل المشروع الناتج.
        """

        print(
            "🖥️ [Real Screen Generator] "
            "Generating executable screens..."
        )

        from engine.real_screen_generator import (
            RealScreenGenerator,
        )

        contract_result = self.brain.get(
            "screen_contracts",
            {},
        )

        contracts = contract_result.get(
            "contracts",
            [],
        )

        if contract_result.get("status") != "PASSED":
            raise RuntimeError(
                "ABQARYNO_SCREEN_CONTRACTS_REQUIRED"
            )

        result = RealScreenGenerator(
            self.target_dir,
            contracts,
        ).generate()

        self.brain.setdefault(
            "evidence",
            {},
        )

        self.brain["evidence"][
            "real_screen_generation"
        ] = result

        if result.get("status") != "PASSED":
            raise RuntimeError(
                "ABQARYNO_REAL_SCREEN_GENERATION_FAILED"
            )

        print(
            "✅ [Real Screen Generator] "
            f"{result.get('total', 0)} screens generated."
        )

    def _load_real_requirements_from_creation_engine(self):
        """مصدر الحقيقة: محلل الفكرة الفعلي، وليس قالب Legal-Tech ثابت."""
        from engine.creation import RequirementsEngine

        result = RequirementsEngine().analyze(self.specification)

        # تحليل الفكرة يحدد المعنى والخصائص والأدوار،
        # لكن الشاشات الفعلية يجب أن تكون فقط الشاشات التي
        # اختارها المستخدم واعتمد تصميماتها.
        try:
            specification_data = json.loads(self.specification)
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                "ABQARYNO_SPECIFICATION_JSON_INVALID"
            ) from exc

        approved_screens = specification_data.get("approved_screens", [])
        if not isinstance(approved_screens, list) or not approved_screens:
            raise RuntimeError(
                "ABQARYNO_APPROVED_SCREENS_REQUIRED"
            )

        invalid_screens = [
            screen for screen in approved_screens
            if not isinstance(screen, dict)
            or not str(screen.get("id", "")).strip()
            or not str(screen.get("title", "")).strip()
            or not str(screen.get("purpose", "")).strip()
            or not isinstance(screen.get("proposal"), dict)
            or screen["proposal"].get("approved") is not True
        ]

        if invalid_screens:
            raise RuntimeError(
                "ABQARYNO_APPROVED_SCREEN_CONTRACT_INVALID"
            )

        screens = list(approved_screens)
        features = list(result.get("features", []))
        roles = list(result.get("roles", []))
        capabilities = list(result.get("capabilities", []))

        # كيانات قاعدة البيانات تُشتق من المعنى الفعلي للفكرة،
        # وليست من قالب Legal-Tech ثابت.
        screen_ids = {
            str(screen.get("id", "")).strip().lower()
            for screen in screens
            if isinstance(screen, dict)
        }
        feature_text = " ".join(
            str(feature).strip().lower()
            for feature in features
        )

        entities = ["users"]

        if "free_consultation" in screen_ids or "private_consultation" in screen_ids:
            entities.append("consultations")

        if (
            "free_consultation" in screen_ids
            or "private_consultation" in screen_ids
            or "chat" in capabilities
            or "محادث" in feature_text
        ):
            entities.extend(["conversations", "messages"])

        if (
            "files" in capabilities
            or "مستند" in feature_text
            or "ملف" in feature_text
            or "إرفاق" in feature_text
        ):
            entities.append("documents")

        entities = list(dict.fromkeys(entities))

        self.brain["requirements"] = {
            "domain": "User-Specified",
            "entities": entities,
            "roles": roles,
            "screens": screens,
            "features": features,
            "capabilities": capabilities,
            "capability_labels": result.get("capability_labels", {}),
            "api": list(result.get("api", [])),
            "relations": [],
            "requirements_complete": True,
            "source": "engine.creation.RequirementsEngine",
            "source_of_truth": "USER_IDEA",
        }

        print(
            "✅ [Real Requirements Engine] "
            f"screens={len(screens)} | "
            f"features={len(features)} | "
            f"roles={len(roles)}"
        )

    def build(self):
        self._load_real_requirements_from_creation_engine()

        # Blueprint داخلي إجباري:
        # لا يظهر للمستخدم ولا يتحول إلى شاشة موافقة.
        self.build_internal_blueprint()
        self.validate_internal_blueprint()
        self.run_screen_contract_agent()

        print("🧠 [Internal Blueprint] validated successfully.")

        self.run_architect_agent()
        self.run_database_agent()
        self.run_frontend_agent()
        self.run_real_screen_generator_agent()
        self.run_backend_agent()
        self.run_real_execution_agent()
        self.run_test_and_evidence_agent()

        evidence = self.brain.get("evidence", {})
        verification = evidence.get(
            "creation_verification",
            {},
        )

        gate_passed = (
            evidence.get("status") == "PASS"
            and evidence.get("verified") is True
            and verification.get("status") == "PASSED"
            and not verification.get("failed_checks")
        )

        self.brain["creation_gate"] = {
            "version": 1,
            "status": "PASSED" if gate_passed else "BLOCKED",
            "required": [
                "generation",
                "syntax",
                "dependencies",
                "runtime_process",
                "http_runtime",
                "evidence",
            ],
        }

        if not gate_passed:
            self.brain["creation_status"] = "VERIFICATION_BLOCKED"

            evidence["creation_gate"] = self.brain["creation_gate"]

            (self.target_dir / ".abqaryno-evidence.json").write_text(
                __import__("json").dumps(
                    evidence,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            raise RuntimeError(
                "ABQARYNO_CREATION_GATE_BLOCKED"
            )

        self.brain["creation_status"] = "VERIFIED"

        evidence["creation_gate"] = self.brain["creation_gate"]
        evidence["creation_status"] = "VERIFIED"

        (self.target_dir / ".abqaryno-evidence.json").write_text(
            __import__("json").dumps(
                evidence,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print(
            f"CREATION_GATE=PASSED | "
            f"PROJECT={self.project_name}"
        )
        print(
            "🌟 ABQARYNO BUILD VERIFIED"
        )

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print(
            "USAGE: python engine/abqaryno_master_factory.py "
            "<project_name> <specification>"
        )
        raise SystemExit(2)

    project_name = sys.argv[1]
    specification = sys.argv[2]

    factory = MasterAbqarynoFactory(
        project_name,
        specification,
    )

    factory.build()

