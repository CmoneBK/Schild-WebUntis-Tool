"""
Erzieher-/Ansprechpartner-Verarbeitung (Phase 2).

Portiert die Logik des Standalone-Tools "SchildNRW-WebUntis Erzieher-Konvertierer"
ohne Pandas-Abhängigkeit (kleinere EXE, weniger Bloat).

Idee:
  - Schild exportiert Erzieher (Hauptdaten) und Ansprechpartner (separate Datei
    mit Telefonnummern) getrennt.
  - Wir bauen pro „n-tem Erzieher" eines Schülers eine eigene Import-Datei
    (Erzieher_1.csv, Erzieher_2.csv, …) und packen alle in ein ZIP.

WebUntis-Realitaet (Stand: Mai 2026):
  Der WebUntis-Erzieher-Import wertet derzeit nur Schueler-ID, Vorname, Nachname,
  E-Mail und (optional) Eltern-ID aus. Anrede, Briefanrede, Titel, Anschluss-Art,
  Bemerkung, Telefon-Nummer werden mit-exportiert, damit der Import nicht
  angepasst werden muss, falls WebUntis seine Verarbeitung erweitert.

  Die Telefon-Verarbeitungsoptionen (Smart-Match, phone_from_erz_first,
  lift_limit) halten die Daten-Aufbereitung trotzdem sauber — fuer die Tool-
  interne Vorschau, den Klassen-Report und einen moeglichen WebUntis-Upgrade.

Datenquellen-Strategie (welche Spalte kommt woher?):
  Beide Schild-Quellen (Erzieher- und Ansprechpartner-Export) koennen ueberlappende
  Daten enthalten. Das Tool kombiniert sie nach folgenden Regeln:

  - Erzieher-Stammdaten (Erzieher i: Vorname/Nachname/E-Mail): PFLICHT aus dem
    Erzieher-Export. Fehlt eines dieser Felder, crasht process() mit ValueError.

  - Schueler-Stammdaten (Klasse / Vorname / Nachname): PRIMAER aus dem Anspr-
    Export (Spalten 'Schueler-...'). FALLBACK aus dem Erzieher-Export, sofern die
    Schule die Spalten dort mit aufgenommen hat (mehrere Spaltennamen-Varianten
    werden erkannt — siehe _STUDENT_*_COLS). Merge: Anspr gewinnt pro Schueler,
    Erzieher fuellt einzelne Leerstellen. Siehe _merge_student_lookups().

  - Volljaehrigkeits-Erkennung: PRIMAER ueber Geburtsdatum aus dem Erzieher-Export
    (Spalten-Varianten in _GEBURTSDATUM_COLS, akzeptiert TT.MM.JJJJ und ISO).
    ZUSAETZLICH (ODER-verknuepft) ueber die Heuristik 'Erzieher: Art (Klartext)'
    enthaelt 'volljaehrig' — diese deckt Sonderfaelle ab, in denen ein Schueler
    ausdruecklich auf Erziehungsberechtigte verzichtet hat (Self-Ansprech-
    partner-Markierung), und greift als Fallback bei fehlendem Geburtsdatum.
    Siehe _is_self_volljaehrig().

  - Telefonnummern: PRIMAER die im Erzieher-Export hinterlegte primaere Nummer
    (Spaltengruppe 'Telefon-Nummern: ...') als Pseudo-Anspr-Zeile, SEKUNDAER die
    Zeilen aus dem Anspr-Export. Duplikate (gleiche Nummer normalisiert) aus dem
    Anspr-Export werden gefiltert. Siehe _merge_phone_sources(). Optional ueber
    Setting phone_from_erz_first deaktivierbar.

  Empfehlung an die Schule: All-in-One-Erzieher-Vorlage (Klasse + Geburtsdatum
  zusaetzlich zu Erzieher-Daten). Damit ist der Anspr-Export rein optional und
  alle Tool-Features (UI-Anzeige, Klassen-Report, deterministischer Vollj.-Check)
  funktionieren vollstaendig. Die Status-Box im Frontend zeigt per Badge an,
  welches Setup erkannt wurde (siehe _inspect_erz_source()).

Filter-Optionen im Ueberblick (alle persistent in [Erzieher]-Section):
  Schueler-Auswahl (greift VOR der Verarbeitung):
    - class_filter         — Klassen-Whitelist analog Ausbilder: Liste oder
                             ['__NONE__'] Sentinel; leer = alle Klassen.
                             Spiegelt UI-Chip-Auswahl. Siehe _resolve_class_filter()
                             und _student_passes_class().
    - filter_volljaehrig   — Schueler ueber _is_self_volljaehrig() rauswerfen.

  Erzieher-Slot-Auswahl (greift beim Zusammenbau der Output-CSVs):
    - require_email        — Slots ohne E-Mail ueberspringen.
    - fill_dummies         — Leere Felder mit DUMMY-Werten fuellen (siehe
                             DUMMY_VALUES).

  Telefon/Slot-Mapping:
    - smart_match          — Anschluss-Art-basiertes Slot-Mapping (siehe
                             _smart_match_student()).
    - phone_from_erz_first — Erzieher-interne Telefonnummer als prioritaere
                             Pseudo-Anspr-Zeile (siehe _erz_phone_pseudo()
                             und _merge_phone_sources()).
    - lift_limit           — Ueberzaehlige Telefon-Zeilen werden zu virtuellen
                             Erzieher_3/_4/...-Slots statt zu Orphans
                             (Phase 3 in _smart_match_student()).

  Output-Erweiterung:
    - assign_eltern_ids    — Persistente schulweite Eltern-IDs via
                             eltern_id_manager (Vorname+Nachname+E-Mail als Key).
"""

import os
import io
import re
import csv
import zipfile
import configparser
from datetime import datetime, date


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

DEFAULT_ZIP_NAME_TEMPLATE = 'Erzieher_Import_{datum}'

# Erzieher-spezifische Spalten im Erzieher-Export (i = Erzieher-Nummer)
ERZIEHER_FIELDS = ['Anrede', 'Briefanrede', 'Titel', 'Nachname', 'Vorname', 'E-Mail']

# Ansprechpartner-spezifische Felder, die wir pro Erzieher mit aufnehmen
ANSPRECHPARTNER_FIELD_MAP = {
    'Anschluss-Art':  'Anschluss Art',
    'Bemerkung':      'Bemerkung',
    'Telefon-Nummer': 'Telefon-Nummer',
}

# Spalten der "primaeren" Telefonnummer im Erzieher-Export (eine pro Schueler)
ERZ_PHONE_COLS = {
    'Anschluss-Art':  'Telefon-Nummern: Anschluss-Art',
    'Bemerkung':      'Telefon-Nummern: Bemerkung',
    'Telefon-Nummer': 'Telefon-Nummern: Telefon-Nummer',
}

# ---------------------------------------------------------------------------
# Smart-Match: Anschluss-Art -> Geschlecht/Rolle (zur Zuordnung an Erzieher i)
# ---------------------------------------------------------------------------
# Werte basieren auf einer Analyse von >2000 echten Schild-Ansprechpartner-
# Zeilen: Mutter/Vater + Varianten sind die haeufigsten typisierten Werte.

_ANSCHLUSS_FEMININ = {
    'mutter', 'mama', 'mami',
    'handy mutter', 'arbeit mutter',
    'oma', 'oma handy', 'großmutter', 'grossmutter',
    'schwester', 'tante', 'pflegemutter',
}
_ANSCHLUSS_MASKULIN = {
    'vater', 'papa', 'papi',
    'handy vater', 'arbeit vater',
    'opa', 'großvater', 'grossvater',
    'bruder', 'onkel', 'pflegevater',
}
# Alle anderen Werte (Eltern, Notfallnummer, Vormund, Pflegeeltern, Ehepartner(in),
# sonstiges, ...) bleiben "neutral" und werden nach Position zugeordnet.


def _gender_from_anschluss(art):
    """Liefert 'w' / 'm' / None aus dem Anschluss-Art-Feld."""
    a = (art or '').strip().lower()
    if a in _ANSCHLUSS_FEMININ:  return 'w'
    if a in _ANSCHLUSS_MASKULIN: return 'm'
    return None


def _gender_from_anrede(anrede):
    """Liefert 'w' / 'm' / None aus dem Anrede-Feld des Erziehers."""
    a = (anrede or '').strip().lower()
    if a in ('frau', 'fr.', 'fr'):  return 'w'
    if a in ('herr', 'hr.', 'hr'):  return 'm'
    return None


def safe_read_config(config, path):
    try:
        config.read(path, encoding='utf-8-sig')
        return True
    except Exception:
        return False


def get_erzieher_export_dir():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'erzieher_export_directory', fallback='ErzieherExport').strip() or 'ErzieherExport'


def get_ansprechpartner_export_dir():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'ansprechpartner_export_directory', fallback='AnsprechpartnerExport').strip() or 'AnsprechpartnerExport'


def get_output_dir():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'erzieher_output_directory', fallback='ErzieherImporte').strip() or 'ErzieherImporte'


