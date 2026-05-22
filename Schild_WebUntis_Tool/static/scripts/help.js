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

        // Nach Kategorie gruppieren — Reihenfolge anhand des ersten Vorkommens
        // jeder Kategorie in der Server-Response (entspricht HELP_CATEGORIES-Reihenfolge).
        const groups = new Map();  // category → [{key, entry}]
        for (const key of Object.keys(data)) {
            const cat = data[key].category || 'Sonstiges';
            if (!groups.has(cat)) groups.set(cat, []);
            groups.get(cat).push({ key, entry: data[key] });
        }

        let html = "";
        for (const [cat, entries] of groups) {
            html += `
                <h6 class="text-muted mt-3 mb-2 help-category-heading"
                    style="text-transform:uppercase;font-size:0.78rem;letter-spacing:0.05em;border-bottom:1px solid #dee2e6;padding-bottom:4px">
                    ${cat}
                    <small class="text-muted ml-1" style="text-transform:none;letter-spacing:0">(${entries.length})</small>
                </h6>
            `;
            html += entries.map(({ key, entry }) => `
                <div class="card mb-2 help-entry" data-key="${key}" data-category="${cat}">
                    <div class="card-header py-2" style="cursor:pointer" data-toggle="collapse" data-target="#help-coll-${key}">
                        <strong>${entry.title || key}</strong>
                        <small class="text-muted ml-2">(${key})</small>
                    </div>
                    <div class="collapse" id="help-coll-${key}">
                        <div class="card-body">${entry.html || ""}</div>
                    </div>
                </div>
            `).join("");
        }
        container.innerHTML = html;
    }

    function filterGlossar(query) {
        const q = (query || "").trim().toLowerCase();
        const entries = document.querySelectorAll(".help-entry");
        let visible = 0;
        const visibleByCategory = {};
        entries.forEach(el => {
            const matches = !q || el.textContent.toLowerCase().includes(q);
            el.style.display = matches ? "" : "none";
            if (matches) {
                visible++;
                const cat = el.dataset.category || 'Sonstiges';
                visibleByCategory[cat] = (visibleByCategory[cat] || 0) + 1;
            }
        });
        // Kategorie-Überschriften ein-/ausblenden je nachdem ob in der Kategorie sichtbares
        document.querySelectorAll(".help-category-heading").forEach(h => {
            const catText = (h.textContent || '').trim();
            // Die Kategorie steht als erstes Wort/Stück, vergleichen wir ohne den (n)-Counter
            const cat = catText.replace(/\s*\(\d+\)\s*$/, '').trim();
            // Da wir matchen wollen mit dem Datenattribut: nimm das visibleByCategory mit gleichem Anfang
            const visKey = Object.keys(visibleByCategory).find(k => k.trim() === cat || cat.startsWith(k.trim()) || k.trim().startsWith(cat));
            const visCount = visKey ? visibleByCategory[visKey] : 0;
            h.style.display = (visCount > 0 || !q) ? "" : "none";
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
