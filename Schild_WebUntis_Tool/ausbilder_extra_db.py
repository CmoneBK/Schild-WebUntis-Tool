"""
Ausbilder-Zusatz-DB (3.3).

Hintergrund: In Schild duerfen pro Auszubildendem mehrere Betreuer/Ausbilder
hinterlegt werden, der CSV-Export liefert aber pro Schueler-Zeile nur EINEN
(meist den primaeren). Damit fehlen in der WebUntis-Import-CSV die Co-Ausbilder,
obwohl diese in Schild gepflegt sind.

Diese kleine, dateibasierte JSON-DB sammelt deshalb ALLE jemals beobachteten
Schild-Ausbilder pro Schueler (per Schueler-Interner-ID) und laesst sich
zusaetzlich manuell um weitere Ausbilder ergaenzen. Beim Erzeugen der WebUntis-
Import-CSV (filter_and_write in ausbilder_processor.py) wird pro Schueler-Zeile
fuer jeden in der DB gefundenen Co-Ausbilder eine weitere Zeile geschrieben.

Designprinzipien:
  - DB-Datei liegt neben settings.ini im CWD: 'ausbilder_extra.json'.
    Vermeidet Konflikte mit Multi-User-Deployments — jede Tool-Instanz hat
    ihre eigene DB pro Working-Dir (genauso wie settings.ini).
  - Sync ist automatisch beim Schild-Lesen (list_students() ruft sync_from_schild
    auf), manuelle Eintraege bleiben dabei garantiert unangetastet (source-Tag).
  - Schueler-Key: 'Interne ID-Nummer' aus Schild (stabil ueber Exporte).
  - Ausbilder-Match: erst per E-Mail (case-insensitive), dann per Nachname+
    Vorname. Beide Felder leer -> kein Match (Ausbilder wird neu angelegt).

Schema (Version 1):
  {
    "version": 1,
    "students": {
      "<schueler_id>": {
        "first_seen":          "YYYY-MM-DD",
        "last_seen_in_schild": "YYYY-MM-DD",
        "schueler": {"vorname": "...", "nachname": "...", "klasse": "..."},
        "ausbilder": [
          {
            "id":                  "<auto-id>",
            "source":              "schild" | "manual",
            "first_seen":          "YYYY-MM-DD",
            "last_seen_in_schild": "YYYY-MM-DD" | null,
            "anrede":    "...", "titel":     "...", "vorname":  "...",
            "nachname":  "...", "email":     "...", "telefon":  "...",
            "abteilung": "...", "fax":       "..."
          },
          ...
        ]
      }
    }
  }
"""

import os
import json
import uuid
from datetime import datetime


DB_FILENAME = 'ausbilder_extra.json'
CURRENT_VERSION = 1

# Diese Felder beschreiben einen Ausbilder — identisch zu den Schild-CSV-
# Spalten 'Allg. Adresse: Betreuer ...'. Reihenfolge ist Anzeige-Reihenfolge
# in UI + JSON.
AUSBILDER_FIELDS = ('anrede', 'titel', 'vorname', 'nachname',
                    'email', 'telefon', 'abteilung', 'fax')


def _today_iso():
    return datetime.now().strftime('%Y-%m-%d')


def get_db_path():
    """Pfad zur DB-Datei — relativ zum aktuellen Working-Dir, neben
    settings.ini. Wird absichtlich nicht absolut aufgeloest, damit das
    Verhalten konsistent zu allen anderen Settings-Lesern in diesem Tool
    bleibt."""
    return DB_FILENAME


def load_db():
    """Liest die DB. Wenn die Datei fehlt oder kaputt ist, kommt eine leere
    Default-DB zurueck — kein Exception, damit ein neuer Working-Dir bzw.
    eine versehentlich geloeschte Datei das Tool nicht blockiert."""
    path = get_db_path()
    if not os.path.isfile(path):
        return {'version': CURRENT_VERSION, 'students': {}}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {'version': CURRENT_VERSION, 'students': {}}
    if not isinstance(db, dict):
        return {'version': CURRENT_VERSION, 'students': {}}
    db.setdefault('version', CURRENT_VERSION)
    db.setdefault('students', {})
    if not isinstance(db['students'], dict):
        db['students'] = {}
    return db


