// Ausbilder-Workflow (Phase 3): Status laden, Klassen-Whitelist + Schueler-Blacklist
// pflegen, Verarbeitung anstossen, CSV herunterladen.

document.addEventListener("DOMContentLoaded", function () {

    const statusEl       = document.getElementById("ausbilderStatus");
    const chipsEl        = document.getElementById("ausbilderClassChips");
    const firmaChipsEl   = document.getElementById("ausbilderFirmaChips");
    const firmaSearchEl  = document.getElementById("ausbilderFirmaSearch");
    const firmaCountEl   = document.getElementById("ausbilderFirmaCount");
    const firmaModeLabel = document.getElementById("ausbilderFirmaModeLabel");
    const firmaModeHint  = document.getElementById("ausbilderFirmaModeHint");
    const firmaInteractHint = document.getElementById("ausbilderFirmaInteractHint");
    const blacklistPanel = document.getElementById("ausbilderBlacklistPanel");
    const blacklistChips = document.getElementById("ausbilderBlacklistChips");
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
        firms: [],
        classFilter: [],
        blacklist: new Set(),
        firmaWhitelist: new Set(),
        firmaBlacklist: new Set(),
        firmaMode: 'blacklist',  // 'whitelist' oder 'blacklist'
        haveCsv: false,
        expandedRows: new Set(),  // ids von Schuelern, deren Detail-Zeile geoeffnet ist
    };
    // Sortier-Status (Klick auf Tabellen-Header). Default: nichts gesetzt
    // -> Backend liefert bereits nach Klasse/Nachname/Vorname vorsortiert.
    let sortBy  = null;
    let sortDir = 'asc';

    function escapeHtml(s) {
        return String(s ?? '').replace(/[&<>"']/g, c => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
    }

    function renderStatus(d) {
        const lines = [];
        lines.push(`<strong>Eingabe-Verzeichnis:</strong> <code>${escapeHtml(d.input_directory || '–')}</code>`);

        // Single-File-Konsolidierung (3.2): Resolver hat schon entschieden,
        // welche Quelle wirksam ist (ausbilder_input vs. schueler_export).
        // Anzeige: aktive Quelle inkl. Mode/Fallback-Marker.
        const sourceInfo = d.schueler_export_source || {};
        const sourceMode = d.schueler_export_mode || 'off';
        const activeSource = sourceInfo.source; // 'ausbilder_input' | 'schueler_export' | null
        const haveS = !!sourceInfo.schueler_available;
        if (activeSource === 'schueler_export') {
            lines.push(`→ <span class="badge badge-success">Schüler-Export aus Schild-Exporte-Verzeichnis aktiv${sourceInfo.fell_back ? ' (Fallback)' : ''}</span> <code>${escapeHtml(d.latest_schueler_export || '')}</code>`);
        } else {
            lines.push(d.latest_csv
                ? `→ Aktuelle Datei: <code>${escapeHtml(d.latest_csv)}</code>`
                : `→ <span class="text-warning">Keine CSV gefunden.</span>`);
        }
        lines.push(`<strong>Ausgabeverzeichnis:</strong> <code>${escapeHtml(d.output_directory || '–')}</code>`);

        // Konsolidierungs-Block: 'Schild Exporte'-Hauptverzeichnis als
        // alternative Quelle sichtbar machen. Anzeige-Logik (symmetrisch zum
        // Erzieher-Workflow):
        //  - mode != 'off' (User hat den Modus aktiv ausgewaehlt) -> immer
        //    zeigen, inkl. Warnung bei fehlenden Spalten
        //  - mode == 'off' + Datei voll tauglich -> positiver Discovery-Hinweis
        //  - mode == 'off' + Datei nicht tauglich -> NICHTS (kein Laerm fuer
        //    User, die den Modus bewusst deaktiviert haben)
        const inspect = sourceInfo.schueler_inspect || {};
        if (sourceMode !== 'off' || haveS) {
            const schexpDir = escapeHtml(d.schildexport_directory || '–');
            lines.push(`<strong>🟦📥 Schild-Exporte-Verzeichnis</strong> <span class="text-muted">(Single-File-Konsolidierung, Mode <code>${escapeHtml(sourceMode)}</code>)</span>: <code>${schexpDir}</code>`);
            if (haveS) {
                const fname = escapeHtml(d.latest_schueler_export || '');
                const usedBadge = activeSource === 'schueler_export'
                    ? ` <span class="badge badge-success">aktiv genutzt${sourceInfo.fell_back ? ' (Fallback)' : ''}</span>`
                    : ` <span class="badge badge-light border">tauglich (Mode <code>${escapeHtml(sourceMode)}</code>)</span>`;
                lines.push(`→ Schüler-Export: <code>${fname}</code>${usedBadge}`);
            } else if (inspect.file_exists && inspect.is_schueler_export) {
                const missingHard = inspect.missing_required_hard || [];
                lines.push(`→ <span class="text-warning">⚠️ Schüler-Export gefunden, aber für Ausbilder-Single-File-Modus nicht tauglich:</span><br>`
                    + `<span class="small text-muted ml-3">Pflichtspalten fehlen: ${missingHard.map(c => `<code>${escapeHtml(c)}</code>`).join(', ')}</span>`
                    + `<br><span class="small text-muted ml-3">→ Bitte beim nächsten Schild-Export die fehlenden Spalten in der Vorlage mit-auswählen (Datenart <em>Schüler</em>: <em>Allg. Adresse: Name1</em>, <em>Allg. Adresse: Betreuer …</em>).</span>`);
            } else if (inspect.file_exists) {
                lines.push(`→ <span class="text-muted">CSV vorhanden, aber kein Schüler-Export (Spalten <code>Interne ID-Nummer</code> + <code>Vorname</code>/<code>Nachname</code>/<code>Klasse</code> fehlen).</span>`);
            } else {
                lines.push(`→ <span class="text-muted">Keine CSV im Verzeichnis gefunden.</span>`);
            }
        }

        // Konsolidierungs-Hinweis: Schueler-Export hat bereits Betreuer-Felder
        // (Anrede/Name/E-Mail/Telefon/Abteilung/Fax), die der separate
        // Schild-Export 'Allgemeine Adressen' gar nicht liefert.
        if (d.latest_csv && Array.isArray(d.students)) {
            const withBetreuer = d.students.filter(s => {
                const a = s.ausbilder || {};
                return a.vorname || a.nachname || a.email || a.telefon || a.abteilung;
            }).length;
            if (withBetreuer > 0) {
                lines.push(`<div class="mt-1">`
                    + `<span class="badge badge-success">✓ Betreuer-Daten erkannt (${withBetreuer} Schüler)</span>`
                    + `</div>`
                    + `<small class="text-muted">Der Schild-Schüler-Export enthält die kompletten Betreuer-Felder (Anrede/Name/E-Mail/Telefon/Abteilung/Fax), die der separate Schild-Export „Allgemeine Adressen" gar nicht liefert.</small>`);
            }
        }

        const ready = !!d.latest_csv;
        statusEl.className = ready ? "alert alert-success py-2 mb-3" : "alert alert-warning py-2 mb-3";
        const hint = ready
            ? ''
            : (haveS
                ? '<br><br>Im <strong>🟦📥 Schild-Exporte-Verzeichnis</strong> liegt bereits ein nutzbarer Schüler-Export — Modus auf <code>fallback</code> oder <code>always</code> stellen (<em>Einstellungen → Quelle für den Ausbilder-Workflow</em>), oder eine CSV ins Ausbilder-Eingabeverzeichnis legen.'
                : '<br><br>Bitte zuerst die Schild-CSV ins Eingabe-Verzeichnis legen (Einstellungen → Quelldaten-Verzeichnis) oder den Schüler-Export der Hauptverarbeitung (<strong>🟦📥 Schild-Exporte-Verzeichnis</strong>) nutzen und Modus umschalten.');
        statusEl.innerHTML = lines.join("<br>") + hint;
        if (procBtn) procBtn.disabled = !ready;

        // Quell-Modus-Toggle rendern (auch bei mode='off' sichtbar, damit
        // User die Option entdeckt). Cache-Invalidation triggert ein
        // loadStudents() — neuer Datensatz, neue Klassen/Firmen.
        renderAusbilderSchuelerExportToggle(sourceMode, haveS, sourceInfo.schueler_inspect || {});
    }

    // Sentinel im class_filter, der explizit "keine Klasse aktiv" bedeutet
    // (sonst kollidiert das mit der Default-Semantik "leer = alle Klassen").
    const NONE_SENTINEL = '__NONE__';

    function isNoneMode() {
        return state.classFilter.length === 1 && state.classFilter[0] === NONE_SENTINEL;
    }
    function isAllMode() {
        return !isNoneMode() && state.classFilter.length === 0;
    }

    function collapseFilter(cur) {
        // cur: Set<string>. Liefert das Filter-Array in normalisierter Form.
        if (cur.size === state.classes.length) return [];                  // alle -> Default
        if (cur.size === 0)                    return [NONE_SENTINEL];     // keine -> explizit nichts
        return Array.from(cur);
    }

    function renderClassChips() {
        if (!chipsEl) return;
        if (!state.classes.length) {
            chipsEl.innerHTML = '<span class="text-muted small">Keine Klassen in der CSV gefunden.</span>';
            return;
        }
        const allMode  = isAllMode();
        const noneMode = isNoneMode();
        const filterSet = new Set(state.classFilter);
        const chips = state.classes.map(k => {
            let active;
            if (allMode)       active = true;
            else if (noneMode) active = false;
            else               active = filterSet.has(k);
            const cls = active ? 'btn-success' : 'btn-outline-secondary';
            return `<button type="button" class="btn btn-sm ${cls} mr-1 mb-1 ausbilder-class-chip" data-class="${escapeHtml(k)}">${escapeHtml(k)}</button>`;
        }).join('');
        let allLabel, allCls;
        if (allMode)       { allLabel = 'Alle abwählen'; allCls = 'btn-info'; }
        else if (noneMode) { allLabel = 'Alle wählen';   allCls = 'btn-outline-info'; }
        else               { allLabel = 'Alle wählen';   allCls = 'btn-outline-info'; }
        const allBtn = `<button type="button" class="btn btn-sm ${allCls} mr-2 mb-1" id="ausbilderClassAll" title="Schaltet zwischen 'alle Klassen aktiv' und 'keine Klasse aktiv' um.">${allLabel}</button>`;
        let warning = '';
        if (noneMode) {
            warning = '<div class="text-danger small mt-2">⚠️ Keine Klasse aktiv — es würde nichts exportiert.</div>';
        }
        chipsEl.innerHTML = allBtn + chips + warning;

        chipsEl.querySelectorAll('.ausbilder-class-chip').forEach(btn => {
            btn.addEventListener('click', () => {
                const k = btn.dataset.class;
                let cur;
                if (allMode) {
                    // Start: alle aktiv -> diese eine wird abgewählt
                    cur = new Set(state.classes);
                    cur.delete(k);
                } else if (noneMode) {
                    // Start: keine aktiv -> nur diese wird aktiviert
                    cur = new Set([k]);
                } else {
                    cur = new Set(state.classFilter);
                    if (cur.has(k)) cur.delete(k); else cur.add(k);
                }
                state.classFilter = collapseFilter(cur);
                saveClassFilter();
                renderClassChips();
                // Schueler aus jetzt abgewaehlten Klassen aus der Tabelle ausblenden
                renderStudents();
            });
        });
        const allBtnEl = document.getElementById('ausbilderClassAll');
        if (allBtnEl) allBtnEl.addEventListener('click', () => {
            // Toggle: allMode -> noneMode, sonst -> allMode
            state.classFilter = allMode ? [NONE_SENTINEL] : [];
            saveClassFilter();
            renderClassChips();
            renderStudents();
        });
    }

    function renderFirmaChips() {
        if (!firmaChipsEl) return;
        const mode = state.firmaMode;
        const setRef = mode === 'whitelist' ? state.firmaWhitelist : state.firmaBlacklist;
        const activeCls = mode === 'whitelist' ? 'btn-success' : 'btn-danger';

        // Mode-spezifische Labels/Hinweise oben
        if (firmaModeLabel) {
            firmaModeLabel.textContent = mode === 'whitelist' ? 'Whitelist' : 'Blacklist';
            firmaModeLabel.className = mode === 'whitelist' ? 'text-success' : 'text-danger';
        }
        if (firmaModeHint) {
            firmaModeHint.innerHTML = mode === 'whitelist'
                ? '(<em>nur</em> markierte Firmen werden exportiert · leer = alle erlaubt · Modus umstellbar in den Einstellungen)'
                : '(markierte Firmen werden <em>nie</em> exportiert · leer = keine ausgeschlossen · Modus umstellbar in den Einstellungen)';
        }
        if (firmaInteractHint) {
            firmaInteractHint.innerHTML = mode === 'whitelist'
                ? '<span class="badge badge-success">Grün</span> = auf Whitelist (wird exportiert).'
                : '<span class="badge badge-danger">Rot</span> = auf Blacklist (wird nicht exportiert).';
        }

        if (!state.firms.length && setRef.size === 0) {
            firmaChipsEl.innerHTML = '<span class="text-muted small">Keine Firmen in der CSV gefunden.</span>';
            if (firmaCountEl) firmaCountEl.textContent = '—';
            return;
        }

        // Such-Filter (Client-side)
        const q = (firmaSearchEl?.value || '').trim().toLowerCase();
        const matches = f => !q || f.toLowerCase().includes(q);
        const visibleKnown = state.firms.filter(matches);
        // Stale-Firmen (in Settings, aber nicht im aktuellen CSV)
        const knownSet = new Set(state.firms);
        const staleAll = Array.from(setRef).filter(f => !knownSet.has(f)).sort();
        const visibleStale = staleAll.filter(matches);

        const inactiveCls = 'btn-outline-secondary';
        const titleAct = mode === 'whitelist'
            ? 'Klick entfernt Firma von der Whitelist'
            : 'Klick entfernt Firma von der Blacklist';
        const titleInact = mode === 'whitelist'
            ? 'Klick fügt Firma zur Whitelist hinzu'
            : 'Klick fügt Firma zur Blacklist hinzu';

        const chipHtml = (f, isStale) => {
            const active = setRef.has(f);
            const cls = active ? activeCls : inactiveCls;
            const title = active ? titleAct : titleInact;
            const staleMark = isStale ? ' <span class="text-muted small">(nicht im Import)</span>' : '';
            return `<button type="button"
                            class="btn btn-sm ${cls} mr-1 mb-1 ausbilder-firma-chip"
                            data-firma="${escapeHtml(f)}"
                            title="${escapeHtml(title)}">${escapeHtml(f)}${staleMark}</button>`;
        };

        const knownChips = visibleKnown.map(f => chipHtml(f, false)).join('');
        const staleChips = visibleStale.map(f => chipHtml(f, true)).join('');
        firmaChipsEl.innerHTML = knownChips + staleChips
            || '<span class="text-muted small">Keine Treffer.</span>';

        if (firmaCountEl) {
            const totalVisible = visibleKnown.length + visibleStale.length;
            const totalAll = state.firms.length + staleAll.length;
            const sel = setRef.size;
            const staleNote = staleAll.length ? ` · ${staleAll.length} Stale` : '';
            firmaCountEl.textContent = `${sel} ausgewählt · ${totalVisible} sichtbar von ${totalAll}${staleNote}`;
        }

        firmaChipsEl.querySelectorAll('.ausbilder-firma-chip').forEach(btn => {
            btn.addEventListener('click', async () => {
                const f = btn.dataset.firma;
                if (setRef.has(f)) setRef.delete(f); else setRef.add(f);
                await saveFirmaList(mode);
                renderFirmaChips();
                // Schueler aus jetzt blacklisteten / nicht-whitelisteten Firmen
                // sofort aus der Tabelle ausblenden (bzw. wieder einblenden).
                renderStudents();
            });
        });
    }

    async function saveFirmaList(mode) {
        const endpoint = mode === 'whitelist'
            ? '/api/ausbilder/save_firma_whitelist'
            : '/api/ausbilder/save_firma_blacklist';
        const setRef = mode === 'whitelist' ? state.firmaWhitelist : state.firmaBlacklist;
        try {
            const r = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ firms: Array.from(setRef) }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) throw new Error(d.error || r.statusText);
        } catch (e) {
            alert('Fehler beim Speichern der Firma-' + mode + ': ' + e);
        }
    }

    function renderBlacklistPanel() {
        if (!blacklistPanel || !blacklistChips) return;
        const ids = Array.from(state.blacklist);
        if (!ids.length) {
            blacklistPanel.style.display = 'none';
            blacklistChips.innerHTML = '';
            return;
        }
        // Schüler-Stammdaten zum schnellen Lookup
        const byId = new Map(state.students.map(s => [s.id, s]));
        // Sortierung: zuerst die mit bekannten Daten (Klasse/Nachname), dann Stale-IDs
        const known = [], stale = [];
        ids.forEach(id => {
            const s = byId.get(id);
            if (s) known.push(s);
            else   stale.push(id);
        });
        known.sort((a, b) => (a.klasse + a.nachname + a.vorname).localeCompare(b.klasse + b.nachname + b.vorname));
        stale.sort();

        const knownChips = known.map(s => {
            const firmaHtml = s.firma ? ` <span class="text-muted">·</span> <span class="text-muted">${escapeHtml(s.firma)}</span>` : '';
            return `
            <button type="button"
                    class="btn btn-sm btn-outline-danger mr-2 mb-1 ausbilder-blk-chip"
                    data-id="${escapeHtml(s.id)}"
                    title="Klick zum Reaktivieren (von Blacklist entfernen)">
                ${escapeHtml(s.nachname)}, ${escapeHtml(s.vorname)}
                <span class="text-muted">(${escapeHtml(s.klasse)})</span>${firmaHtml}
                <span class="ml-1" aria-hidden="true">✕</span>
            </button>`;
        }).join('');
        const staleChips = stale.map(id => `
            <button type="button"
                    class="btn btn-sm btn-outline-secondary mr-2 mb-1 ausbilder-blk-chip"
                    data-id="${escapeHtml(id)}"
                    title="ID nicht im aktuellen CSV-Import — Klick zum Entfernen aus der Blacklist">
                <span class="text-muted">ID</span> <code>${escapeHtml(id)}</code>
                <span class="text-muted small">(nicht im Import)</span>
                <span class="ml-1" aria-hidden="true">✕</span>
            </button>`).join('');

        blacklistPanel.style.display = '';
        blacklistChips.innerHTML =
            `<div class="small text-muted mb-1">${known.length + stale.length} Eintrag(e)${stale.length ? ` · ${stale.length} nicht im aktuellen Import` : ''}</div>`
            + knownChips + staleChips;

        blacklistChips.querySelectorAll('.ausbilder-blk-chip').forEach(btn => {
            btn.addEventListener('click', async () => {
                const sid = btn.dataset.id;
                btn.disabled = true;
                try {
                    const r = await fetch('/api/ausbilder/blacklist/toggle', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id: sid, add: false }),
                    });
                    const d = await r.json();
                    if (!r.ok || !d.success) throw new Error(d.error || r.statusText);
                    state.blacklist = new Set(d.blacklist || []);
                    renderBlacklistPanel();
                    // Checkbox in der Haupttabelle synchronisieren, falls sichtbar
                    const cb = bodyEl?.querySelector(`.ausbilder-blk[data-id="${CSS.escape(sid)}"]`);
                    if (cb) cb.checked = true;
                    updateStudentCount();
                } catch (e) {
                    alert('Fehler beim Reaktivieren: ' + e);
                    btn.disabled = false;
                }
            });
        });
    }

    function updateStudentCount() {
        if (!countEl || !bodyEl) return;
        // Wir zaehlen nur die main-rows (nicht die Detail-Aufklapp-Zeilen).
        const visible = bodyEl.querySelectorAll('tr.ausb-row').length;
        const bl = state.students.filter(x => state.blacklist.has(x.id)).length;
        const classHiddenCount = state.students.filter(s => !passesClassFilter(s)).length;
        const firmaHiddenCount = state.students.filter(s =>
            passesClassFilter(s) && !passesFirmaFilter(s)).length;
        let txt = `${visible} sichtbar · ${state.students.length} insgesamt · ${bl} auf Blacklist`;
        if (classHiddenCount > 0) {
            txt += ` · ${classHiddenCount} aus abgewählten Klassen`;
        }
        if (firmaHiddenCount > 0) {
            const word = state.firmaMode === 'whitelist' ? 'ausserhalb Firmen-Whitelist' : 'durch Firmen-Blacklist ausgeblendet';
            txt += ` · ${firmaHiddenCount} ${word}`;
        }
        countEl.textContent = txt;
    }

    /**
     * Filtert Schueler nach dem aktiven Firma-Modus exakt wie das Backend:
     * - Whitelist-Modus mit leerer Liste: alle durch
     * - Whitelist-Modus mit gefuellter Liste: nur Schueler, deren Firma drin ist
     *   (Schueler ohne Firma fallen damit raus — wie im Backend)
     * - Blacklist-Modus: Schueler ohne Firma kommen durch, sonst nur wenn die
     *   Firma NICHT auf der Blacklist steht
     * Schueler aus geblacklisteten / nicht-whitelisteten Firmen werden damit
     * aus der Schueler-Tabelle ausgeblendet — sie werden ohnehin nicht
     * exportiert und sollen den Nutzer nicht verwirren.
     */
    function passesFirmaFilter(s) {
        if (state.firmaMode === 'whitelist') {
            if (state.firmaWhitelist.size === 0) return true;
            return state.firmaWhitelist.has(s.firma);
        }
        if (!s.firma) return true;
        return !state.firmaBlacklist.has(s.firma);
    }

    /**
     * Filtert Schueler nach der aktiven Klassen-Whitelist — analog zum Backend
     * in filter_and_write():
     * - All-Mode (classFilter leer): alle Klassen sichtbar
     * - None-Mode (classFilter === ['__NONE__']): nichts sichtbar
     * - sonst: nur Schueler aus Klassen in classFilter
     * Schueler aus abgewaehlten Klassen werden so ebenfalls ausgeblendet, statt
     * den Nutzer mit "warum taucht der noch auf" verwirren zu lassen.
     */
    function passesClassFilter(s) {
        if (isNoneMode())  return false;
        if (isAllMode())   return true;
        return state.classFilter.includes(s.klasse);
    }

    function passesSearch(s, q) {
        if (!q) return true;
        q = q.toLowerCase();
        return (s.nachname || '').toLowerCase().includes(q)
            || (s.vorname  || '').toLowerCase().includes(q)
            || (s.klasse   || '').toLowerCase().includes(q)
            || (s.firma    || '').toLowerCase().includes(q)
            || (s.id       || '').toLowerCase().includes(q);
    }

    function sortStudents(list) {
        if (!sortBy) return list;
        const mul = sortDir === 'asc' ? 1 : -1;
        return [...list].sort((a, b) => {
            const va = (a[sortBy] || '').toString();
            const vb = (b[sortBy] || '').toString();
            return mul * va.localeCompare(vb, 'de', { sensitivity: 'base', numeric: true });
        });
    }

    function renderSortIndicators() {
        document.querySelectorAll('#ausbilderStudentsTable th.ausb-sort').forEach(th => {
            const ind = th.querySelector('.ausb-sort-ind');
            if (!ind) return;
            if (th.dataset.sortCol === sortBy) {
                ind.textContent = sortDir === 'asc' ? '▲' : '▼';
                th.classList.add('text-primary');
            } else {
                ind.textContent = '';
                th.classList.remove('text-primary');
            }
        });
    }

    function renderStudentDetailRow(s, expanded) {
        const a = s.ausbilder || {};
        const fieldsLeft = [
            ['Anrede',    a.anrede],
            ['Titel',     a.titel],
            ['Vorname',   a.vorname],
            ['Nachname',  a.nachname],
        ];
        const fieldsRight = [
            ['📧 E-Mail',    a.email],
            ['📞 Telefon',   a.telefon],
            ['🏷️ Abteilung', a.abteilung],
            ['📠 Fax',       a.fax],
        ];
        const renderField = ([label, val]) => `
            <div class="d-flex small mb-1">
                <div class="text-muted" style="min-width:110px;">${label}:</div>
                <div>${val ? escapeHtml(val) : '<span class="text-muted">—</span>'}</div>
            </div>`;
        const isEmpty = !a.vorname && !a.nachname && !a.email && !a.telefon && !a.abteilung && !a.fax && !a.titel && !a.anrede;
        const inner = isEmpty
            ? '<div class="text-muted small fst-italic">Keine Ausbilder-/Betreuer-Daten in der CSV.</div>'
            : `<div class="row">
                  <div class="col-md-6">${fieldsLeft.map(renderField).join('')}</div>
                  <div class="col-md-6">${fieldsRight.map(renderField).join('')}</div>
                  ${s.firma ? `<div class="col-12 mt-1 small"><strong>🏢 Firma:</strong> ${escapeHtml(s.firma)}</div>` : ''}
               </div>`;
        const display = expanded ? '' : 'display:none;';
        return `<tr class="ausb-detail-row" data-detail-for="${escapeHtml(s.id)}" style="${display}">
                    <td colspan="6" style="background:#fafbfc; border-top:0;">
                        <div class="p-2"><strong class="small text-muted">Ausbilder/Betreuer:</strong>${inner}</div>
                    </td>
                </tr>`;
    }

    function renderStudents() {
        if (!bodyEl) return;
        if (!state.students.length) {
            bodyEl.innerHTML = '<tr><td colspan="6" class="text-center text-muted py-3">Keine Schüler in der CSV.</td></tr>';
            if (countEl) countEl.textContent = '—';
            renderSortIndicators();
            return;
        }
        const q = (searchInput?.value || '').trim();
        // Schueler aus abgewaehlten Klassen + blacklisteten / nicht-whitelisteten
        // Firmen werden ausgeblendet (Backend filtert sie ohnehin beim Export raus
        // — so sieht der Nutzer gleich, dass sie nicht mitkommen, und blackt sie
        // nicht versehentlich ein zweites Mal).
        const filtered = state.students.filter(s =>
            passesClassFilter(s) && passesFirmaFilter(s) && passesSearch(s, q));
        const list = sortStudents(filtered);
        const blacklistedTotal = state.students.filter(s => state.blacklist.has(s.id)).length;
        const classHiddenCount = state.students.filter(s => !passesClassFilter(s)).length;
        const firmaHiddenCount = state.students.filter(s =>
            passesClassFilter(s) && !passesFirmaFilter(s)).length;
        if (countEl) {
            let txt = `${list.length} sichtbar · ${state.students.length} insgesamt · ${blacklistedTotal} auf Blacklist`;
            if (classHiddenCount > 0) {
                txt += ` · ${classHiddenCount} aus abgewählten Klassen`;
            }
            if (firmaHiddenCount > 0) {
                const word = state.firmaMode === 'whitelist' ? 'ausserhalb Firmen-Whitelist' : 'durch Firmen-Blacklist ausgeblendet';
                txt += ` · ${firmaHiddenCount} ${word}`;
            }
            countEl.textContent = txt;
        }
        const rows = list.flatMap(s => {
            const checked  = !state.blacklist.has(s.id);
            const expanded = state.expandedRows.has(s.id);
            const chev     = expanded ? '▾' : '▸';
            const main = `<tr class="ausb-row" data-id="${escapeHtml(s.id)}" style="cursor:pointer;">
                <td class="text-center ausb-checkbox-cell" style="cursor:default;"><input type="checkbox" class="ausbilder-blk" data-id="${escapeHtml(s.id)}" ${checked ? 'checked' : ''}></td>
                <td><span class="ausb-chev text-muted small mr-1">${chev}</span>${escapeHtml(s.klasse)}</td>
                <td>${escapeHtml(s.nachname)}</td>
                <td>${escapeHtml(s.vorname)}</td>
                <td>${escapeHtml(s.firma)}</td>
                <td><code>${escapeHtml(s.id)}</code></td>
            </tr>`;
            const detail = renderStudentDetailRow(s, expanded);
            return [main, detail];
        });
        bodyEl.innerHTML = rows.join('') || '<tr><td colspan="6" class="text-center text-muted py-3">Keine Treffer.</td></tr>';
        renderSortIndicators();

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
                    // Tabelle nicht komplett neu rendern (Scroll-Position halten),
                    // nur Counter + Blacklist-Panel aktualisieren.
                    updateStudentCount();
                    renderBlacklistPanel();
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

    // -------------------------------------------------------------------
    // Single-File-Konsolidierung (3.2): Quell-Modus-Toggle
    // 3 Modi: off | fallback | always — symmetrisch zum Erzieher-Workflow.
    // -------------------------------------------------------------------
    const ausbSourceToggleEl = document.getElementById("ausbilderSchuelerExportToggle");

    function renderAusbilderSchuelerExportToggle(currentMode, schuelerAvailable, inspect) {
        if (!ausbSourceToggleEl) return;
        inspect = inspect || {};
        const MODES = [
            { key: 'off',      label: 'Nur Ausbilder-Eingabeverzeichnis', desc: 'Schüler-Export der Hauptverarbeitung wird ignoriert (Default).' },
            { key: 'fallback', label: 'Fallback: Schüler-Export',         desc: 'Nur wenn Ausbilder-Eingabeverzeichnis leer ist — sonst weiterhin dortige CSV.' },
            { key: 'always',   label: 'Immer Schüler-Export',             desc: 'Schüler-Export aus dem Schild-Exporte-Verzeichnis hat Vorrang.' },
        ];
        const radios = MODES.map(m => {
            const checked = m.key === currentMode ? 'checked' : '';
            return `<div class="form-check form-check-inline mr-3">
                <input class="form-check-input ausb-source-radio" type="radio"
                       name="ausb_source_mode" id="ausb_src_${m.key}"
                       value="${m.key}" ${checked}>
                <label class="form-check-label small" for="ausb_src_${m.key}"
                       title="${escapeHtml(m.desc)}">
                    <strong>${escapeHtml(m.label)}</strong>
                </label>
            </div>`;
        }).join('');
        let note;
        if (schuelerAvailable) {
            note = `<small class="text-muted">Schüler-Export ist <strong>tauglich</strong> — Umschalten lädt die Schülertabelle neu.</small>`;
        } else if (inspect.file_exists && inspect.is_schueler_export) {
            note = `<small class="text-warning">⚠️ Schüler-Export gefunden, aber für Single-File-Modus <strong>nicht tauglich</strong> — siehe Status-Box oben für die konkreten Spalten, die in der Schild-Export-Vorlage zusätzlich aktiviert werden müssen.</small>`;
        } else if (inspect.file_exists) {
            note = `<small class="text-muted">CSV im <strong>🟦📥 Schild-Exporte-Verzeichnis</strong> vorhanden, aber kein Schüler-Export (Pflicht-Stammdaten fehlen). Im Modus <code>always</code> würde die Verarbeitung scheitern.</small>`;
        } else {
            note = `<small class="text-muted">Keine CSV im <strong>🟦📥 Schild-Exporte-Verzeichnis</strong>. Im Modus <code>always</code> würde die Verarbeitung scheitern, solange dort keine Schild-Schüler-CSV liegt.</small>`;
        }
        ausbSourceToggleEl.innerHTML = radios + `<div class="mt-1">${note}</div>`;
        ausbSourceToggleEl.querySelectorAll('.ausb-source-radio').forEach(r => {
            r.addEventListener('change', () => saveAusbilderSchuelerExportMode(r.value));
        });
    }

    async function saveAusbilderSchuelerExportMode(mode) {
        try {
            const r = await fetch('/api/ausbilder/save_schueler_export_mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) throw new Error(d.error || r.statusText);
            // Quellwechsel: Schueler-Tabelle (Klassen/Firmen/Stammdaten) komplett
            // neu laden — kann komplett anderer Datensatz sein.
            loadStudents();
        } catch (e) {
            alert('Fehler beim Speichern des Quell-Modus: ' + e);
        }
    }

    async function loadStudents() {
        if (!statusEl) return;
        statusEl.textContent = "Lade Status…";
        try {
            const r = await fetch('/api/ausbilder/students');
            const d = await r.json();

            if (tplInput && !tplInput.value) tplInput.value = d.output_name_template || 'WebUntis_Ausbilder_Import_{datetime}';

            state.students       = d.students || [];
            state.classes        = d.classes || [];
            state.firms          = d.firms || [];
            state.classFilter    = d.class_filter || [];
            state.blacklist      = new Set(d.blacklist || []);
            state.firmaWhitelist = new Set(d.firma_whitelist || []);
            state.firmaBlacklist = new Set(d.firma_blacklist || []);
            state.firmaMode      = (d.firma_filter_mode === 'whitelist') ? 'whitelist' : 'blacklist';
            state.haveCsv        = !!d.csv_path;
            // KL-Mail-Settings vom Backend; werden beim Open des Settings-
            // Panels in die Form-Felder reflektiert (siehe panel-Toggle).
            state.klMail = {
                kl_mail_respect_class_whitelist: !!d.kl_mail_respect_class_whitelist,
                kl_mail_respect_blacklist:       !!d.kl_mail_respect_blacklist,
                kl_mail_respect_firma_filter:    !!d.kl_mail_respect_firma_filter,
                kl_mail_include_stv_kl:          !!d.kl_mail_include_stv_kl,
                kl_mail_subject_suffix:          d.kl_mail_subject_suffix || '',
            };

            renderStatus(d);
            renderClassChips();
            renderFirmaChips();
            renderBlacklistPanel();
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
    firmaSearchEl?.addEventListener('input', renderFirmaChips);

    // Aktive Firmen-Liste leeren (Mode bleibt). Nutzt die bestehende
    // save_firma_whitelist/blacklist-Route mit leerem Array — kein neuer
    // Backend-Endpoint noetig. Confirm-Dialog mit Count + Mode, damit der
    // User klar sieht, was geloescht wird.
    document.getElementById('ausbilderFirmaClear')?.addEventListener('click', async () => {
        const mode = state.firmaMode;
        const active = mode === 'whitelist' ? state.firmaWhitelist : state.firmaBlacklist;
        if (active.size === 0) {
            alert(`Die ${mode}-Liste ist bereits leer.`);
            return;
        }
        const msg =
            `Die aktuelle ${mode}-Liste mit ${active.size} Firma(en) wirklich komplett leeren?\n\n` +
            `Modus bleibt: ${mode}.\n` +
            `Die andere (gerade nicht aktive) Liste bleibt ebenfalls unangetastet.\n\n` +
            `Diese Aktion kann nicht rückgängig gemacht werden.`;
        if (!confirm(msg)) return;
        const btn = document.getElementById('ausbilderFirmaClear');
        btn.disabled = true;
        const orig = btn.textContent;
        btn.textContent = '⌛ Leere…';
        const endpoint = mode === 'whitelist'
            ? '/api/ausbilder/save_firma_whitelist'
            : '/api/ausbilder/save_firma_blacklist';
        try {
            const r = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ firms: [] }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) throw new Error(d.error || r.statusText);
            if (typeof showToast === 'function') {
                showToast(`${mode}-Liste geleert (${active.size} entfernt).`);
            }
            // Lokalen State auch aktualisieren und UI re-rendern, ohne den
            // ganzen Workflow neu zu laden.
            if (mode === 'whitelist') state.firmaWhitelist = new Set();
            else                      state.firmaBlacklist = new Set();
            renderFirmaChips();
            renderStudents();
        } catch (e) {
            alert('Fehler beim Leeren: ' + e);
        } finally {
            btn.disabled = false;
            btn.textContent = orig;
        }
    });

    // Liste invertieren + Modus wechseln. Berechnet die Vorschau-Counts aus
    // state (state.firms = alle Firmen in CSV, state.firmaWhitelist/Blacklist
    // = aktive Liste) — Backend rechnet identisch nach. Bei Bestaetigung wird
    // die POST-Route gerufen, die danach loadStudents() triggern wird.
    document.getElementById('ausbilderFirmaInvert')?.addEventListener('click', async () => {
        const mode = state.firmaMode;
        const allFirms = new Set(state.firms || []);
        if (allFirms.size === 0) {
            alert('Keine Firmen in der aktuellen CSV gefunden — Invertierung nicht möglich.');
            return;
        }
        const active = mode === 'whitelist' ? state.firmaWhitelist : state.firmaBlacklist;
        // Nur Firmen zaehlen, die tatsaechlich in der CSV vorkommen
        // (sonst verzerren stale Settings-Eintraege die Vorschau).
        const activeInCsv = Array.from(active).filter(f => allFirms.has(f));
        const inverseSize = allFirms.size - activeInCsv.length;
        const newMode = mode === 'whitelist' ? 'blacklist' : 'whitelist';
        const msg =
            `Aktueller Modus: ${mode} mit ${activeInCsv.length} Firmen (in CSV).\n` +
            `Nach der Invertierung: ${newMode} mit ${inverseSize} Firmen.\n` +
            `(Basis: ${allFirms.size} Firmen in der aktuellen CSV.)\n\n` +
            `Hinweis: Die ${mode}-Liste bleibt unverändert gespeichert — durch erneutes ` +
            `Klicken auf diesen Button kommst du wieder zurück.\n\n` +
            `Fortfahren?`;
        if (!confirm(msg)) return;
        const btn = document.getElementById('ausbilderFirmaInvert');
        btn.disabled = true;
        const orig = btn.textContent;
        btn.textContent = '⌛ Invertiere…';
        try {
            const r = await fetch('/api/ausbilder/firma_invert', { method: 'POST' });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) {
                throw new Error(d.error || r.statusText);
            }
            if (typeof showToast === 'function') {
                showToast(`Modus ${d.old_mode} (${d.old_count}) → ${d.new_mode} (${d.new_count})`);
            }
            // Komplettes Neuladen — neue Listen, neuer Modus, UI rendert sich.
            loadStudents();
        } catch (e) {
            alert('Fehler beim Invertieren: ' + e);
        } finally {
            btn.disabled = false;
            btn.textContent = orig;
        }
    });

    // Klick auf Zeile (ausser Checkbox-Zelle) klappt Detail-Zeile auf/zu.
    // Delegate-Handler bleibt nach renderStudents() bestehen.
    bodyEl?.addEventListener('click', (e) => {
        if (e.target.closest('.ausb-checkbox-cell, .ausbilder-blk')) return;
        const tr = e.target.closest('tr.ausb-row');
        if (!tr) return;
        const id = tr.dataset.id;
        const detail = tr.nextElementSibling;
        if (!detail || !detail.classList.contains('ausb-detail-row')) return;
        const isShown = detail.style.display !== 'none';
        detail.style.display = isShown ? 'none' : '';
        if (isShown) state.expandedRows.delete(id);
        else         state.expandedRows.add(id);
        const chev = tr.querySelector('.ausb-chev');
        if (chev) chev.textContent = isShown ? '▸' : '▾';
    });

    // Klick auf einen sortierbaren Spaltenkopf: gleiche Spalte -> Richtung kippen,
    // andere Spalte -> aufsteigend dort starten.
    document.querySelectorAll('#ausbilderStudentsTable th.ausb-sort').forEach(th => {
        th.addEventListener('click', () => {
            const col = th.dataset.sortCol;
            if (!col) return;
            if (sortBy === col) {
                sortDir = sortDir === 'asc' ? 'desc' : 'asc';
            } else {
                sortBy = col;
                sortDir = 'asc';
            }
            renderStudents();
        });
    });

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

    // -------------------------------------------------------------------
    // KL-Mail-Versand (3.2): aktuelle Ausbilder-/Betreuer-Daten an
    // Klassenlehrkraefte mailen (Vorschau-Aufklapper + Auswahl + Versand)
    // -------------------------------------------------------------------
    const klMailBtn       = document.getElementById('ausbilderToggleKlMail');
    const klMailArea      = document.getElementById('ausbilderKlMailArea');
    const klMailStats     = document.getElementById('ausbilderKlMailStats');
    const klMailList      = document.getElementById('ausbilderKlMailList');
    const klMailSend      = document.getElementById('ausbilderKlMailSend');
    const klMailSelAll    = document.getElementById('ausbilderKlMailSelectAll');
    const klMailSelNone   = document.getElementById('ausbilderKlMailSelectNone');
    const klMailResult    = document.getElementById('ausbilderKlMailResult');
    let klMailData = null;

    function selectedKlMailClasses() {
        return Array.from(klMailList?.querySelectorAll('.klmail-cls-cb:checked') || [])
            .map(cb => cb.dataset.klasse);
    }
    function updateKlMailSendBtn() {
        if (!klMailSend) return;
        klMailSend.disabled = selectedKlMailClasses().length === 0;
    }

    function renderKlMailStats() {
        if (!klMailStats || !klMailData) return;
        const s   = klMailData.stats || {};
        const opt = klMailData.options_used || {};
        const filterBits = [];
        filterBits.push(opt.respect_class     ? 'Klassen-Whitelist ✓' : 'Klassen-Whitelist ✗');
        filterBits.push(opt.respect_blacklist ? 'Schüler-Blacklist ✓' : 'Schüler-Blacklist ✗');
        filterBits.push(opt.respect_firma     ? 'Firmen-Filter ✓'      : 'Firmen-Filter ✗');
        filterBits.push(opt.include_stv_kl    ? 'Stv-KL als CC ✓'      : 'Stv-KL als CC ✗');
        const cls = klMailData.classes || [];
        const noKlCount = cls.filter(c => !c.kl_email).length;
        const noKlBlock = noKlCount
            ? ` · <span class="text-warning">${noKlCount} Klasse(n) ohne aufgelöste KL-E-Mail</span>`
            : '';
        klMailStats.className = (s.classes_total === 0)
            ? 'alert alert-warning py-2 mb-2'
            : 'alert alert-info py-2 mb-2';
        klMailStats.innerHTML =
            `<strong>${s.classes_total}</strong> Klasse(n) · `
            + `<strong>${s.students_after_filters}</strong> von ${s.students_total} Schülern nach Filtern${noKlBlock}<br>`
            + `<span class="small text-muted">Quelle: <code>${escapeHtml(klMailData.csv_path || '')}</code> · Stand <strong>${escapeHtml(klMailData.stand || '')}</strong></span><br>`
            + `<span class="small text-muted">Filter-Optionen: ${filterBits.join(' · ')} — änderbar in den Einstellungen.</span>`;
    }

    function renderKlMailList() {
        if (!klMailList || !klMailData) return;
        const cls = klMailData.classes || [];
        if (!cls.length) {
            klMailList.innerHTML = '<p class="text-muted small m-0">Keine Klassen — vermutlich filtern Ihre KL-Mail-Einstellungen alles weg.</p>';
            updateKlMailSendBtn();
            return;
        }
        const html = cls.map(c => {
            const id = `klmail_cls_${c.klasse.replace(/[^a-zA-Z0-9_-]/g, '_')}`;
            const hasMail = !!c.kl_email;
            const noEmailWarn = hasMail
                ? ''
                : `<div class="text-danger small ml-4 mt-1">⚠️ Keine KL-E-Mail aufgelöst — Versand wird übersprungen. Lehrkräfte-CSV im Klassen-/Lehrer-Verzeichnis prüfen.</div>`;
            const ccPart = c.cc?.length
                ? ` <span class="text-muted small">CC: ${c.cc.map(e => `<code>${escapeHtml(e)}</code>`).join(', ')}</span>`
                : '';
            const xlsxLink = `<a href="/api/ausbilder/kl_mail/download_xlsx?klasse=${encodeURIComponent(c.klasse)}" class="badge badge-light border ml-1" title="Excel-Anhang vorab herunterladen">📎 ${escapeHtml(c.xlsx_filename)}</a>`;
            return `<div class="mb-2 pb-2 border-bottom">
                <div class="form-check">
                    <input class="form-check-input klmail-cls-cb" type="checkbox" id="${id}" data-klasse="${escapeHtml(c.klasse)}" ${hasMail ? 'checked' : ''} ${hasMail ? '' : 'disabled'}>
                    <label class="form-check-label font-weight-bold" for="${id}">
                        Klasse <code>${escapeHtml(c.klasse)}</code>
                        <span class="badge badge-info ml-1">${c.students_count} Schüler</span>
                    </label>
                </div>
                <div class="small text-muted ml-4">
                    KL: ${escapeHtml(c.kl_name || '—')}${hasMail ? ` <code>${escapeHtml(c.kl_email)}</code>` : ''}${ccPart}
                </div>
                ${noEmailWarn}
                <details class="ml-4 mt-1">
                    <summary class="text-info small" style="cursor:pointer;">👁️ Vorschau (Subject + Body) · ${xlsxLink}</summary>
                    <div class="mt-2 border rounded p-2 bg-light">
                        <div class="small text-muted">Betreff:</div>
                        <div class="mb-2"><code>${escapeHtml(c.subject)}</code></div>
                        <div class="small text-muted">Body (HTML, wie sie ihn sehen):</div>
                        <div class="border bg-white p-2" style="font-size:0.9em;">${c.body_html}</div>
                    </div>
                </details>
            </div>`;
        }).join('');
        klMailList.innerHTML = html;
        klMailList.querySelectorAll('.klmail-cls-cb').forEach(cb => {
            cb.addEventListener('change', updateKlMailSendBtn);
        });
        updateKlMailSendBtn();
    }

    async function loadKlMailPreview() {
        if (!klMailArea) return;
        klMailArea.style.display = '';
        if (klMailStats) { klMailStats.className = 'alert alert-secondary py-2 mb-2'; klMailStats.textContent = 'Lade KL-Mail-Vorschau…'; }
        if (klMailList) klMailList.innerHTML = '';
        try {
            const r = await fetch('/api/ausbilder/kl_mail/preview');
            const d = await r.json();
            if (!r.ok) throw new Error(d.error || r.statusText);
            klMailData = d;
            renderKlMailStats();
            renderKlMailList();
        } catch (e) {
            if (klMailStats) {
                klMailStats.className = 'alert alert-danger py-2 mb-2';
                klMailStats.textContent = 'Fehler: ' + e;
            }
        }
    }

    klMailBtn?.addEventListener('click', () => {
        if (!klMailArea) return;
        const visible = klMailArea.style.display !== 'none';
        if (visible) klMailArea.style.display = 'none';
        else         loadKlMailPreview();
    });

    klMailSelAll?.addEventListener('click', () => {
        klMailList?.querySelectorAll('.klmail-cls-cb:not(:disabled)').forEach(cb => cb.checked = true);
        updateKlMailSendBtn();
    });
    klMailSelNone?.addEventListener('click', () => {
        klMailList?.querySelectorAll('.klmail-cls-cb').forEach(cb => cb.checked = false);
        updateKlMailSendBtn();
    });

    klMailSend?.addEventListener('click', async () => {
        const classes = selectedKlMailClasses();
        if (!classes.length) return;
        const cnt = classes.length;
        if (!confirm(`Wirklich KL-Mails an ${cnt} Klassenlehrkraft/-kräfte versenden?\n\nDieser Versand kann nicht rückgängig gemacht werden.`)) return;
        klMailSend.disabled = true;
        const orig = klMailSend.textContent;
        klMailSend.textContent = '⌛ Versende…';
        if (klMailResult) klMailResult.textContent = '';
        try {
            const r = await fetch('/api/ausbilder/kl_mail/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ classes }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || !d.success) {
                if (klMailResult) klMailResult.innerHTML = `<span class="text-danger">❌ ${escapeHtml(d.error || r.statusText)}</span>`;
                return;
            }
            if (klMailResult) {
                klMailResult.innerHTML = `✅ Gesendet: <strong>${d.sent}</strong> · Übersprungen: ${d.skipped} · Fehler: ${d.failed} · `
                    + `Excel-Anhänge: <code>${escapeHtml(d.xlsx_directory || '')}</code>`;
            }
            if (typeof showToast === 'function') showToast(`KL-Mails: ${d.sent} gesendet, ${d.failed} Fehler.`);
        } catch (e) {
            if (klMailResult) klMailResult.innerHTML = `<span class="text-danger">❌ ${escapeHtml(String(e))}</span>`;
        } finally {
            klMailSend.disabled = false; klMailSend.textContent = orig;
            updateKlMailSendBtn();
        }
    });

    // Initialisierung: Status laden, sobald der Workflow sichtbar wird.
    // workflow_switcher.js dispatcht 'workflow:shown' sowohl beim Tab-Klick
    // als auch beim initialen Restore aus localStorage (F5).
    document.addEventListener('workflow:shown', (e) => {
        if (e.detail?.workflow === 'ausbilder') loadStudents();
    });

    // Toggle: eigenes Ausbilder-Settings-Panel
    document.getElementById("toggle-settings-ausbilder")?.addEventListener("click", () => {
        const panel = document.getElementById("ausbilderSettingsPanel");
        if (!panel) return;
        const willShow = panel.style.display === "none" || !panel.style.display;
        panel.style.display = willShow ? "block" : "none";
        if (willShow) {
            // Aktuellen Firma-Mode in den Radios reflektieren (kommt aus state)
            const radio = document.getElementById(`firma_filter_mode_${state.firmaMode}`);
            if (radio) radio.checked = true;
            // KL-Mail-Felder aus state spiegeln (werden ueber loadStudents()
            // in state.klMail gespeichert — siehe loadStudents-Callback).
            const klm = state.klMail || {};
            const setCb = (id, v) => { const el = document.getElementById(id); if (el) el.checked = !!v; };
            const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v || ''; };
            setCb('ausbilder_kl_mail_respect_class_whitelist', klm.kl_mail_respect_class_whitelist);
            setCb('ausbilder_kl_mail_respect_blacklist',       klm.kl_mail_respect_blacklist);
            setCb('ausbilder_kl_mail_respect_firma_filter',    klm.kl_mail_respect_firma_filter);
            setCb('ausbilder_kl_mail_include_stv_kl',          klm.kl_mail_include_stv_kl);
            setVal('ausbilder_kl_mail_subject_suffix',         klm.kl_mail_subject_suffix);
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
            // Trenne nach Section: Directories vs. [Ausbilder] (firma_filter_mode).
            // KL-Mail-Felder gehen ueber den dedizierten kl_mail/save_settings-
            // Endpoint, weil FormData unchecked Boxes weglaesst — so wuerden
            // ausgeschaltete Filter-Booleans NICHT als False persistiert. Der
            // dedizierte Endpoint nimmt das ganze Set explizit entgegen.
            const klMailKeys = new Set([
                'kl_mail_respect_class_whitelist',
                'kl_mail_respect_blacklist',
                'kl_mail_respect_firma_filter',
                'kl_mail_include_stv_kl',
                'kl_mail_subject_suffix',
            ]);
            const directories = {};
            const ausbilder = {};
            new FormData(form).forEach((value, key) => {
                if (key === 'ausb_source_mode')   return;  // separater Endpoint
                if (klMailKeys.has(key))          return;  // separater Endpoint
                if (key === 'firma_filter_mode')  ausbilder[key] = value;
                else                              directories[key] = value;
            });
            const sectionsToSave = {};
            if (Object.keys(directories).length) sectionsToSave.Directories = directories;
            if (Object.keys(ausbilder).length)   sectionsToSave.Ausbilder   = ausbilder;
            const r = await fetch("/save-settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ settings: sectionsToSave }),
            });
            const d = await r.json().catch(() => ({}));
            if (!r.ok || d.status !== "success") {
                throw new Error(d.error || r.statusText);
            }
            // KL-Mail-Felder separat via dediziertem Endpoint (Checkboxen
            // direkt per .checked, damit unchecked auch als False ankommt).
            const cbVal = (id) => !!document.getElementById(id)?.checked;
            const txtVal = (id) => document.getElementById(id)?.value || '';
            const klMailPayload = {
                kl_mail_respect_class_whitelist: cbVal('ausbilder_kl_mail_respect_class_whitelist'),
                kl_mail_respect_blacklist:       cbVal('ausbilder_kl_mail_respect_blacklist'),
                kl_mail_respect_firma_filter:    cbVal('ausbilder_kl_mail_respect_firma_filter'),
                kl_mail_include_stv_kl:          cbVal('ausbilder_kl_mail_include_stv_kl'),
                kl_mail_subject_suffix:          txtVal('ausbilder_kl_mail_subject_suffix').trim(),
            };
            const r2 = await fetch('/api/ausbilder/kl_mail/save_settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(klMailPayload),
            });
            const d2 = await r2.json().catch(() => ({}));
            if (!r2.ok || !d2.success) throw new Error(d2.error || r2.statusText);
            if (typeof showToast === "function") showToast("Ausbilder-Einstellungen gespeichert.");
            setTimeout(loadStudents, 100);
        } catch (e) {
            alert("Fehler beim Speichern: " + e);
        } finally {
            btn.disabled = false;
            btn.textContent = orig;
        }
    });
});