def get_zip_name_template():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Erzieher', 'zip_name_template', fallback=DEFAULT_ZIP_NAME_TEMPLATE).strip() or DEFAULT_ZIP_NAME_TEMPLATE


def save_zip_name_template(template):
    template = (template or '').strip()
    if not template:
        return
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    config.set('Erzieher', 'zip_name_template', template)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_smart_match():
    """True = Telefonnummern werden per Anschluss-Art an Erzieher gemappt
    (Mutter -> Frau-Erzieher, Vater -> Herr-Erzieher); Output enthaelt nur
    so viele Erzieher-CSVs wie der Erzieher-Export Slots hergibt.
    False = altes Verhalten: positional, kann "Geister-Erzieher" mit leeren
    Stammdaten erzeugen, wenn mehr Anspr-Zeilen als Erzieher existieren.

    Hinweis: WebUntis wertet die Telefon-Spalte aktuell nicht aus — die
    Smart-Match-Zuordnung ist primaer fuer Tool-interne Vorschau und Daten-
    Hygiene relevant (falls WebUntis Telefon spaeter unterstuetzt)."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'smart_match', fallback=True)


def save_smart_match(value):
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    config.set('Erzieher', 'smart_match', 'True' if value else 'False')
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_filter_volljaehrig():
    """True = Schueler, deren Erzieher-Art (Klartext) 'volljaehrig' enthaelt,
    werden komplett aus dem Erzieher-Export herausgefiltert (kein
    sinnvoller Erzieher-Datensatz fuer self-Ansprechpartner)."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'filter_volljaehrig', fallback=False)


def save_filter_volljaehrig(value):
    _set_erz_bool('filter_volljaehrig', value)


def get_require_email():
    """True = Erzieher ohne E-Mail-Adresse werden nicht exportiert
    (sie koennen sich in WebUntis ohnehin nicht anmelden)."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'require_email', fallback=False)


def save_require_email(value):
    _set_erz_bool('require_email', value)


def get_fill_dummies():
    """True = leere Erzieher-Felder werden mit eindeutig erkennbaren Dummy-
    Werten (DUMMY / dummy@invalid.local / 000) gefuellt, damit WebUntis nicht
    auf Pflichtfeldern stolpert und Dummies nachtraeglich gefiltert werden
    koennen."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'fill_dummies', fallback=False)


def save_fill_dummies(value):
    _set_erz_bool('fill_dummies', value)


def get_assign_eltern_ids():
    """True = jedem Erzieher wird eine schulweit eindeutige Eltern-ID zugewiesen
    (persistent in eltern_ids.json), damit WebUntis denselben Erzieher ueber
    Geschwister hinweg als denselben Account erkennt."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'assign_eltern_ids', fallback=False)


def save_assign_eltern_ids(value):
    _set_erz_bool('assign_eltern_ids', value)


def get_phone_from_erz_first():
    """True = die im Erzieher-Export hinterlegte primaere Telefonnummer
    (Spaltengruppe 'Telefon-Nummern: ...') wird als ZUSAETZLICHE erste
    Anspr-Pseudozeile pro Schueler behandelt — bekommt damit Vorrang beim
    Slot-Mapping. Duplikate gegenueber dem Anspr-Export werden gefiltert."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'phone_from_erz_first', fallback=True)


def save_phone_from_erz_first(value):
    _set_erz_bool('phone_from_erz_first', value)


def get_class_filter():
    """Klassen-Whitelist analog Ausbilder. Liefert Liste der zu beruecksichtigenden
    Klassen (leer = alle). Sentinel '__NONE__' = explizit keine Klasse aktiv
    (Default ist 'leer = alle', deshalb braucht's den Marker, um 'explizit
    nichts' von 'noch nicht konfiguriert' zu unterscheiden)."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    raw = config.get('Erzieher', 'class_filter', fallback='').strip()
    if not raw:
        return []
    return [c.strip() for c in raw.split(',') if c.strip()]


def save_class_filter(classes):
    """Speichert die Klassen-Whitelist (Liste[str])."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    cleaned = [str(c).strip() for c in (classes or []) if str(c).strip()]
    config.set('Erzieher', 'class_filter', ','.join(cleaned))
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def _resolve_class_filter(class_filter):
    """Normalisiert die Whitelist in (mode, set_of_classes):
       mode='all'  -> Set ist leer und ignoriert; alle Klassen durch
       mode='none' -> keine Klasse durch (Sentinel __NONE__)
       mode='set'  -> nur die Klassen aus dem Set durch
    """
    cf = list(class_filter or [])
    if not cf:
        return ('all', set())
    if '__NONE__' in cf:
        return ('none', set())
    return ('set', {c.strip() for c in cf if c.strip()})


def _student_passes_class(stamm, mode, klassen_set):
    """Spiegelt die Backend-Filter-Logik aus filter_and_write() (Ausbilder):
    mode='all'  -> True
    mode='none' -> False
    mode='set'  -> Klasse muss im Set sein (Schueler ohne Klasse faellt raus)
    """
    if mode == 'all':  return True
    if mode == 'none': return False
    klasse = (stamm or {}).get('klasse', '') or ''
    return klasse.strip() in klassen_set


def get_lift_limit():
    """True = Anzahl Erzieher pro Schueler ist nicht mehr auf die Slots im
    Schild-Erzieher-Export begrenzt. Ueberzaehlige Ansprechpartner-Telefonzeilen
    werden zu zusaetzlichen Erzieher_N.csv-Slots (Stammdaten ggf. Dummy)."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'lift_limit', fallback=False)


def save_lift_limit(value):
    _set_erz_bool('lift_limit', value)


def _set_erz_bool(key, value):
    """Helper: bool in [Erzieher] speichern (idempotent, legt Section ggf. an)."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    config.set('Erzieher', key, 'True' if value else 'False')
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


# Spaltennamen-Varianten fuer Geburtsdatum im Erzieher-Export
_GEBURTSDATUM_COLS = ('Geburtsdatum', 'Schüler-Geburtsdatum', 'Schüler: Geburtsdatum')


def _calc_age_from_str(geb_str, today=None):
    """Liefert Alter (int) zum Stichtag (Default: heute), oder None wenn das
    Geburtsdatum nicht parsbar ist. Akzeptiert TT.MM.JJJJ (Schild-Standard)
    sowie ISO YYYY-MM-DD als Fallback."""
    if not geb_str:
        return None
    today = today or date.today()
    for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
        try:
            geb = datetime.strptime(geb_str.strip(), fmt).date()
            return today.year - geb.year - ((today.month, today.day) < (geb.month, geb.day))
        except (ValueError, TypeError):
            continue
    return None


def _is_self_volljaehrig(erz_row):
    """True wenn der Schueler als volljaehrig gilt. Nutzt zwei Quellen:
    1. PRIMAER: Geburtsdatum aus dem Erzieher-Export (deterministisch — wenn
       die Schild-Vorlage 'Geburtsdatum' mit-exportiert; ≥ 18 = volljaehrig).
    2. ZUSAETZLICH/Fallback: Schild-Heuristik via 'Erzieher: Art (Klartext)'
       enthaelt 'volljaehrig' — deckt Sonderfaelle ab, in denen ein Schueler
       ausdruecklich auf Erziehungsberechtigte verzichtet hat (Self-
       Ansprechpartner-Markierung), und greift, wenn kein Geburtsdatum
       verfuegbar ist.
    """
    # 1) Geburtsdatum-basiert
    age = None
    for col in _GEBURTSDATUM_COLS:
        geb_str = (erz_row.get(col, '') or '').strip()
        if geb_str:
            age = _calc_age_from_str(geb_str)
            break
    if age is not None and age >= 18:
        return True
    # 2) Schild-Heuristik (Fallback + Sonderfall-Override)
    art = (erz_row.get('Erzieher: Art (Klartext)', '') or '').lower()
    return 'volljährig' in art or 'volljaehrig' in art


# ---------------------------------------------------------------------------
# Dummy-Fuellwerte (eindeutig erkennbar — leicht in WebUntis filterbar)
# ---------------------------------------------------------------------------
DUMMY_VALUES = {
    'Anrede':         '',
    'Briefanrede':    'DUMMY',
    'Titel':          '',
    'Nachname':       'DUMMY',
    'Vorname':        'DUMMY',
    'E-Mail':         'dummy@invalid.local',
    'Anschluss Art':  'DUMMY',
    'Bemerkung':      'DUMMY (automatisch ergaenzt)',
    'Telefon-Nummer': '000',
}


def _normalize_phone(num):
    """Normalisiert eine Telefonnummer fuer Duplikat-Erkennung — alle Nicht-
    Ziffern entfernen, fuehrende Nullen / +49 vereinheitlichen ist OPTIONAL und
    macht zu viele falsch-positive Treffer; daher nur Leerzeichen/Trenner weg."""
    return re.sub(r'[^0-9+]', '', (num or '').strip())