def save_db(db):
    """Persistiert die DB. UTF-8 ohne BOM (wie wir es bei JSON immer machen),
    pretty-printed damit man die Datei zur Not auch per Texteditor reparieren
    kann (sehr kleine Datei, paar tausend Schueler max)."""
    path = get_db_path()
    db = db or {'version': CURRENT_VERSION, 'students': {}}
    db['version'] = CURRENT_VERSION
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Match-Heuristik
# ---------------------------------------------------------------------------

def _norm(s):
    return (s or '').strip().lower()


def _ausbilder_signature(a):
    """Liefert (email_lower, name_key) — zwei einfache Match-Schluessel.
    Leere Strings werden nicht gematcht (sonst wuerde jedes leere Feld auf
    jedes leere Feld treffen)."""
    email = _norm(a.get('email'))
    name_key = (_norm(a.get('nachname')), _norm(a.get('vorname')))
    if not name_key[0] and not name_key[1]:
        name_key = None
    return email, name_key


def _find_match(existing_list, candidate):
    """Sucht in existing_list nach einem Ausbilder, der zu candidate passt.
    Reihenfolge: E-Mail-Match schlaegt Namens-Match (E-Mail ist eindeutiger).
    Gibt den Index zurueck oder None."""
    cand_email, cand_name = _ausbilder_signature(candidate)
    if cand_email:
        for i, a in enumerate(existing_list):
            ex_email, _ = _ausbilder_signature(a)
            if ex_email and ex_email == cand_email:
                return i
    if cand_name:
        for i, a in enumerate(existing_list):
            _, ex_name = _ausbilder_signature(a)
            if ex_name and ex_name == cand_name:
                return i
    return None


def _ausbilder_is_empty(a):
    """True, wenn der Ausbilder-Datensatz ueberhaupt keine identifizierende
    Information enthaelt (alle Pflichtfelder leer). Solche werden aus dem
    Schild-Sync ausgefiltert, sonst wuerde jede Schueler-Zeile ohne Betreuer
    einen Geister-Eintrag erzeugen."""
    return not any(_norm(a.get(k)) for k in AUSBILDER_FIELDS)


# ---------------------------------------------------------------------------
# Sync vom Schild-Export
# ---------------------------------------------------------------------------

def sync_from_schild(students_with_ausbilder):
    """Wird einmal pro Schild-Read aufgerufen. Updated die DB:
      - Pro Schueler aus Schild: Schueler-Eintrag anlegen/updaten.
      - Pro Schueler: Schild-Betreuer (1 pro Zeile in der CSV) mit den
        bestehenden Ausbildern matchen. Match -> last_seen_in_schild + Felder
        refreshen (Schild ist primaere Wahrheitsquelle fuer source=schild).
        Kein Match -> neuen Ausbilder mit source='schild' anlegen.
      - Manuell hinzugefuegte Ausbilder (source='manual') werden NIE aus dem
        Schild-Sync ueberschrieben oder geloescht — der Sync laesst sie in
        Ruhe.

    students_with_ausbilder kommt von list_students() in ausbilder_processor.py
    und hat die Form:
        [{'id': '...', 'vorname': '...', 'nachname': '...', 'klasse': '...',
          'ausbilder': {anrede, titel, vorname, nachname, email, telefon,
                        abteilung, fax}}, ...]

    Returns: Statistik-Dict {'students_seen': n, 'ausbilder_added': n,
                             'ausbilder_updated': n}
    """
    db = load_db()
    today = _today_iso()
    stats = {'students_seen': 0, 'ausbilder_added': 0, 'ausbilder_updated': 0}

    for s in students_with_ausbilder:
        sid = (s.get('id') or '').strip()
        if not sid:
            continue
        stats['students_seen'] += 1

        student_entry = db['students'].setdefault(sid, {
            'first_seen': today,
            'last_seen_in_schild': today,
            'schueler': {},
            'ausbilder': [],
        })
        student_entry['last_seen_in_schild'] = today
        # Aktuelle Schueler-Metadaten — koennen sich aendern (Klasse vor allem)
        student_entry['schueler'] = {
            'vorname':  (s.get('vorname') or '').strip(),
            'nachname': (s.get('nachname') or '').strip(),
            'klasse':   (s.get('klasse') or '').strip(),
        }

        # Schild-Ausbilder normalisieren (nur die acht Felder, in unserer
        # Reihenfolge).
        schild_a = s.get('ausbilder') or {}
        cand = {k: (schild_a.get(k) or '').strip() for k in AUSBILDER_FIELDS}
        if _ausbilder_is_empty(cand):
            # Schueler hat keinen Betreuer im aktuellen Export — manuelle und
            # ggf. fruehere Schild-Eintraege bleiben in der DB unangetastet.
            continue

        existing = student_entry['ausbilder']
        idx = _find_match(existing, cand)
        if idx is None:
            new_entry = {
                'id': uuid.uuid4().hex,
                'source': 'schild',
                'first_seen': today,
                'last_seen_in_schild': today,
                **cand,
            }
            existing.append(new_entry)
            stats['ausbilder_added'] += 1
        else:
            target = existing[idx]
            # source='manual' -> NICHT mit Schild-Daten ueberschreiben (User-
            # Vorrang). last_seen_in_schild tracken wir trotzdem, damit das UI
            # zeigen kann "auch in Schild aktuell vorhanden".
            target['last_seen_in_schild'] = today
            if target.get('source') == 'schild':
                # Felder von Schild auffrischen. first_seen NICHT ueberschreiben.
                for k in AUSBILDER_FIELDS:
                    if cand[k] != (target.get(k) or ''):
                        target[k] = cand[k]
            stats['ausbilder_updated'] += 1

    save_db(db)
    return stats


