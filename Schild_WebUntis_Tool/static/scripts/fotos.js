// Foto-Verwaltung: Panel-Toggle, Übersicht laden, ZIP erstellen, verwaiste archivieren
document.addEventListener("DOMContentLoaded", function () {

    const panel = document.getElementById("fotoPanel");
    const toggleBtn = document.getElementById("toggleFotoPanel");

    function togglePanel() {
        if (!panel) return;
        const willShow = panel.style.display === "none" || !panel.style.display;
        // Andere große Panels schließen (best effort)
        ["dashboardPanel", "historyPanel", "infoMailPanel", "warningsPanel",
         "settingsPanel", "emailEditor", "shortcutCreator", "uploadArea", "adminPanel"]
            .forEach(id => { const el = document.getElementById(id); if (el) el.style.display = "none"; });
        panel.style.display = willShow ? "block" : "none";
        if (willShow) {
            loadFotos();
            // Automatisches Scrollen zum Bereich — wie bei den anderen Panels
            setTimeout(() => {
                panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
    }
    toggleBtn?.addEventListener("click", togglePanel);
    document.getElementById("fotoReload")?.addEventListener("click", loadFotos);

    function fmtBytes(n) {
        if (n < 1024) return n + " B";
        if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
        return (n / 1024 / 1024).toFixed(1) + " MB";
    }

    // Status-Checkboxen nur beim ersten Laden mit den vorkommenden Stati vorbelegen
    let statusCheckboxesInitialized = false;

    async function loadFotos() {
        const statusEl = document.getElementById("fotoStatus");
        const tbody = document.getElementById("fotoTableBody");
        if (statusEl) statusEl.textContent = "Lade Foto-Übersicht…";
        try {
            const r = await fetch("/api/fotos/list");
            const d = await r.json();
            // ZIP-Namen-Template vorbelegen
            const tplInput = document.getElementById("fotoZipNameTemplate");
            if (tplInput && !tplInput.value) tplInput.value = d.zip_name_template || "Fotos_{datum}";
            // Rename-Vorlage + Unterordner vorbelegen
            const renTpl = document.getElementById("fotoRenameTemplate");
            if (renTpl && !renTpl.value) renTpl.value = d.rename_template || "{nachname}_{vorname}_{id}";
            const renSub = document.getElementById("fotoRenameSubdir");
            if (renSub && !renSub.value) renSub.value = d.rename_subdir || "Umbenannt";

            // Status-Checkboxen: beim ersten Laden genau die Stati ankreuzen,
            // die im aktuellen Import vorkommen (danach bleibt die Auswahl erhalten)
            if (!statusCheckboxesInitialized) {
                const present = new Set((d.present_statuses || []).map(String));
                document.querySelectorAll(".foto-status-cb").forEach(cb => {
                    cb.checked = present.has(cb.value);
                });
                statusCheckboxesInitialized = true;
            }

            const fotos = d.fotos || [];
            const archived = fotos.filter(f => f.archived).length;
            const orphans = fotos.filter(f => !f.archived && !f.in_import).length;
            const matched = fotos.filter(f => !f.archived && f.in_import).length;
            if (statusEl) {
                if (!d.foto_directory) {
                    statusEl.className = "alert alert-warning py-2 mb-3";
                    statusEl.innerHTML = "⚠️ Kein Foto-Verzeichnis konfiguriert. Bitte unter <strong>⚙️ Einstellungen → Verzeichnisse → Foto-Verzeichnis</strong> eintragen.";
                } else {
                    statusEl.className = "alert alert-secondary py-2 mb-3";
                    statusEl.innerHTML = `Verzeichnis: <code>${d.foto_directory}</code> — `
                        + `<strong>${matched}</strong> Fotos zu aktuellen Schülern, `
                        + `<strong>${orphans}</strong> verwaist (nicht im Import), `
                        + `<strong>${archived}</strong> archiviert. `
                        + `(${d.student_count} Schüler im aktuellen Import)`;
                }
            }
            // Tabelle
            tbody.innerHTML = fotos.map(f => {
                const imgSrc = f.archived
                    ? `/api/fotos/image/${encodeURIComponent(f.id)}?archived=1`
                    : `/api/fotos/image/${encodeURIComponent(f.id)}`;
                let importCell;
                if (f.archived) importCell = '<span class="badge badge-secondary">archiviert</span>';
                else if (f.in_import) importCell = '<span class="badge badge-success">ja</span>';
                else importCell = '<span class="badge badge-warning">verwaist</span>';
                const restoreBtn = f.archived
                    ? `<button class="btn btn-xs btn-outline-success py-0 foto-restore-btn" style="font-size:0.75rem" data-filename="${f.filename}">↩️ Zurückholen</button>`
                    : '';
                return `<tr${f.archived ? ' class="text-muted"' : ''}>
                    <td><img src="${imgSrc}" alt="" class="foto-thumb"
                             data-fullsrc="${imgSrc}" data-student="${(f.name || '').replace(/"/g,'&quot;')}"
                             style="max-height:42px;max-width:42px;border-radius:3px;cursor:zoom-in"
                             onerror="this.style.display='none'"
                             title="Klicken für Vorschau"></td>
                    <td>${f.filename}</td>
                    <td>${f.id}</td>
                    <td>${f.name || '<span class="text-muted">–</span>'}</td>
                    <td>${f.klasse || ''}</td>
                    <td>${f.status || ''}</td>
                    <td>${importCell}</td>
                    <td>${restoreBtn}</td>
                </tr>`;
            }).join("") || '<tr><td colspan="8" class="text-center text-muted">Keine Fotos gefunden.</td></tr>';
        } catch (e) {
            if (statusEl) {
                statusEl.className = "alert alert-danger py-2 mb-3";
                statusEl.textContent = "Fehler beim Laden: " + e;
            }
        }
    }

    // ZIP erstellen (server-seitig, im foto_zip_directory ablegen)
    let zipReady = false;
    document.getElementById("fotoCreateZip")?.addEventListener("click", async () => {
        const statuses = Array.from(document.querySelectorAll(".foto-status-cb:checked")).map(cb => cb.value);
        const nameTemplate = document.getElementById("fotoZipNameTemplate")?.value.trim() || null;
        const btn = document.getElementById("fotoCreateZip");
        const dlBtn = document.getElementById("fotoDownloadZip");
        const resultEl = document.getElementById("fotoZipResult");
        btn.disabled = true; btn.textContent = "⌛ Erstelle ZIP…";
        if (resultEl) resultEl.textContent = "";
        try {
            const r = await fetch("/api/fotos/zip/create", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ statuses: statuses.length ? statuses : null, name_template: nameTemplate }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) {
                if (resultEl) resultEl.innerHTML = `<span class="text-danger">❌ ${d.error || r.statusText}</span>`;
                return;
            }
            zipReady = true;
            if (dlBtn) { dlBtn.disabled = false; }
            if (resultEl) {
                resultEl.innerHTML = `✅ <code>${d.name}</code> erstellt in <code>${d.directory}</code> — `
                    + `${d.included} Fotos${d.missing ? `, ${d.missing} ohne Foto übersprungen` : ""}.`;
            }
            if (typeof showToast === "function") showToast(`ZIP erstellt: ${d.included} Fotos.`);
        } catch (e) {
            if (resultEl) resultEl.innerHTML = `<span class="text-danger">❌ Fehler: ${e}</span>`;
        } finally {
            btn.disabled = false; btn.textContent = "📦 ZIP erstellen";
        }
    });

    // ZIP herunterladen (das zuletzt erstellte)
    document.getElementById("fotoDownloadZip")?.addEventListener("click", async () => {
        if (!zipReady) { alert("Bitte zuerst ein ZIP erstellen."); return; }
        try {
            const r = await fetch("/api/fotos/zip/download");
            if (!r.ok) {
                const err = await r.json().catch(() => ({}));
                alert("Fehler: " + (err.error || r.statusText));
                return;
            }
            const blob = await r.blob();
            let fname = "Fotos.zip";
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

    // Umbenanntes Kopieren in Unterordner
    document.getElementById("fotoRenameCopy")?.addEventListener("click", async () => {
        const statuses = Array.from(document.querySelectorAll(".foto-status-cb:checked")).map(cb => cb.value);
        const template = document.getElementById("fotoRenameTemplate")?.value.trim() || null;
        const subdir = document.getElementById("fotoRenameSubdir")?.value.trim() || null;
        const btn = document.getElementById("fotoRenameCopy");
        const resultEl = document.getElementById("fotoRenameResult");
        btn.disabled = true; btn.textContent = "⌛ Kopiere…";
        if (resultEl) resultEl.textContent = "";
        try {
            const r = await fetch("/api/fotos/rename-copy", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    statuses: statuses.length ? statuses : null,
                    template, subdir,
                }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) {
                if (resultEl) resultEl.innerHTML = `<span class="text-danger">❌ ${d.error || r.statusText}</span>`;
                return;
            }
            if (resultEl) {
                resultEl.innerHTML = `✅ ${d.copied} Fotos kopiert nach <code>${d.target_dir}</code>`
                    + (d.missing ? `, ${d.missing} ohne Foto übersprungen` : "")
                    + ".";
            }
            if (typeof showToast === "function") showToast(`${d.copied} Foto(s) kopiert.`);
        } catch (e) {
            if (resultEl) resultEl.innerHTML = `<span class="text-danger">❌ Fehler: ${e}</span>`;
        } finally {
            btn.disabled = false; btn.textContent = "📂 Kopieren mit Umbenennung";
        }
    });

    // Verwaiste archivieren
    document.getElementById("fotoArchiveOrphans")?.addEventListener("click", async () => {
        if (!confirm("Alle Fotos von Schülern, die nicht mehr im aktuellen Import sind, in den Archiv-Ordner verschieben?")) return;
        const btn = document.getElementById("fotoArchiveOrphans");
        btn.disabled = true; btn.textContent = "⌛ Archiviere…";
        try {
            const r = await fetch("/api/fotos/archive", { method: "POST" });
            const d = await r.json();
            if (!r.ok) { alert("Fehler: " + (d.error || r.statusText)); return; }
            if (typeof showToast === "function") showToast(`${d.count} Foto(s) archiviert.`);
            loadFotos();
        } catch (e) {
            alert("Fehler beim Archivieren: " + e);
        } finally {
            btn.disabled = false; btn.textContent = "🗄️ Verwaiste jetzt archivieren";
        }
    });

    // Foto-Vorschau (Thumbnail anklicken → Modal)
    document.getElementById("fotoTableBody")?.addEventListener("click", (e) => {
        const thumb = e.target.closest(".foto-thumb");
        if (!thumb) return;
        const img = document.getElementById("fotoPreviewImg");
        const label = document.getElementById("fotoPreviewModalLabel");
        if (img) img.src = thumb.dataset.fullsrc;
        if (label) label.textContent = "🖼️ Foto-Vorschau" + (thumb.dataset.student ? ` — ${thumb.dataset.student}` : "");
        $('#fotoPreviewModal').modal('show');
    });

    // Archivierte zurückholen (Event-Delegation)
    document.getElementById("fotoTableBody")?.addEventListener("click", async (e) => {
        const btn = e.target.closest(".foto-restore-btn");
        if (!btn) return;
        const filename = btn.dataset.filename;
        try {
            const r = await fetch("/api/fotos/restore", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ filename }),
            });
            const d = await r.json();
            if (d.ok) { if (typeof showToast === "function") showToast("Foto zurückgeholt."); loadFotos(); }
            else alert("Konnte Foto nicht zurückholen (existiert evtl. schon im Hauptverzeichnis).");
        } catch (e) {
            alert("Fehler: " + e);
        }
    });
});
