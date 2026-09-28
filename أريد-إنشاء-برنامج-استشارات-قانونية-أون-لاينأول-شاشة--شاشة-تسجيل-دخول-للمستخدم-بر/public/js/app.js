const AbqarynoAPI = {
    async request(path, options = {}) {
        const response = await fetch(path, {
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            },
            ...options
        });

        let data = {};
        try {
            data = await response.json();
        } catch (error) {
            data = {
                ok: false,
                error: "استجابة API غير صالحة."
            };
        }

        if (!response.ok) {
            const error = new Error(
                data.error || `HTTP ${response.status}`
            );
            error.status = response.status;
            error.data = data;
            throw error;
        }

        return data;
    },

    health() {
        return this.request("/api/health");
    },

    search(query, items = []) {
        return this.request("/api/search", {
            method: "POST",
            body: JSON.stringify({
                query,
                items
            })
        });
    },

    report(title, data = {}) {
        return this.request("/api/advanced_reports", {
            method: "POST",
            body: JSON.stringify({
                title,
                data
            })
        });
    },

    ocr(data = {}) {
        return this.request("/api/ocr", {
            method: "POST",
            body: JSON.stringify(data)
        });
    },

    translation(data = {}) {
        return this.request("/api/translation", {
            method: "POST",
            body: JSON.stringify(data)
        });
    },

    voice(data = {}) {
        return this.request("/api/voice", {
            method: "POST",
            body: JSON.stringify(data)
        });
    }
};

window.abqarynoAPI = AbqarynoAPI;

function optionIds(project) {
    return (project.options || [])
        .map(option => {
            if (typeof option === "string") {
                return option;
            }
            return option && option.option_id;
        })
        .filter(Boolean);
}

function createServicePanel(project) {
    const ids = optionIds(project);

    if (!ids.length) {
        return;
    }

    const main = document.querySelector("main");

    if (!main) {
        return;
    }

    if (document.getElementById("abqaryno-api-tools")) {
        return;
    }

    const panel = document.createElement("section");
    panel.id = "abqaryno-api-tools";
    panel.className = "tools-panel";

    panel.innerHTML = `
        <div class="tool-card">
            <h3>🔌 خدمات البرنامج</h3>
            <p>الخدمات التي تم اختيارها أثناء إنشاء المشروع.</p>
            <div id="abqaryno-api-status">جاري فحص الاتصال...</div>
        </div>
    `;

    if (ids.includes("search")) {
        const card = document.createElement("div");
        card.className = "tool-card";
        card.innerHTML = `
            <h3>🔎 البحث</h3>
            <input id="abqaryno-api-search-input"
                   type="text"
                   placeholder="اكتب عبارة البحث...">
            <button id="abqaryno-api-search-button" type="button">
                بحث
            </button>
            <div id="abqaryno-api-search-results"></div>
        `;
        panel.appendChild(card);
    }

    if (ids.includes("advanced_reports")) {
        const card = document.createElement("div");
        card.className = "tool-card";
        card.innerHTML = `
            <h3>📊 التقارير</h3>
            <input id="abqaryno-api-report-title"
                   type="text"
                   placeholder="عنوان التقرير">
            <button id="abqaryno-api-report-button" type="button">
                إنشاء تقرير
            </button>
            <div id="abqaryno-api-report-result"></div>
        `;
        panel.appendChild(card);
    }

    for (const [id, label] of [
        ["ocr", "📄 OCR"],
        ["translation", "🌐 الترجمة"],
        ["voice", "🎙️ الصوت"]
    ]) {
        if (!ids.includes(id)) {
            continue;
        }

        const card = document.createElement("div");
        card.className = "tool-card";
        card.innerHTML = `
            <h3>${label}</h3>
            <p>الخدمة موجودة في المشروع، لكن محركها غير موصل بعد.</p>
        `;
        panel.appendChild(card);
    }

    main.appendChild(panel);

    const searchButton = document.getElementById(
        "abqaryno-api-search-button"
    );

    if (searchButton) {
        searchButton.addEventListener("click", async () => {
            const input = document.getElementById(
                "abqaryno-api-search-input"
            );
            const output = document.getElementById(
                "abqaryno-api-search-results"
            );

            const query = String(
                input ? input.value : ""
            ).trim();

            if (!query) {
                output.textContent = "اكتب عبارة البحث أولًا.";
                return;
            }

            output.textContent = "جاري البحث...";

            try {
                const result = await AbqarynoAPI.search(
                    query,
                    []
                );

                output.textContent = (
                    result.results || []
                ).join("، ") || "لا توجد نتائج.";
            } catch (error) {
                output.textContent =
                    error.data?.error ||
                    error.message ||
                    "تعذر تنفيذ البحث.";
            }
        });
    }

    const reportButton = document.getElementById(
        "abqaryno-api-report-button"
    );

    if (reportButton) {
        reportButton.addEventListener("click", async () => {
            const input = document.getElementById(
                "abqaryno-api-report-title"
            );
            const output = document.getElementById(
                "abqaryno-api-report-result"
            );

            const title = String(
                input ? input.value : ""
            ).trim();

            if (!title) {
                output.textContent = "اكتب عنوان التقرير أولًا.";
                return;
            }

            output.textContent = "جاري إنشاء التقرير...";

            try {
                const result = await AbqarynoAPI.report(
                    title,
                    {}
                );

                output.textContent =
                    result.title || "تم إنشاء التقرير.";
            } catch (error) {
                output.textContent =
                    error.data?.error ||
                    error.message ||
                    "تعذر إنشاء التقرير.";
            }
        });
    }
}

async function loadProject() {
    try {
        const response = await fetch("/project.json");
        const project = await response.json();

        const container = document.querySelector("main");

        if (!container) {
            return;
        }

        container.dataset.project = project.name || "";

        createServicePanel(project);

        try {
            const health = await AbqarynoAPI.health();
            const status = document.getElementById(
                "abqaryno-api-status"
            );

            if (status) {
                status.textContent = health.ok
                    ? "متصل بخدمات البرنامج."
                    : "الخدمة غير متاحة.";
            }
        } catch (error) {
            const status = document.getElementById(
                "abqaryno-api-status"
            );

            if (status) {
                status.textContent =
                    "تعذر الاتصال بخدمات البرنامج.";
            }
        }

        console.log(
            "تم تحميل مشروع عبقرينو:",
            project.name
        );
    } catch (error) {
        console.error(
            "تعذر تحميل مواصفات المشروع:",
            error
        );
    }
}

document.addEventListener(
    "DOMContentLoaded",
    loadProject
);
