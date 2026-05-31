// Erzieher-Workflow (Phase 2): Status laden, Verarbeitung anstoßen, ZIP herunterladen.

document.addEventListener("DOMContentLoaded", function () {

    const statusEl   = document.getElementById("erzieherStatus");
    const tplInput   = document.getElementById("erzieherZipNameTemplate");
    const procBtn    = document.getElementById("erzieherProcess");
    const dlBtn      = document.getElementById("erzieherDownload");
    const resultEl   = document.getElementById("erzieherResult");
    const classChipsEl = document.getElementById("erzieherClassChips");

    let zipReady = false;

    // ---- Klassen-Whitelist State (analog Ausbilder-Workflow) -----------
    const NONE_SENTINEL = '__NONE__';
    const classState = {
        classes: [],         // alle verfuegbaren Klassen aus der Quelle
        classFilter: [],     // aktiver Filter (leer = alle, ['__NONE__'] = keine)
    };

    function escHtmlBasic(s) {
        return String(s ?? '').replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
    }

    function isNoneClassMode() {
        return classState.classFilter.length === 1 && classState.classFilter[0] === NONE_SENTINEL;
    }
    function isAllClassMode() {
        return !isNoneClassMode() && classState.classFilter.length === 0;
    }
    function collapseClassFilter(cur) {
        // cur: Set<string>
        if (cur.size === classState.classes.length) return [];               // alle -> Default
        if (cur.size === 0)                          return [NONE_SENTINEL]; // keine -> explizit nichts
        return Array.from(cur);
    }

    function renderClassChips() {
        if (!classChipsEl) return;
        if (!classState.classes.length) {
            classChipsEl.innerHTML = '<span class="text-muted small">Keine Klassen in der Quelle gefunden. (Schüler-Stammdaten fehlen im Erzieher- und Anspr-Export?)</span>';
            return;
        }
        const allMode  = isAllClassMode();
        const noneMode = isNoneClassMode();
        const filterSet = new Set(classState.classFilter);
        const chips = classState.classes.map(k => {
            let active;
            if (allMode)       active = true;
            else if (noneMode) active = false;
            else               active = filterSet.has(k);
            const cls = active ? 'btn-success' : 'btn-outline-secondary';
            return `<button type="button" class="btn btn-sm ${cls} mr-1 mb-1 erz-class-chip" data-class="${escHtmlBasic(k)}">${escHtmlBasic(k)}</button>`;
        }).join('');
        const allLabel = allMode ? 'Alle abwählen' : 'Alle wählen';
        const allCls   = allMode ? 'btn-info'     : 'btn-outline-info';
        const allBtn   = `<button type="button" class="btn btn-sm ${allCls} mr-2 mb-1" id="erzClassAll" title="Schaltet zwischen 'alle Klassen aktiv' und 'keine Klasse aktiv' um.">${allLabel}</button>`;
        const warning  = noneMode
            ? '<div class="text-danger small mt-2">⚠️ Keine Klasse aktiv — es würde nichts exportiert (Vorschau und Klassen-Report sind leer).</div>'
            : '';
        classChipsEl.innerHTML = allBtn + chips + warning;

        classChipsEl.querySelectorAll('.erz-class-chip').forEach(btn => {
            btn.addEventListener('click', () => toggleClassChip(btn.dataset.class));
        });
        document.getElementById('erzClassAll')?.addEventListener('click', () => {
            classState.classFilter = isAllClassMode() ? [NONE_SENTINEL] : [];
            saveClassFilter();
            renderClassChips();
            invalidateCachedErzieherViews();
        });
    }

    function toggleClassChip(k) {
        const allMode  = isAllClassMode();
        const noneMode = isNoneClassMode();
        let cur;
        if (allMode) {
            cur = new Set(classState.classes); cur.delete(k);
        } else if (noneMode) {
            cur = new Set([k]);
        } else {
            cur = new Set(classState.classFilter);
            if (cur.has(k)) cur.delete(k); else cur.add(k);
        }
        classState.classFilter = collapseClassFilter(cur);
        saveClassFilter();
        renderClassChips();
        invalidateCachedErzieherViews();
    }

    async function saveClassFilter() {
        try {
            const r = await fetch('/api/erzieher/save_class_filter', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ classes: classState.classFilter }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) throw new Error(d.error || r.statusText);
        } catch (e) {
            alert('Fehler beim Speichern der Klassen-Whitelist: ' + e);
        }
    }

    function invalidateCachedErzieherViews() {
        // Caches der Preview/Missing-Bereiche verwerfen (sie verwenden den
        // Klassen-Filter im Backend) und ggf. neu laden, wenn gerade sichtbar.
        previewData = null;
        missingData = null;
        if (previewArea && previewArea.style.display !== 'none') loadPreview();
        if (missingArea && missingArea.style.display !== 'none') loadMissing();
    }

    // -------------------------------------------------------------------
    // Schueler-Export-Modus (Single-File-Konsolidierung)
    // 3 Modi: off | fallback | always — siehe Module-Docstring im Processor.
    // -------------------------------------------------------------------
    const sourceToggleEl = document.getElementById("erzieherSchuelerExportToggle");

    function renderSchuelerExportToggle(currentMode, schuelerAvailable, inspect) {
        if (!sourceToggleEl) return;
        inspect = inspect || {};
        const MODES = [
            { key: 'off',      label: 'Nur Erzieher-Export',         desc: 'Schüler-Export der Hauptverarbeitung wird ignoriert (Default).' },
            { key: 'fallback', label: 'Fallback: Schüler-Export',    desc: 'Nur wenn Erzieher-Export fehlt — sonst weiterhin Erzieher-Export.' },
            { key: 'always',   label: 'Immer Schüler-Export',        desc: 'Schüler-Export aus dem Schild-Exporte-Verzeichnis hat Vorrang.' },
        ];
        const radios = MODES.map(m => {
            const checked = m.key === currentMode ? 'checked' : '';
            // 'always' ohne tauglichen Schueler-Export waere kaputt — wir
            // erlauben es zu wählen (User sieht Warnung im Status), disablen
            // aber nichts (Lock-In waere uebergriffig).
            return `<div class="form-check form-check-inline mr-3">
                <input class="form-check-input erz-source-radio" type="radio"
                       name="erz_source_mode" id="erz_src_${m.key}"
                       value="${m.key}" ${checked}>
                <label class="form-check-label small" for="erz_src_${m.key}"
                       title="${escHtmlBasic(m.desc)}">
                    <strong>${escHtmlBasic(m.label)}</strong>
                </label>
            </div>`;
        }).join('');
        // Statusnachricht je nach 3-Fall-Detection (siehe loadStatus())
        let note;
        if (schuelerAvailable) {
            note = `<small class="text-muted">Schüler-Export ist <strong>tauglich</strong> — Umschalten wirkt sofort auf Vorschau, Klassen-Report und Export.</small>`;
        } else if (inspect.file_exists && inspect.is_schueler_export) {
            note = `<small class="text-warning">⚠️ Schüler-Export gefunden, aber für Single-File-Modus <strong>nicht tauglich</strong> — siehe Status-Box oben für die konkreten Spalten, die in der Schild-Export-Vorlage zusätzlich aktiviert werden müssen.</small>`;
        } else if (inspect.file_exists) {
            note = `<small class="text-muted">CSV im <strong>🟦📥 Schild-Exporte-Verzeichnis</strong> vorhanden, aber kein Schüler-Export (Pflicht-Stammdaten fehlen). Im Modus <code>always</code> würde die Verarbeitung scheitern.</small>`;
        } else {
            note = `<small class="text-muted">Keine CSV im <strong>🟦📥 Schild-Exporte-Verzeichnis</strong>. Im Modus <code>always</code> würde die Verarbeitung scheitern, solange dort keine Schild-Schüler-CSV liegt.</small>`;
        }
        sourceToggleEl.innerHTML = radios + `<div class="mt-1">${note}</div>`;
        sourceToggleEl.querySelectorAll('.erz-source-radio').forEach(r => {
            r.addEventListener('change', () => saveSchuelerExportMode(r.value));
        });
    }

    async function saveSchuelerExportMode(mode) {
        try {
            const r = await fetch('/api/erzieher/save_schueler_export_mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) throw new Error(d.error || r.statusText);
            // Quellwechsel ändert sowohl Klassen-Pool (anderer Datensatz)
            // als auch Status-Badges — Status neu laden, dann Caches kicken.
            invalidateCachedErzieherViews();
            loadStatus();
        } catch (e) {
            alert('Fehler beim Speichern des Quell-Modus: ' + e);
        }
    }

    async function loadStatus() {
        if (!statusEl) return;
        statusEl.textContent = "Lade Status…";
        try {
            const r = await fetch("/api/erzieher/status");
            const d = await r.json();
            if (tplInput && !tplInput.value) tplInput.value = d.zip_name_template || "Erzieher_Import_{datum}";
            // Settings-Checkboxes aus Backend uebernehmen
            const smartCb = document.getElementById('erzieher_smart_match');
            if (smartCb && typeof d.smart_match === 'boolean') smartCb.checked = d.smart_match;
            const volljCb = document.getElementById('erzieher_filter_volljaehrig');
            if (volljCb && typeof d.filter_volljaehrig === 'boolean') volljCb.checked = d.filter_volljaehrig;
            const emailCb = document.getElementById('erzieher_require_email');
            if (emailCb && typeof d.require_email === 'boolean') emailCb.checked = d.require_email;
            const dummyCb = document.getElementById('erzieher_fill_dummies');
            if (dummyCb && typeof d.fill_dummies === 'boolean') dummyCb.checked = d.fill_dummies;
            const liftCb  = document.getElementById('erzieher_lift_limit');
            if (liftCb  && typeof d.lift_limit === 'boolean') liftCb.checked = d.lift_limit;
            const phoneCb = document.getElementById('erzieher_phone_from_erz_first');
            if (phoneCb && typeof d.phone_from_erz_first === 'boolean') phoneCb.checked = d.phone_from_erz_first;
            const eltCb   = document.getElementById('erzieher_assign_eltern_ids');
            if (eltCb && typeof d.assign_eltern_ids === 'boolean') eltCb.checked = d.assign_eltern_ids;
            // Eltern-ID-DB-Status nachladen, wenn das Settings-Panel offen ist
            loadElternIdStats();

            // Klassen-Whitelist: Liste der verfuegbaren Klassen + aktiver Filter
            classState.classes     = Array.isArray(d.classes_available) ? d.classes_available : [];
            classState.classFilter = Array.isArray(d.class_filter)      ? d.class_filter      : [];
            renderClassChips();

            const haveE = !!d.latest_erzieher_export;
            const haveA = !!d.latest_ansprechpartner_export;
            // Single-File-Konsolidierung: das Backend hat ueber den Resolver
            // schon entschieden, welche Quelle wirksam ist. 'ready' richtet
            // sich nach dem Resolver-Ergebnis, nicht nur nach haveE — sonst
            // bleibt der Verarbeiten-Button im 'always'-Mode (mit Schueler-
            // Export aber ohne Erzieher-Export) faelschlicherweise disabled.
            const sourceInfo = d.schueler_export_source || {};
            const sourceMode = d.schueler_export_mode || 'off';
            const activeSource = sourceInfo.source; // 'erzieher_export' | 'schueler_export' | null
            const haveS = !!sourceInfo.schueler_available;
            const ready = !!activeSource;
            const lines = [];
            lines.push(`<strong>Erzieher-Export-Verzeichnis:</strong> <code>${d.erzieher_export_directory || '–'}</code>`);
            lines.push(haveE
                ? `→ Aktuelle Datei: <code>${d.latest_erzieher_export}</code>`
                : `→ <span class="text-warning">Keine CSV gefunden.</span>`);
            lines.push(`<strong>Ansprechpartner-Export-Verzeichnis</strong> <span class="text-muted">(optional)</span>: <code>${d.ansprechpartner_export_directory || '–'}</code>`);
            lines.push(haveA
                ? `→ Aktuelle Datei: <code>${d.latest_ansprechpartner_export}</code>`
                : `→ <span class="text-info">Keine CSV gefunden — Telefondaten/Schüler-Stammdaten kommen dann ausschließlich aus dem Erzieher-Export.</span>`);
            // Hinweis zur Erzieher-Vorlage: welche optionalen Spalten gefunden wurden
            const ins = d.erz_source_inspect || {};
            if (haveE) {
                const badges = [];
                if (ins.has_student_stamm) {
                    badges.push(`<span class="badge badge-success">👨‍🎓 Schüler-Stammdaten in Erzieher-Export</span>`);
                } else if (haveA) {
                    badges.push(`<span class="badge badge-secondary">👨‍🎓 Schüler-Stammdaten aus Anspr-Export gejoint</span>`);
                } else {
                    badges.push(`<span class="badge badge-warning">⚠️ Schüler-Stammdaten fehlen (weder Erzieher- noch Anspr-Export)</span>`);
                }
                if (ins.has_geburtsdatum) {
                    badges.push(`<span class="badge badge-success">🎂 Geburtsdatum vorhanden (deterministischer Volljährig-Check)</span>`);
                } else {
                    badges.push(`<span class="badge badge-secondary" title="Kein Geburtsdatum im Erzieher-Export → Volljährigkeit nur per Schild-Heuristik 'Erzieher: Art (Klartext)' erkannt">🎂 Kein Geburtsdatum (nur Schild-Heuristik)</span>`);
                }
                lines.push(`<div class="mt-1">${badges.join(' ')}</div>`);
            }
            lines.push(`<strong>Ausgabeverzeichnis:</strong> <code>${d.output_directory || '–'}</code>`);

            // Konsolidierungs-Block: 'Schild Exporte'-Hauptverzeichnis als
            // Schueler-Export-Quelle sichtbar machen. Anzeige-Logik:
            //  - mode != 'off' (User hat den Modus aktiv ausgewaehlt) -> immer
            //    zeigen, inkl. Warnung bei fehlenden Spalten
            //  - mode == 'off' + Datei voll tauglich -> positiver Discovery-
            //    Hinweis ('koennten Sie auch nutzen')
            //  - mode == 'off' + Datei nicht tauglich -> NICHTS zeigen, sonst
            //    Laerm fuer User, die den Modus bewusst deaktiviert haben
            // Fall-Aufteilung im else-if-Block:
            //  a) gar keine CSV im Verzeichnis
            //  b) CSV vorhanden, aber kein Schueler-Export (z.B. Lehrer-CSV)
            //  c) CSV vorhanden + ist Schueler-Export, aber Pflichtspalten fehlen
            //     -> konkrete Spalten-Liste anzeigen (Handlungsaufforderung)
            //  d) CSV vorhanden + alle Pflichtspalten -> aktiv nutzbar
            const inspect = sourceInfo.schueler_inspect || {};
            if (sourceMode !== 'off' || haveS) {
                const schexpDir = escHtmlBasic(d.schildexport_directory || '–');
                const schFile   = escHtmlBasic(d.latest_schueler_export || sourceInfo.schueler_csv_present ? '' : '');
                lines.push(`<strong>🟦📥 Schild-Exporte-Verzeichnis</strong> <span class="text-muted">(Single-File-Konsolidierung, Mode <code>${escHtmlBasic(sourceMode)}</code>)</span>: <code>${schexpDir}</code>`);
                if (haveS) {
                    // Fall (d): tauglich + (ggf.) aktiv
                    const fname = escHtmlBasic(d.latest_schueler_export || '');
                    const usedBadge = activeSource === 'schueler_export'
                        ? ` <span class="badge badge-success">aktiv genutzt${sourceInfo.fell_back ? ' (Fallback)' : ''}</span>`
                        : ` <span class="badge badge-light border">tauglich (Mode <code>${escHtmlBasic(sourceMode)}</code>)</span>`;
                    lines.push(`→ Schüler-Export: <code>${fname}</code>${usedBadge}`);
                } else if (inspect.file_exists && inspect.is_schueler_export) {
                    // Fall (c): CSV ist Schueler-Export, aber Spalten fehlen
                    const missingHard = inspect.missing_required_hard || [];
                    const missingAny  = inspect.missing_required_any  || [];
                    const slots       = inspect.erzieher_slots_in_header || 0;
                    const fname = escHtmlBasic(inspect.file_exists ? '(neueste CSV im Verzeichnis)' : '');
                    const parts = [];
                    if (missingHard.length) {
                        parts.push(`Pflichtspalten fehlen: ${missingHard.map(c => `<code>${escHtmlBasic(c)}</code>`).join(', ')}`);
                    }
                    if (missingAny.length) {
                        parts.push(`mindestens eine dieser Spalten erforderlich: ${missingAny.map(c => `<code>${escHtmlBasic(c)}</code>`).join(' / ')}`);
                    }
                    if (slots === 0) {
                        parts.push(`keine <code>Erzieher N: …</code>-Slot-Spalte gefunden`);
                    }
                    lines.push(`→ <span class="text-warning">⚠️ Schüler-Export gefunden, aber für Single-File-Modus nicht tauglich:</span><br>`
                        + `<span class="small text-muted ml-3">${parts.join('<br>')}</span>`
                        + `<br><span class="small text-muted ml-3">→ Bitte beim nächsten Schild-Export die fehlenden Spalten in der Vorlage mit-auswählen (Datenart <em>Schüler</em>: Erzieher 1/2 Anrede/Briefanrede/Titel/Vorname/Nachname/E-Mail, Telefon-Nummern: Anschluss-Art/Bemerkung/Telefon-Nummer, Geburtsdatum, Erzieher: Art (Klartext)).</span>`);
                } else if (inspect.file_exists) {
                    // Fall (b): irgendeine CSV, aber kein Schueler-Export
                    lines.push(`→ <span class="text-muted">CSV vorhanden, aber kein Schüler-Export (Spalten <code>Interne ID-Nummer</code> + <code>Vorname</code>/<code>Nachname</code>/<code>Klasse</code> fehlen).</span>`);
                } else {
                    // Fall (a): leeres Verzeichnis
                    lines.push(`→ <span class="text-muted">Keine CSV im Verzeichnis gefunden.</span>`);
                }
                if (activeSource === 'schueler_export') {
                    lines.push(`<span class="text-info small">⚠️ Im Schüler-Export-Modus gilt: max. 2 Erzieher pro Schüler, max. 1 Telefonnummer pro Schüler. Für mehr Erzieher/Telefone weiterhin separaten Schild-Erzieher-Export verwenden.</span>`);
                }
            }
            // Farbe: rot bei fehlender Quelle, gelb bei nur fehlendem Anspr (optional), grün sonst
            let cls = "alert-success";
            if (!ready) cls = "alert-warning";
            else if (!haveA && activeSource !== 'schueler_export') cls = "alert-info";
            statusEl.className = `alert ${cls} py-2 mb-3`;
            const hint = ready
                ? ''
                : (haveS
                    ? '<br><br>Im <strong>🟦📥 Schild-Exporte-Verzeichnis</strong> liegt bereits ein nutzbarer Schüler-Export — Modus auf <code>fallback</code> oder <code>always</code> stellen (<em>Einstellungen → Quelle für den Erzieher-Workflow</em>), oder einen separaten Erzieher-Export in das Erzieher-Verzeichnis legen.'
                    : '<br><br>Bitte zuerst den Schild-Erzieher-Export in das Verzeichnis legen (Einstellungen → Quelldaten-Verzeichnisse) oder den Schüler-Export der Hauptverarbeitung (<strong>🟦📥 Schild-Exporte-Verzeichnis</strong>) nutzen und Modus umschalten.');
            statusEl.innerHTML = lines.join("<br>") + hint;
            if (procBtn) procBtn.disabled = !ready;

            // Konsolidierungs-Radios: 3-Stufen-Switch unter dem Status. Wird
            // immer gerendert (auch bei mode='off') — sonst wuerde der User die
            // Option nie entdecken, falls er den Erzieher-Export nicht pflegt.
            renderSchuelerExportToggle(sourceMode, haveS, sourceInfo.schueler_inspect || {});

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
        if (e.telefon) {
            const src = e.telefon_from_erz
                ? ` <span class="badge badge-success" title="primäre Telefonnummer aus Erzieher-Export">Erz</span>`
                : ``;
            bits.push(`📞 <span class="small">${escHtml(e.telefon)}</span>${src}`);
        }
        if (e.anschluss)bits.push(`<span class="badge badge-light border">${escHtml(e.anschluss)}</span>`);
        if (e.bemerkung)bits.push(`<span class="text-muted small">${escHtml(e.bemerkung)}</span>`);
        // Dummy-Vorschau (welche Felder wuerden beim Export mit DUMMY gefuellt?)
        if (e.dummies && Object.keys(e.dummies).length) {
            const dummyText = Object.entries(e.dummies)
                .map(([k, v]) => `${k}=<code>${escHtml(v)}</code>`).join(' · ');
            bits.push(`<span class="text-info small">🧪 Dummy: ${dummyText}</span>`);
        }
        // Flags
        const flags = [];
        if (e.virtual) flags.push(`<span class="badge badge-info">virtuell</span>`);
        if (e.would_skip_email) flags.push(`<span class="badge badge-warning">würde übersprungen (keine E-Mail)</span>`);
        if (e.eltern_id) {
            const cls = e.eltern_id_status === 'new' ? 'badge-warning' : 'badge-primary';
            const ttl = e.eltern_id_status === 'new'
                ? 'Eltern-ID wird beim nächsten Verarbeiten neu vergeben'
                : 'Eltern-ID bereits in der DB';
            flags.push(`<span class="badge ${cls}" title="${ttl}">🆔 ${escHtml(e.eltern_id)}</span>`);
        }
        const flagHtml = flags.length ? ` ${flags.join(' ')}` : '';
        const borderCls = e.virtual ? 'border-info' : (e.would_skip_email ? 'border-warning' : 'border-info');
        return `<div class="ml-3 mb-1 pl-2 border-left ${borderCls}">
                    <strong>Erzieher ${e.nr}:</strong> ${name}${flagHtml}
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

        // Smart-Match-Block
        let matchBlock = '';
        const ms = s.match_stats || {};
        if (s.match_mode === 'smart') {
            const gender   = ms.gender || 0;
            const pos      = ms.positional || 0;
            const orph_a   = s.orphan_anspr_count || ms.orphan_anspr || 0;
            const orph_e   = ms.orphan_erz || 0;
            const total    = gender + pos;
            const pct      = total > 0 ? Math.round(100 * gender / total) : 0;
            matchBlock = `<br><span class="small">
                <strong>🧠 Smart-Match:</strong>
                <span class="text-success">${gender} per Anschluss-Art (${pct}%)</span> ·
                <span class="text-muted">${pos} positional (neutrale Anschluss-Arten)</span> ·
                ${orph_a > 0 ? `<span class="text-warning">${orph_a} Telefon-Zeilen ohne Erzieher-Slot</span>` : '0 Telefon-Zeilen unzugeordnet'} ·
                ${orph_e > 0 ? `<span class="text-warning">${orph_e} Erzieher ohne Telefon</span>` : '0 Erzieher ohne Telefon'}
            </span>`;
        } else if (s.match_mode === 'positional') {
            matchBlock = `<br><span class="small text-muted">
                <strong>⚙️ Positionales Matching</strong> (Smart-Match in den Einstellungen aktivieren, um Telefon ↔ Erzieher per Anschluss-Art zu mappen)
            </span>`;
        }

        const volljBlock = (s.filter_volljaehrig && s.volljaehrig_filtered)
            ? ` · <span class="text-info">🔞 ${s.volljaehrig_filtered} volljährige Schüler herausgefiltert</span>`
            : '';
        const emailBlock = (s.require_email && s.skipped_no_email)
            ? ` · <span class="text-warning">📧 ${s.skipped_no_email} Erzieher-Slots ohne E-Mail würden übersprungen</span>`
            : '';
        const dummyBlock = (s.fill_dummies && s.dummy_fills)
            ? ` · <span class="text-info">🧪 ${s.dummy_fills} leere Felder mit Dummies gefüllt</span>`
            : '';
        const virtBlock = (s.lift_limit && (s.match_stats?.virtual || 0))
            ? ` · <span class="text-info">♾️ ${s.match_stats.virtual} überzählige Telefon-Zeilen als virtuelle Slots (3, 4, …)</span>`
            : '';
        const phoneBlock = s.phone_from_erz_first
            ? ` · <span class="text-success">📞 ${s.phone_from_erz_used || 0} primäre Telefon-Nrn aus Erzieher-Export`
              + (s.phone_from_erz_duplicates ? `, ${s.phone_from_erz_duplicates} Duplikat(e) gefiltert` : '')
              + `</span>`
            : '';
        const elternBlock = s.assign_eltern_ids
            ? ` · <span class="text-primary">🆔 ${s.eltern_id_total || 0} Erzieher mit Eltern-ID `
              + `(${s.eltern_id_known || 0} bekannt, ${s.eltern_id_would_new || 0} würden neu vergeben)</span>`
            : '';

        const anspSource = s.anspr_available === false
            ? `<span class="text-info">kein Anspr-Export</span>`
            : `<code>${escHtml(src.ansprechpartner_export_file || '')}</code> · ${s.ansprechpartner_rows} Ansprechpartner-Zeilen`;
        previewStats.innerHTML =
            `<strong>${s.students_count}</strong> Schüler · <strong>${s.unique_erzieher}</strong> verschiedene Erzieher `
            + `(${s.erzieher_total} Zuordnungen, max. ${s.max_erzieher} pro Schüler)${noErz}${volljBlock}${emailBlock}${dummyBlock}${virtBlock}${phoneBlock}${elternBlock}<br>`
            + `<span class="small text-muted">Quellen: <code>${escHtml(src.erzieher_export_file || '')}</code> + ${anspSource}</span>`
            + matchBlock;
    }

    function renderOrphanList() {
        const cont = document.getElementById('erzieherOrphanArea');
        if (!cont || !previewData) return;
        const s = previewData.stats || {};
        const rows = s.orphan_anspr_rows || [];
        if (!rows.length) {
            cont.style.display = 'none';
            return;
        }
        cont.style.display = '';
        const cap = s.orphan_anspr_count > rows.length
            ? ` <span class="text-muted small">(zeige erste ${rows.length} von ${s.orphan_anspr_count})</span>`
            : '';
        const items = rows.map(r => `<tr>
            <td><code>${escHtml(r.student_id)}</code></td>
            <td>${escHtml(r.student_name)} <span class="text-muted small">(${escHtml(r.klasse)})</span></td>
            <td><span class="badge badge-light border">${escHtml(r.anschluss || '—')}</span></td>
            <td class="small text-muted">${escHtml(r.bemerkung)}</td>
            <td><code>${escHtml(r.telefon)}</code></td>
        </tr>`).join('');
        cont.innerHTML = `<details class="mt-2">
            <summary class="text-warning" style="cursor:pointer;">
                ⚠️ ${s.orphan_anspr_count} Telefon-Zeile(n) ohne Erzieher-Slot${cap}
            </summary>
            <p class="small text-muted mt-2 mb-1">Diese Telefon-Zeilen passen zu keinem im Erzieher-Export hinterlegten Erzieher (z. B. weitere Telefone für Mutter/Vater, Oma, Notfallnummern). Sie werden beim Export <em>nicht</em> in die WebUntis-CSV übernommen.</p>
            <div class="table-responsive" style="max-height:240px; overflow-y:auto;">
                <table class="table table-sm mb-0">
                    <thead class="thead-light"><tr><th>ID</th><th>Schüler</th><th>Anschluss-Art</th><th>Bemerkung</th><th>Telefon</th></tr></thead>
                    <tbody>${items}</tbody>
                </table>
            </div>
        </details>`;
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
            renderOrphanList();
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
        if (!previewArea) return;
        // 'display' kann '', 'none' oder konkrete Werte sein. Sichtbar = ALLES ausser 'none'.
        const isVisible = previewArea.style.display !== 'none';
        if (isVisible) previewArea.style.display = 'none';
        else           loadPreview();
    });

    // -------------------------------------------------------------------
    // Quelldateien-Viewer (Rohinhalte der beiden Schild-CSVs)
    // -------------------------------------------------------------------
    const rawBtn      = document.getElementById('erzieherToggleRawSource');
    const rawArea     = document.getElementById('erzieherRawSourceArea');
    const rawStats    = document.getElementById('erzieherRawSourceStats');
    const rawSearch   = document.getElementById('erzieherRawSourceSearch');
    const rawTable    = document.getElementById('erzieherRawSourceTable');
    let rawData = null;
    let rawWhich = 'erzieher';   // 'erzieher' oder 'ansprechpartner'

    function activeRawFile() {
        return rawWhich === 'erzieher' ? rawData?.erzieher : rawData?.ansprechpartner;
    }
    function activeUsedCols() {
        return new Set(rawWhich === 'erzieher'
            ? (rawData?.used_erzieher_cols || [])
            : (rawData?.used_ansprechpartner_cols || []));
    }

    function renderRawTable() {
        if (!rawTable || !rawData) return;
        const file = activeRawFile();
        if (!file) {
            rawTable.querySelector('thead').innerHTML = '';
            rawTable.querySelector('tbody').innerHTML = '<tr><td class="text-muted small p-3">Keine CSV gefunden.</td></tr>';
            return;
        }
        const used = activeUsedCols();
        const q = (rawSearch?.value || '').trim().toLowerCase();
        const cols = file.columns;
        // Spaltenkopf — genutzte Spalten gruen markiert
        const ths = cols.map(c => {
            const isUsed = used.has(c);
            const badge = isUsed ? ' style="background:#d4edda;"' : '';
            return `<th${badge} title="${escHtml(c)}">${escHtml(c)}</th>`;
        }).join('');
        rawTable.querySelector('thead').innerHTML = `<tr><th class="text-muted small">#</th>${ths}</tr>`;
        // Zeilen filtern
        let rows = file.rows;
        if (q) {
            rows = rows.filter(r => r.some(v => String(v).toLowerCase().includes(q)));
        }
        if (!rows.length) {
            rawTable.querySelector('tbody').innerHTML = '<tr><td class="text-muted small p-3" colspan="' + (cols.length + 1) + '">Keine Treffer.</td></tr>';
            return;
        }
        // Cap fuer Performance bei sehr breiten/vielen Zeilen
        const VIEW_CAP = 1000;
        const view = rows.slice(0, VIEW_CAP);
        const trs = view.map((r, idx) => {
            const tds = r.map((v, ci) => {
                const isUsed = used.has(cols[ci]);
                const cls = isUsed ? '' : ' class="text-muted"';
                return `<td${cls}>${escHtml(v)}</td>`;
            }).join('');
            return `<tr><td class="text-muted small">${idx + 1}</td>${tds}</tr>`;
        }).join('');
        const more = rows.length > VIEW_CAP
            ? `<tr><td colspan="${cols.length + 1}" class="text-muted small text-center py-2">… weitere ${rows.length - VIEW_CAP} Zeilen ausgeblendet (Suche eingrenzen)</td></tr>`
            : '';
        rawTable.querySelector('tbody').innerHTML = trs + more;
    }

    function renderRawStats() {
        if (!rawStats || !rawData) return;
        const e = rawData.erzieher;
        const a = rawData.ansprechpartner;
        const lines = [];
        if (e) lines.push(`<strong>Erzieher-Export</strong>: <code>${escHtml(e.file)}</code> · ${e.rows_total} Zeile(n) · ${e.columns.length} Spalten` + (e.rows_shown < e.rows_total ? ` <span class="text-warning">(zeige erste ${e.rows_shown})</span>` : ''));
        else   lines.push(`<span class="text-warning"><strong>Erzieher-Export</strong>: keine CSV gefunden.</span>`);
        if (a) lines.push(`<strong>Ansprechpartner-Export</strong>: <code>${escHtml(a.file)}</code> · ${a.rows_total} Zeile(n) · ${a.columns.length} Spalten` + (a.rows_shown < a.rows_total ? ` <span class="text-warning">(zeige erste ${a.rows_shown})</span>` : ''));
        else   lines.push(`<span class="text-warning"><strong>Ansprechpartner-Export</strong>: keine CSV gefunden.</span>`);
        rawStats.innerHTML = lines.join('<br>');
    }

    async function loadRawSource() {
        if (!rawArea) return;
        rawArea.style.display = '';
        if (rawStats) rawStats.textContent = "Lade Quelldateien…";
        try {
            const r = await fetch('/api/erzieher/raw_source');
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || r.statusText);
            rawData = d;
            renderRawStats();
            renderRawTable();
        } catch (e) {
            if (rawStats) {
                rawStats.className = "alert alert-danger py-2 mb-2";
                rawStats.textContent = "Fehler: " + e;
            }
        }
    }

    rawBtn?.addEventListener('click', () => {
        if (!rawArea) return;
        const isVisible = rawArea.style.display !== 'none';
        if (isVisible) rawArea.style.display = 'none';
        else           loadRawSource();
    });

    rawSearch?.addEventListener('input', renderRawTable);

    document.querySelectorAll('#erzieherRawSourceTabs [data-raw-which]').forEach(a => {
        a.addEventListener('click', (ev) => {
            ev.preventDefault();
            rawWhich = a.dataset.rawWhich;
            document.querySelectorAll('#erzieherRawSourceTabs [data-raw-which]').forEach(x =>
                x.classList.toggle('active', x.dataset.rawWhich === rawWhich));
            renderRawTable();
        });
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

    // -------------------------------------------------------------------
    // Eltern-ID-Datenbank: Stats anzeigen + Reset
    // -------------------------------------------------------------------
    async function loadElternIdStats() {
        const el = document.getElementById('erzieher_eltern_id_stats');
        if (!el) return;
        try {
            const r = await fetch('/api/erzieher/eltern_ids/status');
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || r.statusText);
            const lines = [];
            if (d.exists) {
                lines.push(`<strong>📁 ${escHtml(d.path)}</strong> · <strong>${d.total_ids}</strong> ID(s) vergeben · nächste: <code>${escHtml(d.next_id)}</code>`);
                if (d.modified) lines.push(`<span class="text-muted">Letzte Änderung: ${escHtml(d.modified.replace('T', ' '))}</span>`);
            } else {
                lines.push(`<span class="text-muted">📁 <code>${escHtml(d.path)}</code> existiert noch nicht — wird beim ersten Verarbeitungslauf mit aktivierter Option erzeugt.</span>`);
            }
            el.innerHTML = lines.join('<br>');
        } catch (e) {
            el.innerHTML = `<span class="text-danger">Fehler: ${escHtml(String(e))}</span>`;
        }
    }
    document.getElementById('erzieher_eltern_id_reset')?.addEventListener('click', async () => {
        if (!confirm('Eltern-ID-Datenbank wirklich KOMPLETT löschen?\n\nNach dem Reset werden beim nächsten Verarbeitungslauf alle IDs neu vergeben — bestehende WebUntis-Verknüpfungen brechen damit.')) return;
        try {
            const r = await fetch('/api/erzieher/eltern_ids/reset', { method: 'POST' });
            const d = await r.json();
            if (!r.ok || !d.success) throw new Error(d.error || r.statusText);
            if (typeof showToast === 'function') showToast(d.removed ? 'Eltern-ID-Datenbank gelöscht.' : 'Keine Datenbank vorhanden.');
            loadElternIdStats();
        } catch (e) {
            alert('Fehler beim Zurücksetzen: ' + e);
        }
    });

    // -------------------------------------------------------------------
    // Missing-Erzieher-Report (klassenweise Auswertung)
    // -------------------------------------------------------------------
    const missingBtn      = document.getElementById('erzieherToggleMissing');
    const missingArea     = document.getElementById('erzieherMissingArea');
    const missingStats    = document.getElementById('erzieherMissingStats');
    const missingList     = document.getElementById('erzieherMissingList');
    const missingExport   = document.getElementById('erzieherMissingExport');
    const missingDownload = document.getElementById('erzieherMissingDownload');
    const missingResult   = document.getElementById('erzieherMissingResult');
    const missingSelAll   = document.getElementById('erzieherMissingSelectAll');
    const missingSelNone  = document.getElementById('erzieherMissingSelectNone');
    const missingCritBox  = document.getElementById('erzieherMissingCriteriaBox');
    let missingData = null;
    let missingZipReady = false;
    let missingCritInited = false;
    const DEFAULT_MISSING_CRIT = ['no_erzieher'];

    function getMissingCriteria() {
        return Array.from(missingCritBox?.querySelectorAll('.miss-crit-cb:checked') || [])
            .map(cb => cb.dataset.key);
    }
    function getMissingMode() {
        return document.querySelector('input[name="missing_mode"]:checked')?.value || 'any';
    }
    function renderMissingCriteria(available, used) {
        if (!missingCritBox) return;
        missingCritBox.innerHTML = (available || []).map(c => {
            const id = `miss_crit_${c.key}`;
            const checked = used.includes(c.key) ? 'checked' : '';
            return `<div class="form-check form-check-inline">
                <input class="form-check-input miss-crit-cb" type="checkbox" id="${id}" data-key="${c.key}" ${checked}>
                <label class="form-check-label small" for="${id}">${escHtml(c.label)}</label>
            </div>`;
        }).join('');
        missingCritBox.querySelectorAll('.miss-crit-cb').forEach(cb => {
            cb.addEventListener('change', () => {
                // Mindestens ein Kriterium muss aktiv sein
                if (getMissingCriteria().length === 0) {
                    cb.checked = true;
                    return;
                }
                loadMissing();
            });
        });
    }
    document.querySelectorAll('input[name="missing_mode"]').forEach(r => {
        r.addEventListener('change', () => {
            if (missingArea && missingArea.style.display !== 'none') loadMissing();
        });
    });

    function renderMissingStats() {
        if (!missingStats || !missingData) return;
        // Hinweis, wenn Stammdaten nicht aufgelöst werden konnten (z.B. weil
        // Anspr-Export fehlt UND Erzieher-Export keine Schüler-Stammdaten-Spalten hat)
        const unknownBlock = missingData.students_unknown
            ? `<br><span class="text-warning small">⚠️ Für ${missingData.students_unknown} Schüler konnte weder Klasse noch Name aufgelöst werden — sie landen unter „(ohne Klasse)" mit leerem Namen.`
              + (missingData.anspr_available
                  ? ` Diese Schüler-IDs sind nur im Erzieher-Export, nicht im Ansprechpartner-Export hinterlegt.`
                  : ` Ohne Ansprechpartner-CSV müsste der Erzieher-Export die Spalten <code>Schüler-Klasse</code>/<code>-Vorname</code>/<code>-Nachname</code> (oder <code>Klasse</code>/<code>Vorname</code>/<code>Nachname</code>) enthalten, damit die Stammdaten aufgelöst werden können.`)
              + `</span>`
            : '';
        const anspBlock = !missingData.anspr_available
            ? `<br><span class="text-info small">ℹ️ Ohne Ansprechpartner-Export — Schüler-Stammdaten werden aus dem Erzieher-Export gezogen (falls dort vorhanden).</span>`
            : '';
        if (missingData.total_students === 0) {
            missingStats.className = "alert alert-success py-2 mb-2";
            missingStats.innerHTML = `✅ Keine minderjährigen Schüler ohne Erzieher-Daten gefunden — alles vollständig.<br>`
                + `<span class="small text-muted">Quelle: <code>${escHtml(missingData.source_file || '')}</code></span>`
                + anspBlock;
        } else {
            missingStats.className = "alert alert-warning py-2 mb-2";
            missingStats.innerHTML = `<strong>${missingData.total_students}</strong> minderjährige Schüler in `
                + `<strong>${missingData.total_classes}</strong> Klasse(n) ohne hinterlegte Erzieher-Daten.<br>`
                + `<span class="small text-muted">Quelle: <code>${escHtml(missingData.source_file || '')}</code></span>`
                + anspBlock + unknownBlock;
        }
    }

    function renderMissingList() {
        if (!missingList || !missingData) return;
        const classes = missingData.classes || [];
        if (!classes.length) {
            missingList.innerHTML = '<p class="text-muted small m-0">Keine Treffer.</p>';
            if (missingExport) missingExport.disabled = true;
            return;
        }
        // Lookup: criterion key -> label
        const critLabels = {};
        (missingData.available_criteria || []).forEach(c => critLabels[c.key] = c.label);
        const html = classes.map(c => {
            const id = `miss_cls_${c.klasse.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
            const studs = c.students.map(s => {
                const reasons = (s.reasons || []).map(k =>
                    `<span class="badge badge-light border ml-1">${escHtml(critLabels[k] || k)}</span>`
                ).join('');
                return `<li><strong>${escHtml(s.nachname)}, ${escHtml(s.vorname)}</strong>
                  <span class="text-muted small">· ID <code>${escHtml(s.id)}</code></span>${reasons}</li>`;
            }).join('');
            return `<div class="mb-2 pb-2 border-bottom">
                <div class="form-check">
                    <input class="form-check-input miss-cls-cb" type="checkbox" id="${id}" data-klasse="${escHtml(c.klasse)}" checked>
                    <label class="form-check-label font-weight-bold" for="${id}">
                        Klasse <code>${escHtml(c.klasse)}</code>
                        <span class="badge badge-warning ml-1">${c.count} Schüler</span>
                    </label>
                </div>
                <ul class="mb-0 mt-1">${studs}</ul>
            </div>`;
        }).join('');
        missingList.innerHTML = html;
        missingList.querySelectorAll('.miss-cls-cb').forEach(cb => {
            cb.addEventListener('change', updateMissingExportBtn);
        });
        updateMissingExportBtn();
    }

    function selectedMissingClasses() {
        return Array.from(missingList?.querySelectorAll('.miss-cls-cb:checked') || [])
            .map(cb => cb.dataset.klasse);
    }
    function updateMissingExportBtn() {
        if (!missingExport) return;
        missingExport.disabled = selectedMissingClasses().length === 0;
    }

    async function loadMissing() {
        if (!missingArea) return;
        missingArea.style.display = '';
        if (missingStats) {
            missingStats.className = "alert alert-secondary py-2 mb-2";
            missingStats.textContent = "Lade Klassen-Auswertung…";
        }
        if (missingList) missingList.innerHTML = '';
        // Beim ersten Aufruf gibts noch keine Checkboxes -> Default-Kriterien senden
        const crit = missingCritInited ? getMissingCriteria() : DEFAULT_MISSING_CRIT;
        const mode = getMissingMode();
        const qs = new URLSearchParams({
            criteria: (crit && crit.length ? crit : DEFAULT_MISSING_CRIT).join(','),
            mode,
        });
        try {
            const r = await fetch('/api/erzieher/missing_report?' + qs.toString());
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || r.statusText);
            missingData = d;
            // Kriterien-UI nach erstem Call befuellen (nur einmal — sonst werden
            // die User-Auswahlen bei jedem Reload ueberschrieben)
            if (!missingCritInited) {
                renderMissingCriteria(d.available_criteria || [], d.criteria_used || DEFAULT_MISSING_CRIT);
                missingCritInited = true;
            }
            renderMissingStats();
            renderMissingList();
        } catch (e) {
            if (missingStats) {
                missingStats.className = "alert alert-danger py-2 mb-2";
                missingStats.textContent = "Fehler: " + e;
            }
        }
    }

    missingBtn?.addEventListener('click', () => {
        if (!missingArea) return;
        const isVisible = missingArea.style.display !== 'none';
        if (isVisible) missingArea.style.display = 'none';
        else           loadMissing();
    });

    missingSelAll?.addEventListener('click', () => {
        missingList?.querySelectorAll('.miss-cls-cb').forEach(cb => cb.checked = true);
        updateMissingExportBtn();
    });
    missingSelNone?.addEventListener('click', () => {
        missingList?.querySelectorAll('.miss-cls-cb').forEach(cb => cb.checked = false);
        updateMissingExportBtn();
    });

    missingExport?.addEventListener('click', async () => {
        const classes = selectedMissingClasses();
        if (!classes.length) return;
        missingExport.disabled = true;
        const orig = missingExport.textContent;
        missingExport.textContent = "⌛ Exportiere…";
        if (missingResult) missingResult.textContent = '';
        try {
            const r = await fetch('/api/erzieher/missing_export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    classes,
                    criteria: getMissingCriteria(),
                    mode:     getMissingMode(),
                }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) {
                if (missingResult) missingResult.innerHTML = `<span class="text-danger">❌ ${d.error || r.statusText}</span>`;
                return;
            }
            missingZipReady = true;
            if (missingDownload) missingDownload.disabled = false;
            if (missingResult) {
                missingResult.innerHTML = `✅ <code>${d.name}</code> in <code>${d.directory}</code> · `
                    + `${d.counts.classes} Klasse(n), ${d.counts.students} Schüler.`;
            }
            if (typeof showToast === 'function') showToast(`Missing-ZIP erstellt: ${d.counts.classes} Klasse(n).`);
        } catch (e) {
            if (missingResult) missingResult.innerHTML = `<span class="text-danger">❌ ${e}</span>`;
        } finally {
            missingExport.disabled = false; missingExport.textContent = orig;
            updateMissingExportBtn();
        }
    });

    missingDownload?.addEventListener('click', async () => {
        if (!missingZipReady) { alert("Bitte zuerst exportieren."); return; }
        try {
            const r = await fetch('/api/erzieher/missing_download');
            if (!r.ok) {
                const err = await r.json().catch(() => ({}));
                alert("Fehler: " + (err.error || r.statusText));
                return;
            }
            const blob = await r.blob();
            let fname = "FehlendeErzieher.zip";
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

    // Save: Directories + [Erzieher].smart_match speichern
    document.getElementById("saveErzieherSettings")?.addEventListener("click", async () => {
        const form = document.getElementById("form-erzieher-settings");
        if (!form) return;
        const btn = document.getElementById("saveErzieherSettings");
        btn.disabled = true; const orig = btn.textContent; btn.textContent = "⌛ Speichere…";
        try {
            // Felder nach Section aufteilen. Checkboxen werden direkt per .checked
            // gelesen, weil FormData unchecked-Boxen weglaesst (waeren sonst nicht
            // auf False zu setzen).
            const directories = {};
            const erzieher = {};
            const smartCb = document.getElementById('erzieher_smart_match');
            if (smartCb) erzieher.smart_match = smartCb.checked ? 'True' : 'False';
            const volljCb = document.getElementById('erzieher_filter_volljaehrig');
            if (volljCb) erzieher.filter_volljaehrig = volljCb.checked ? 'True' : 'False';
            const emailCb = document.getElementById('erzieher_require_email');
            if (emailCb) erzieher.require_email = emailCb.checked ? 'True' : 'False';
            const dummyCb = document.getElementById('erzieher_fill_dummies');
            if (dummyCb) erzieher.fill_dummies = dummyCb.checked ? 'True' : 'False';
            const liftCb  = document.getElementById('erzieher_lift_limit');
            if (liftCb)  erzieher.lift_limit = liftCb.checked ? 'True' : 'False';
            const phoneCb = document.getElementById('erzieher_phone_from_erz_first');
            if (phoneCb) erzieher.phone_from_erz_first = phoneCb.checked ? 'True' : 'False';
            const eltCb   = document.getElementById('erzieher_assign_eltern_ids');
            if (eltCb)   erzieher.assign_eltern_ids = eltCb.checked ? 'True' : 'False';
            const erzCbKeys = new Set(['smart_match', 'filter_volljaehrig',
                                       'require_email', 'fill_dummies', 'lift_limit',
                                       'phone_from_erz_first', 'assign_eltern_ids']);
            // Konsolidierungs-Radios werden auto-gespeichert beim Toggle
            // (saveSchuelerExportMode), gehoeren NICHT in [Directories].
            // Trotzdem im <form> drin (UI-Gruppierung) — explizit ueberspringen.
            const erzSkipKeys = new Set(['erz_source_mode']);
            new FormData(form).forEach((value, key) => {
                if (erzCbKeys.has(key))   return;  // schon oben behandelt
                if (erzSkipKeys.has(key)) return;  // separater Endpoint
                directories[key] = value;
            });
            const sections = {};
            if (Object.keys(directories).length) sections.Directories = directories;
            if (Object.keys(erzieher).length)    sections.Erzieher    = erzieher;
            const r = await fetch("/save-settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ settings: sections }),
            });
            const d = await r.json().catch(() => ({}));
            if (r.ok && d.status === "success") {
                if (typeof showToast === "function") showToast("Erzieher-Einstellungen gespeichert.");
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