def _erz_phone_pseudo(erz_row):
    """Liefert eine Pseudo-Anspr-Zeile aus den 'Telefon-Nummern: ...'-Spalten
    des Erzieher-Exports — oder None, wenn keine Telefonnummer gepflegt ist."""
    nr = (erz_row.get(ERZ_PHONE_COLS['Telefon-Nummer'], '') or '').strip()
    if not nr:
        return None
    return {
        'Anschluss-Art':  (erz_row.get(ERZ_PHONE_COLS['Anschluss-Art'],  '') or '').strip(),
        'Bemerkung':      (erz_row.get(ERZ_PHONE_COLS['Bemerkung'],      '') or '').strip(),
        'Telefon-Nummer': nr,
        '_from_erz':      True,   # Marker fuer Stats / UI
    }


def _merge_phone_sources(erz_phone, anspr_list):
    """Fuegt die Erzieher-Export-Pseudozeile als ERSTES Element in die Liste
    ein und entfernt Duplikate (gleiche normalisierte Nummer) — die aus dem
    Erzieher-Export hat Vorrang, Duplikate aus dem Anspr-Export werden
    geloescht."""
    if not erz_phone:
        return list(anspr_list)
    key = _normalize_phone(erz_phone['Telefon-Nummer'])
    deduped = [a for a in anspr_list
               if _normalize_phone(a.get('Telefon-Nummer', '')) != key]
    return [erz_phone] + deduped


def _apply_dummies(row_out, i):
    """Fuellt leere Werte in einer Output-Zeile mit Dummy-Werten. Mutates+returns."""
    for col in list(row_out.keys()):
        if col == 'Interne_ID_Nummer':
            continue
        if row_out[col]:
            continue
        prefix = f'Erzieher {i}: '
        if not col.startswith(prefix):
            continue
        short = col[len(prefix):]
        if short in DUMMY_VALUES:
            row_out[col] = DUMMY_VALUES[short]
    return row_out


def _smart_match_student(erz_row, anspr_list, max_slots, lift_limit=False):
    """Ordnet Anspr-Zeilen den i-ten Erzieher-Slots zu — primaer per
    Anschluss-Art-Gender, Fallback per Position fuer neutrale / unklare Faelle.

    Wenn lift_limit=True werden uebrig gebliebene Anspr-Zeilen auf virtuelle
    Slots oberhalb von max_slots verteilt (statt zu Orphans zu werden).

    Returns:
        assigned: {erz_idx (1..N): anspr_dict}
        stats:    {'gender': N, 'positional': N, 'virtual': N, 'orphan_anspr': N, 'orphan_erz': N}
    """
    # Echte Erzieher-Slots (gefuellt) ermitteln
    erz_slots = []  # [(idx, gender_or_None)]
    for i in range(1, max_slots + 1):
        vor  = (erz_row.get(f'Erzieher {i}: Vorname',  '') or '').strip()
        nach = (erz_row.get(f'Erzieher {i}: Nachname', '') or '').strip()
        if not (vor or nach):
            continue
        erz_slots.append((i, _gender_from_anrede(erz_row.get(f'Erzieher {i}: Anrede', ''))))

    assigned = {}
    used = set()
    stats = {'gender': 0, 'positional': 0, 'virtual': 0, 'orphan_anspr': 0, 'orphan_erz': 0}

    # Phase 1: Anspr mit klarem Gender auf passenden Erzieher legen
    for j, anspr in enumerate(anspr_list):
        ag = _gender_from_anschluss(anspr.get('Anschluss-Art', ''))
        if ag is None:
            continue
        for idx, eg in erz_slots:
            if idx in assigned or eg != ag:
                continue
            assigned[idx] = anspr
            used.add(j)
            stats['gender'] += 1
            break

    # Phase 2: alle uebrigen Anspr-Zeilen positional auf freie Slots
    for j, anspr in enumerate(anspr_list):
        if j in used:
            continue
        for idx, _eg in erz_slots:
            if idx in assigned:
                continue
            assigned[idx] = anspr
            used.add(j)
            stats['positional'] += 1
            break

    # Phase 3 (optional): Rest auf virtuelle Slots oberhalb des Schild-Headers
    if lift_limit:
        used_idx = max((idx for idx, _ in erz_slots), default=0)
        next_slot = max(max_slots, used_idx) + 1
        for j, anspr in enumerate(anspr_list):
            if j in used:
                continue
            assigned[next_slot] = anspr
            used.add(j)
            stats['virtual'] += 1
            next_slot += 1

    stats['orphan_anspr'] = len(anspr_list) - len(used)
    stats['orphan_erz']   = sum(1 for idx, _ in erz_slots if idx not in assigned)
    return assigned, stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_zip_name(template):
    """Ersetzt Platzhalter im ZIP-Namen-Template."""
    now = datetime.now()
    repl = {
        'datum':    now.strftime('%Y-%m-%d'),
        'date':     now.strftime('%Y-%m-%d'),
        'datetime': now.strftime('%Y-%m-%d_%H-%M-%S'),
        'zeit':     now.strftime('%H-%M-%S'),
        'jahr':     now.strftime('%Y'),
        'monat':    now.strftime('%m'),
        'tag':      now.strftime('%d'),
    }
    name = template
    for k, v in repl.items():
        name = name.replace('{' + k + '}', v)
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    if not name.lower().endswith('.zip'):
        name += '.zip'
    return name


def _latest_csv(directory):
    """Liefert den Pfad zur neuesten .csv-Datei im Verzeichnis (oder None)."""
    if not directory or not os.path.isdir(directory):
        return None
    files = [f for f in os.listdir(directory) if f.lower().endswith('.csv')]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getctime(os.path.join(directory, f)), reverse=True)
    return os.path.join(directory, files[0])


def _read_csv_rows(path):
    """Liest eine CSV mit ';'-Separator als Liste von Dicts (gestrippte Spaltennamen)."""
    rows = []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        if reader.fieldnames:
            reader.fieldnames = [(c or '').strip() for c in reader.fieldnames]
        for row in reader:
            rows.append({(k or '').strip(): (v or '') for k, v in row.items()})
    return rows


def _read_csv_header(path):
    """Liest nur den Header der CSV (gestrippt) — billig auch bei sehr grossen
    Dateien. Liefert [] bei Fehler/leerer Datei."""
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            return [(c or '').strip() for c in (reader.fieldnames or [])]
    except Exception:
        return []


def _inspect_erz_source(path):
    """Schaut sich den Erzieher-Export-Header an und liefert Flags, welche
    optionalen Spalten die genutzte Schild-Vorlage enthaelt — fuer die UI,
    damit der Nutzer sieht, dass z.B. Stammdaten- oder Geburtsdatum-Spalten
    vorhanden sind und der Anspr-Export entsprechend (un-)noetig ist."""
    headers = set(_read_csv_header(path))
    if not headers:
        return {
            'has_student_stamm':  False,
            'has_geburtsdatum':   False,
            'klasse_col':         None,
            'vorname_col':        None,
            'nachname_col':       None,
            'geburtsdatum_col':   None,
        }
    klasse_col   = next((c for c in _STUDENT_KLASSE_COLS   if c in headers), None)
    vorname_col  = next((c for c in _STUDENT_VORNAME_COLS  if c in headers), None)
    nachname_col = next((c for c in _STUDENT_NACHNAME_COLS if c in headers), None)
    geb_col      = next((c for c in _GEBURTSDATUM_COLS     if c in headers), None)
    return {
        'has_student_stamm':  bool(klasse_col and vorname_col and nachname_col),
        'has_geburtsdatum':   bool(geb_col),
        'klasse_col':         klasse_col,
        'vorname_col':        vorname_col,
        'nachname_col':       nachname_col,
        'geburtsdatum_col':   geb_col,
    }


# ---------------------------------------------------------------------------
# Verarbeitung
# ---------------------------------------------------------------------------

def status_info():
    """Liefert Info über aktuelle Eingabedateien + letztes ZIP für die UI."""
    erz_dir   = get_erzieher_export_dir()
    ansp_dir  = get_ansprechpartner_export_dir()
    out_dir   = get_output_dir()
    erz_file  = _latest_csv(erz_dir)
    ansp_file = _latest_csv(ansp_dir)
    erz_inspect = _inspect_erz_source(erz_file)
    # Verfuegbare Klassen + aktiver Whitelist-Filter — fuer die Chip-UI.
    # Klassen kommen primaer aus dem Anspr-Export (Schueler-Klasse), Fallback
    # aus dem Erzieher-Export (falls Klasse-Spalte vorhanden).
    classes_available = []
    if erz_file:
        try:
            lookup = _merge_student_lookups(
                _student_lookup_from_anspr(ansp_file),
                _student_lookup_from_erz(_read_csv_rows(erz_file)),
            )
            classes_available = sorted({s['klasse'] for s in lookup.values()
                                        if s.get('klasse')})
        except Exception:
            classes_available = []
    return {
        'erzieher_export_directory':        erz_dir,
        'ansprechpartner_export_directory': ansp_dir,
        'output_directory':                 out_dir,
        # Welche optionalen Spalten enthaelt die genutzte Erzieher-Vorlage?
        'erz_source_inspect':               erz_inspect,
        # Klassen-Whitelist (analog Ausbilder)
        'classes_available':                classes_available,
        'class_filter':                     get_class_filter(),
        'zip_name_template':                get_zip_name_template(),
        'smart_match':                      get_smart_match(),
        'filter_volljaehrig':               get_filter_volljaehrig(),
        'require_email':                    get_require_email(),
        'fill_dummies':                     get_fill_dummies(),
        'lift_limit':                       get_lift_limit(),
        'phone_from_erz_first':             get_phone_from_erz_first(),
        'assign_eltern_ids':                get_assign_eltern_ids(),
        'latest_erzieher_export':           os.path.basename(erz_file) if erz_file else None,
        'latest_ansprechpartner_export':    os.path.basename(ansp_file) if ansp_file else None,
        'erzieher_export_path':             erz_file,
        'ansprechpartner_export_path':      ansp_file,
        # Anspr-Export ist optional — Process- und Preview-Buttons brauchen ihn nicht
        'anspr_available':                  bool(ansp_file),
        'anspr_optional':                   True,
    }


