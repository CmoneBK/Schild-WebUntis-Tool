"""
Foto-Verwaltung: Schüler-Fotos aus Schild (benannt nach Interner ID) verwalten.

- Fotos liegen im konfigurierten foto_directory, Dateiname = Interne ID (z.B. 12345.jpg)
- Anzeige einzelner Fotos (Dashboard)
- ZIP-Export für WebUntis (Auswahl nach Schild-Status)
- Verwaiste Fotos (Schüler nicht mehr im Import) in einen Archiv-Unterordner verschieben
"""
import os
import io
import re
import shutil
import zipfile
import configparser
from datetime import datetime

# Erlaubte Bild-Endungen
FOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
ARCHIVE_SUBDIR = 'Archiv'


def safe_read_config(config, path):
    try:
        config.read(path, encoding='utf-8-sig')
        return True
    except Exception:
        return False


def get_foto_directory():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'foto_directory', fallback='').strip()


def get_zip_name_template():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('FotoOptions', 'zip_name_template', fallback='Fotos_{datum}').strip() or 'Fotos_{datum}'


def get_zip_directory():
    """Verzeichnis, in das erzeugte Foto-ZIPs geschrieben werden."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'foto_zip_directory', fallback='SchuelerFotosZips').strip() or 'SchuelerFotosZips'


def get_rename_template():
    """Vorlage für die Umbenennung beim Kopieren in den Unterordner."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('FotoOptions', 'rename_template', fallback='{nachname}_{vorname}_{id}').strip() or '{nachname}_{vorname}_{id}'