# ---------------------------------------------------------------------------
# Read / Mutations fuer UI + Export
# ---------------------------------------------------------------------------

def get_student_entry(sid):
    """Liefert den DB-Eintrag fuer einen Schueler oder None."""
    db = load_db()
    return db['students'].get((sid or '').strip())


def list_all_students_with_extras():
    """Liefert alle Schueler aus der DB als Liste — fuer die UI-Tabelle.
    Sortiert nach Klasse, Nachname, Vorname (so wie list_students)."""
    db = load_db()
    out = []
    for sid, entry in db['students'].items():
        s = entry.get('schueler') or {}
        out.append({
            'id':       sid,
            'vorname':  s.get('vorname', ''),
            'nachname': s.get('nachname', ''),
            'klasse':   s.get('klasse', ''),
            'first_seen':          entry.get('first_seen'),
            'last_seen_in_schild': entry.get('last_seen_in_schild'),
            'ausbilder_count':         len(entry.get('ausbilder') or []),
            'ausbilder_manual_count':  sum(1 for a in (entry.get('ausbilder') or [])
                                            if a.get('source') == 'manual'),
            'ausbilder_schild_count':  sum(1 for a in (entry.get('ausbilder') or [])
                                            if a.get('source') == 'schild'),
        })
    out.sort(key=lambda x: (x['klasse'], x['nachname'], x['vorname']))
    return out


def add_manual_ausbilder(sid, data, schueler_meta=None):
    """Fuegt einen manuell gepflegten Ausbilder hinzu. data muss mind. ein
    nicht-leeres Identifikations-Feld (nachname/vorname/email) enthalten.

    schueler_meta (optional) ist ein Dict mit vorname/nachname/klasse —
    wird nur dann gesetzt, wenn der Schueler noch nicht in der DB ist (z.B.
    Pflege fuer einen Schueler, der gerade nicht im Schild-Export liegt).

    Wirft ValueError bei leerem Datensatz.
    Returns: der neu angelegte Ausbilder-Eintrag (mit id).
    """
    sid = (sid or '').strip()
    if not sid:
        raise ValueError('Schueler-ID fehlt.')

    clean = {k: ((data or {}).get(k) or '').strip() for k in AUSBILDER_FIELDS}
    if _ausbilder_is_empty(clean):
        raise ValueError('Mindestens ein identifizierendes Feld noetig.')

    db = load_db()
    today = _today_iso()
    student_entry = db['students'].setdefault(sid, {
        'first_seen': today,
        'last_seen_in_schild': None,
        'schueler': {},
        'ausbilder': [],
    })
    if schueler_meta and not student_entry['schueler']:
        student_entry['schueler'] = {
            'vorname':  (schueler_meta.get('vorname')  or '').strip(),
            'nachname': (schueler_meta.get('nachname') or '').strip(),
            'klasse':   (schueler_meta.get('klasse')   or '').strip(),
        }

    new_entry = {
        'id': uuid.uuid4().hex,
        'source': 'manual',
        'first_seen': today,
        'last_seen_in_schild': None,
        **clean,
    }
    student_entry['ausbilder'].append(new_entry)
    save_db(db)
    return new_entry