def process(erzieher_path=None, ansprechpartner_path=None, smart_match=None,
            filter_volljaehrig=None, require_email=None, fill_dummies=None,
            lift_limit=None, phone_from_erz_first=None, assign_eltern_ids=None,
            class_filter=None):
    """
    Verarbeitet die zwei CSVs und liefert (result_files, stats).

    Optionen (default = jeweiliges Setting in settings.ini):
      smart_match          — Telefon ↔ Erzieher-Slot per Anschluss-Art (Mutter/Vater/...)
      filter_volljaehrig   — Schueler mit Self-Ansprechpartner ("volljaehrig") rauswerfen
      require_email        — Erzieher ohne E-Mail nicht exportieren
      fill_dummies         — Leere Erzieher-Felder mit eindeutigen Dummies fuellen
      lift_limit           — Limit von 2 Erziehern pro Schueler aufheben (zusaetzliche
                             Telefon-Zeilen landen in Erzieher_3.csv, _4.csv, ...)
      phone_from_erz_first — Telefonnummer aus dem Erzieher-Export (Spalten
                             'Telefon-Nummern: ...') wird als zusaetzliche, prioritaere
                             Pseudo-Anspr-Zeile pro Schueler behandelt; Duplikate
                             gegenueber dem Anspr-Export werden gefiltert.
    """
    if smart_match is None:        smart_match = get_smart_match()
    if filter_volljaehrig is None: filter_volljaehrig = get_filter_volljaehrig()
    if require_email is None:      require_email = get_require_email()
    if fill_dummies is None:       fill_dummies = get_fill_dummies()
    if lift_limit is None:         lift_limit = get_lift_limit()
    if phone_from_erz_first is None: phone_from_erz_first = get_phone_from_erz_first()
    if assign_eltern_ids is None:    assign_eltern_ids = get_assign_eltern_ids()
    if class_filter is None:         class_filter = get_class_filter()

    erzieher_path = erzieher_path or _latest_csv(get_erzieher_export_dir())
    ansprechpartner_path = ansprechpartner_path or _latest_csv(get_ansprechpartner_export_dir())

    if not erzieher_path or not os.path.isfile(erzieher_path):
        raise FileNotFoundError("Keine Erzieher-Export-CSV gefunden. Bitte Verzeichnis prüfen.")

    erz_rows = _read_csv_rows(erzieher_path)
    if not erz_rows:
        raise ValueError("Erzieher-Export ist leer.")
    if 'Interne ID-Nummer' not in erz_rows[0]:
        raise ValueError("Spalte 'Interne ID-Nummer' fehlt im Erzieher-Export.")

    # Ansprechpartner-Export ist OPTIONAL — wenn er fehlt, laufen alle Telefon-
    # Verarbeitungsschritte ueber die im Erzieher-Export hinterlegte primaere
    # Telefonnummer (Spaltengruppe 'Telefon-Nummern: ...') bzw. entfallen.
    anspr_available = bool(ansprechpartner_path and os.path.isfile(ansprechpartner_path))
    ansp_rows = []
    if anspr_available:
        ansp_rows = _read_csv_rows(ansprechpartner_path)
        if ansp_rows and 'Schüler_ID' not in ansp_rows[0]:
            raise ValueError("Spalte 'Schüler_ID' fehlt im Ansprechpartner-Export.")

    # Klassen-Whitelist anwenden — VOR allen anderen Filterstufen, damit die
    # nachfolgenden Stats (volljaehrig_filtered, dummy_fills, …) sich nur auf
    # den vom Nutzer ausgewaehlten Klassen-Pool beziehen.
    class_mode, classes_set = _resolve_class_filter(class_filter)
    class_filtered = 0
    if class_mode != 'all':
        student_lookup = _merge_student_lookups(
            _student_lookup_from_anspr(ansprechpartner_path),
            _student_lookup_from_erz(erz_rows),
        )
        before = len(erz_rows)
        erz_rows = [r for r in erz_rows
                    if _student_passes_class(
                        student_lookup.get((r.get('Interne ID-Nummer', '') or '').strip(), {}),
                        class_mode, classes_set)]
        class_filtered = before - len(erz_rows)

    # Volljaehrige Schueler filtern + Stats
    volljaehrig_filtered = 0
    if filter_volljaehrig:
        before = len(erz_rows)
        erz_rows = [r for r in erz_rows if not _is_self_volljaehrig(r)]
        volljaehrig_filtered = before - len(erz_rows)

    # Anspr-Zeilen pro Schueler-ID sammeln (Reihenfolge der CSV bewahrt)
    ansp_by_sid = {}
    for r in ansp_rows:
        ansp_by_sid.setdefault(r.get('Schüler_ID', ''), []).append(r)

    # Maximale Erzieher-Slot-Nummer aus dem Erzieher-CSV-Header ableiten
    max_slots_in_csv = 0
    for col in (erz_rows[0].keys() if erz_rows else []):
        m = re.match(r'Erzieher\s+(\d+):', col)
        if m:
            max_slots_in_csv = max(max_slots_in_csv, int(m.group(1)))

    # Pro Schueler die Anspr-Zuordnung berechnen
    match_stats_total = {'gender': 0, 'positional': 0, 'virtual': 0,
                         'orphan_anspr': 0, 'orphan_erz': 0}
    assignment_by_sid = {}  # sid -> {erz_idx: anspr_dict}
    phone_from_erz_used      = 0  # wie oft pseudo-Zeile uebernommen wurde
    phone_from_erz_duplicates = 0  # wie oft Duplikate im Anspr-Export gefiltert wurden
    for erz_row in erz_rows:
        sid = erz_row.get('Interne ID-Nummer', '').strip()
        if not sid:
            continue
        anspr_list = ansp_by_sid.get(sid, [])
        if phone_from_erz_first:
            erz_phone = _erz_phone_pseudo(erz_row)
            if erz_phone:
                before = len(anspr_list)
                anspr_list = _merge_phone_sources(erz_phone, anspr_list)
                phone_from_erz_used += 1
                # +1 fuer die neue Pseudo-Zeile; Differenz = entfernte Duplikate
                phone_from_erz_duplicates += (before + 1) - len(anspr_list)
        if smart_match:
            assigned, st = _smart_match_student(erz_row, anspr_list, max_slots_in_csv,
                                                lift_limit=lift_limit)
            for k in match_stats_total:
                match_stats_total[k] += st[k]
        else:
            # Positional: i-te Anspr-Zeile -> Erzieher i (lift_limit ist hier ohnehin
            # implizit aktiv, da nicht durch max_slots_in_csv begrenzt)
            assigned = {i + 1: anspr_list[i] for i in range(len(anspr_list))}
        assignment_by_sid[sid] = assigned

    # max_erzieher (= Anzahl Output-CSVs) aus den tatsaechlich getroffenen
    # Zuweisungen + gefuellten Stammdaten-Slots ableiten
    max_erzieher = 0
    for er in erz_rows:
        sid = er.get('Interne ID-Nummer', '').strip()
        # Gefuellte Stammdaten-Slots
        upper_for_stamm = max_slots_in_csv
        for i in range(1, upper_for_stamm + 1):
            if (er.get(f'Erzieher {i}: Vorname', '') or er.get(f'Erzieher {i}: Nachname', '')).strip():
                max_erzieher = max(max_erzieher, i)
        # Zugeordnete Slots (inkl. virtueller bei lift_limit)
        for idx in assignment_by_sid.get(sid, {}).keys():
            max_erzieher = max(max_erzieher, idx)

    # Eltern-ID-DB einmal laden (Batch-Modus), spaeter atomar speichern
    eltern_db        = None
    eltern_id_new    = 0
    eltern_id_reused = 0
    if assign_eltern_ids:
        import eltern_id_manager
        eltern_db = eltern_id_manager.load_db()

    # Pro Erzieher-Index eine Ergebnisdatei bauen
    result_files = {}
    skipped_no_email = 0
    dummy_fills      = 0
    for i in range(1, max_erzieher + 1):
        header = ['Interne_ID_Nummer']
        for field in ERZIEHER_FIELDS:
            header.append(f'Erzieher {i}: {field}')
        for src in ANSPRECHPARTNER_FIELD_MAP.values():
            header.append(f'Erzieher {i}: {src}')
        if assign_eltern_ids:
            header.append(f'Erzieher {i}: Eltern-ID')

        result_rows = []
        for erz_row in erz_rows:
            sid = erz_row.get('Interne ID-Nummer', '').strip()
            if not sid:
                continue
            ansp = assignment_by_sid.get(sid, {}).get(i, {})
            stamm = {fld: (erz_row.get(f'Erzieher {i}: {fld}', '') or '').strip()
                     for fld in ERZIEHER_FIELDS}
            has_stamm = any(stamm.values())
            has_ansp  = any((ansp.get(c, '') or '').strip() for c in ANSPRECHPARTNER_FIELD_MAP)
            if not (has_stamm or has_ansp):
                continue  # leerer Slot fuer diesen Schueler -> nicht exportieren
            if require_email and not stamm.get('E-Mail', ''):
                skipped_no_email += 1
                continue

            row_out = {'Interne_ID_Nummer': sid}
            for field in ERZIEHER_FIELDS:
                row_out[f'Erzieher {i}: {field}'] = stamm[field]
            for src_col, tgt_col_short in ANSPRECHPARTNER_FIELD_MAP.items():
                row_out[f'Erzieher {i}: {tgt_col_short}'] = ansp.get(src_col, '')

            # Eltern-ID auf Basis der ECHTEN Stammdaten (vor Dummy-Fill) holen
            if assign_eltern_ids:
                import eltern_id_manager
                key = eltern_id_manager._key(stamm['Vorname'], stamm['Nachname'],
                                             stamm['E-Mail'])
                existed = key in eltern_db['mappings']
                eid = eltern_id_manager.get_or_assign(
                    stamm['Vorname'], stamm['Nachname'], stamm['E-Mail'],
                    db=eltern_db)
                row_out[f'Erzieher {i}: Eltern-ID'] = eid or ''
                if eid is not None:
                    if existed: eltern_id_reused += 1
                    else:       eltern_id_new    += 1

            if fill_dummies:
                before = sum(1 for v in row_out.values() if not v)
                _apply_dummies(row_out, i)
                after  = sum(1 for v in row_out.values() if not v)
                dummy_fills += (before - after)

            result_rows.append(row_out)

        result_files[f'Erzieher_{i}'] = {'header': header, 'rows': result_rows}

    # Eltern-ID-DB persistieren (atomar)
    if assign_eltern_ids and eltern_db is not None:
        import eltern_id_manager
        eltern_id_manager.save_db(eltern_db)

    stats = {
        'erzieher_rows':        len(erz_rows),
        'ansprechpartner_rows': len(ansp_rows),
        'anspr_available':      anspr_available,
        'max_erzieher':         max_erzieher,
        'output_files':         list(result_files.keys()),
        'match_mode':           'smart' if smart_match else 'positional',
        'match_stats':          match_stats_total,
        'filter_volljaehrig':       filter_volljaehrig,
        'volljaehrig_filtered':     volljaehrig_filtered,
        'require_email':            require_email,
        'skipped_no_email':         skipped_no_email,
        'fill_dummies':             fill_dummies,
        'dummy_fills':              dummy_fills,
        'lift_limit':               lift_limit,
        'phone_from_erz_first':         phone_from_erz_first,
        'phone_from_erz_used':          phone_from_erz_used,
        'phone_from_erz_duplicates':    phone_from_erz_duplicates,
        'assign_eltern_ids':            assign_eltern_ids,
        'eltern_id_new':                eltern_id_new,
        'eltern_id_reused':             eltern_id_reused,
        'class_filter':                 list(class_filter or []),
        'class_filter_mode':            class_mode,
        'class_filtered':               class_filtered,
    }
    return result_files, stats


