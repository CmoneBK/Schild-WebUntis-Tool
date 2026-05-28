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


DEFAULT_OUTPUT_NAME_TEMPLATE = 'WebUntis_Ausbilder_Import_{datetime}'


def safe_read_config(config, path):
    try:
        config.read(path, encoding='utf-8-sig')
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

def get_input_dir():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'ausbilder_input_directory', fallback='AusbilderInput').strip() or 'AusbilderInput'


def get_output_dir():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'ausbilder_output_directory', fallback='AusbilderImportDateien').strip() or 'AusbilderImportDateien'


def get_output_name_template():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Ausbilder', 'output_name_template', fallback=DEFAULT_OUTPUT_NAME_TEMPLATE).strip() or DEFAULT_OUTPUT_NAME_TEMPLATE


def save_output_name_template(template):
    template = (template or '').strip()
    if not template:
        return
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    config.set('Ausbilder', 'output_name_template', template)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_class_filter():
    """Liefert Liste der zu berücksichtigenden Klassen (leer = alle)."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    raw = config.get('Ausbilder', 'class_filter', fallback='').strip()
    if not raw:
        return []
    return [c.strip() for c in raw.split(',') if c.strip()]


def save_class_filter(classes):
    """Speichert Klassen-Whitelist (List[str])."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    cleaned = [str(c).strip() for c in (classes or []) if str(c).strip()]
    config.set('Ausbilder', 'class_filter', ','.join(cleaned))
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_blacklist():
    """Liefert Set von Schüler-IDs, die ausgeschlossen werden."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    raw = config.get('Ausbilder', 'blacklist_ids', fallback='').strip()
    if not raw:
        return set()
    return {s.strip() for s in raw.split(',') if s.strip()}


def save_blacklist(ids):
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
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
    config = configparser.ConfigParser()
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
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
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
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    mode = config.get('Ausbilder', 'firma_filter_mode', fallback='blacklist').strip().lower()
    return mode if mode in ('whitelist', 'blacklist') else 'blacklist'


def save_firma_filter_mode(mode):
    mode = (mode or '').strip().lower()
    if mode not in ('whitelist', 'blacklist'):
        raise ValueError("mode muss 'whitelist' oder 'blacklist' sein.")
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('Ausbilder'):
        config.add_section('Ausbilder')
    config.set('Ausbilder', 'firma_filter_mode', mode)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


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
    csv_path = _latest_csv(in_dir)
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
        except Exception:
            pass

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
    }


def filter_and_write(input_path=None, classes=None, blacklist=None, output_dir=None,
                     name_template=None, firma_whitelist=None, firma_blacklist=None,
                     firma_filter_mode=None):
    """
    Liest die CSV, filtert nach Klassen-Whitelist, Schueler-Blacklist und (je nach
    firma_filter_mode) Firma-Whitelist ODER Firma-Blacklist, schreibt eine neue
    CSV ins Ausgabeverzeichnis.
    Liefert (output_pfad, output_name, anzahl_eingang, anzahl_ausgang).
    """
    input_path        = input_path or _latest_csv(get_input_dir())
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

    with open(out_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()
        for row in filtered:
            # Nur die Original-Spalten ausgeben (verhindert dass evtl. ergänzte Keys mit reinrutschen)
            writer.writerow({k: row.get(k, '') for k in fieldnames})

    return out_path, name, len(rows), len(filtered)
