// Erzieher-Workflow (Phase 2): Status laden, Verarbeitung anstoßen, ZIP herunterladen.

document.addEventListener("DOMContentLoaded", function () {

    const statusEl   = document.getElementById("erzieherStatus");
    const tplInput   = document.getElementById("erzieherZipNameTemplate");
    const procBtn    = document.getElementById("erzieherProcess");
    const dlBtn      = document.getElementById("erzieherDownload");
    const resultEl   = document.getElementById("erzieherResult");

    let zipReady = false;

    async function loadStatus() {
        if (!statusEl) return;
        statusEl.textContent = "Lade Status…";
        try {
            const r = await fetch("/api/erzieher/status");
            const d = await r.json();
            if (tplInput && !tplInput.value) tplInput.value = d.zip_name_template || "Erzieher_Import_{datum}";

            const haveE = !!d.latest_erzieher_export;
            const haveA = !!d.latest_ansprechpartner_export;
            const ready = haveE && haveA;
            const lines = [];
            lines.push(`<strong>Erzieher-Export-Verzeichnis:</strong> <code>${d.erzieher_export_directory || '–'}</code>`);
            lines.push(haveE
                ? `→ Aktuelle Datei: <code>${d.latest_erzieher_export}</code>`
                : `→ <span class="text-warning">Keine CSV gefunden.</span>`);
            lines.push(`<strong>Ansprechpartner-Export-Verzeichnis:</strong> <code>${d.ansprechpartner_export_directory || '–'}</code>`);
            lines.push(haveA
                ? `→ Aktuelle Datei: <code>${d.latest_ansprechpartner_export}</code>`
                : `→ <span class="text-warning">Keine CSV gefunden.</span>`);
            lines.push(`<strong>Ausgabeverzeichnis:</strong> <code>${d.output_directory || '–'}</code>`);
            statusEl.className = ready ? "alert alert-success py-2 mb-3" : "alert alert-warning py-2 mb-3";
            statusEl.innerHTML = lines.join("<br>")
                + (ready ? "" : "<br><br>Bitte zuerst die Schild-Exporte in die jeweiligen Verzeichnisse legen (Einstellungen → Quelldaten-Verzeichnisse).");
            if (procBtn) procBtn.disabled = !ready;

            // Falls zuvor schon ein ZIP erstellt wurde (z.B. nach Neuladen)
            if (d.last_zip) {
                zipReady = true;
                if (dlBtn) dlBtn.disabled = false;
            }
        } catch (e) {
            statusEl.className = "alert alert-danger py-2 mb-3";
            statusEl.textContent = "Fehler beim Laden des Status: " + e;
        }
    }

    procBtn?.addEventListener("click", async () => {
        const nameTemplate = tplInput?.value.trim() || null;
        procBtn.disabled = true; procBtn.textContent = "⌛ Verarbeite…";
        if (resultEl) resultEl.textContent = "";
        try {
            const r = await fetch("/api/erzieher/process", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name_template: nameTemplate }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) {
                if (resultEl) resultEl.innerHTML = `<span class="text-danger">❌ ${d.error || r.statusText}</span>`;
                return;
            }
            zipReady = true;
            if (dlBtn) dlBtn.disabled = false;
            const s = d.stats || {};
            if (resultEl) {
                resultEl.innerHTML = `✅ <code>${d.name}</code> erstellt in <code>${d.directory}</code>. `
                    + `${s.erzieher_rows || 0} Schüler, ${s.ansprechpartner_rows || 0} Ansprechpartner-Einträge → `
                    + `${s.max_erzieher || 0} Erzieher-Datei(en) (${(s.output_files || []).join(", ")}).`;
            }
            if (typeof showToast === "function") showToast(`Erzieher-Import erstellt: ${s.max_erzieher || 0} Datei(en).`);
        } catch (e) {
            if (resultEl) resultEl.innerHTML = `<span class="text-danger">❌ Fehler: ${e}</span>`;
        } finally {
            procBtn.disabled = false; procBtn.textContent = "▶️ Verarbeiten & ZIP erzeugen";
        }
    });

    dlBtn?.addEventListener("click", async () => {
        if (!zipReady) { alert("Bitte zuerst verarbeiten."); return; }
        try {
            const r = await fetch("/api/erzieher/download");
            if (!r.ok) {
                const err = await r.json().catch(() => ({}));
                alert("Fehler: " + (err.error || r.statusText));
                return;
            }
            const blob = await r.blob();
            let fname = "Erzieher_Import.zip";
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

    // -------------------------------------------------------------------
    // Vorschau Schueler <-> Erzieher
    // -------------------------------------------------------------------
    const previewBtn   = document.getElementById("erzieherTogglePreview");
    const previewArea  = document.getElementById("erzieherPreviewArea");
    const previewStats = document.getElementById("erzieherPreviewStats");
    const previewList  = document.getElementById("erzieherPreviewList");
    const previewSearch= document.getElementById("erzieherPreviewSearch");
    const mappingErzEl = document.getElementById("erzieherMappingFromErz");
    const mappingAnpEl = document.getElementById("erzieherMappingFromAnsp");

    let previewData = null;
    let previewView = 'students';  // 'students' oder 'erzieher'

    function escHtml(s) {
        return String(s ?? '').replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
    }

    function renderFieldMapping(fm) {
        if (!fm) return;
        const renderRow = m =>
            `<div class="d-flex small mb-1">
                <code class="mr-2" style="min-width:200px;">${escHtml(m.src)}</code>
                <span class="text-muted mr-2">→</span>
                <code>${escHtml(m.target)}</code>
            </div>`;
        if (mappingErzEl) mappingErzEl.innerHTML = (fm.from_erzieher_csv || []).map(renderRow).join('');
        if (mappingAnpEl) mappingAnpEl.innerHTML = (fm.from_ansprechpartner_csv || []).map(renderRow).join('');
    }

    function studentMatches(s, q) {
        if (!q) return true;
        q = q.toLowerCase();
        if ((s.nachname||'').toLowerCase().includes(q)) return true;
        if ((s.vorname||'').toLowerCase().includes(q))  return true;
        if ((s.klasse||'').toLowerCase().includes(q))   return true;
        if ((s.id||'').toLowerCase().includes(q))       return true;
        return (s.erzieher||[]).some(e =>
            (e.nachname||'').toLowerCase().includes(q) ||
            (e.vorname||'').toLowerCase().includes(q)  ||
            (e.email||'').toLowerCase().includes(q)    ||
            (e.telefon||'').toLowerCase().includes(q));
    }

    function groupMatches(g, q) {
        if (!q) return true;
        q = q.toLowerCase();
        const e = g.erzieher || {};
        if ((e.nachname||'').toLowerCase().includes(q)) return true;
        if ((e.vorname||'').toLowerCase().includes(q))  return true;
        if ((e.email||'').toLowerCase().includes(q))    return true;
        if ((e.telefon||'').toLowerCase().includes(q))  return true;
        return (g.students||[]).some(s =>
            (s.nachname||'').toLowerCase().includes(q) ||
            (s.vorname||'').toLowerCase().includes(q)  ||
            (s.klasse||'').toLowerCase().includes(q)   ||
            (s.id||'').toLowerCase().includes(q));
    }

    function renderErzieherCard(e) {
        const name = `${escHtml(e.vorname)} ${escHtml(e.nachname)}`.trim() || '<em>(ohne Name)</em>';
        const bits = [];
        if (e.anrede || e.titel) bits.push(`<span class="text-muted small">${escHtml([e.anrede, e.titel].filter(Boolean).join(' '))}</span>`);
        if (e.email)    bits.push(`📧 <a href="mailto:${escHtml(e.email)}" class="small">${escHtml(e.email)}</a>`);
        if (e.telefon)  bits.push(`📞 <span class="small">${escHtml(e.telefon)}</span>`);
        if (e.anschluss)bits.push(`<span class="badge badge-light border">${escHtml(e.anschluss)}</span>`);
        if (e.bemerkung)bits.push(`<span class="text-muted small">${escHtml(e.bemerkung)}</span>`);
        return `<div class="ml-3 mb-1 pl-2 border-left border-info">
                    <strong>Erzieher ${e.nr}:</strong> ${name}
                    <div class="ml-3">${bits.join(' · ')}</div>
                </div>`;
    }

    function renderListByStudents(q) {
        const list = (previewData.students || []).filter(s => studentMatches(s, q));
        if (!list.length) return '<p class="text-muted small m-0">Keine Treffer.</p>';
        return list.map(s => {
            const hdr = `<div><strong>${escHtml(s.nachname)}, ${escHtml(s.vorname)}</strong>
                        <span class="text-muted small">· Klasse ${escHtml(s.klasse) || '—'} · ID <code>${escHtml(s.id)}</code></span></div>`;
            const erz = (s.erzieher || []);
            const body = erz.length
                ? erz.map(renderErzieherCard).join('')
                : `<div class="ml-3 small text-warning">⚠️ Keine Erzieher in den Quelldaten.</div>`;
            return `<div class="mb-2 pb-2 border-bottom">${hdr}${body}</div>`;
        }).join('');
    }

    function renderListByErzieher(q) {
        const list = (previewData.erzieher_groups || []).filter(g => groupMatches(g, q));
        if (!list.length) return '<p class="text-muted small m-0">Keine Treffer.</p>';
        return list.map(g => {
            const e = g.erzieher;
            const name = `${escHtml(e.vorname)} ${escHtml(e.nachname)}`.trim() || '<em>(ohne Name)</em>';
            const meta = [];
            if (e.email)   meta.push(`📧 <a href="mailto:${escHtml(e.email)}">${escHtml(e.email)}</a>`);
            if (e.telefon) meta.push(`📞 ${escHtml(e.telefon)}`);
            const cnt = g.students.length;
            const studentsHtml = g.students.map(s =>
                `<li><strong>${escHtml(s.nachname)}, ${escHtml(s.vorname)}</strong>
                  <span class="text-muted small">· Klasse ${escHtml(s.klasse) || '—'} · ID <code>${escHtml(s.id)}</code> · Erzieher Nr. ${s.nr}</span></li>`
            ).join('');
            return `<div class="mb-2 pb-2 border-bottom">
                <div><strong>${name}</strong>
                  <span class="badge badge-info ml-1">${cnt} Schüler</span>
                  <div class="ml-3 small">${meta.join(' · ')}</div>
                </div>
                <ul class="mb-0 mt-1">${studentsHtml}</ul>
            </div>`;
        }).join('');
    }

    function renderPreviewList() {
        if (!previewList || !previewData) return;
        const q = (previewSearch?.value || '').trim();
        previewList.innerHTML = previewView === 'students'
            ? renderListByStudents(q)
            : renderListByErzieher(q);
    }

    function renderPreviewStats() {
        if (!previewStats || !previewData) return;
        const s = previewData.stats || {};
        const src = previewData.sources || {};
        const noErz = s.students_without_erzieher
            ? ` · <span class="text-warning">${s.students_without_erzieher} ohne Erzieher</span>`
            : '';
        previewStats.innerHTML =
            `<strong>${s.students_count}</strong> Schüler · <strong>${s.unique_erzieher}</strong> verschiedene Erzieher `
            + `(${s.erzieher_total} Zuordnungen, max. ${s.max_erzieher} pro Schüler)${noErz}<br>`
            + `<span class="small text-muted">Quellen: <code>${escHtml(src.erzieher_export_file || '')}</code> + `
            + `<code>${escHtml(src.ansprechpartner_export_file || '')}</code> · ${s.ansprechpartner_rows} Ansprechpartner-Zeilen</span>`;
    }

    async function loadPreview() {
        if (!previewArea) return;
        previewArea.style.display = '';
        if (previewStats) previewStats.textContent = "Lade Vorschau…";
        if (previewList)  previewList.innerHTML = '';
        try {
            const r = await fetch('/api/erzieher/preview');
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || r.statusText);
            previewData = d;
            renderPreviewStats();
            renderFieldMapping(d.field_mapping);
            renderPreviewList();
        } catch (e) {
            if (previewStats) {
                previewStats.className = "alert alert-danger py-2 mb-2";
                previewStats.textContent = "Fehler beim Laden der Vorschau: " + e;
            }
        }
    }

    previewBtn?.addEventListener('click', () => {
        const willShow = previewArea && (previewArea.style.display === 'none' || !previewArea.style.display);
        if (willShow) loadPreview();
        else if (previewArea) previewArea.style.display = 'none';
    });

    previewSearch?.addEventListener('input', renderPreviewList);

    document.querySelectorAll('#erzieherPreviewArea [data-erz-view]').forEach(btn => {
        btn.addEventListener('click', () => {
            previewView = btn.dataset.erzView;
            document.querySelectorAll('#erzieherPreviewArea [data-erz-view]').forEach(b => {
                const active = b.dataset.erzView === previewView;
                b.classList.toggle('btn-primary',  active);
                b.classList.toggle('btn-outline-primary', !active);
                b.classList.toggle('active', active);
            });
            renderPreviewList();
        });
    });

    // Status laden, sobald der Erzieher-Workflow sichtbar wird.
    // workflow_switcher.js dispatcht 'workflow:shown' sowohl beim Tab-Klick
    // als auch beim initialen Restore aus localStorage (F5).
    document.addEventListener('workflow:shown', (e) => {
        if (e.detail?.workflow === 'erzieher') loadStatus();
    });

    // Toggle: eigenes Erzieher-Settings-Panel
    document.getElementById("toggle-settings-erzieher")?.addEventListener("click", () => {
        const panel = document.getElementById("erzieherSettingsPanel");
        if (!panel) return;
        const willShow = panel.style.display === "none" || !panel.style.display;
        panel.style.display = willShow ? "block" : "none";
        if (willShow) {
            setTimeout(() => panel.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
        }
    });

    // Save: nur die Erzieher-spezifischen Felder speichern
    document.getElementById("saveErzieherSettings")?.addEventListener("click", async () => {
        const form = document.getElementById("form-erzieher-settings");
        if (!form) return;
        const btn = document.getElementById("saveErzieherSettings");
        btn.disabled = true; const orig = btn.textContent; btn.textContent = "⌛ Speichere…";
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
                if (typeof showToast === "function") showToast("Erzieher-Einstellungen gespeichert.");
                // Status neu laden — zeigt ob nun in den neuen Verzeichnissen Dateien gefunden werden
                setTimeout(loadStatus, 100);
            } else {
                alert("Fehler beim Speichern: " + (d.error || r.statusText));
            }
        } catch (e) {
            alert("Fehler beim Speichern: " + e);
        } finally {
            btn.disabled = false; btn.textContent = orig;
        }
    });
});