def update_ausbilder(sid, ausbilder_id, data):
    """Aktualisiert die Felder eines Ausbilders. source und first_seen bleiben
    unveraendert. last_seen_in_schild wird nicht angefasst (das macht nur der
    Sync). Wirft KeyError, wenn der Eintrag nicht existiert. ValueError, wenn
    nach dem Update alle Felder leer waeren."""
    sid = (sid or '').strip()
    db = load_db()
    student_entry = db['students'].get(sid)
    if not student_entry:
        raise KeyError(f'Schueler {sid} nicht in DB.')
    for a in student_entry['ausbilder']:
        if a['id'] == ausbilder_id:
            updated = {k: ((data or {}).get(k) or '').strip()
                       for k in AUSBILDER_FIELDS}
            if _ausbilder_is_empty(updated):
                raise ValueError('Mindestens ein identifizierendes Feld noetig.')
            for k in AUSBILDER_FIELDS:
                a[k] = updated[k]
            save_db(db)
            return a
    raise KeyError(f'Ausbilder {ausbilder_id} nicht in Schueler {sid}.')


def delete_ausbilder(sid, ausbilder_id):
    """Loescht einen Ausbilder. Funktioniert fuer beide source-Typen — wenn der
    User einen alten Schild-Eintrag explizit raus haben moechte (z.B. weil der
    Ausbilder nicht mehr zustaendig ist), kann er das aktiv tun. Beim naechsten
    Schild-Sync taucht er nur wieder auf, wenn er im aktuellen Schild-Export
    noch enthalten ist."""
    sid = (sid or '').strip()
    db = load_db()
    student_entry = db['students'].get(sid)
    if not student_entry:
        raise KeyError(f'Schueler {sid} nicht in DB.')
    for i, a in enumerate(student_entry['ausbilder']):
        if a['id'] == ausbilder_id:
            student_entry['ausbilder'].pop(i)
            save_db(db)
            return
    raise KeyError(f'Ausbilder {ausbilder_id} nicht in Schueler {sid}.')


# ---------------------------------------------------------------------------
# Aggregation: alle jemals gesehenen Ausbilder (fuer Quick-Pick + Autocomplete)
# ---------------------------------------------------------------------------

