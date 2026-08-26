"""
Ausbilder-/Betreuer-Workflow (Phase 3).

Portiert die Logik des Standalone-Tools "AusbilderImporterFlask" — speziell für
Berufskollegs in NRW — ohne Pandas-Abhängigkeit.

Idee:
  - Schild exportiert Auszubildende inkl. Betreuer-Daten als CSV.
  - In WebUntis dürfen Ausbilder nur Fehlstunden derjenigen Azubis sehen, die der
    Datenverarbeitung zugestimmt haben (VO DVI, DSGVO).
  - Tool filtert die CSV nach mehreren Whitelists/Blacklists und schreibt eine
    bereinigte WebUntis-Import-CSV.

Quell-Modi (Single-File-Konsolidierung, neu in 3.2):
  Standard ist 'off': der Workflow liest den Schueler-Export aus dem
  Ausbilder-Eingabeverzeichnis (Setting ausbilder_input_directory). Der
  Schild-Schueler-Export der Hauptverarbeitung liegt aber typischerweise
  schon im 'Schild Exporte'-Verzeichnis (Setting schildexport_directory)
  und enthaelt exakt dieselben Spalten ('Klasse', 'Vorname', 'Nachname',
  'Interne ID-Nummer', 'Allg. Adresse: Name1', 'Allg. Adresse: Betreuer ...'
  etc.). Damit kann diese eine Datei beide Workflows speisen.

  Setting [Ausbilder].schueler_export_mode:
    - 'off'      (Default) — Verhalten wie bisher: nur ausbilder_input_directory.
    - 'fallback' — Wenn ausbilder_input_directory leer/ohne CSV ist, wird die
                   neueste CSV aus schildexport_directory verwendet (sofern
                   ein Schueler-Export erkannt — Marker via _is_schueler_export_file).
    - 'always'   — schildexport_directory hat IMMER Vorrang.

Filter-Stufen (alle persistent in [Ausbilder]-Section, werden in
filter_and_write() in dieser Reihenfolge angewendet):
  - class_filter (Komma-getrennt, Sentinel '__NONE__' = nichts; leer = alle)
    Klassen-Whitelist — nur diese Klassen werden exportiert. Im UI als farbige
    Chips ueber der Schueler-Tabelle gepflegt; das Frontend spiegelt den Filter
    zusaetzlich live in der Schueler-Tabelle (Hidden-Count im Counter).
  - blacklist_ids (Komma-getrennt)
    Schueler-Blacklist nach Interner ID-Nummer — Schueler ohne DSGVO-Einwilligung
    werden hier dauerhaft ausgeschlossen, im UI ueber Checkbox-Spalte pro Zeile.
  - firma_filter_mode = 'whitelist' | 'blacklist' (Default 'blacklist')
    + firma_whitelist (JSON-Liste) bzw. firma_blacklist (JSON-Liste)
    Firmen-Filter — JSON wegen Kommas in Firmennamen ('Meyer, Schmidt & Co.').
    Pro Modus ist nur EINE der beiden Listen wirksam, die andere bleibt
    persistiert aber inaktiv. Verhalten:
      - Whitelist + gefuellt  → nur Schueler aus diesen Firmen
      - Whitelist + leer      → alle Schueler durch
      - Blacklist + gefuellt  → Schueler aus diesen Firmen raus
      - Blacklist + leer      → keine Filterung
    Schueler ohne Firma (Spalte 'Allg. Adresse: Name1' leer) fallen im
    Whitelist-Modus mit gefuellter Liste heraus; im Blacklist-Modus kommen sie
    durch (analog zur Schild-/Frontend-Semantik).
"""

import os
import re
import csv
import json
import configparser
from datetime import datetime

import ausbilder_extra_db
from utils import safe_read_config, read_config_for_update, ConfigReadError


DEFAULT_OUTPUT_NAME_TEMPLATE = 'WebUntis_Ausbilder_Import_{datetime}'



# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

def get_input_dir():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'ausbilder_input_directory', fallback='AusbilderInput').strip() or 'AusbilderInput'


def get_output_dir():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'ausbilder_output_directory', fallback='AusbilderImportDateien').strip() or 'AusbilderImportDateien'


def get_output_name_template():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Ausbilder', 'output_name_template', fallback=DEFAULT_OUTPUT_NAME_TEMPLATE).strip() or DEFAULT_OUTPUT_NAME_TEMPLATE


def save_output_name_template(template):
    template = (template or '').strip()
    if not template:
        return
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    config.set('Ausbilder', 'output_name_template', template)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_class_filter():
    """Liefert Liste der zu berücksichtigenden Klassen (leer = alle)."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    raw = config.get('Ausbilder', 'class_filter', fallback='').strip()
    if not raw:
        return []
    return [c.strip() for c in raw.split(',') if c.strip()]


def save_class_filter(classes):
    """Speichert Klassen-Whitelist (List[str])."""
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    cleaned = [str(c).strip() for c in (classes or []) if str(c).strip()]
    config.set('Ausbilder', 'class_filter', ','.join(cleaned))
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_blacklist():
    """Liefert Set von Schüler-IDs, die ausgeschlossen werden."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    raw = config.get('Ausbilder', 'blacklist_ids', fallback='').strip()
    if not raw:
        return set()
    return {s.strip() for s in raw.split(',') if s.strip()}


def save_blacklist(ids):
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    cleaned = sorted({str(i).strip() for i in (ids or []) if str(i).strip()})
    config.set('Ausbilder', 'blacklist_ids', ','.join(cleaned))
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


# ---------- Firma-Whitelist / -Blacklist ---------------------------------
# JSON-codiert in settings.ini, weil Firmen-Namen Kommas enthalten koennen
# ("Mueller, Schmidt & Co. GmbH"). Klassen-Filter + Schueler-Blacklist nutzen
# weiterhin Komma-Separation, weil dort Kommas faktisch nicht vorkommen.

def _read_json_list(key):
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    raw = config.get('Ausbilder', key, fallback='').strip()
    if not raw:
        return []
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass
    return []


def _write_json_list(key, items):
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    cleaned = sorted({str(x).strip() for x in (items or []) if str(x).strip()})
    config.set('Ausbilder', key, json.dumps(cleaned, ensure_ascii=False))
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_firma_whitelist():
    """Liefert Liste der zu beruecksichtigenden Firmen (leer = alle)."""
    return _read_json_list('firma_whitelist')


