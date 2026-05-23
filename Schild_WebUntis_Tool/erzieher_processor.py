"""
Erzieher-/Ansprechpartner-Verarbeitung (Phase 2).

Portiert die Logik des Standalone-Tools "SchildNRW-WebUntis Erzieher-Konvertierer"
ohne Pandas-Abhängigkeit (kleinere EXE, weniger Bloat).

Idee:
  - Schild exportiert Erzieher (Hauptdaten) und Ansprechpartner (separate Datei
    mit Telefonnummern) getrennt.
  - WebUntis erwartet pro Erzieher/Ansprechpartner einen eigenen Datensatz inkl.
    Telefonnummer.
  - Wir bauen pro „n-tem Erzieher" eines Schülers eine eigene Import-Datei
    (Erzieher_1.csv, Erzieher_2.csv, …) und packen alle in ein ZIP.
"""

import os
import io
import re
import csv
import zipfile
import configparser
from datetime import datetime


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
    return {
        'erzieher_export_directory':        erz_dir,
        'ansprechpartner_export_directory': ansp_dir,
        'output_directory':                 out_dir,
        'zip_name_template':                get_zip_name_template(),
        'latest_erzieher_export':           os.path.basename(erz_file) if erz_file else None,
        'latest_ansprechpartner_export':    os.path.basename(ansp_file) if ansp_file else None,
        'erzieher_export_path':             erz_file,
        'ansprechpartner_export_path':      ansp_file,
    }


