// Inline-Hilfe-System: Einzel-Buttons (data-help="...") + Glossar-Modus.

document.addEventListener("DOMContentLoaded", function () {

    // ---- Einzelner Hilfe-Eintrag (Klick auf .help-btn) ----
    async function openHelp(key) {
        try {
            const r = await fetch(`/api/help/${encodeURIComponent(key)}`);
            if (!r.ok) {
                alert("Hilfe-Eintrag nicht verfügbar (" + key + ").");
                return;
            }
            const d = await r.json();
            document.getElementById("helpModalTitle").textContent = d.title || "Hilfe";
            document.getElementById("helpModalBody").innerHTML = d.html || "";
            $('#helpModal').modal('show');
        } catch (e) {
            alert("Fehler beim Laden der Hilfe: " + e);
        }
    }
    window.openHelp = openHelp;

    document.addEventListener("click", (e) => {
        const btn = e.target.closest(".help-btn");
        if (!btn) return;
        e.preventDefault();
        const key = btn.dataset.help;
        if (key) openHelp(key);
    });

    // ---- Glossar (alle Einträge) ----
    let glossarCache = null;

    async function loadGlossar() {
        if (glossarCache) return glossarCache;
        const r = await fetch("/api/help");
        if (!r.ok) throw new Error("Konnte Glossar nicht laden.");
        glossarCache = await r.json();
        return glossarCache;
    }

    function renderGlossar(data) {
        const container = document.getElementById("helpGlossarList");
        if (!container) return;
        const keys = Object.keys(data);
        container.innerHTML = keys.map(key => `
            <div class="card mb-2 help-entry" data-key="${key}">
                <div class="card-header py-2" style="cursor:pointer" data-toggle="collapse" data-target="#help-coll-${key}">
                    <strong>${data[key].title || key}</strong>
                    <small class="text-muted ml-2">(${key})</small>
                </div>
                <div class="collapse" id="help-coll-${key}">
                    <div class="card-body">${data[key].html || ""}</div>
                </div>
            </div>
        `).join("");
    }

    function filterGlossar(query) {
        const q = (query || "").trim().toLowerCase();
        const entries = document.querySelectorAll(".help-entry");
        let visible = 0;
        entries.forEach(el => {
            const matches = !q || el.textContent.toLowerCase().includes(q);
            el.style.display = matches ? "" : "none";
            if (matches) visible++;
        });
        const empty = document.getElementById("helpGlossarEmpty");
        if (empty) empty.style.display = (visible === 0 && q) ? "" : "none";
    }

    async function openGlossar() {
        try {
            const data = await loadGlossar();
            renderGlossar(data);
            const searchInp = document.getElementById("helpGlossarSearch");
            if (searchInp) { searchInp.value = ""; filterGlossar(""); }
            $('#helpGlossarModal').modal('show');
        } catch (e) {
            alert("Fehler beim Öffnen des Glossars: " + e);
        }
    }
    window.openHelpGlossar = openGlossar;

    // Suche im Glossar
    document.getElementById("helpGlossarSearch")?.addEventListener("input", (e) => {
        filterGlossar(e.target.value);
    });

    // Button im Einzel-Modal: zum Glossar wechseln
    document.getElementById("helpModalOpenGlossar")?.addEventListener("click", () => {
        $('#helpModal').modal('hide');
        setTimeout(openGlossar, 250);  // kurz warten bis erstes Modal weg
    });

    // Globaler Trigger via Button mit id="openHelpGlossar"
    document.getElementById("openHelpGlossar")?.addEventListener("click", openGlossar);
});