def save_firma_whitelist(firms):
    _write_json_list('firma_whitelist', firms)


def get_firma_blacklist():
    """Liefert Liste der auszuschliessenden Firmen (leer = keine ausgeschlossen)."""
    return _read_json_list('firma_blacklist')


def save_firma_blacklist(firms):
    _write_json_list('firma_blacklist', firms)


def get_firma_filter_mode():
    """'whitelist' oder 'blacklist' — bestimmt welche Firma-Liste beim Export wirksam ist.
    Default: 'blacklist' (haeufigster Use-Case: einzelne Firmen ausschliessen)."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    mode = config.get('Ausbilder', 'firma_filter_mode', fallback='blacklist').strip().lower()
    return mode if mode in ('whitelist', 'blacklist') else 'blacklist'


def save_firma_filter_mode(mode):
    mode = (mode or '').strip().lower()
    if mode not in ('whitelist', 'blacklist'):
        raise ValueError("mode muss 'whitelist' oder 'blacklist' sein.")
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    config.set('Ausbilder', 'firma_filter_mode', mode)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


# ---------------------------------------------------------------------------
# Single-File-Konsolidierung (3.2): Schueler-Export aus schildexport_directory
# auch als Ausbilder-Quelle nutzbar. Details siehe Module-Docstring oben.
# Symmetrisch zum schueler_export_mode im Erzieher-Workflow.
# ---------------------------------------------------------------------------

_SCHUELER_EXPORT_MODES = ('off', 'fallback', 'always')

# Basis-Marker fuer "ist eine per-Schueler-CSV" (bewusst dupliziert zu
# erzieher_processor, um Cross-Modul-Querbezuege zu vermeiden; wer einen
# aendert, muss den anderen mit-aendern). 'Interne ID-Nummer' + mind. EINE
# Stamm-Spalte trennt Schueler-Exporte verlaesslich von anderen CSV-Typen.
_SCHUELER_BASIC_REQUIRED = ('Interne ID-Nummer',)
_SCHUELER_BASIC_STAMM    = ('Vorname', 'Nachname', 'Klasse')

# Spalten, die der Ausbilder-Workflow konkret braucht. Diese ergeben sich
# direkt aus list_students() / filter_and_write() — siehe row.get(...)-Stellen:
_AUSBILDER_REQUIRED_HARD = (
    'Interne ID-Nummer',         # Matching + Blacklist
    'Klasse',                    # Klassen-Whitelist + UI-Spalte
    'Vorname', 'Nachname',       # UI-Spalten
    'Allg. Adresse: Name1',      # Firma-Filter + UI-Spalte
)
# Optional, aber empfohlen — der Detail-Aufklapper in der Schueler-Tabelle
# zeigt diese Felder; ohne sie wird er rein leer angezeigt.
_AUSBILDER_RECOMMENDED = (
    'Allg. Adresse: Betreuer Anrede',
    'Allg. Adresse: Betreuer Titel',
    'Allg. Adresse: Betreuer Vorname',
    'Allg. Adresse: Betreuer Name',
    'Allg. Adresse: Betreuer E-Mail',
    'Allg. Adresse: Betreuer Telefon',
    'Allg. Adresse: Betreuer Abteilung',
    'Allg. Adresse: Fax-Nr.',
)


def get_schildexport_dir():
    """Liest das Schild-Exporte-Hauptverzeichnis aus settings.ini (gleiche
    Quelle wie die Schueler-Hauptverarbeitung). Default '.': CWD."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'schildexport_directory',
                      fallback='.').strip() or '.'


