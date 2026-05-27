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
            // Trenne nach Section: Directories vs. [Ausbilder] (firma_filter_mode)
            const directories = {};
            const ausbilder = {};
            new FormData(form).forEach((value, key) => {
                if (key === 'firma_filter_mode') ausbilder[key] = value;
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