def preview(erzieher_path=None, ansprechpartner_path=None):
    """
    Liefert eine Vorschau der kombinierten Schueler+Erzieher-Daten ohne ZIP-
    Generierung. Geeignet, um in der UI sowohl Schueler->Erzieher als auch
    Erzieher->Schueler (gruppiert) darzustellen.

    Returns dict mit:
      - students:        Liste[{id, vorname, nachname, klasse, erzieher: [...]}]
      - erzieher_groups: Liste[{erzieher: {...}, students: [{id, vorname, nachname, klasse, nr}, ...]}]
      - stats:           {students_count, erzieher_total, max_erzieher, students_without_erzieher}
      - field_mapping:   {from_erzieher_csv: [{src,target}], from_ansprechpartner_csv: [{src,target}]}
      - sources:         {erzieher_export_file, ansprechpartner_export_file, headers_*}
    """
    erzieher_path = erzieher_path or _latest_csv(get_erzieher_export_dir())
    ansprechpartner_path = ansprechpartner_path or _latest_csv(get_ansprechpartner_export_dir())

    if not erzieher_path or not os.path.isfile(erzieher_path):
        raise FileNotFoundError("Keine Erzieher-Export-CSV gefunden. Bitte Verzeichnis pruefen.")

    erz_rows = _read_csv_rows(erzieher_path)
    if not erz_rows:
        raise ValueError("Erzieher-Export ist leer.")
    if 'Interne ID-Nummer' not in erz_rows[0]:
        raise ValueError("Spalte 'Interne ID-Nummer' fehlt im Erzieher-Export.")

    # Anspr-Export ist optional
    anspr_available = bool(ansprechpartner_path and os.path.isfile(ansprechpartner_path))
    ansp_rows = []
    if anspr_available:
        ansp_rows = _read_csv_rows(ansprechpartner_path)
        if ansp_rows and 'Schüler_ID' not in ansp_rows[0]:
            raise ValueError("Spalte 'Schüler_ID' fehlt im Ansprechpartner-Export.")

    # Header der Eingabe-Dateien (fuer die Anzeige im Field-Mapping-Block)
    erz_header  = list(erz_rows[0].keys())  if erz_rows  else []
    ansp_header = list(ansp_rows[0].keys()) if ansp_rows else []

    # Schueler-Stammdaten-Lookup — kombiniert aus beiden Quellen.
    # Anspr-Export ist die primaere Quelle (Schild-Standard); Erzieher-Export
    # ist Fallback, falls die Schule die Stammdaten-Spalten ebenfalls in die
    # Erzieher-Vorlage aufgenommen hat oder der Anspr-Export gar nicht existiert.
    # Brauchen wir frueh, weil der Klassen-Filter darauf zugreift.
    student_lookup = _merge_student_lookups(
        _student_lookup_from_anspr(ansprechpartner_path),
        _student_lookup_from_erz(erz_rows),
    )

    # Klassen-Whitelist anwenden — VOR allen anderen Filterstufen, damit die
    # nachfolgenden Stats sich nur auf den vom Nutzer ausgewaehlten Pool beziehen.
    class_filter = get_class_filter()
    class_mode, classes_set = _resolve_class_filter(class_filter)
    class_filtered = 0
    if class_mode != 'all':
        before = len(erz_rows)
        erz_rows = [r for r in erz_rows
                    if _student_passes_class(
                        student_lookup.get((r.get('Interne ID-Nummer', '') or '').strip(), {}),
                        class_mode, classes_set)]
        class_filtered = before - len(erz_rows)

    # Volljaehrige Schueler optional rausfiltern
    filter_volljaehrig = get_filter_volljaehrig()
    volljaehrig_filtered = 0
    if filter_volljaehrig:
        before = len(erz_rows)
        erz_rows = [r for r in erz_rows if not _is_self_volljaehrig(r)]
        volljaehrig_filtered = before - len(erz_rows)

    # Ansprechpartner-Zeilen pro Schueler-ID gruppieren (Reihenfolge aus CSV bewahrt).
    ansp_by_sid = {}
    for r in ansp_rows:
        ansp_by_sid.setdefault(r.get('Schüler_ID', ''), []).append(r)

    # Maximale Erzieher-Slot-Nummer aus dem Header ableiten
    max_in_header = 0
    for col in erz_header:
        m = re.match(r'Erzieher\s+(\d+):', col)
        if m:
            max_in_header = max(max_in_header, int(m.group(1)))
    if max_in_header == 0:
        max_in_header = max((len(v) for v in ansp_by_sid.values()), default=0)

    smart_match          = get_smart_match()
    require_email        = get_require_email()
    fill_dummies         = get_fill_dummies()
    lift_limit           = get_lift_limit()
    phone_from_erz_first = get_phone_from_erz_first()
    assign_eltern_ids    = get_assign_eltern_ids()
    # Eltern-IDs in der Preview NUR lesen — Vergabe erst beim Verarbeiten
    eltern_db_preview = None
    eltern_id_total      = 0
    eltern_id_known      = 0
    eltern_id_would_new  = 0
    if assign_eltern_ids:
        import eltern_id_manager
        eltern_db_preview = eltern_id_manager.load_db()

    students = []
    students_without_erzieher = 0
    skipped_no_email = 0
    dummy_fills      = 0
    match_stats = {'gender': 0, 'positional': 0, 'virtual': 0,
                   'orphan_anspr': 0, 'orphan_erz': 0}
    orphan_anspr_rows = []   # fuer detaillierte Anzeige in der Preview
    phone_from_erz_used       = 0
    phone_from_erz_duplicates = 0
    # Pro Student max-Slot ermitteln, damit virtuelle Slots (lift_limit) sichtbar werden
    assignments = {}
    for erz_row in erz_rows:
        sid = erz_row.get('Interne ID-Nummer', '').strip()
        if not sid:
            continue
        anspr_list = ansp_by_sid.get(sid, [])
        if phone_from_erz_first:
            erz_phone = _erz_phone_pseudo(erz_row)
            if erz_phone:
                before = len(anspr_list)
                anspr_list = _merge_phone_sources(erz_phone, anspr_list)
                phone_from_erz_used += 1
                phone_from_erz_duplicates += (before + 1) - len(anspr_list)
        if smart_match:
            assigned, st = _smart_match_student(erz_row, anspr_list, max_in_header,
                                                lift_limit=lift_limit)
            for k in match_stats:
                match_stats[k] += st[k]
            if not lift_limit:
                used_anspr = set(id(v) for v in assigned.values())
                for a in anspr_list:
                    if id(a) not in used_anspr:
                        stamm_o = student_lookup.get(sid, {})
                        orphan_anspr_rows.append({
                            'student_id':   sid,
                            'student_name': f"{stamm_o.get('nachname','')}, {stamm_o.get('vorname','')}".strip(', '),
                            'klasse':       stamm_o.get('klasse', ''),
                            'anschluss':    (a.get('Anschluss-Art')  or '').strip(),
                            'bemerkung':    (a.get('Bemerkung')      or '').strip(),
                            'telefon':      (a.get('Telefon-Nummer') or '').strip(),
                            'from_erz':     bool(a.get('_from_erz')),
                        })
        else:
            assigned = {i + 1: anspr_list[i] for i in range(len(anspr_list))}
        assignments[sid] = assigned

    for erz_row in erz_rows:
        sid = erz_row.get('Interne ID-Nummer', '').strip()
        if not sid:
            continue
        assigned = assignments.get(sid, {})
        # Anzeige bis max. (Header-Slots) plus alle virtuellen Slots
        max_for_student = max([max_in_header] + list(assigned.keys()), default=max_in_header)

        erzieher_list = []
        for i in range(1, max_for_student + 1):
            erz_data = {
                'nr':          i,
                'anrede':      erz_row.get(f'Erzieher {i}: Anrede',      '').strip(),
                'briefanrede': erz_row.get(f'Erzieher {i}: Briefanrede', '').strip(),
                'titel':       erz_row.get(f'Erzieher {i}: Titel',       '').strip(),
                'nachname':    erz_row.get(f'Erzieher {i}: Nachname',    '').strip(),
                'vorname':     erz_row.get(f'Erzieher {i}: Vorname',     '').strip(),
                'email':       erz_row.get(f'Erzieher {i}: E-Mail',      '').strip(),
            }
            ansp = assigned.get(i, {})
            erz_data.update({
                'anschluss':       (ansp.get('Anschluss-Art')  or '').strip(),
                'bemerkung':       (ansp.get('Bemerkung')      or '').strip(),
                'telefon':         (ansp.get('Telefon-Nummer') or '').strip(),
                'telefon_from_erz': bool(ansp.get('_from_erz')),
            })
            has_anything = any(v for k, v in erz_data.items()
                               if k not in ('nr', 'telefon_from_erz'))
            if not has_anything:
                continue
            # Flags fuer die UI
            erz_data['virtual']           = i > max_in_header
            erz_data['would_skip_email']  = bool(require_email and not erz_data['email'])
            # Eltern-ID-Preview (nur lookup, ohne neue zu erzeugen)
            if assign_eltern_ids and not erz_data['would_skip_email']:
                import eltern_id_manager
                if not eltern_id_manager.is_dummy(erz_data['vorname'],
                                                  erz_data['nachname'],
                                                  erz_data['email']) and \
                   (erz_data['vorname'] or erz_data['nachname']):
                    key = eltern_id_manager._key(erz_data['vorname'],
                                                  erz_data['nachname'],
                                                  erz_data['email'])
                    existing = eltern_db_preview['mappings'].get(key)
                    if existing is not None:
                        erz_data['eltern_id']        = eltern_id_manager._format_id(existing)
                        erz_data['eltern_id_status'] = 'known'
                        eltern_id_known += 1
                    else:
                        erz_data['eltern_id']        = '(neu)'
                        erz_data['eltern_id_status'] = 'new'
                        eltern_id_would_new += 1
                    eltern_id_total += 1
            # Dummy-Vorschau (vor allem fuer virtuelle Slots interessant)
            if fill_dummies:
                erz_data['dummies'] = {}
                for short, dummy in DUMMY_VALUES.items():
                    if short == 'E-Mail':
                        key = 'email'
                    elif short == 'Telefon-Nummer':
                        key = 'telefon'
                    elif short == 'Anschluss Art':
                        key = 'anschluss'
                    else:
                        key = short.lower()
                    if key in erz_data and not erz_data[key]:
                        erz_data['dummies'][key] = dummy
                # Zaehler aktualisieren — fuer Stats
                if erz_data.get('would_skip_email'):
                    pass  # wird ja eh nicht exportiert
                else:
                    dummy_fills += len(erz_data['dummies'])
            erzieher_list.append(erz_data)

        # Stats: wuerde dieser Slot wegen E-Mail rausfliegen?
        if require_email:
            skipped_no_email += sum(1 for e in erzieher_list if e.get('would_skip_email'))

        if not erzieher_list:
            students_without_erzieher += 1
        stamm = student_lookup.get(sid, {})
        students.append({
            'id':       sid,
            'vorname':  stamm.get('vorname')  or (erz_row.get('Vorname',  '') or '').strip(),
            'nachname': stamm.get('nachname') or (erz_row.get('Nachname', '') or '').strip(),
            'klasse':   stamm.get('klasse')   or (erz_row.get('Klasse',   '') or '').strip(),
            'erzieher': erzieher_list,
        })
    students.sort(key=lambda s: (s['klasse'], s['nachname'], s['vorname']))

    # Erzieher gruppieren ueber alle Schueler (Schluessel: nachname|vorname|email, case-insensitive)
    groups = {}
    for s in students:
        for e in s['erzieher']:
            key = (e['nachname'].lower(), e['vorname'].lower(), e['email'].lower())
            if not any(key):
                continue
            entry = groups.setdefault(key, {'erzieher': e.copy(), 'students': []})
            entry['students'].append({
                'id':       s['id'],
                'vorname':  s['vorname'],
                'nachname': s['nachname'],
                'klasse':   s['klasse'],
                'nr':       e['nr'],
            })
    erzieher_groups = sorted(
        groups.values(),
        key=lambda g: (g['erzieher']['nachname'].lower(), g['erzieher']['vorname'].lower()),
    )

    erzieher_total = sum(len(s['erzieher']) for s in students)
    max_erzieher   = max((len(s['erzieher']) for s in students), default=0)

    # Feld-Mapping: was wandert aus welcher CSV in die i-te Output-CSV?
    # 'i' ist Platzhalter; der konkrete Wert haengt vom Output-File ab.
    from_erzieher = [{'src': 'Interne ID-Nummer', 'target': 'Interne_ID_Nummer'}]
    for f in ERZIEHER_FIELDS:
        from_erzieher.append({'src': f'Erzieher i: {f}', 'target': f'Erzieher i: {f}'})
    from_ansprechpartner = [{'src': 'Schueler_ID', 'target': 'Interne_ID_Nummer (Matching)'}]
    for src, tgt in ANSPRECHPARTNER_FIELD_MAP.items():
        from_ansprechpartner.append({'src': src, 'target': f'Erzieher i: {tgt}'})

    return {
        'students':        students,
        'erzieher_groups': [
            {
                'erzieher': g['erzieher'],
                'students': sorted(g['students'], key=lambda x: (x['klasse'], x['nachname'], x['vorname'])),
            }
            for g in erzieher_groups
        ],
        'stats': {
            'students_count':            len(students),
            'students_without_erzieher': students_without_erzieher,
            'erzieher_total':            erzieher_total,
            'unique_erzieher':           len(erzieher_groups),
            'max_erzieher':              max_erzieher,
            'ansprechpartner_rows':      len(ansp_rows),
            'anspr_available':           anspr_available,
            'match_mode':                'smart' if smart_match else 'positional',
            'match_stats':               match_stats,
            'orphan_anspr_rows':         orphan_anspr_rows[:200],  # Cap fuer UI
            'orphan_anspr_count':        len(orphan_anspr_rows),
            'filter_volljaehrig':        filter_volljaehrig,
            'volljaehrig_filtered':      volljaehrig_filtered,
            'require_email':             require_email,
            'skipped_no_email':          skipped_no_email,
            'fill_dummies':              fill_dummies,
            'dummy_fills':               dummy_fills,
            'lift_limit':                lift_limit,
            'phone_from_erz_first':         phone_from_erz_first,
            'phone_from_erz_used':          phone_from_erz_used,
            'phone_from_erz_duplicates':    phone_from_erz_duplicates,
            'assign_eltern_ids':            assign_eltern_ids,
            'eltern_id_total':              eltern_id_total,
            'eltern_id_known':              eltern_id_known,
            'eltern_id_would_new':          eltern_id_would_new,
            'class_filter':                 list(class_filter or []),
            'class_filter_mode':            class_mode,
            'class_filtered':               class_filtered,
        },
        'field_mapping': {
            'from_erzieher_csv':        from_erzieher,
            'from_ansprechpartner_csv': from_ansprechpartner,
        },
        'sources': {
            'erzieher_export_file':        os.path.basename(erzieher_path),
            'ansprechpartner_export_file': os.path.basename(ansprechpartner_path) if anspr_available else None,
            'erzieher_headers':            erz_header,
            'ansprechpartner_headers':     ansp_header,
        },
    }


