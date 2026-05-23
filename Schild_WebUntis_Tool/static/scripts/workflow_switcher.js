// Top-Level Workflow-Switcher: schaltet zwischen Schüler-, Erzieher- und
// Ausbilder-Workflow um. Phase 1 — nur UI-Skeleton; Erzieher/Ausbilder sind
// noch Platzhalter, werden in einer späteren Version mit Inhalt befüllt.

document.addEventListener("DOMContentLoaded", function () {
    const STORAGE_KEY = "activeWorkflow";
    const validWorkflows = ["schueler", "erzieher", "ausbilder"];

    // Pop-Up-Panels, die nach Workflow-Wechsel geschlossen werden sollten.
    // Schüler-spezifisch + shared, da bei Workflow-Wechsel sonst der vorherige
    // Kontext „hängen bleibt".
    const PANELS_TO_CLOSE = [
        "dashboardPanel", "warningsPanel", "infoMailPanel", "adminPanel",
        "fotoPanel", "historyPanel",
        "settingsPanel", "emailEditor", "shortcutCreator", "uploadArea",
        "erzieherSettingsPanel", "ausbilderSettingsPanel",
    ];

    function showWorkflow(wf) {
        if (!validWorkflows.includes(wf)) wf = "schueler";

        // Workflow-Sektionen toggeln
        document.querySelectorAll(".workflow-section").forEach(el => {
            el.style.display = (el.id === "workflow-" + wf) ? "" : "none";
        });

        // Tab-Aktivierung
        document.querySelectorAll("#workflowTabs .nav-link").forEach(a => {
            a.classList.toggle("active", a.dataset.workflow === wf);
        });

        // Beim Workflow-Wechsel ALLE bekannten Panels schließen (vermeidet,
        // dass ein vom vorherigen Workflow offen gelassenes Panel sichtbar bleibt).
        PANELS_TO_CLOSE.forEach(id => {
            const p = document.getElementById(id);
            if (p) p.style.display = "none";
        });

        // Persistieren
        try { localStorage.setItem(STORAGE_KEY, wf); } catch (_) {}
    }

    // Click-Handler für Tab-Pills
    document.querySelectorAll("#workflowTabs .nav-link").forEach(a => {
        a.addEventListener("click", (e) => {
            e.preventDefault();
            showWorkflow(a.dataset.workflow);
        });
    });

    // Initial-Zustand aus localStorage wiederherstellen
    let initial = "schueler";
    try { initial = localStorage.getItem(STORAGE_KEY) || "schueler"; } catch (_) {}
    showWorkflow(initial);
});
