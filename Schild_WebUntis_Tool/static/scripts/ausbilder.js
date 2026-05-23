// Ausbilder-Workflow (Phase 3): Status laden, Klassen-Whitelist + Schueler-Blacklist
// pflegen, Verarbeitung anstossen, CSV herunterladen.

document.addEventListener("DOMContentLoaded", function () {

    const statusEl       = document.getElementById("ausbilderStatus");
    const chipsEl        = document.getElementById("ausbilderClassChips");
    const bodyEl         = document.getElementById("ausbilderStudentsBody");
    const searchInput    = document.getElementById("ausbilderStudentSearch");
    const countEl        = document.getElementById("ausbilderStudentCount");
    const tplInput       = document.getElementById("ausbilderOutputNameTemplate");
    const procBtn        = document.getElementById("ausbilderProcess");
    const dlBtn          = document.getElementById("ausbilderDownload");
    const resultEl       = document.getElementById("ausbilderResult");

    let csvReady = false;
    let state = {
        students: [],
        classes: [],
        classFilter: [],
        blacklist: new Set(),
        haveCsv: false,
    };

    function escapeHtml(s) {
        return String(s ?? '').replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
    }

    function renderStatus(d) {
        const lines = [];
        lines.push(`<strong>Eingabe-Verzeichnis:</strong> <code>${escapeHtml(d.input_directory || '–')}</code>`);
        lines.push(d.latest_csv
            ? `→ Aktuelle Datei: <code>${escapeHtml(d.latest_csv)}</code>`
            : `→ <span class="text-warning">Keine CSV gefunden.</span>`);
        lines.push(`<strong>Ausgabeverzeichnis:</strong> <code>${escapeHtml(d.output_directory || '–')}</code>`);
        const ready = !!d.latest_csv;
        statusEl.className = ready ? "alert alert-success py-2 mb-3" : "alert alert-warning py-2 mb-3";
        statusEl.innerHTML = lines.join("<br>")
            + (ready ? "" : "<br><br>Bitte zuerst die Schild-CSV ins Eingabe-Verzeichnis legen (Einstellungen → Quelldaten-Verzeichnis).");
        if (procBtn) procBtn.disabled = !ready;
    }

    function renderClassChips() {
        if (!chipsEl) return;
        if (!state.classes.length) {
            chipsEl.innerHTML = '<span class="text-muted small">Keine Klassen in der CSV gefunden.</span>';
            return;
        }
        const filterSet = new Set(state.classFilter);
        const allActive = filterSet.size === 0;
        const chips = state.classes.map(k => {
            const active = allActive || filterSet.has(k);
            const cls = active ? 'btn-success' : 'btn-outline-secondary';
            return `<button type="button" class="btn btn-sm ${cls} mr-1 mb-1 ausbilder-class-chip" data-class="${escapeHtml(k)}">${escapeHtml(k)}</button>`;
        }).join('');
        const allBtn = `<button type="button" class="btn btn-sm ${allActive ? 'btn-info' : 'btn-outline-info'} mr-2 mb-1" id="ausbilderClassAll">Alle</button>`;
        chipsEl.innerHTML = allBtn + chips;

        chipsEl.querySelectorAll('.ausbilder-class-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                const k = btn.dataset.class;
                let cur = new Set(state.classFilter);
                if (cur.size === 0) {
                    // war "alle" — nun nur dieser
                    cur = new Set(state.classes);
                }
                if (cur.has(k)) cur.delete(k); else cur.add(k);
                // Wenn alle ausgewaehlt -> leeren (== alle)
                if (cur.size === state.classes.length) cur = new Set();
                state.classFilter = Array.from(cur);
                saveClassFilter();
                renderClassChips();
            });
        });
        const allBtnEl = document.getElementById('ausbilderClassAll');
        if (allBtnEl) allBtnEl.addEventListener('click', () => {
            state.classFilter = [];
            saveClassFilter();
            renderClassChips();
        });
    }

    function passesSearch(s, q) {
        if (!q) return true;
        q = q.toLowerCase();
        return (s.nachname || '').toLowerCase().includes(q)
            || (s.vorname  || '').toLowerCase().includes(q)
            || (s.klasse   || '').toLowerCase().includes(q)
            || (s.id       || '').toLowerCase().includes(q);
    }

    function renderStudents() {
        if (!bodyEl) return;
        if (!state.students.length) {
            bodyEl.innerHTML = '<tr><td colspan="5" class="text-center text-muted py-3">Keine Schüler in der CSV.</td></tr>';
            if (countEl) countEl.textContent = '—';
            return;
        }
        const q = (searchInput?.value || '').trim();
        const list = state.students.filter(s => passesSearch(s, q));
        const blacklistedTotal = state.students.filter(s => state.blacklist.has(s.id)).length;
        if (countEl) {
            countEl.textContent = `${list.length} sichtbar · ${state.students.length} insgesamt · ${blacklistedTotal} auf Blacklist`;
        }
        const rows = list.map(s => {
            const checked = !state.blacklist.has(s.id);
            return `<tr>
                <td class="text-center"><input type="checkbox" class="ausbilder-blk" data-id="${escapeHtml(s.id)}" ${checked ? 'checked' : ''}></td>
                <td>${escapeHtml(s.klasse)}</td>
                <td>${escapeHtml(s.nachname)}</td>
                <td>${escapeHtml(s.vorname)}</td>
                <td><code>${escapeHtml(s.id)}</code></td>
            </tr>`;
        });
        bodyEl.innerHTML = rows.join('') || '<tr><td colspan="5" class="text-center text-muted py-3">Keine Treffer.</td></tr>';

        bodyEl.querySelectorAll('.ausbilder-blk').forEach(cb => {
            cb.addEventListener('change', async () => {
                const sid = cb.dataset.id;
                const add = !cb.checked; // unchecked = auf Blacklist
                try {
                    const r = await fetch('/api/ausbilder/blacklist/toggle', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: sid, add }),
                    });
                    const d = await r.json();
                    if (!r.ok || !d.success) throw new Error(d.error || r.statusText);
                    state.blacklist = new Set(d.blacklist || []);
                    // Counter aktualisieren, Liste nicht komplett neu rendern (Scroll-Position halten)
                    const bl = state.students.filter(x => state.blacklist.has(x.id)).length;
                    if (countEl) {
                        const visible = bodyEl.querySelectorAll('tr').length;
                        countEl.textContent = `${visible} sichtbar · ${state.students.length} insgesamt · ${bl} auf Blacklist`;
                    }
                } catch (e) {
                    alert('Fehler beim Speichern der Blacklist: ' + e);
                    cb.checked = !cb.checked; // revert
                }
            });
        });
    }

    async function saveClassFilter() {
        try {
            await fetch('/api/ausbilder/save_filter', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ classes: state.classFilter }),
            });
        } catch (e) {
            console.warn('Klassen-Filter konnte nicht gespeichert werden:', e);
        }
    }

    async function loadStudents() {
        if (!statusEl) return;
        statusEl.textContent = "Lade Status…";
        try {
            const r = await fetch('/api/ausbilder/students');
            const d = await r.json();

            if (tplInput && !tplInput.value) tplInput.value = d.output_name_template || 'WebUntis_Ausbilder_Import_{datetime}';

            state.students = d.students || [];
            state.classes = d.classes || [];
            state.classFilter = d.class_filter || [];
            state.blacklist = new Set(d.blacklist || []);
            state.haveCsv = !!d.csv_path;

            renderStatus(d);
            renderClassChips();
            renderStudents();

            if (d.last_csv) {
                csvReady = true;
                if (dlBtn) dlBtn.disabled = false;
            }
        } catch (e) {
            statusEl.className = "alert alert-danger py-2 mb-3";
            statusEl.textContent = "Fehler beim Laden des Status: " + e;
        }
    }

    searchInput?.addEventListener('input', renderStudents);

    procBtn?.addEventListener('click', async () => {
        const nameTemplate = tplInput?.value.trim() || null;
        procBtn.disabled = true;
        const origText = procBtn.textContent;
        procBtn.textContent = "⌛ Verarbeite…";
        if (resultEl) resultEl.textContent = "";
        try {
            const r = await fetch('/api/ausbilder/process', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name_template: nameTemplate }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) {
                if (resultEl) resultEl.innerHTML = `<span class="text-danger">❌ ${escapeHtml(d.error || r.statusText)}</span>`;
                return;
            }
            csvReady = true;
            if (dlBtn) dlBtn.disabled = false;
            if (resultEl) {
                resultEl.innerHTML = `✅ <code>${escapeHtml(d.name)}</code> erstellt in <code>${escapeHtml(d.directory)}</code>. `
                    + `${d.rows_out} von ${d.rows_in} Schülern exportiert `
                    + `(${d.rows_in - d.rows_out} ausgeschlossen).`;
            }
            if (typeof showToast === "function") showToast(`Ausbilder-Import erstellt: ${d.rows_out} Schüler.`);
        } catch (e) {
            if (resultEl) resultEl.innerHTML = `<span class="text-danger">❌ Fehler: ${escapeHtml(String(e))}</span>`;
        } finally {
            procBtn.disabled = false;
            procBtn.textContent = origText;
        }
    });

    dlBtn?.addEventListener('click', async () => {
        if (!csvReady) { alert("Bitte zuerst verarbeiten."); return; }
        try {
            const r = await fetch('/api/ausbilder/download');
            if (!r.ok) {
                const err = await r.json().catch(() => ({}));
                alert("Fehler: " + (err.error || r.statusText));
                return;
            }
            const blob = await r.blob();
            let fname = "WebUntis_Ausbilder_Import.csv";
            const cd = r.headers.get("Content-Disposition") || "";
            const m = cd.match(/filename\*?=(?:UTF-8'')?"?([^";]+)"?/i);
            if (m) fname = decodeURIComponent(m[1]);
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url; a.download = fname; document.body.appendChild(a); a.click();
            a.remove(); URL.revokeObjectURL(url);
        } catch (e) {
            alert("Fehler beim Herunterladen: " + e);
        }
    });

    // Initialisierung: bei Workflow-Wechsel + initialem Laden
    const ausbilderSection = document.getElementById("workflow-ausbilder");
    if (ausbilderSection) {
        document.querySelectorAll('#workflowTabs .nav-link[data-workflow="ausbilder"]').forEach(a => {
            a.addEventListener("click", () => setTimeout(loadStudents, 50));
        });
        if (ausbilderSection.style.display !== "none") loadStudents();
    }

    // Toggle: eigenes Ausbilder-Settings-Panel
    document.getElementById("toggle-settings-ausbilder")?.addEventListener("click", () => {
        const panel = document.getElementById("ausbilderSettingsPanel");
        if (!panel) return;
        const willShow = panel.style.display === "none" || !panel.style.display;
        panel.style.display = willShow ? "block" : "none";
        if (willShow) {
            setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
        }
    });

    // Save: nur die Ausbilder-spezifischen Felder speichern
    document.getElementById("saveAusbilderSettings")?.addEventListener("click", async () => {
        const form = document.getElementById("form-ausbilder-settings");
        if (!form) return;
        const btn = document.getElementById("saveAusbilderSettings");
        btn.disabled = true;
        const orig = btn.textContent;
        btn.textContent = "⌛ Speichere…";
        try {
            const directories = {};
            new FormData(form).forEach((value, key) => { directories[key] = value; });
            const r = await fetch("/save-settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ settings: { Directories: directories } }),
            });
            const d = await r.json().catch(() => ({}));
            if (r.ok && d.status === "success") {
                if (typeof showToast === "function") showToast("Ausbilder-Einstellungen gespeichert.");
                // Neu laden – zeigt ob nun im neuen Eingabeverzeichnis Dateien gefunden werden
                setTimeout(loadStudents, 100);
            } else {
                alert("Fehler beim Speichern: " + (d.error || r.statusText));
            }
        } catch (e) {
            alert("Fehler beim Speichern: " + e);
        } finally {
            btn.disabled = false;
            btn.textContent = orig;
        }
    });
});