def raw_source(max_rows=500):
    """Liefert die ersten max_rows beider Quell-CSVs als tabular dicts fuer
    die UI — damit der Nutzer schnell verifizieren kann, dass der Schild-Export
    so aussieht wie erwartet. Markiert auch welche Spalten der Workflow
    tatsaechlich liest."""
    erz_path = _latest_csv(get_erzieher_export_dir())
    anp_path = _latest_csv(get_ansprechpartner_export_dir())

    def _capped(path):
        if not path or not os.path.isfile(path):
            return None
        rows = _read_csv_rows(path)
        headers = list(rows[0].keys()) if rows else []
        sample = rows[:max_rows]
        return {
            'file':       os.path.basename(path),
            'columns':    headers,
            'rows_total': len(rows),
            'rows_shown': len(sample),
            'rows':       [[r.get(h, '') for h in headers] for r in sample],
        }

    # Welche Spalten werden vom Workflow tatsaechlich genutzt?
    # Aus dem Erzieher-Export: 'Interne ID-Nummer' + 'Erzieher i: <Field>' fuer i=1..max
    used_erz = {'Interne ID-Nummer'}
    if erz_path and os.path.isfile(erz_path):
        # Max-Slot aus dem Header lesen
        max_slot = 0
        with open(erz_path, 'r', encoding='utf-8-sig', newline='') as f:
            for col in (csv.DictReader(f, delimiter=';').fieldnames or []):
                m = re.match(r'Erzieher\s+(\d+):', (col or '').strip())
                if m:
                    max_slot = max(max_slot, int(m.group(1)))
        for i in range(1, max_slot + 1):
            for fld in ERZIEHER_FIELDS:
                used_erz.add(f'Erzieher {i}: {fld}')
    # Erzieher-Export-Telefon (Pseudo-Anspr-Zeile fuer phone_from_erz_first)
    used_erz.update(ERZ_PHONE_COLS.values())
    # Klasse / Name / Geburtsdatum / Vollj.-Flag (fuer UI-Anzeige, Missing-Report
    # und Vollj.-Filter)
    used_erz.update({'Klasse', 'Erzieher: Art (Klartext)', 'Vorname', 'Nachname'})
    used_erz.update(_GEBURTSDATUM_COLS)
    used_anp = set(ANSPRECHPARTNER_FIELD_MAP.keys()) | {'Schüler_ID'}

    return {
        'erzieher':        _capped(erz_path),
        'ansprechpartner': _capped(anp_path),
        'used_erzieher_cols':        sorted(used_erz),
        'used_ansprechpartner_cols': sorted(used_anp),
        'cap':             max_rows,
    }


