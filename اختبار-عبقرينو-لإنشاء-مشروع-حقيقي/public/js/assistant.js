
(() => {
    "use strict";

    const state = {
        context: null,
        messages: []
    };

    const $ = id => document.getElementById(id);

    function addMessage(text, type) {
        const container = $("assistant-messages");
        if (!container) return;

        const item = document.createElement("div");
        item.className = "assistant-message " + type;
        item.textContent = text;
        container.appendChild(item);

        container.scrollTop = container.scrollHeight;
        state.messages.push({text, type});
    }

    function capabilityLabel(key) {
        const labels =
            state.context &&
            state.context.capability_labels;

        return (labels && labels[key]) || key;
    }

    function currentScreen() {
        const screens =
            state.context && state.context.screens;

        if (!Array.isArray(screens) || !screens.length) {
            return null;
        }

        const visible = Array.from(
            document.querySelectorAll(".screen")
        );

        if (visible.length) {
            const index = Math.min(
                Math.max(
                    window.scrollY > 20 ? 1 : 0,
                    0
                ),
                screens.length - 1
            );

            return screens[index] || screens[0];
        }

        return screens[0];
    }

    function answer(question) {
        const q = String(question || "").trim().toLowerCase();

        if (!state.context) {
            return "المساعد ما زال يحمّل معلومات البرنامج. حاول مرة أخرى.";
        }

        const screen = currentScreen();
        const screens = Array.isArray(state.context.screens)
            ? state.context.screens
            : [];

        const capabilities = Array.isArray(state.context.capabilities)
            ? state.context.capabilities
            : [];

        if (
            q.includes("ماذا") &&
            (q.includes("أفعل") || q.includes("هنا"))
        ) {
            if (screen) {
                return (
                    "أنت الآن في شاشة " +
                    (screen.title || "الحالية") +
                    ". " +
                    (screen.purpose || "يمكنك استخدام الوظائف المتاحة في هذه الشاشة.") +
                    (
                        Array.isArray(screen.actions) &&
                        screen.actions.length
                            ? " الإجراءات المتاحة: " +
                              screen.actions.join("، ") +
                              "."
                            : ""
                    )
                );
            }

            return "يمكنك استخدام الشاشات والوظائف التي أنشأها البرنامج حسب صلاحياتك.";
        }

        if (
            q.includes("الشاشات") ||
            q.includes("شاشة") ||
            q.includes("الصفحات")
        ) {
            if (!screens.length) {
                return "لم يتم اعتماد شاشات إضافية لهذا البرنامج.";
            }

            return (
                "الشاشات المعتمدة: " +
                screens
                    .map(item => item.title || item.id)
                    .filter(Boolean)
                    .join("، ") +
                "."
            );
        }

        if (
            q.includes("الوظائف") ||
            q.includes("القدرات") ||
            q.includes("ماذا يمكن")
        ) {
            if (!capabilities.length) {
                return "لم يتم تسجيل قدرات إضافية لهذا البرنامج.";
            }

            return (
                "الوظائف المتاحة تشمل: " +
                capabilities
                    .map(capabilityLabel)
                    .join("، ") +
                "."
            );
        }

        if (
            q.includes("ترجم") ||
            q.includes("ترجمة")
        ) {
            if (capabilities.includes("translation")) {
                return "البرنامج يدعم الترجمة. استخدم وظيفة المستندات أو الترجمة المتاحة في الشاشة المناسبة.";
            }

            return "ميزة الترجمة غير مفعلة في هذا البرنامج.";
        }

        if (
            q.includes("مستند") ||
            q.includes("pdf") ||
            q.includes("word")
        ) {
            if (
                capabilities.includes("document_processing") ||
                capabilities.includes("files")
            ) {
                return "البرنامج يحتوي على قدرات للتعامل مع المستندات والملفات. يمكنك اختيار الملف من وظيفة المرفقات أو المستندات.";
            }

            return "لا توجد قدرة مستندات مسجلة لهذا البرنامج.";
        }

        if (
            q.includes("صوت") ||
            q.includes("تسجيل")
        ) {
            if (
                capabilities.includes("microphone") ||
                capabilities.includes("speech_to_text") ||
                capabilities.includes("text_to_speech")
            ) {
                return "البرنامج يحتوي على وظائف صوتية مفعلة، ويمكن استخدامها حسب الأدوات الموجودة في الشاشة.";
            }

            return "الوظائف الصوتية غير مفعلة في هذا البرنامج.";
        }

        if (
            q.includes("من أنت") ||
            q.includes("المساعد")
        ) {
            return "أنا المساعد الذكي المدمج في هذا البرنامج. أقرأ سياق البرنامج والشاشات والقدرات لمساعدتك أثناء الاستخدام.";
        }

        return (
            "أفهم سؤالك. أستطيع مساعدتك في التنقل وفهم الشاشات والوظائف والمستندات والقدرات المتاحة. " +
            "جرّب السؤال عن الشاشة الحالية أو الوظائف المتاحة."
        );
    }

    async function send(question) {
        const input = $("assistant-input");
        const value = String(
            question !== undefined
                ? question
                : input && input.value
        ).trim();

        if (!value) return;

        addMessage(value, "user");

        if (input) {
            input.value = "";
        }

        try {
            const screen = currentScreen() || {};

            const response = await fetch("/api/assistant", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    prompt: value,
                    idea: state.context && state.context.idea
                        ? state.context.idea
                        : "",
                    requirements: state.context || {},
                    screen: screen,
                    user: {}
                })
            });

            if (!response.ok) {
                throw new Error("تعذر الاتصال بالمساعد الذكي");
            }

            const result = await response.json();

            if (!result.ok) {
                throw new Error(
                    result.error || "تعذر معالجة طلب المساعد"
                );
            }

            addMessage(
                result.answer || "تم تحليل طلبك.",
                "assistant"
            );

            if (Array.isArray(result.actions) && result.actions.length) {
                result.actions.forEach(action => {
                    const needsConfirmation =
                        Boolean(action.requires_confirmation);

                    const suffix = needsConfirmation
                        ? " — يحتاج إلى تأكيدك قبل التنفيذ."
                        : "";

                    addMessage(
                        "اقتراح: " +
                        (action.title || action.action_id || "إجراء") +
                        suffix,
                        "assistant"
                    );

                    if (needsConfirmation) {
                        addConfirmationControls(action);
                    }
                });
            }
        } catch (error) {
            addMessage(
                "تعذر الاتصال بالمساعد الذكي حاليًا. " +
                "جرّب مرة أخرى.",
                "assistant"
            );
        }
    }

    function addConfirmationControls(action) {
        const container = $("assistant-messages");
        if (!container) return;

        const wrapper = document.createElement("div");
        wrapper.className = "assistant-action-confirmation";

        const confirmButton = document.createElement("button");
        confirmButton.type = "button";
        confirmButton.textContent = "تأكيد التنفيذ";

        const cancelButton = document.createElement("button");
        cancelButton.type = "button";
        cancelButton.textContent = "إلغاء";

        const status = document.createElement("span");
        status.className = "assistant-action-status";
        status.textContent = "بانتظار تأكيدك";

        const setDisabled = () => {
            confirmButton.disabled = true;
            cancelButton.disabled = true;
        };

        const confirm = async confirmed => {
            setDisabled();
            status.textContent = "جارٍ معالجة التأكيد...";

            try {
                const response = await fetch(
                    "/api/assistant/confirm",
                    {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json"
                        },
                        body: JSON.stringify({
                            confirmed,
                            action: {
                                action_id: action.action_id || "",
                                title: action.title || "",
                                description: action.description || "",
                                requires_confirmation:
                                    Boolean(action.requires_confirmation),
                                status: action.status || "proposed"
                            }
                        })
                    }
                );

                if (!response.ok) {
                    throw new Error("تعذر إرسال التأكيد");
                }

                const result = await response.json();

                if (!result.ok) {
                    throw new Error(
                        result.error || "تعذر معالجة التأكيد"
                    );
                }

                const finalStatus =
                    result.action && result.action.status
                        ? result.action.status
                        : (confirmed ? "approved" : "cancelled");

                status.textContent =
                    finalStatus === "approved"
                        ? "تم تأكيد الإجراء."
                        : "تم إلغاء الإجراء.";

                if (finalStatus === "approved") {
                    addMessage(
                        "تم اعتماد الإجراء بعد تأكيدك.",
                        "assistant"
                    );
                } else {
                    addMessage(
                        "تم إلغاء الإجراء.",
                        "assistant"
                    );
                }
            } catch (error) {
                confirmButton.disabled = false;
                cancelButton.disabled = false;
                status.textContent =
                    "تعذر معالجة التأكيد. حاول مرة أخرى.";
            }
        };

        confirmButton.addEventListener(
            "click",
            () => confirm(true)
        );

        cancelButton.addEventListener(
            "click",
            () => confirm(false)
        );

        wrapper.appendChild(confirmButton);
        wrapper.appendChild(cancelButton);
        wrapper.appendChild(status);

        container.appendChild(wrapper);
        container.scrollTop = container.scrollHeight;
    }

    function clearMessages() {
        const container = $("assistant-messages");
        if (container) {
            container.innerHTML = "";
        }

        state.messages = [];

        addMessage(
            "مرحبًا. أنا المساعد الذكي للبرنامج. كيف أساعدك؟",
            "assistant"
        );
    }

    async function initialize() {
        try {
            const response = await fetch(
                "/assistant-context.json",
                {cache: "no-store"}
            );

            if (!response.ok) {
                throw new Error("تعذر تحميل سياق البرنامج");
            }

            state.context = await response.json();

            const label = $("assistant-context-label");

            if (label && state.context.idea) {
                label.textContent =
                    "المساعد يفهم برنامج: " +
                    state.context.idea;
            }

            addMessage(
                "مرحبًا. أنا المساعد الذكي للبرنامج. اسألني عن الشاشة الحالية أو الوظائف المتاحة.",
                "assistant"
            );
        } catch (error) {
            addMessage(
                "تعذر تحميل سياق البرنامج حاليًا.",
                "assistant"
            );
        }

        const input = $("assistant-input");
        const sendButton = $("assistant-send");
        const clearButton = $("assistant-clear");

        if (sendButton) {
            sendButton.addEventListener(
                "click",
                () => send()
            );
        }

        if (input) {
            input.addEventListener(
                "keydown",
                event => {
                    if (event.key === "Enter") {
                        event.preventDefault();
                        send();
                    }
                }
            );
        }

        if (clearButton) {
            clearButton.addEventListener(
                "click",
                clearMessages
            );
        }

        document
            .querySelectorAll("[data-assistant-question]")
            .forEach(button => {
                button.addEventListener(
                    "click",
                    () => send(
                        button.getAttribute(
                            "data-assistant-question"
                        )
                    )
                );
            });
    }

    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initialize,
            {once: true}
        );
    } else {
        initialize();
    }
})();
