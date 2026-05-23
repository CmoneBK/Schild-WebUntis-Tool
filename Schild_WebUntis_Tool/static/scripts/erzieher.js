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

    // Status laden, sobald der Erzieher-Workflow sichtbar wird
    // (initial-Load: nur wenn dieser Workflow aktiv ist; sonst beim Tab-Wechsel)
    const erzieherSection = document.getElementById("workflow-erzieher");
    if (erzieherSection) {
        // Klick auf den Erzieher-Tab triggert das Laden
        document.querySelectorAll('#workflowTabs .nav-link[data-workflow="erzieher"]').forEach(a => {
            a.addEventListener("click", () => setTimeout(loadStatus, 50));
        });
        // Initial: wenn Workflow beim Seiten-Start aktiv ist
        if (erzieherSection.style.display !== "none") loadStatus();
    }

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