# ---------------------------------------------------------------------------
# Missing-Erzieher-Report (Klassenweise Auswertung minderjaehriger Schueler
# ohne hinterlegte Erzieher-Daten)
# ---------------------------------------------------------------------------

def _is_minor(erz_row):
    """Heuristik: Schueler gilt als minderjaehrig, wenn er NICHT explizit als
    volljaehrig markiert ist. (Schild hat keine separate Volljaehrig-Spalte;
    wir nutzen denselben Proxy wie _is_self_volljaehrig.)"""
    return not _is_self_volljaehrig(erz_row)


# Kriterien fuer den Missing-Report: Key -> (Label, Test-Funktion)
# Jede Test-Funktion bekommt (erz_row, max_slots) und liefert True, wenn der
# Schueler nach DIESEM Kriterium als "fehlend" gilt.
MISSING_CRITERIA = {
    'no_erzieher': {
        'label': 'Kein Erzieher hinterlegt',
        'test':  lambda er, n: all(
            not (er.get(f'Erzieher {i}: {f}', '') or '').strip()
            for i in range(1, n + 1)
            for f in ('Vorname', 'Nachname', 'E-Mail')
        ),
    },
    'no_nachname': {
        'label': 'Mind. ein Erzieher ohne Nachname',
        'test':  lambda er, n: any(
            _slot_used(er, i) and not (er.get(f'Erzieher {i}: Nachname', '') or '').strip()
            for i in range(1, n + 1)
        ),
    },
    'no_vorname': {
        'label': 'Mind. ein Erzieher ohne Vorname',
        'test':  lambda er, n: any(
            _slot_used(er, i) and not (er.get(f'Erzieher {i}: Vorname', '') or '').strip()
            for i in range(1, n + 1)
        ),
    },
    'no_email': {
        'label': 'Mind. ein Erzieher ohne E-Mail',
        'test':  lambda er, n: any(
            _slot_used(er, i) and not (er.get(f'Erzieher {i}: E-Mail', '') or '').strip()
            for i in range(1, n + 1)
        ),
    },
}


def _slot_used(erz_row, i):
    """True wenn Erzieher-Slot i ueberhaupt benutzt wird (mind. ein Feld gefuellt)."""
    for f in ('Anrede', 'Briefanrede', 'Titel', 'Nachname', 'Vorname', 'E-Mail'):
        if (erz_row.get(f'Erzieher {i}: {f}', '') or '').strip():
            return True
    return False


# Spaltennamen-Varianten fuer Schueler-Stammdaten — Schild liefert je nach
# Export-Vorlage unterschiedliche Bezeichnungen. Wir suchen die erste nicht-leere.
_STUDENT_KLASSE_COLS   = (
    'Klasse', 'Schüler-Klasse', 'Schüler: Klasse', 'Schueler-Klasse',
    'Schueler: Klasse', 'aktuelle Klasse', 'Klasse (aktuell)',
)
_STUDENT_VORNAME_COLS  = (
    'Vorname', 'Schüler-Vorname', 'Schüler: Vorname', 'Schueler-Vorname',
    'Schueler: Vorname',
)
_STUDENT_NACHNAME_COLS = (
    'Nachname', 'Schüler-Nachname', 'Schüler: Nachname', 'Schueler-Nachname',
    'Schueler: Nachname',
)


def _first_nonempty(row, cols):
    """Liefert den ersten nicht-leeren, getrimmten Wert aus row fuer die
    gegebenen Spaltennamen-Kandidaten."""
    for c in cols:
        v = (row.get(c, '') or '').strip()
        if v:
            return v
    return ''


def _extract_student_stamm(row):
    """Versucht Schueler-Stammdaten (Klasse, Vorname, Nachname) aus EINEM Row
    zu extrahieren — toleriert verschiedene Spaltennamen-Varianten."""
    return {
        'klasse':   _first_nonempty(row, _STUDENT_KLASSE_COLS),
        'vorname':  _first_nonempty(row, _STUDENT_VORNAME_COLS),
        'nachname': _first_nonempty(row, _STUDENT_NACHNAME_COLS),
    }


def _student_lookup_from_erz(erz_rows):
    """Lookup {sid: {klasse, vorname, nachname}} aus dem Erzieher-Export.
    Wirksam nur, wenn die Schild-Export-Vorlage diese Spalten enthaelt (Standard-
    Vorlage hat sie NICHT — der Anspr-Export ist die primaere Quelle)."""
    lookup = {}
    for r in (erz_rows or []):
        sid = (r.get('Interne ID-Nummer', '') or '').strip()
        if not sid or sid in lookup:
            continue
        stamm = _extract_student_stamm(r)
        if any(stamm.values()):
            lookup[sid] = stamm
    return lookup


