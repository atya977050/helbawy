async function loadProject() {
    try {
        const response = await fetch("/project.json");
        const project = await response.json();

        const container = document.querySelector("main");

        if (!container) {
            return;
        }

        container.dataset.project = project.name || "";

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