def get_schueler_export_mode():
    """Liefert den aktiven Quell-Modus fuer den Ausbilder-Workflow:
    'off' (Default) / 'fallback' / 'always'. Siehe Modul-Docstring."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    mode = config.get('Ausbilder', 'schueler_export_mode',
                      fallback='off').strip().lower()
    return mode if mode in _SCHUELER_EXPORT_MODES else 'off'


def save_schueler_export_mode(mode):
    """Speichert den Quell-Modus. Wirft ValueError bei unbekanntem Wert."""
    mode = (mode or '').strip().lower()
    if mode not in _SCHUELER_EXPORT_MODES:
        raise ValueError(
            f"schueler_export_mode muss eines von {_SCHUELER_EXPORT_MODES} sein.")
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    config.set('Ausbilder', 'schueler_export_mode', mode)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def _read_csv_header(path):
    """Liest nur den Header der CSV (gestrippt) — billig auch bei sehr grossen
    Dateien. Liefert [] bei Fehler/leerer Datei."""
    if not path or not os.path.isfile(path):
        return []
    try:
        enc = _detect_encoding(path)
        with open(path, 'r', encoding=enc, newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            return [(c or '').strip() for c in (reader.fieldnames or [])]
    except Exception:
        return []


def _is_schueler_export_file(path):
    """True wenn die CSV grundsaetzlich als 'per-Schueler-Export' erkennbar ist
    (Interne ID-Nummer + mind. eine Stamm-Spalte). Sagt NICHTS darueber aus,
    ob die fuer den Ausbilder-Workflow noetigen Allg.-Adresse-Spalten drin
    sind — dafuer: inspect_schueler_for_ausbilder()."""
    if not path or not os.path.isfile(path):
        return False
    headers = set(_read_csv_header(path))
    if not all(c in headers for c in _SCHUELER_BASIC_REQUIRED):
        return False
    return any(c in headers for c in _SCHUELER_BASIC_STAMM)


def inspect_schueler_for_ausbilder(path):
    """Detail-Inspektion der CSV im schildexport_directory fuer den Ausbilder-
    Single-File-Modus. Symmetrisch zu erzieher_processor.inspect_schueler_for_erzieher.

    Returns dict mit:
      file_exists                 — ist ueberhaupt eine CSV im Verzeichnis?
      is_schueler_export          — Basis-Marker (ID + Stamm) erfuellt?
      usable_for_single_file_mode — alle Ausbilder-Pflichtspalten vorhanden?
      missing_required_hard       — Liste der fehlenden Hart-Pflichtspalten
      present_recommended         — vorhandene empfohlene Spalten (Betreuer-Felder)
      missing_recommended         — fehlende empfohlene Spalten
    """
    info = {
        'file_exists':                 False,
        'is_schueler_export':          False,
        'usable_for_single_file_mode': False,
        'missing_required_hard':       list(_AUSBILDER_REQUIRED_HARD),
        'present_recommended':         [],
        'missing_recommended':         list(_AUSBILDER_RECOMMENDED),
    }
    if not path or not os.path.isfile(path):
        return info
    info['file_exists'] = True
    headers = set(_read_csv_header(path))
    info['is_schueler_export']    = _is_schueler_export_file(path)
    info['missing_required_hard'] = [c for c in _AUSBILDER_REQUIRED_HARD if c not in headers]
    info['present_recommended']   = [c for c in _AUSBILDER_RECOMMENDED if c in headers]
    info['missing_recommended']   = [c for c in _AUSBILDER_RECOMMENDED if c not in headers]
    info['usable_for_single_file_mode'] = not info['missing_required_hard']
    return info


def _resolve_input_path():
    """Liefert den effektiv genutzten Ausbilder-Input-Pfad + Quell-Info fuer
    die UI — analog zu erzieher_processor._resolve_erzieher_path().

    Returns:
        (path_or_None, source_info_dict)
        source_info_dict enthaelt:
          mode               — aktueller Mode ('off'/'fallback'/'always')
          source             — 'ausbilder_input' | 'schueler_export' | None
          ausbilder_csv_path — neueste CSV im ausbilder_input_directory
          schueler_csv_path  — neuester Schueler-Export im schildexport_directory
          schueler_available — True wenn schildexport-CSV ein erkannter Schueler-Export ist
          fell_back          — True wenn mode='fallback' und tatsaechlich auf
                               schildexport_directory ausgewichen wurde
    """
    mode = get_schueler_export_mode()
    ausb_path = _latest_csv(get_input_dir())
    sch_path  = _latest_csv(get_schildexport_dir())
    sch_inspect = inspect_schueler_for_ausbilder(sch_path)
    sch_usable  = sch_inspect['usable_for_single_file_mode']
    info = {
        'mode':                 mode,
        'source':               None,
        'ausbilder_csv_path':   ausb_path,
        'schueler_csv_path':    sch_path if sch_usable else None,
        'schueler_csv_present': bool(sch_path),
        'schueler_available':   sch_usable,
        'schueler_inspect':     sch_inspect,
        'fell_back':            False,
    }
    if mode == 'always' and sch_usable:
        info['source'] = 'schueler_export'
        return sch_path, info
    if mode == 'fallback' and not ausb_path and sch_usable:
        info['source']    = 'schueler_export'
        info['fell_back'] = True
        return sch_path, info
    if ausb_path:
        info['source'] = 'ausbilder_input'
        return ausb_path, info
    return None, info


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_output_name(template):
    now = datetime.now()
    repl = {
        'datum':    now.strftime('%Y-%m-%d'),
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
    if not name.lower().endswith('.csv'):
        name += '.csv'
    return name


def _latest_csv(directory):
    if not directory or not os.path.isdir(directory):
        return None
    files = [f for f in os.listdir(directory) if f.lower().endswith('.csv')]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getctime(os.path.join(directory, f)), reverse=True)
    return os.path.join(directory, files[0])


def _detect_encoding(path):
    """Probiert utf-8-sig zuerst (Standard für Schild-Exports), fällt auf cp1252 zurück."""
    with open(path, 'rb') as f:
        head = f.read(4096)
    if head.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    try:
        head.decode('utf-8')
        return 'utf-8'
    except UnicodeDecodeError:
        return 'cp1252'


def _read_csv_rows(path):
    """Liest die CSV mit ';'-Separator als Liste von Dicts (Header gestrippt)."""
    enc = _detect_encoding(path)
    rows = []
    fieldnames = []
    with open(path, 'r', encoding=enc, newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        if reader.fieldnames:
            reader.fieldnames = [(c or '').strip() for c in reader.fieldnames]
            fieldnames = reader.fieldnames
        for row in reader:
            rows.append({(k or '').strip(): (v or '') for k, v in row.items()})
    return fieldnames, rows


# ---------------------------------------------------------------------------
# Verarbeitung
# ---------------------------------------------------------------------------

def list_students():
    """
    Liest die neueste CSV im Input-Verzeichnis und liefert für die UI:
      {
        'input_directory', 'output_directory', 'output_name_template',
        'latest_csv', 'csv_path',
        'students': [{id, vorname, nachname, klasse, blacklisted}, ...],
        'classes':  [klasse, ...],  # alle vorkommenden Klassen
        'class_filter': [klasse, ...],  # aktuell aktiver Filter
        'blacklist': [id, ...],         # aktuelle Blacklist
      }
    """
    in_dir   = get_input_dir()
    out_dir  = get_output_dir()
    tpl      = get_output_name_template()
    # Resolver respektiert schueler_export_mode — kann auf den Schueler-Export
    # aus schildexport_directory ausweichen / dort sogar Vorrang nehmen.
    csv_path, source_info = _resolve_input_path()
    class_filter      = get_class_filter()
    blacklist         = get_blacklist()
    firma_whitelist   = get_firma_whitelist()
    firma_blacklist   = get_firma_blacklist()
    firma_filter_mode = get_firma_filter_mode()

    students = []
    classes = []
    firms = []
    if csv_path:
        try:
            _, rows = _read_csv_rows(csv_path)
            for row in rows:
                sid     = row.get('Interne ID-Nummer', '').strip()
                klasse  = row.get('Klasse', '').strip()
                if not sid:
                    continue
                students.append({
                    'id':           sid,
                    'vorname':      row.get('Vorname', '').strip(),
                    'nachname':     row.get('Nachname', '').strip(),
                    'klasse':       klasse,
                    'firma':        row.get('Allg. Adresse: Name1', '').strip(),
                    'blacklisted':  sid in blacklist,
                    'ausbilder': {
                        'anrede':    row.get('Allg. Adresse: Betreuer Anrede',    '').strip(),
                        'titel':     row.get('Allg. Adresse: Betreuer Titel',     '').strip(),
                        'vorname':   row.get('Allg. Adresse: Betreuer Vorname',   '').strip(),
                        'nachname':  row.get('Allg. Adresse: Betreuer Name',      '').strip(),
                        'email':     row.get('Allg. Adresse: Betreuer E-Mail',    '').strip(),
                        'telefon':   row.get('Allg. Adresse: Betreuer Telefon',   '').strip(),
                        'abteilung': row.get('Allg. Adresse: Betreuer Abteilung', '').strip(),
                        'fax':       row.get('Allg. Adresse: Fax-Nr.',            '').strip(),
                    },
                })
            # Default-Sortierung: Klasse, Nachname, Vorname (Frontend kann umsortieren)
            students.sort(key=lambda s: (s['klasse'], s['nachname'], s['vorname']))
            classes = sorted({s['klasse'] for s in students if s['klasse']})
            firms   = sorted({s['firma']  for s in students if s['firma']})
            # Zusatz-Ausbilder-DB automatisch aus dem aktuellen Schild-Export
            # befuellen. Sync ist idempotent + schuetzt manuelle Eintraege.
            # Fehler hier bleiben still — die DB ist ein Sekundaer-Feature,
            # darf den Hauptflow nicht blockieren.
            try:
                ausbilder_extra_db.sync_from_schild(students)
            except Exception:
                pass
            # Schueler mit Zusatz-Ausbilder-Anzahl annotieren (>0 = es gibt
            # weitere Co-Ausbilder, die im Schild-Export NICHT auftauchen).
            try:
                for s in students:
                    extras = ausbilder_extra_db.extra_ausbilder_for_export(
                        s['id'], s.get('ausbilder'))
                    s['extra_ausbilder_count'] = len(extras)
            except Exception:
                for s in students:
                    s['extra_ausbilder_count'] = 0
        except Exception:
            pass

    sch_csv = source_info.get('schueler_csv_path')
    return {
        'input_directory':      in_dir,
        'output_directory':     out_dir,
        'output_name_template': tpl,
        'latest_csv':           os.path.basename(csv_path) if csv_path else None,
        'csv_path':             csv_path,
        'students':             students,
        'classes':              classes,
        'firms':                firms,
        'class_filter':         class_filter,
        'blacklist':            sorted(blacklist),
        'firma_whitelist':      firma_whitelist,
        'firma_blacklist':      firma_blacklist,
        'firma_filter_mode':    firma_filter_mode,
        # Single-File-Konsolidierung (3.2)
        'schueler_export_mode':   get_schueler_export_mode(),
        'schueler_export_source': source_info,
        'schildexport_directory': get_schildexport_dir(),
        'latest_schueler_export': os.path.basename(sch_csv) if sch_csv else None,
        # KL-Mail-Versand (3.2) — fuer Settings-Panel-Hydration
        'kl_mail_respect_class_whitelist': get_kl_mail_respect_class_whitelist(),
        'kl_mail_respect_blacklist':       get_kl_mail_respect_blacklist(),
        'kl_mail_respect_firma_filter':    get_kl_mail_respect_firma_filter(),
        'kl_mail_include_stv_kl':          get_kl_mail_include_stv_kl(),
        'kl_mail_subject_suffix':          get_kl_mail_subject_suffix(),
    }


def filter_and_write(input_path=None, classes=None, blacklist=None, output_dir=None,
                     name_template=None, firma_whitelist=None, firma_blacklist=None,
                     firma_filter_mode=None):
    """
    Liest die CSV, filtert nach Klassen-Whitelist, Schueler-Blacklist und (je nach
    firma_filter_mode) Firma-Whitelist ODER Firma-Blacklist, schreibt eine neue
    CSV ins Ausgabeverzeichnis.
    Liefert (output_pfad, output_name, anzahl_eingang, anzahl_ausgang,
             anzahl_extra_rows).
    anzahl_ausgang = primaere Schueler-Zeilen aus Schild,
    anzahl_extra_rows = zusaetzliche Zeilen aus der Zusatz-Ausbilder-DB
    (jeweils derselbe Schueler mit einem Co-Ausbilder, der in der Schild-
    Zeile nicht stand).
    """
    if input_path is None:
        # Resolver respektiert schueler_export_mode — siehe list_students()
        # fuer Details.
        input_path, _src = _resolve_input_path()
    classes           = list(classes) if classes is not None else get_class_filter()
    blacklist_set     = set(blacklist) if blacklist is not None else get_blacklist()
    firma_mode        = (firma_filter_mode or get_firma_filter_mode())
    # Es ist immer nur EINE der beiden Firma-Listen wirksam (per Mode-Setting).
    # Die andere bleibt zwar in der INI gespeichert, wirkt aber nicht auf den Export.
    if firma_mode == 'whitelist':
        firma_white_set = set(firma_whitelist) if firma_whitelist is not None else set(get_firma_whitelist())
        firma_black_set = set()
    else:  # 'blacklist'
        firma_white_set = set()
        firma_black_set = set(firma_blacklist) if firma_blacklist is not None else set(get_firma_blacklist())
    output_dir        = output_dir or get_output_dir()
    name_template     = name_template or get_output_name_template()

    if not input_path or not os.path.isfile(input_path):
        raise FileNotFoundError("Keine CSV-Datei im Ausbilder-Input-Verzeichnis gefunden.")

    fieldnames, rows = _read_csv_rows(input_path)
    if not fieldnames:
        raise ValueError("Eingangsdatei hat keine Spaltenüberschriften.")

    klassen_set = {c.strip() for c in classes if c.strip()}
    # Sentinel '__NONE__': Benutzer hat explizit "keine Klasse aktiv" gewaehlt
    # (im Gegensatz zur Default-Semantik leer = alle Klassen).
    none_mode = '__NONE__' in klassen_set
    if none_mode:
        klassen_set = set()
    filtered = []
    for row in rows:
        if none_mode:
            continue
        sid    = row.get('Interne ID-Nummer', '').strip()
        klasse = row.get('Klasse', '').strip()
        firma  = row.get('Allg. Adresse: Name1', '').strip()
        if klassen_set and klasse not in klassen_set:
            continue
        if sid in blacklist_set:
            continue
        # Firma-Whitelist: wenn gesetzt, muss die Firma drin sein
        if firma_white_set and firma not in firma_white_set:
            continue
        # Firma-Blacklist: wenn die Firma drin steht, raus damit
        if firma and firma in firma_black_set:
            continue
        filtered.append(row)

    os.makedirs(output_dir, exist_ok=True)
    name = _resolve_output_name(name_template)
    out_path = os.path.join(output_dir, name)
    # Konfliktauflösung
    if os.path.exists(out_path):
        base, ext = os.path.splitext(name)
        name = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"
        out_path = os.path.join(output_dir, name)

    # Mapping DB-Feldnamen -> Schild-CSV-Spaltennamen fuer die Co-Ausbilder-
    # Zeilen. 'fax' nutzt die generische Fax-Nr. (identisch zu list_students).
    _BETREUER_COL = {
        'anrede':    'Allg. Adresse: Betreuer Anrede',
        'titel':     'Allg. Adresse: Betreuer Titel',
        'vorname':   'Allg. Adresse: Betreuer Vorname',
        'nachname':  'Allg. Adresse: Betreuer Name',
        'email':     'Allg. Adresse: Betreuer E-Mail',
        'telefon':   'Allg. Adresse: Betreuer Telefon',
        'abteilung': 'Allg. Adresse: Betreuer Abteilung',
        'fax':       'Allg. Adresse: Fax-Nr.',
    }

    extra_rows_total = 0
    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for row in filtered:
            # 1) Original-Zeile aus Schild (= primaerer Betreuer)
            writer.writerow({k: row.get(k, '') for k in fieldnames})
            # 2) Zusatz-Zeilen aus der Ausbilder-Extra-DB — pro Co-Ausbilder
            #    eine weitere Zeile mit identischem Schueler-Teil und ueber-
            #    schriebenem Betreuer-Block. Fehler hier sind Sekundaer-Feature-
            #    Fehler und duerfen den Hauptexport nicht stoppen.
            try:
                sid = (row.get('Interne ID-Nummer') or '').strip()
                if not sid:
                    continue
                current = {
                    db_k: (row.get(csv_k) or '').strip()
                    for db_k, csv_k in _BETREUER_COL.items()
                }
                extras = ausbilder_extra_db.extra_ausbilder_for_export(
                    sid, current)
                for extra in extras:
                    new_row = {k: row.get(k, '') for k in fieldnames}
                    for db_k, csv_k in _BETREUER_COL.items():
                        if csv_k in new_row:
                            new_row[csv_k] = extra.get(db_k, '') or ''
                    writer.writerow(new_row)
                    extra_rows_total += 1
            except Exception:
                continue

    return out_path, name, len(rows), len(filtered), extra_rows_total


# ===========================================================================
# KL-Mail-Versand (3.2): Aktuelle Ausbilder-/Betreuer-Daten an Klassen-
# lehrkraefte zur Info + Kontrolle (Korrektur ueber das Sekretariat in Schild).
# ===========================================================================
#
# Designprinzip: dieselbe Quelle wie die WebUntis-Verarbeitung (Schueler-Export,
# je nach schueler_export_mode aus AusbilderInput oder schildexport_directory).
# KL/Stv-KL + E-Mails kommen aus dem bestehenden classes_by_name-Lookup (main.py
# read_classes()) — identisch zu admin_warnings(), damit keine Sondersemantik.
#
# Optionen (alle in [Ausbilder]-Section, default = bisheriges Verhalten gespiegelt):
#   kl_mail_respect_class_whitelist (bool, default True)
#     Klassen-Whitelist greift auch auf die KL-Mail. False = ALLE Klassen aus
#     dem Schueler-Export bekommen eine Mail, egal welche Whitelist-Konfiguration.
#   kl_mail_respect_blacklist (bool, default True)
#     Schueler-Blacklist greift. False = auch geblacklistete Schueler tauchen in
#     der KL-Mail-Tabelle auf (DSGVO-relevant — pruefen!).
#   kl_mail_respect_firma_filter (bool, default True)
#     Firmen-Whitelist/-Blacklist greift identisch zur Verarbeitung.
#   kl_mail_include_stv_kl (bool, default True)
#     Stv-Klassenlehrkraft als CC-Empfaenger der Mail.
#   kl_mail_subject_suffix (str, default '')
#     Optionaler Zusatz im Betreff (z.B. '[TEST]' fuer Probelaeufe).
# ---------------------------------------------------------------------------

# Default-Templates fuer die KL-Mail. Werden bei Bedarf in email_settings.ini
# als [Templates].subject_ausbilder_kl_uebersicht / body_ausbilder_kl_uebersicht
# ergaenzt — der bestehende E-Mail-Editor kann sie dann WYSIWYG anpassen.
DEFAULT_KL_MAIL_SUBJECT = (
    'Ausbilder-/Betreuer-Daten Ihrer Klasse $Klasse — Stand $Stand'
)
DEFAULT_KL_MAIL_BODY = (
    '<p>Sehr geehrte/r $Klassenlehrer_Anrede $Klassenlehrer_Name,</p>'
    '<p>anbei die aktuell in Schild hinterlegten Ausbilder-/Betreuer-Daten '
    'Ihrer Klasse <strong>$Klasse</strong> (Stand $Stand). Diese werden in '
    'WebUntis übernommen, damit die Ausbilder die Fehlstunden ihrer '
    'Auszubildenden einsehen können.</p>'
    '<p><strong>Bitte prüfen</strong> Sie die Daten und veranlassen Sie ggf. '
    'eine Korrektur über das Sekretariat in Schild. Eine Excel-Datei mit '
    'denselben Daten finden Sie zusätzlich im Anhang (zur Weiterleitung an '
    'das Sekretariat oder zur Bearbeitung).</p>'
    '$Schueler_Tabelle_HTML'
    '<p>Mit freundlichen Grüßen<br>'
    'Ihre WebUntis-Pflege</p>'
)


def _get_bool(key, default):
    """Liest [Ausbilder].<key> als bool (Default identisch zu allen
    bisherigen Settings-Gettern in dieser Datei)."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Ausbilder', key, fallback=default)