def process(erzieher_path=None, ansprechpartner_path=None):
    """
    Verarbeitet die zwei CSVs und liefert (result_files, stats):
      result_files: {dateiname_ohne_ext: [row_dict, ...]}
      stats: {'erzieher_rows', 'ansprechpartner_rows', 'max_erzieher', 'output_files'}
    """
    erzieher_path = erzieher_path or _latest_csv(get_erzieher_export_dir())
    ansprechpartner_path = ansprechpartner_path or _latest_csv(get_ansprechpartner_export_dir())

    if not erzieher_path or not os.path.isfile(erzieher_path):
        raise FileNotFoundError("Keine Erzieher-Export-CSV gefunden. Bitte Verzeichnis prüfen.")
    if not ansprechpartner_path or not os.path.isfile(ansprechpartner_path):
        raise FileNotFoundError("Keine Ansprechpartner-Export-CSV gefunden. Bitte Verzeichnis prüfen.")

    erz_rows  = _read_csv_rows(erzieher_path)
    ansp_rows = _read_csv_rows(ansprechpartner_path)

    if not erz_rows:
        raise ValueError("Erzieher-Export ist leer.")
    if not ansp_rows:
        raise ValueError("Ansprechpartner-Export ist leer.")

    # Spalten-Validierung
    if 'Interne ID-Nummer' not in erz_rows[0]:
        raise ValueError("Spalte 'Interne ID-Nummer' fehlt im Erzieher-Export.")
    if 'Schüler_ID' not in ansp_rows[0]:
        raise ValueError("Spalte 'Schüler_ID' fehlt im Ansprechpartner-Export.")

    # Ansprechpartner: nach Schüler-ID sortieren und Erzieher_Nummer (1..N) je Schüler zuweisen
    ansp_rows.sort(key=lambda r: r.get('Schüler_ID', ''))
    last_sid, counter = None, 0
    for row in ansp_rows:
        sid = row.get('Schüler_ID', '')
        if sid != last_sid:
            counter = 1
            last_sid = sid
        else:
            counter += 1
        row['Erzieher_Nummer'] = counter

    max_erzieher = max((r['Erzieher_Nummer'] for r in ansp_rows), default=0)

    # Pro Erzieher-Index eine Ergebnisdatei bauen
    result_files = {}
    for i in range(1, max_erzieher + 1):
        # Nur die i-ten Ansprechpartner je Schüler-ID
        ansp_by_sid = {
            r['Schüler_ID']: r for r in ansp_rows if r['Erzieher_Nummer'] == i
        }

        # Header dynamisch erzeugen
        header = ['Interne_ID_Nummer']
        for field in ERZIEHER_FIELDS:
            header.append(f'Erzieher {i}: {field}')
        for src in ANSPRECHPARTNER_FIELD_MAP.values():
            header.append(f'Erzieher {i}: {src}')

        # Zeilen aufbauen — eine pro Schüler aus Erzieher-Export
        result_rows = []
        for erz_row in erz_rows:
            sid = erz_row.get('Interne ID-Nummer', '').strip()
            if not sid:
                continue
            ansp = ansp_by_sid.get(sid, {})
            row_out = {'Interne_ID_Nummer': sid}
            for field in ERZIEHER_FIELDS:
                col_in = f'Erzieher {i}: {field}'
                row_out[f'Erzieher {i}: {field}'] = erz_row.get(col_in, '')
            for src_col, target_col_short in ANSPRECHPARTNER_FIELD_MAP.items():
                row_out[f'Erzieher {i}: {target_col_short}'] = ansp.get(src_col, '')
            result_rows.append(row_out)

        result_files[f'Erzieher_{i}'] = {'header': header, 'rows': result_rows}

    stats = {
        'erzieher_rows':        len(erz_rows),
        'ansprechpartner_rows': len(ansp_rows),
        'max_erzieher':         max_erzieher,
        'output_files':         list(result_files.keys()),
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
    if not ansprechpartner_path or not os.path.isfile(ansprechpartner_path):
        raise FileNotFoundError("Keine Ansprechpartner-Export-CSV gefunden. Bitte Verzeichnis pruefen.")

    erz_rows  = _read_csv_rows(erzieher_path)
    ansp_rows = _read_csv_rows(ansprechpartner_path)
    if not erz_rows:
        raise ValueError("Erzieher-Export ist leer.")
    if 'Interne ID-Nummer' not in erz_rows[0]:
        raise ValueError("Spalte 'Interne ID-Nummer' fehlt im Erzieher-Export.")
    if ansp_rows and 'Schüler_ID' not in ansp_rows[0]:
        raise ValueError("Spalte 'Schüler_ID' fehlt im Ansprechpartner-Export.")

    # Header der Eingabe-Dateien (fuer die Anzeige im Field-Mapping-Block)
    erz_header  = list(erz_rows[0].keys())  if erz_rows  else []
    ansp_header = list(ansp_rows[0].keys()) if ansp_rows else []

    # Ansprechpartner-Zeilen per Schueler-ID sortieren und nummerieren (analog process())
    ansp_rows.sort(key=lambda r: r.get('Schüler_ID', ''))
    last_sid, counter = None, 0
    for row in ansp_rows:
        sid = row.get('Schüler_ID', '')
        if sid != last_sid:
            counter = 1
            last_sid = sid
        else:
            counter += 1
        row['Erzieher_Nummer'] = counter
    # Lookup: sid -> [ansp_row sortiert nach Erzieher_Nummer]
    ansp_by_sid = {}
    for r in ansp_rows:
        ansp_by_sid.setdefault(r.get('Schüler_ID', ''), []).append(r)
    for lst in ansp_by_sid.values():
        lst.sort(key=lambda r: r.get('Erzieher_Nummer', 0))

    # Maximale Erzieher-Anzahl ueber alle Schueler hinweg ermitteln (aus den
    # Spalten "Erzieher i: Anrede" o.ae. im Erzieher-Export).
    max_in_header = 0
    for col in erz_header:
        m = re.match(r'Erzieher\s+(\d+):', col)
        if m:
            max_in_header = max(max_in_header, int(m.group(1)))
    # Sicherheits-Fallback, falls Header nichts hergibt
    if max_in_header == 0:
        max_in_header = max((len(v) for v in ansp_by_sid.values()), default=0)

    students = []
    students_without_erzieher = 0
    for erz_row in erz_rows:
        sid = erz_row.get('Interne ID-Nummer', '').strip()
        if not sid:
            continue
        ansp_list = ansp_by_sid.get(sid, [])
        erzieher_list = []
        for i in range(1, max_in_header + 1):
            erz_data = {
                'nr':          i,
                'anrede':      erz_row.get(f'Erzieher {i}: Anrede',      '').strip(),
                'briefanrede': erz_row.get(f'Erzieher {i}: Briefanrede', '').strip(),
                'titel':       erz_row.get(f'Erzieher {i}: Titel',       '').strip(),
                'nachname':    erz_row.get(f'Erzieher {i}: Nachname',    '').strip(),
                'vorname':     erz_row.get(f'Erzieher {i}: Vorname',     '').strip(),
                'email':       erz_row.get(f'Erzieher {i}: E-Mail',      '').strip(),
            }
            ansp = ansp_list[i-1] if i-1 < len(ansp_list) else {}
            erz_data.update({
                'anschluss': ansp.get('Anschluss-Art',  '').strip(),
                'bemerkung': ansp.get('Bemerkung',      '').strip(),
                'telefon':   ansp.get('Telefon-Nummer', '').strip(),
            })
            # Leere Erzieher-Slots (nichts in beiden Quellen) ueberspringen
            if any(v for k, v in erz_data.items() if k != 'nr'):
                erzieher_list.append(erz_data)
        if not erzieher_list:
            students_without_erzieher += 1
        students.append({
            'id':       sid,
            'vorname':  erz_row.get('Vorname',  '').strip(),
            'nachname': erz_row.get('Nachname', '').strip(),
            'klasse':   erz_row.get('Klasse',   '').strip(),
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
        },
        'field_mapping': {
            'from_erzieher_csv':        from_erzieher,
            'from_ansprechpartner_csv': from_ansprechpartner,
        },
        'sources': {
            'erzieher_export_file':        os.path.basename(erzieher_path),
            'ansprechpartner_export_file': os.path.basename(ansprechpartner_path),
            'erzieher_headers':            erz_header,
            'ansprechpartner_headers':     ansp_header,
        },
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