def list_all_known_ausbilder(klasse_filter=None, exclude_sid=None):
    """Liefert eine deduplizierte Liste aller jemals beobachteten Ausbilder
    aus der DB, jeweils mit Kontext (in welchen Schuelern + Klassen er
    vorkommt). Eingesetzt fuer:
      - Quickpick aus derselben Klasse beim manuellen Hinzufuegen.
      - Globale Autocomplete im Formular.

    Args:
        klasse_filter (str|None): nur Ausbilder, die mindestens bei einem
            Schueler dieser Klasse vorkommen.
        exclude_sid (str|None): Ausbilder, die bereits diesem Schueler
            zugeordnet sind, ausschliessen (z.B. der aktuell editierte
            Schueler im Modal — vermeidet 'Duplikate vorschlagen').

    Returns: Liste sortiert nach (nachname, vorname, email):
        [{anrede, titel, vorname, nachname, email, telefon, abteilung, fax,
          klassen: [...], schueler: [{id, name}], occurrences: n,
          schild_count: n, manual_count: n}, ...]
    """
    db = load_db()
    exclude_sid = (exclude_sid or '').strip() or None
    klasse_filter = (klasse_filter or '').strip() or None

    # Erst alle relevanten Schueler-Eintraege durchgehen und (Match-Key ->
    # aggregierter Eintrag)-Dict aufbauen. Match-Key = E-Mail (lower) bevor-
    # zugt, sonst (nachname_lower, vorname_lower). Verschiedene Ausbilder
    # mit gleichem Namen aber unterschiedlicher E-Mail bleiben getrennt.
    aggregated = {}
    for sid, entry in db['students'].items():
        sch = entry.get('schueler') or {}
        klasse = (sch.get('klasse') or '').strip()
        for a in entry.get('ausbilder') or []:
            email = _norm(a.get('email'))
            if email:
                key = ('email', email)
            else:
                key = ('name', _norm(a.get('nachname')), _norm(a.get('vorname')))
                if key == ('name', '', ''):
                    continue  # ohne identifizierende Info ueberspringen
            agg = aggregated.get(key)
            if agg is None:
                agg = {
                    'anrede':    a.get('anrede', '') or '',
                    'titel':     a.get('titel', '') or '',
                    'vorname':   a.get('vorname', '') or '',
                    'nachname':  a.get('nachname', '') or '',
                    'email':     a.get('email', '') or '',
                    'telefon':   a.get('telefon', '') or '',
                    'abteilung': a.get('abteilung', '') or '',
                    'fax':       a.get('fax', '') or '',
                    'klassen':       set(),
                    'schueler':      [],   # [(sid, name)]
                    'occurrences':   0,
                    'schild_count':  0,
                    'manual_count':  0,
                }
                aggregated[key] = agg
            else:
                # Bei Mehrfachvorkommen das vollstaendigste Feld behalten —
                # fuellt Luecken aus anderen Eintraegen auf.
                for f in AUSBILDER_FIELDS:
                    if not (agg.get(f) or '').strip() and (a.get(f) or '').strip():
                        agg[f] = a[f]
            if klasse:
                agg['klassen'].add(klasse)
            schueler_name = ', '.join(p for p in (
                (sch.get('nachname') or '').strip(),
                (sch.get('vorname')  or '').strip()) if p)
            agg['schueler'].append({'id': sid, 'name': schueler_name, 'klasse': klasse})
            agg['occurrences'] += 1
            if a.get('source') == 'manual':
                agg['manual_count'] += 1
            else:
                agg['schild_count'] += 1

    # Filter anwenden + serialisieren
    result = []
    for agg in aggregated.values():
        if klasse_filter and klasse_filter not in agg['klassen']:
            continue
        if exclude_sid and any(s['id'] == exclude_sid for s in agg['schueler']):
            continue
        result.append({
            **{f: agg[f] for f in AUSBILDER_FIELDS},
            'klassen':      sorted(agg['klassen']),
            'schueler':     agg['schueler'],
            'occurrences':  agg['occurrences'],
            'schild_count': agg['schild_count'],
            'manual_count': agg['manual_count'],
        })
    result.sort(key=lambda x: (
        (x.get('nachname') or '').lower(),
        (x.get('vorname')  or '').lower(),
        (x.get('email')    or '').lower()))
    return result


# ---------------------------------------------------------------------------
# Helper fuer den WebUntis-Export
# ---------------------------------------------------------------------------

def extra_ausbilder_for_export(sid, current_schild_ausbilder):
    """Liefert die Liste der Ausbilder, die ZUSAETZLICH zum aktuellen Schild-
    Betreuer in die WebUntis-Import-CSV geschrieben werden sollen.

    Heuristik: alle DB-Ausbilder des Schuelers, die nicht mit dem aktuellen
    Schild-Betreuer matchen (per _find_match). Damit:
      - der primaere Schild-Betreuer landet wie bisher in seiner Zeile,
      - jeder zusaetzliche Ausbilder (manuell ODER aus alten Schild-Exports
        archiviert) bekommt eine eigene Zeile.

    current_schild_ausbilder darf None/leer sein (Schueler ohne Betreuer im
    aktuellen Export) — dann werden ALLE DB-Ausbilder zurueckgegeben.
    """
    entry = get_student_entry(sid)
    if not entry:
        return []
    extras = list(entry.get('ausbilder') or [])
    if current_schild_ausbilder and not _ausbilder_is_empty(current_schild_ausbilder):
        cand = {k: (current_schild_ausbilder.get(k) or '').strip()
                for k in AUSBILDER_FIELDS}
        idx = _find_match(extras, cand)
        if idx is not None:
            extras.pop(idx)
    return extras