def _set_bool(key, value):
    """Speichert [Ausbilder].<key> als True/False."""
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    config.set('Ausbilder', key, 'True' if value else 'False')
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_kl_mail_respect_class_whitelist(): return _get_bool('kl_mail_respect_class_whitelist', True)
def get_kl_mail_respect_blacklist():       return _get_bool('kl_mail_respect_blacklist', True)
def get_kl_mail_respect_firma_filter():    return _get_bool('kl_mail_respect_firma_filter', True)
def get_kl_mail_include_stv_kl():          return _get_bool('kl_mail_include_stv_kl', True)


def get_kl_mail_subject_suffix():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Ausbilder', 'kl_mail_subject_suffix', fallback='').strip()


def save_kl_mail_settings(settings):
    """Bulk-Speichern aller KL-Mail-Einstellungen aus einem Dict.
    Akzeptierte Keys: kl_mail_respect_class_whitelist, kl_mail_respect_blacklist,
    kl_mail_respect_firma_filter, kl_mail_include_stv_kl, kl_mail_subject_suffix."""
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    bool_keys = ('kl_mail_respect_class_whitelist', 'kl_mail_respect_blacklist',
                 'kl_mail_respect_firma_filter', 'kl_mail_include_stv_kl')
    for k in bool_keys:
        if k in settings:
            config.set('Ausbilder', k, 'True' if settings[k] else 'False')
    if 'kl_mail_subject_suffix' in settings:
        config.set('Ausbilder', 'kl_mail_subject_suffix',
                   str(settings['kl_mail_subject_suffix'] or '').strip())
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


