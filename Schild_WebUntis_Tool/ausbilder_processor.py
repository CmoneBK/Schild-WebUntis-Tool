"""
Ausbilder-/Betreuer-Workflow (Phase 3).

Portiert die Logik des Standalone-Tools "AusbilderImporterFlask" — speziell für
Berufskollegs in NRW — ohne Pandas-Abhängigkeit.

Idee:
  - Schild exportiert Auszubildende inkl. Betreuer-Daten als CSV.
  - In WebUntis dürfen Ausbilder nur Fehlstunden derjenigen Azubis sehen, die der
    Datenverarbeitung zugestimmt haben (VO DVI, DSGVO).
  - Tool filtert die CSV nach Klassen-Whitelist UND blendet Schüler aus, die auf
    einer Blacklist stehen (keine Einwilligung) → fertige WebUntis-Import-CSV.
"""

import os
import re
import csv
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
    class_filter = get_class_filter()
    blacklist = get_blacklist()

    students = []
    classes = []
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
                    'blacklisted':  sid in blacklist,
                })
            # Sortierung: Klasse, dann Nachname
            students.sort(key=lambda s: (s['klasse'], s['nachname'], s['vorname']))
            classes = sorted({s['klasse'] for s in students if s['klasse']})
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
        'class_filter':         class_filter,
        'blacklist':            sorted(blacklist),
    }


def filter_and_write(input_path=None, classes=None, blacklist=None, output_dir=None, name_template=None):
    """
    Liest die CSV, filtert nach Klassen-Whitelist UND Blacklist, schreibt
    eine neue CSV ins Ausgabeverzeichnis.
    Liefert (output_pfad, output_name, anzahl_eingang, anzahl_ausgang).
    """
    input_path    = input_path or _latest_csv(get_input_dir())
    classes       = list(classes) if classes is not None else get_class_filter()
    blacklist_set = set(blacklist) if blacklist is not None else get_blacklist()
    output_dir    = output_dir or get_output_dir()
    name_template = name_template or get_output_name_template()

    if not input_path or not os.path.isfile(input_path):
        raise FileNotFoundError("Keine CSV-Datei im Ausbilder-Input-Verzeichnis gefunden.")

    fieldnames, rows = _read_csv_rows(input_path)
    if not fieldnames:
        raise ValueError("Eingangsdatei hat keine Spaltenüberschriften.")

    klassen_set = {c.strip() for c in classes if c.strip()}
    filtered = []
    for row in rows:
        sid    = row.get('Interne ID-Nummer', '').strip()
        klasse = row.get('Klasse', '').strip()
        if klassen_set and klasse not in klassen_set:
            continue
        if sid in blacklist_set:
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