def get_rename_subdir():
    """Name des Unterordners für umbenannte Foto-Kopien."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('FotoOptions', 'rename_subdir', fallback='Umbenannt').strip() or 'Umbenannt'


def save_rename_settings(template=None, subdir=None):
    """Speichert Rename-Template und/oder Subdir persistent in settings.ini."""
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('FotoOptions'):
        config.add_section('FotoOptions')
    if template:
        config.set('FotoOptions', 'rename_template', template.strip())
    if subdir:
        config.set('FotoOptions', 'rename_subdir', subdir.strip())
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def save_zip_name_template(template):
    """Speichert die ZIP-Namen-Vorlage persistent in settings.ini."""
    template = (template or '').strip()
    if not template:
        return
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if not config.has_section('FotoOptions'):
        config.add_section('FotoOptions')
    config.set('FotoOptions', 'zip_name_template', template)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def _foto_id_from_filename(filename):
    """Extrahiert die ID aus einem Dateinamen (alles vor der Endung)."""
    stem, ext = os.path.splitext(filename)
    if ext.lower() not in FOTO_EXTENSIONS:
        return None
    return stem.strip()


def list_fotos(foto_dir=None, include_archive=False):
    """Liefert eine Liste von Dicts: {filename, id, ext, size}."""
    foto_dir = foto_dir or get_foto_directory()
    if not foto_dir or not os.path.isdir(foto_dir):
        return []
    result = []
    for fname in sorted(os.listdir(foto_dir)):
        full = os.path.join(foto_dir, fname)
        if not os.path.isfile(full):
            continue
        fid = _foto_id_from_filename(fname)
        if fid is None:
            continue
        result.append({
            'filename': fname,
            'id': fid,
            'ext': os.path.splitext(fname)[1].lower(),
            'size': os.path.getsize(full),
        })
    # Archivierte Fotos optional mitlisten
    if include_archive:
        arch_dir = os.path.join(foto_dir, ARCHIVE_SUBDIR)
        if os.path.isdir(arch_dir):
            for fname in sorted(os.listdir(arch_dir)):
                full = os.path.join(arch_dir, fname)
                if not os.path.isfile(full):
                    continue
                fid = _foto_id_from_filename(fname)
                if fid is None:
                    continue
                result.append({
                    'filename': fname,
                    'id': fid,
                    'ext': os.path.splitext(fname)[1].lower(),
                    'size': os.path.getsize(full),
                    'archived': True,
                })
    return result


def get_foto_path(student_id, foto_dir=None):
    """Pfad zur Fotodatei eines Schülers (erste passende Endung) oder None."""
    foto_dir = foto_dir or get_foto_directory()
    if not foto_dir or not os.path.isdir(foto_dir):
        return None
    sid = str(student_id).strip()
    for ext in FOTO_EXTENSIONS:
        candidate = os.path.join(foto_dir, sid + ext)
        if os.path.isfile(candidate):
            return candidate
    # Case-insensitive Endungen
    for fname in os.listdir(foto_dir):
        if _foto_id_from_filename(fname) == sid:
            return os.path.join(foto_dir, fname)
    return None


def _resolve_zip_name(template):
    """Ersetzt Platzhalter im ZIP-Namen-Template."""
    now = datetime.now()
    repl = {
        'datum':    now.strftime('%Y-%m-%d'),
        'date':     now.strftime('%Y-%m-%d'),
        'datetime': now.strftime('%Y-%m-%d_%H-%M-%S'),
        'zeit':     now.strftime('%H-%M-%S'),
        'jahr':     now.strftime('%Y'),
        'year':     now.strftime('%Y'),
        'monat':    now.strftime('%m'),
        'tag':      now.strftime('%d'),
    }
    name = template
    for k, v in repl.items():
        name = name.replace('{' + k + '}', v)
    # Unerlaubte Zeichen ersetzen
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    if not name.lower().endswith('.zip'):
        name += '.zip'
    return name


def build_foto_zip(student_ids, foto_dir=None, name_template=None):
    """
    Packt die Fotos der angegebenen Schüler-IDs in ein ZIP (im Speicher).
    Liefert (zip_bytes, zip_name, anzahl_enthalten, anzahl_fehlend).
    """
    foto_dir = foto_dir or get_foto_directory()
    name_template = name_template or get_zip_name_template()
    zip_name = _resolve_zip_name(name_template)

    buf = io.BytesIO()
    included, missing = 0, 0
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for sid in student_ids:
            path = get_foto_path(sid, foto_dir)
            if path and os.path.isfile(path):
                zf.write(path, arcname=os.path.basename(path))
                included += 1
            else:
                missing += 1
    buf.seek(0)
    return buf.getvalue(), zip_name, included, missing


def create_zip_file(student_ids, foto_dir=None, name_template=None, output_dir=None):
    """
    Erzeugt das Foto-ZIP und schreibt es in output_dir (Default: get_zip_directory()).
    Liefert (zip_pfad, zip_name, anzahl_enthalten, anzahl_fehlend).
    """
    output_dir = output_dir or get_zip_directory()
    os.makedirs(output_dir, exist_ok=True)
    zip_bytes, zip_name, included, missing = build_foto_zip(student_ids, foto_dir, name_template)
    zip_path = os.path.join(output_dir, zip_name)
    # Falls Datei existiert: mit Zeitstempel-Suffix versehen
    if os.path.exists(zip_path):
        base, ext = os.path.splitext(zip_name)
        zip_name = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"
        zip_path = os.path.join(output_dir, zip_name)
    with open(zip_path, 'wb') as f:
        f.write(zip_bytes)
    return zip_path, zip_name, included, missing


def archive_orphan_fotos(current_student_ids, foto_dir=None):
    """
    Verschiebt alle Fotos, deren ID NICHT in current_student_ids ist,
    in den Unterordner 'Archiv'. Liefert die Liste der verschobenen Dateinamen.
    """
    foto_dir = foto_dir or get_foto_directory()
    if not foto_dir or not os.path.isdir(foto_dir):
        return []
    current = {str(s).strip() for s in current_student_ids}
    arch_dir = os.path.join(foto_dir, ARCHIVE_SUBDIR)
    os.makedirs(arch_dir, exist_ok=True)
    moved = []
    for entry in list_fotos(foto_dir, include_archive=False):
        if entry['id'] not in current:
            src = os.path.join(foto_dir, entry['filename'])
            dst = os.path.join(arch_dir, entry['filename'])
            # Falls Ziel existiert: mit Zeitstempel versehen
            if os.path.exists(dst):
                base, ext = os.path.splitext(entry['filename'])
                dst = os.path.join(arch_dir, f"{base}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}")
            try:
                shutil.move(src, dst)
                moved.append(entry['filename'])
            except Exception:
                pass
    return moved


def _safe_filename_part(s):
    """Macht einen Wert dateinamen-tauglich (verbotene Zeichen entfernen)."""
    s = str(s or '').strip()
    s = re.sub(r'[<>:"/\\|?*\r\n\t]', '_', s)
    s = re.sub(r'\s+', ' ', s)
    return s


def render_rename_template(template, student):
    """Ersetzt Platzhalter im Rename-Template anhand der Schüler-Daten.
    Platzhalter: {id}, {vorname}, {nachname}, {klasse}, {status}, {geschlecht}, {geburtsdatum}."""
    repl = {
        'id':           student.get('Interne ID-Nummer', ''),
        'vorname':      student.get('Vorname', ''),
        'nachname':     student.get('Nachname', ''),
        'klasse':       student.get('Klasse', ''),
        'status':       student.get('Status', ''),
        'geschlecht':   student.get('Geschlecht', ''),
        'geburtsdatum': student.get('Geburtsdatum', ''),
    }
    name = template
    for k, v in repl.items():
        name = name.replace('{' + k + '}', _safe_filename_part(v))
    return _safe_filename_part(name)


def copy_renamed_fotos(students_data, foto_dir=None, template=None, target_subdir=None):
    """
    Kopiert die Fotos aller Schüler aus students_data (Liste von Dicts) in einen
    Unterordner des foto_directory und benennt sie nach dem Template um.
    Liefert (zielverzeichnis, kopiert, fehlend).
    """
    import shutil
    foto_dir = foto_dir or get_foto_directory()
    template = template or get_rename_template()
    target_subdir = (target_subdir or get_rename_subdir()).strip() or 'Umbenannt'

    target_dir = os.path.join(foto_dir, target_subdir)
    os.makedirs(target_dir, exist_ok=True)

    copied, missing = 0, 0
    for student in students_data:
        sid = str(student.get('Interne ID-Nummer', '')).strip()
        if not sid:
            continue
        src = get_foto_path(sid, foto_dir)
        if not src or not os.path.isfile(src):
            missing += 1
            continue
        ext = os.path.splitext(src)[1].lower()
        base = render_rename_template(template, student) or sid
        dst = os.path.join(target_dir, base + ext)
        # Konfliktauflösung mit _1, _2, …
        if os.path.exists(dst):
            counter = 1
            while True:
                candidate = os.path.join(target_dir, f"{base}_{counter}{ext}")
                if not os.path.exists(candidate):
                    dst = candidate
                    break
                counter += 1
        try:
            shutil.copy2(src, dst)
            copied += 1
        except Exception:
            missing += 1
    return target_dir, copied, missing


def restore_archived_foto(filename, foto_dir=None):
    """Verschiebt eine archivierte Foto-Datei zurück ins Hauptverzeichnis."""
    foto_dir = foto_dir or get_foto_directory()
    arch_dir = os.path.join(foto_dir, ARCHIVE_SUBDIR)
    src = os.path.join(arch_dir, filename)
    dst = os.path.join(foto_dir, filename)
    if not os.path.isfile(src):
        return False
    if os.path.exists(dst):
        return False
    try:
        shutil.move(src, dst)
        return True
    except Exception:
        return False