# ---------------------------------------------------------------------------
# Datenaufbereitung
# ---------------------------------------------------------------------------

def _student_passes_kl_mail_filters(row, class_whitelist_set, none_mode,
                                    blacklist_set, firma_white_set,
                                    firma_black_set, opts):
    """Wiederverwendung der filter_and_write()-Logik, aber mit pro-Filter
    Toggle (siehe opts). True = Schueler darf in die KL-Mail-Tabelle.

    opts ist ein Tupel (respect_class, respect_blacklist, respect_firma) —
    zwecks Hot-Path-Klarheit hier inline statt eines Dicts."""
    respect_class, respect_blacklist, respect_firma = opts
    sid    = row.get('Interne ID-Nummer', '').strip()
    klasse = row.get('Klasse', '').strip()
    firma  = row.get('Allg. Adresse: Name1', '').strip()
    if respect_class:
        if none_mode:
            return False
        if class_whitelist_set and klasse not in class_whitelist_set:
            return False
    if respect_blacklist and sid in blacklist_set:
        return False
    if respect_firma:
        # Identische Semantik wie filter_and_write(): Whitelist verlangt
        # Treffer, Blacklist schlaegt zu wenn Firma drin steht.
        if firma_white_set and firma not in firma_white_set:
            return False
        if firma and firma in firma_black_set:
            return False
    return True