def _student_lookup_from_anspr(anspr_path=None):
    """Liefert {sid: {'klasse','vorname','nachname'}} aus dem Anspr-Export.

    Der Schild-Standard-Erzieher-Export enthaelt keine Schueler-Stammdaten —
    der Anspr-Export aber sehr wohl als 'Schueler-Klasse/-Nachname/-Vorname'.
    Wenn der Anspr-Export nicht erreichbar ist -> leerer Lookup (Aufrufer
    sollte dann _student_lookup_from_erz() als Fallback verwenden)."""
    anspr_path = anspr_path or _latest_csv(get_ansprechpartner_export_dir())
    if not anspr_path or not os.path.isfile(anspr_path):
        return {}
    try:
        rows = _read_csv_rows(anspr_path)
    except Exception:
        return {}
    lookup = {}
    for r in rows:
        sid = (r.get('Schüler_ID', '') or '').strip()
        if not sid or sid in lookup:
            continue
        lookup[sid] = _extract_student_stamm(r)
    return lookup


def _merge_student_lookups(*lookups):
    """Kombiniert mehrere Lookups; bei mehrfacher SID gewinnt der erste,
    fehlende Einzelfelder werden aus spaeteren ergaenzt."""
    out = {}
    for lk in lookups:
        for sid, stamm in lk.items():
            if sid not in out:
                out[sid] = dict(stamm)
            else:
                for k, v in stamm.items():
                    if not out[sid].get(k) and v:
                        out[sid][k] = v
    return out


def missing_erzieher_report(erzieher_path=None, criteria=None, match_mode='any'):
    """Liefert pro Klasse die Liste der minderjaehrigen Schueler, die nach
    mindestens einem (match_mode='any') oder allen (match_mode='all')
    aktivierten Kriterien als "fehlend" gelten.

    criteria: Liste der aktivierten Kriterien-Keys aus MISSING_CRITERIA.
              None oder leer -> ['no_erzieher'] (Default = bisheriges Verhalten).
    match_mode: 'any' (Default) oder 'all' — Verknuepfung der Kriterien.

    Returns:
        {
          'classes': [
              {'klasse': 'BK01A', 'count': 3,
               'students': [{id, vorname, nachname, reasons: [keys]}, ...]},
              ...
          ],
          'total_classes':   N,
          'total_students':  N,
          'source_file':     'ErzieherExport.csv',
          'criteria_used':   [keys],
          'available_criteria': [{'key':..., 'label':...}, ...],
          'match_mode':      'any' | 'all',
        }
    """
    if not criteria:
        criteria = ['no_erzieher']
    # Unbekannte Keys aussortieren
    criteria = [c for c in criteria if c in MISSING_CRITERIA]
    if not criteria:
        criteria = ['no_erzieher']

    erzieher_path = erzieher_path or _latest_csv(get_erzieher_export_dir())
    available = [{'key': k, 'label': v['label']} for k, v in MISSING_CRITERIA.items()]
    if not erzieher_path or not os.path.isfile(erzieher_path):
        raise FileNotFoundError("Keine Erzieher-Export-CSV gefunden.")
    erz_rows = _read_csv_rows(erzieher_path)
    if not erz_rows:
        return {'classes': [], 'total_classes': 0, 'total_students': 0,
                'source_file': os.path.basename(erzieher_path),
                'criteria_used': criteria,
                'available_criteria': available,
                'match_mode': match_mode}

    max_slots = 0
    for col in erz_rows[0].keys():
        m = re.match(r'Erzieher\s+(\d+):', col)
        if m:
            max_slots = max(max_slots, int(m.group(1)))

    # Schueler-Stammdaten (Name/Klasse) — kombiniert aus Anspr-Export (primaer,
    # Schild-Standard-Vorlage hat die Spalten dort) und Erzieher-Export (Fallback,
    # falls die Schule sie auch in die Erzieher-Vorlage aufgenommen hat oder
    # wenn der Anspr-Export gar nicht existiert).
    student_lookup = _merge_student_lookups(
        _student_lookup_from_anspr(),
        _student_lookup_from_erz(erz_rows),
    )
    anspr_path_used = _latest_csv(get_ansprechpartner_export_dir())
    anspr_available = bool(anspr_path_used and os.path.isfile(anspr_path_used))

    # Klassen-Whitelist auch fuer den Report respektieren — sonst tauchen
    # Schueler aus abgewaehlten Klassen hier auf, obwohl der Nutzer sie aus
    # dem Workflow ausgeblendet hat.
    class_mode, classes_set = _resolve_class_filter(get_class_filter())

    by_class = {}
    total = 0
    students_unknown = 0   # Schueler komplett ohne Stammdaten in beiden Quellen
    for er in erz_rows:
        if not _is_minor(er):
            continue
        sid = (er.get('Interne ID-Nummer', '') or '').strip()
        stamm = student_lookup.get(sid, {})
        # Klassen-Whitelist
        if not _student_passes_class(stamm, class_mode, classes_set):
            continue
        # Pro Kriterium pruefen + Gruende sammeln
        hits = [k for k in criteria if MISSING_CRITERIA[k]['test'](er, max_slots)]
        if not hits:
            continue
        if match_mode == 'all' and len(hits) != len(criteria):
            continue
        klasse   = stamm.get('klasse')   or '(ohne Klasse)'
        vorname  = stamm.get('vorname',  '')
        nachname = stamm.get('nachname', '')
        if not (vorname or nachname or klasse != '(ohne Klasse)'):
            students_unknown += 1
        by_class.setdefault(klasse, []).append({
            'id':       sid,
            'vorname':  vorname,
            'nachname': nachname,
            'reasons':  hits,
        })
        total += 1

    classes = []
    for k in sorted(by_class.keys()):
        students = sorted(by_class[k], key=lambda s: (s['nachname'].lower(), s['vorname'].lower()))
        classes.append({'klasse': k, 'count': len(students), 'students': students})

    return {
        'classes':            classes,
        'total_classes':      len(classes),
        'total_students':     total,
        'students_unknown':   students_unknown,
        'anspr_available':    anspr_available,
        'class_filter_mode':  class_mode,
        'source_file':        os.path.basename(erzieher_path),
        'criteria_used':      criteria,
        'available_criteria': available,
        'match_mode':         match_mode,
    }


def write_missing_report_zip(selected_classes=None, output_dir=None,
                             criteria=None, match_mode='any'):
    """Schreibt pro ausgewaehlter Klasse eine CSV mit den minderjaehrigen
    Schuelern ohne Erzieher-Daten und packt alles in ein ZIP.

    selected_classes: Liste der Klassennamen, die ins ZIP sollen.
                      None oder leer = alle.

    Returns: (zip_pfad, zip_name, count_dict)
    """
    output_dir = output_dir or get_output_dir()
    os.makedirs(output_dir, exist_ok=True)

    report = missing_erzieher_report(criteria=criteria, match_mode=match_mode)
    sel = set(selected_classes) if selected_classes else None
    chosen = [c for c in report['classes'] if (sel is None or c['klasse'] in sel)]
    if not chosen:
        raise ValueError("Keine Klassen ausgewaehlt oder keine Datensaetze vorhanden.")

    name = f"FehlendeErzieher_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"
    zip_path = os.path.join(output_dir, name)

    # Labels fuer Gruende, kommagetrennt im CSV
    label_by_key = {k: v['label'] for k, v in MISSING_CRITERIA.items()}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for c in chosen:
            csv_buf = io.StringIO()
            writer = csv.writer(csv_buf, delimiter=';')
            writer.writerow(['Interne_ID_Nummer', 'Klasse', 'Nachname',
                             'Vorname', 'Gruende'])
            for s in c['students']:
                gruende = ', '.join(label_by_key.get(r, r) for r in s.get('reasons', []))
                writer.writerow([s['id'], c['klasse'], s['nachname'],
                                 s['vorname'], gruende])
            safe_klasse = re.sub(r'[<>:"/\\|?*]', '_', c['klasse'])
            zf.writestr(f"FehlendeErzieher_{safe_klasse}.csv",
                        csv_buf.getvalue().encode('utf-8-sig'))
    with open(zip_path, 'wb') as f:
        f.write(buf.getvalue())

    return zip_path, name, {
        'classes':  len(chosen),
        'students': sum(c['count'] for c in chosen),
        'criteria_used': report['criteria_used'],
        'match_mode':    report['match_mode'],
    }


def write_zip(result_files, output_dir=None, name_template=None):
    """Schreibt die Ergebnisdateien als ZIP in das Ausgabeverzeichnis.
    Liefert (zip_pfad, zip_name)."""
    output_dir = output_dir or get_output_dir()
    os.makedirs(output_dir, exist_ok=True)
    name_template = name_template or get_zip_name_template()
    zip_name = _resolve_zip_name(name_template)
    zip_path = os.path.join(output_dir, zip_name)
    # Bei Konflikt: Zeitstempel-Suffix
    if os.path.exists(zip_path):
        base, ext = os.path.splitext(zip_name)
        zip_name = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"
        zip_path = os.path.join(output_dir, zip_name)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname, file_data in result_files.items():
            csv_buf = io.StringIO()
            writer = csv.DictWriter(csv_buf, fieldnames=file_data['header'], delimiter=';')
            writer.writeheader()
            writer.writerows(file_data['rows'])
            zf.writestr(f"{fname}.csv", csv_buf.getvalue().encode('utf-8-sig'))
    with open(zip_path, 'wb') as f:
        f.write(buf.getvalue())
    return zip_path, zip_name