def build_kl_mail_data(classes_by_name=None, input_path=None):
    """Liefert die Pro-Klasse-Daten fuer den KL-Mail-Versand.

    Args:
        classes_by_name: dict {klasse.lower(): {Klassenlehrkraft_1, ...,
            Klassenlehrkraft_2_Email}} aus main.read_classes(). Wenn None,
            wird leer angenommen — Empfaenger sind dann nicht aufloesbar
            (UI muss das anzeigen).
        input_path: optional, sonst Resolver wie list_students/filter_and_write.

    Returns:
        {
          'csv_path':      genutzte Quelle (str),
          'classes':       [{
              'klasse':        'DI24a',
              'kl_name':       'Mones, Christoph' (oder ''),
              'kl_email':      'mones@... ' (oder ''),
              'stv_kl_name':   '...',
              'stv_kl_email':  '...',
              'students':      [{
                  'id', 'vorname', 'nachname', 'firma',
                  'betreuer_anrede', 'betreuer_titel',
                  'betreuer_vorname', 'betreuer_nachname',
                  'betreuer_email', 'betreuer_telefon',
                  'betreuer_abteilung', 'betreuer_fax',
              }, ...],
          }, ...],
          'stats': {
              'students_total': int, 'students_after_filters': int,
              'classes_total': int, 'classes_without_kl_email': int,
              'classes_dropped_no_students': int,
          },
          'options_used': {respect_class, respect_blacklist, respect_firma,
                           include_stv_kl, subject_suffix},
        }
    """
    if input_path is None:
        input_path, _ = _resolve_input_path()
    if not input_path or not os.path.isfile(input_path):
        raise FileNotFoundError("Keine Schild-CSV fuer den KL-Mail-Versand gefunden.")
    _, rows = _read_csv_rows(input_path)
    if not rows:
        return {'csv_path': input_path, 'classes': [],
                'stats': {'students_total': 0, 'students_after_filters': 0,
                          'classes_total': 0, 'classes_without_kl_email': 0,
                          'classes_dropped_no_students': 0},
                'options_used': {}}

    # Filter-Optionen
    respect_class     = get_kl_mail_respect_class_whitelist()
    respect_blacklist = get_kl_mail_respect_blacklist()
    respect_firma     = get_kl_mail_respect_firma_filter()
    include_stv_kl    = get_kl_mail_include_stv_kl()
    subject_suffix    = get_kl_mail_subject_suffix()
    opts = (respect_class, respect_blacklist, respect_firma)

    # Filter-Sets vorbereiten (identisch zu filter_and_write())
    classes_list      = get_class_filter()
    klassen_set       = {c.strip() for c in classes_list if c.strip()}
    none_mode         = '__NONE__' in klassen_set
    if none_mode:
        klassen_set = set()
    blacklist_set     = get_blacklist()
    firma_mode        = get_firma_filter_mode()
    if firma_mode == 'whitelist':
        firma_white_set = set(get_firma_whitelist())
        firma_black_set = set()
    else:
        firma_white_set = set()
        firma_black_set = set(get_firma_blacklist())

    students_total           = 0
    students_after_filters   = 0
    by_class                 = {}  # klasse -> list of student dicts
    for row in rows:
        if not row.get('Interne ID-Nummer', '').strip():
            continue
        students_total += 1
        if not _student_passes_kl_mail_filters(
                row, klassen_set, none_mode, blacklist_set,
                firma_white_set, firma_black_set, opts):
            continue
        students_after_filters += 1
        klasse = row.get('Klasse', '').strip() or '(ohne Klasse)'
        by_class.setdefault(klasse, []).append({
            'id':                  row.get('Interne ID-Nummer', '').strip(),
            'vorname':             row.get('Vorname', '').strip(),
            'nachname':            row.get('Nachname', '').strip(),
            'firma':               row.get('Allg. Adresse: Name1', '').strip(),
            'betreuer_anrede':     row.get('Allg. Adresse: Betreuer Anrede', '').strip(),
            'betreuer_titel':      row.get('Allg. Adresse: Betreuer Titel', '').strip(),
            'betreuer_vorname':    row.get('Allg. Adresse: Betreuer Vorname', '').strip(),
            'betreuer_nachname':   row.get('Allg. Adresse: Betreuer Name', '').strip(),
            'betreuer_email':      row.get('Allg. Adresse: Betreuer E-Mail', '').strip(),
            'betreuer_telefon':    row.get('Allg. Adresse: Betreuer Telefon', '').strip(),
            'betreuer_abteilung':  row.get('Allg. Adresse: Betreuer Abteilung', '').strip(),
            'betreuer_fax':        row.get('Allg. Adresse: Fax-Nr.', '').strip(),
        })

    # KL-Lookup
    classes_by_name = classes_by_name or {}
    classes_out = []
    classes_without_kl_email = 0
    for klasse, students in sorted(by_class.items()):
        students.sort(key=lambda s: (s['nachname'].lower(), s['vorname'].lower()))
        klasse_lower = klasse.lower()
        kl_info = classes_by_name.get(klasse_lower, {}) or {}
        kl_email     = (kl_info.get('Klassenlehrkraft_1_Email') or '').strip()
        stv_kl_email = (kl_info.get('Klassenlehrkraft_2_Email') or '').strip() if include_stv_kl else ''
        # 'Keine E-Mail gefunden' ist die Sentinel-Loesung in read_classes() —
        # behandeln wie leer, damit das Frontend dasselbe sieht.
        if kl_email == 'Keine E-Mail gefunden': kl_email = ''
        if stv_kl_email == 'Keine E-Mail gefunden': stv_kl_email = ''
        if not kl_email:
            classes_without_kl_email += 1
        classes_out.append({
            'klasse':       klasse,
            'kl_name':      (kl_info.get('Klassenlehrkraft_1') or '').strip(),
            'kl_email':     kl_email,
            'stv_kl_name':  (kl_info.get('Klassenlehrkraft_2') or '').strip(),
            'stv_kl_email': stv_kl_email,
            'students':     students,
        })

    return {
        'csv_path':     input_path,
        'classes':      classes_out,
        'stats': {
            'students_total':              students_total,
            'students_after_filters':      students_after_filters,
            'classes_total':               len(classes_out),
            'classes_without_kl_email':    classes_without_kl_email,
            'classes_dropped_no_students': 0,  # by_class enthaelt nur nicht-leere Klassen
        },
        'options_used': {
            'respect_class':     respect_class,
            'respect_blacklist': respect_blacklist,
            'respect_firma':     respect_firma,
            'include_stv_kl':    include_stv_kl,
            'subject_suffix':    subject_suffix,
        },
    }


# ---------------------------------------------------------------------------
# HTML-Tabelle + Subject/Body-Rendering (Platzhalter aus Template ersetzen)
# ---------------------------------------------------------------------------

def _kl_anrede_short(kl_full_name):
    """Sehr grobe Heuristik fuer 'Herr/Frau' aus 'Vorname Nachname'. Liefert ''
    wenn unklar — das Template hat dann nur den Nachnamen. Schild liefert
    die Anrede nicht separat in der Klassen-CSV, deshalb diese Naeherung."""
    if not kl_full_name:
        return ''
    # Vorname extrahieren (alles vor dem ersten Leerzeichen)
    first = kl_full_name.strip().split(' ', 1)[0]
    # Sehr typisches deutsches weibl.-endung — alles andere lassen wir leer
    if first.endswith(('a', 'e', 'i')) and len(first) > 2:
        return 'Frau'
    return 'Herr'


def render_student_table_html(students):
    """Baut die HTML-Tabelle, die {Schueler_Tabelle_HTML} im Body ersetzt.
    Inline-Styles, damit's in Outlook/Gmail/Thunderbird zuverlaessig rendert."""
    if not students:
        return '<p><em>Keine Schueler in dieser Klasse nach den aktiven Filtern.</em></p>'
    th = ('background:#f0f0f0; border:1px solid #ccc; padding:6px 8px; '
          'text-align:left; font-size:0.9em;')
    td = 'border:1px solid #ccc; padding:5px 8px; font-size:0.9em; vertical-align:top;'
    out = ['<table style="border-collapse:collapse; border:1px solid #ccc; '
           'margin:8px 0; width:100%;">']
    out.append('<thead><tr>'
               f'<th style="{th}">Schüler</th>'
               f'<th style="{th}">Firma</th>'
               f'<th style="{th}">Betreuer</th>'
               f'<th style="{th}">E-Mail</th>'
               f'<th style="{th}">Telefon</th>'
               f'<th style="{th}">Abteilung</th>'
               '</tr></thead><tbody>')
    for s in students:
        schueler  = _html_escape(f"{s['nachname']}, {s['vorname']}")
        firma     = _html_escape(s['firma'] or '—')
        betreuer  = _html_escape(' '.join(p for p in (
            s['betreuer_anrede'], s['betreuer_titel'],
            s['betreuer_vorname'], s['betreuer_nachname']) if p).strip() or '—')
        email     = _html_escape(s['betreuer_email'] or '—')
        if s['betreuer_email']:
            email = f'<a href="mailto:{email}">{email}</a>'
        telefon   = _html_escape(s['betreuer_telefon'] or '—')
        abteilung = _html_escape(s['betreuer_abteilung'] or '—')
        out.append('<tr>'
                   f'<td style="{td}">{schueler}</td>'
                   f'<td style="{td}">{firma}</td>'
                   f'<td style="{td}">{betreuer}</td>'
                   f'<td style="{td}">{email}</td>'
                   f'<td style="{td}">{telefon}</td>'
                   f'<td style="{td}">{abteilung}</td>'
                   '</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


def _html_escape(s):
    """Minimaler HTML-Escape ohne Modulabhaengigkeit (csv ist auch import)."""
    s = str(s or '')
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


def render_kl_mail(class_data, subject_template=None, body_template=None,
                   stand_date=None, subject_suffix=''):
    """Setzt die Template-Platzhalter ein.

    Returns: (subject_str, body_html_str).
    """
    subject_template = subject_template or DEFAULT_KL_MAIL_SUBJECT
    body_template    = body_template    or DEFAULT_KL_MAIL_BODY
    stand_date       = stand_date       or datetime.now().strftime('%d.%m.%Y')
    kl_full          = class_data.get('kl_name') or ''
    kl_anrede        = _kl_anrede_short(kl_full)
    # Reihenfolge wichtig: laengere Keys zuerst, damit '$Klassenlehrer_Name' nicht
    # versehentlich nur das '$Klasse'-Praefix sieht und der Rest stehen bleibt.
    # OrderedDict-Verhalten ist seit Python 3.7 fuer dicts garantiert; wir
    # listen sie bewusst in fallender Laenge.
    repl_pairs = [
        ('$Schueler_Tabelle_HTML', render_student_table_html(class_data.get('students', []))),
        ('$Klassenlehrer_Anrede',  kl_anrede),
        ('$Klassenlehrer_Name',    kl_full),
        ('$Klassenlehrer_E-Mail',  class_data.get('kl_email', '')),
        ('$Schueler_Anzahl',       str(len(class_data.get('students', [])))),
        ('$Klasse',                class_data.get('klasse', '')),
        ('$Stand',                 stand_date),
    ]
    subject = subject_template
    body    = body_template
    for k, v in repl_pairs:
        subject = subject.replace(k, v)
        body    = body.replace(k, v)
    if subject_suffix:
        subject = f"{subject_suffix} {subject}".strip()
    return subject, body


# ---------------------------------------------------------------------------
# Excel-Anhang (.xlsx) — eine Mappe pro Klasse, identische Datenbasis wie HTML
# ---------------------------------------------------------------------------

def build_kl_mail_xlsx(class_data, stand_date=None):
    """Erzeugt eine xlsx-Mappe (in-memory bytes) fuer eine Klasse.
    Reine Daten-Output, kein File-System-Side-Effect — Caller entscheidet,
    ob Datei oder Mail-Anhang.

    Spalten ausfuehrlicher als die HTML-Tabelle, damit das Sekretariat direkt
    danach filter/sortieren kann.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    import io

    stand_date = stand_date or datetime.now().strftime('%d.%m.%Y')
    wb = Workbook()
    ws = wb.active
    ws.title = (class_data.get('klasse') or 'Klasse')[:31]  # xlsx-Limit

    # Kopfblock (Klasse, Stand) ueber der Tabelle — KL-Mail soll auch nach
    # 'gespeichert + offline geschickt' verstaendlich bleiben.
    ws['A1'] = f"Ausbilder-/Betreuer-Daten Klasse {class_data.get('klasse', '')}"
    ws['A1'].font = Font(bold=True, size=13)
    ws['A2'] = f"Stand: {stand_date}"
    ws['A2'].font = Font(italic=True, size=10)
    kl_line = []
    if class_data.get('kl_name'):
        kl_line.append(f"KL: {class_data['kl_name']}")
    if class_data.get('stv_kl_name'):
        kl_line.append(f"Stv-KL: {class_data['stv_kl_name']}")
    if kl_line:
        ws['A3'] = ' · '.join(kl_line)
        ws['A3'].font = Font(italic=True, size=10)

    header_row = 5
    headers = [
        'Schüler-ID', 'Klasse', 'Nachname', 'Vorname',
        'Firma',
        'Betreuer-Anrede', 'Betreuer-Titel',
        'Betreuer-Vorname', 'Betreuer-Nachname',
        'Betreuer-E-Mail', 'Betreuer-Telefon', 'Betreuer-Abteilung', 'Fax',
    ]
    header_fill = PatternFill('solid', fgColor='DDDDDD')
    header_font = Font(bold=True)
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=header_row, column=ci, value=h)
        c.font = header_font
        c.fill = header_fill
        c.alignment = Alignment(vertical='top')

    klasse_name = class_data.get('klasse', '')
    for ri, s in enumerate(class_data.get('students', []), start=header_row + 1):
        ws.cell(row=ri, column=1,  value=s.get('id', ''))
        ws.cell(row=ri, column=2,  value=klasse_name)
        ws.cell(row=ri, column=3,  value=s.get('nachname', ''))
        ws.cell(row=ri, column=4,  value=s.get('vorname', ''))
        ws.cell(row=ri, column=5,  value=s.get('firma', ''))
        ws.cell(row=ri, column=6,  value=s.get('betreuer_anrede', ''))
        ws.cell(row=ri, column=7,  value=s.get('betreuer_titel', ''))
        ws.cell(row=ri, column=8,  value=s.get('betreuer_vorname', ''))
        ws.cell(row=ri, column=9,  value=s.get('betreuer_nachname', ''))
        ws.cell(row=ri, column=10, value=s.get('betreuer_email', ''))
        ws.cell(row=ri, column=11, value=s.get('betreuer_telefon', ''))
        ws.cell(row=ri, column=12, value=s.get('betreuer_abteilung', ''))
        ws.cell(row=ri, column=13, value=s.get('betreuer_fax', ''))

    # Spaltenbreiten grob an typische Inhalte angepasst.
    widths = [10, 8, 18, 16, 28, 8, 8, 16, 18, 32, 18, 22, 14]
    for ci, w in enumerate(widths, 1):
        ws.column_dimensions[chr(ord('A') + ci - 1)].width = w

    # Autofilter ueber dem Header-Block
    last_col_letter = chr(ord('A') + len(headers) - 1)
    ws.auto_filter.ref = f"A{header_row}:{last_col_letter}{header_row + len(class_data.get('students', []))}"
    ws.freeze_panes = ws.cell(row=header_row + 1, column=1)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def safe_class_filename(klasse):
    """Macht aus 'BSM-3,5 jähr.' einen Datei-Namen-tauglichen String —
    behaelt Lesbarkeit. Spiegelt das Pattern aus write_missing_report_zip im
    erzieher_processor."""
    return re.sub(r'[<>:"/\\|?*]', '_', klasse or 'Klasse')
