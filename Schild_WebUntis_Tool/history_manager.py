import sqlite3
import os
from datetime import datetime
from colorama import Fore, Style, init as colorama_init
from rich.console import Console
colorama_init(autoreset=True)

_console = Console(highlight=False, legacy_windows=False)

def _print_info(msg):    print(f"{Fore.CYAN}ℹ️  [Historie] {msg}{Style.RESET_ALL}", flush=True)
def _print_success(msg): print(f"{Fore.GREEN}✅ [Historie] {msg}{Style.RESET_ALL}", flush=True)
def _print_warning(msg): print(f"{Fore.YELLOW}⚠️  [Historie] {msg}{Style.RESET_ALL}", flush=True)
def _print_error(msg):   print(f"{Fore.RED}❌ [Historie] {msg}{Style.RESET_ALL}", flush=True)
def _print_section(title): _console.rule(f"[Historie] {title}", style="cyan")

DB_PATH = 'history.db'

# Werte die semantisch gleichwertig zu "leer/nicht gesetzt" sind.
# Ein Wechsel zwischen zwei dieser Werte ist keine echte Änderung.
_EMPTY_EQUIVALENTS = {'', 'nein', 'keine', 'keiner', 'keines', 'kein', 'false'}

def _normalize(value):
    """Gibt '' zurück wenn der Wert semantisch leer ist, sonst den bereinigten Originalwert."""
    v = value.strip().replace('\u00a0', '').lower()
    return '' if v in _EMPTY_EQUIVALENTS else value.strip().replace('\u00a0', '')

def _is_meaningful_change(old, new):
    """True wenn sich alter und neuer Wert nach Normalisierung unterscheiden.
    Ein leerer neuer Wert (Spalte fehlte im Export) ist nie eine echte Änderung.
    Beispiele:
      'Ja' -> ''   : False  (Spalte fehlte, kein expliziter Wert)
      'Ja' -> 'Nein': True  (echte Aufhebung)
      ''   -> 'Ja' : True  (Erstzuweisung)
      ''   -> 'Nein': False (beide semantisch leer)
    """
    if _normalize(old) == _normalize(new):
        return False
    # Leerer neuer Wert = Spalte fehlte im Export, keine echte Zustandsänderung
    if new.strip().replace('\u00a0', '') == '':
        return False
    return True

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialisiert die SQLite-Datenbank und erstellt die Tabellen-Struktur."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabelle für Studenten (Stammdaten)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT,
            last_known_class TEXT
        )
    ''')
    
    # Tabelle für Vergleiche (Metadaten der Änderungs-Läufe)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            file_a TEXT,
            file_b TEXT
        )
    ''')
    
    # Tabelle für die einzelnen Feld-Änderungen
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comparison_id INTEGER,
            student_id TEXT,
            field TEXT,
            old_value TEXT,
            new_value TEXT,
            FOREIGN KEY (comparison_id) REFERENCES comparisons (id),
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def record_changes(changes_list, timestamp=None, file_a="N/A", file_b="N/A"):
    """Speichert eine Liste von Änderungen in der Datenbank."""
    if not timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('INSERT INTO comparisons (timestamp, file_a, file_b) VALUES (?, ?, ?)',
                       (timestamp, file_a, file_b))
        comp_id = cursor.lastrowid

        stored_count = 0
        skipped_count = 0
        for change in changes_list:
            student_id = change.get('student_id')
            student_name = change.get('name')

            cursor.execute('''
                INSERT INTO students (id, name) VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name
            ''', (student_id, student_name))

            for field, values in change.get('changes', {}).items():
                if not _is_meaningful_change(values['old'], values['new']):
                    skipped_count += 1
                    continue
                cursor.execute('''
                    INSERT INTO changes (comparison_id, student_id, field, old_value, new_value)
                    VALUES (?, ?, ?, ?, ?)
                ''', (comp_id, student_id, field, values['old'], values['new']))
                stored_count += 1

            current_class = change.get('current_class')
            if current_class:
                cursor.execute('UPDATE students SET last_known_class = ? WHERE id = ?',
                               (current_class, student_id))

        conn.commit()
        _print_info(f"{len(changes_list)} Schüler verarbeitet – {stored_count} Änderungen gespeichert"
                    + (f", {skipped_count} semantisch leer übersprungen" if skipped_count else "") + ".")
    except Exception as e:
        if conn: conn.rollback()
        _print_error(f"Fehler beim Speichern der Historie: {e}")
    finally:
        if conn: conn.close()

def update_student_info(student_id, name, class_name):
    """Aktualisiert die Basisdaten eines Schülers (Name & Klasse)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO students (id, name, last_known_class) VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET name=excluded.name, last_known_class=excluded.last_known_class
    ''', (student_id, name, class_name))
    conn.commit()
    conn.close()

def bulk_update_students(student_list):
    """Aktualisiert eine Liste von Schülern in einer Transaktion."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany('''
            INSERT INTO students (id, name, last_known_class) VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET name=excluded.name, last_known_class=excluded.last_known_class
        ''', [(s['id'], s['name'], s['class']) for s in student_list])
        conn.commit()
        _print_success(f"Klassendaten synchronisiert: {len(student_list)} Schüler aktualisiert.")
    except Exception as e:
        conn.rollback()
        _print_error(f"Fehler beim Bulk-Update der Schülerdaten: {e}")
    finally:
        conn.close()

import re
def reindex_logs(log_dir):
    """Parst vorhandene .log Dateien im Verzeichnis und importiert sie in die DB.
    Überspringt Dateien, die bereits in der DB erfasst sind (Duplikat-Schutz per file_b).
    """
    _print_section("Log-Reindex")
    if not os.path.exists(log_dir):
        _print_warning(f"  Log-Verzeichnis '{log_dir}' nicht gefunden. Reindex abgebrochen.")
        return 0

    conn = get_connection()
    already_imported = set(
        row[0] for row in conn.execute("SELECT file_b FROM comparisons WHERE file_b IS NOT NULL").fetchall()
    )
    conn.close()

    log_files = sorted(
        [f for f in os.listdir(log_dir) if f.endswith('.log') and 'nderungsLog' in f]
    )
    _print_info(f"  {len(log_files)} Log-Datei(en) gefunden, {len(already_imported)} bereits importiert.")
    count = 0

    for filename in log_files:
        if filename in already_imported:
            continue

        filepath = os.path.join(log_dir, filename)

        # Zeitstempel aus Dateiname extrahieren (Format: ÄnderungsLog_YYYY-MM-DD_HH-MM-SS.log)
        match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', filename)
        if match:
            try:
                ts = datetime.strptime(match.group(1), "%Y-%m-%d_%H-%M-%S")
                timestamp = ts.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                timestamp = datetime.fromtimestamp(os.path.getctime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp = datetime.fromtimestamp(os.path.getctime(filepath)).strftime("%Y-%m-%d %H:%M:%S")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Zerlege Inhalt nach Schüler-Blöcken
            student_blocks = content.split('Schüler: ')
            changes_for_db = []

            for block in student_blocks:
                if not block.strip():
                    continue
                lines = block.split('\n')
                # Erkennt: "Name (ID: 123) [Klasse: 5a]" und "Name (ID: 123)"
                header = lines[0]
                match_header = re.search(r'(.*) \(ID: (.*?)\)(?: \[Klasse: (.*?)\])?', header)
                if not match_header:
                    continue

                name = match_header.group(1).strip()
                student_id = match_header.group(2).strip()
                current_class = match_header.group(3).strip() if match_header.group(3) else None

                student_changes = {}
                for line in lines[1:]:
                    if ' -> ' in line:
                        # Format: "  Feld: alt -> neu"
                        # Trennzeichen ist ': ' (Feld von Wert), dann ' -> ' (alt von neu)
                        parts = line.split(': ', 1)
                        if len(parts) < 2:
                            continue
                        field = parts[0].strip()
                        values = parts[1].split(' -> ', 1)
                        if len(values) < 2:
                            continue
                        old_val = values[0].strip()
                        new_val = values[1].strip()
                        if _is_meaningful_change(old_val, new_val):
                            student_changes[field] = {"old": old_val, "new": new_val}

                if student_changes:
                    changes_for_db.append({
                        "student_id": student_id,
                        "name": name,
                        "current_class": current_class,
                        "changes": student_changes
                    })

            if changes_for_db:
                _print_info(f"  Importiere '{filename}' ({len(changes_for_db)} betroffene Schüler)...")
                record_changes(changes_for_db, timestamp=timestamp, file_b=filename)
                count += 1
            else:
                _print_info(f"  Übersprungen: '{filename}' – keine relevanten Änderungen.")

        except Exception as e:
            _print_error(f"  Fehler beim Parsen von '{filename}': {e}")

    _print_success(f"Reindex abgeschlossen: {count} neue Log-Datei(en) importiert.")
    return count

def _cleanup_empty_equivalent_changes(conn):
    """Bereinigt Änderungen, bei denen alter und neuer Wert semantisch gleichwertig zu 'leer' sind.
    Z.B. '' -> 'Nein' oder 'Nein' -> '' werden als keine echte Änderung betrachtet.
    Verwaiste comparisons (ohne verbleibende Änderungen) werden ebenfalls entfernt."""
    equivalents = tuple(_EMPTY_EQUIVALENTS)
    placeholders = ','.join('?' * len(equivalents))
    cursor = conn.cursor()
    # Fall 1: Beide Werte semantisch leer (z.B. '' -> 'Nein')
    # Fall 2: Neuer Wert ist leer (Spalte fehlte im Export, z.B. 'Ja' -> '')
    cursor.execute(f'''
        DELETE FROM changes
        WHERE (LOWER(TRIM(old_value)) IN ({placeholders})
               AND LOWER(TRIM(new_value)) IN ({placeholders}))
           OR TRIM(new_value) = ''
    ''', equivalents + equivalents)
    deleted = cursor.rowcount
    # Verwaiste Vergleiche entfernen (kein einziger change-Eintrag mehr vorhanden)
    cursor.execute('''
        DELETE FROM comparisons
        WHERE id NOT IN (SELECT DISTINCT comparison_id FROM changes)
    ''')
    orphans = cursor.rowcount
    if deleted > 0 or orphans > 0:
        _print_info(f"DB-Bereinigung: {deleted} Pseudoänderungen und {orphans} verwaiste Vergleiche entfernt.")
    conn.commit()


def _migrate_timestamps(conn):
    """Einmalige Migration: korrigiert Timestamps im Format YYYY-MM-DD_HH-MM-SS -> YYYY-MM-DD HH:MM:SS."""
    cursor = conn.cursor()
    cursor.execute("SELECT id, timestamp FROM comparisons WHERE timestamp LIKE '%_%-%-%'")
    rows = cursor.fetchall()
    for row in rows:
        ts = row['timestamp']
        if ts and re.match(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', ts):
            try:
                fixed = datetime.strptime(ts, "%Y-%m-%d_%H-%M-%S").strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("UPDATE comparisons SET timestamp = ? WHERE id = ?", (fixed, row['id']))
            except ValueError:
                pass
    conn.commit()


def get_dashboard_stats(field_filter=None, hotspot_limit=5):
    """Aggregiert Statistiken für das Dashboard."""
    conn = get_connection()
    _migrate_timestamps(conn)
    _cleanup_empty_equivalent_changes(conn)
    cursor = conn.cursor()

    # 1. Änderungen pro Monat (für Liniendiagramm)
    cursor.execute('''
        SELECT strftime('%Y-%m', c.timestamp) as month, COUNT(*) as count
        FROM comparisons c
        JOIN changes ch ON c.id = ch.comparison_id
        WHERE c.timestamp IS NOT NULL
        GROUP BY month ORDER BY month ASC
    ''')
    monthly_changes = {row['month']: row['count'] for row in cursor.fetchall() if row['month'] is not None}

    # 2. Häufigste Änderungsarten (Kategorien)
    cursor.execute('''
        SELECT field, COUNT(*) as count FROM changes
        WHERE field IS NOT NULL AND field != ''
        GROUP BY field ORDER BY count DESC LIMIT 10
    ''')
    category_stats = {row['field']: row['count'] for row in cursor.fetchall() if row['field'] is not None}
    
    # 3. Top-Klassen nach Warnungskategorien (Hotspots)
    # Mapping der vom Frontend gesendeten Kategorien auf SQL-Logik
    warning_categories = {
        'Klassenwechsel': "ch.field = 'Klasse'",
        'Ungünstig verschobene Aufnahmedaten': """
            (ch.field = 'Aufnahmedatum' AND 
             (substr(ch.new_value, 7, 4) || '-' || substr(ch.new_value, 4, 2) || '-' || substr(ch.new_value, 1, 2)) < 
             (substr(ch.old_value, 7, 4) || '-' || substr(ch.old_value, 4, 2) || '-' || substr(ch.old_value, 1, 2)) AND
             (substr(ch.new_value, 7, 4) || '-' || substr(ch.new_value, 4, 2) || '-' || substr(ch.new_value, 1, 2)) < 
             substr(c.timestamp, 1, 10))
        """,
        'Ungünstig verschobene Entlassdaten': """
            (ch.field = 'Entlassdatum' AND 
             (substr(ch.new_value, 7, 4) || '-' || substr(ch.new_value, 4, 2) || '-' || substr(ch.new_value, 1, 2)) > 
             (substr(ch.old_value, 7, 4) || '-' || substr(ch.old_value, 4, 2) || '-' || substr(ch.old_value, 1, 2)) AND
             substr(c.timestamp, 1, 10) > 
             (substr(ch.old_value, 7, 4) || '-' || substr(ch.old_value, 4, 2) || '-' || substr(ch.old_value, 1, 2)))
        """,
        'Neue Schüler': "ch.field = '__SYSTEM__' AND ch.new_value = 'Neu'",
        'Fehlende Schüler': "ch.field = '__SYSTEM__' AND ch.new_value = 'Fehlt'"
    }

    if field_filter and field_filter in warning_categories:
        condition = warning_categories[field_filter]
    else:
        # Standard: Alle Warnungskategorien kombiniert
        condition = f"({' OR '.join(warning_categories.values())})"

    query = f'''
        SELECT s.last_known_class as class, COUNT(*) as count
        FROM changes ch
        JOIN students s ON ch.student_id = s.id
        JOIN comparisons c ON ch.comparison_id = c.id
        WHERE s.last_known_class IS NOT NULL AND s.last_known_class != ''
        AND {condition}
        GROUP BY s.last_known_class ORDER BY count DESC LIMIT {int(hotspot_limit)}
    '''
    cursor.execute(query)
    hotspot_classes = {row['class']: row['count'] for row in cursor.fetchall() if row['class'] is not None}

    # 4. Trends (Monatlich & Wöchentlich nach Feld)
    # Monatlicher Trend
    cursor.execute('''
        SELECT strftime('%Y-%m', c.timestamp) as time_unit, ch.field, COUNT(*) as count
        FROM comparisons c JOIN changes ch ON c.id = ch.comparison_id
        WHERE c.timestamp IS NOT NULL
          AND ch.field IS NOT NULL AND ch.field != ''
        GROUP BY time_unit, ch.field ORDER BY time_unit ASC
    ''')
    monthly_trends = {}
    for row in cursor.fetchall():
        t, f, cnt = row['time_unit'], row['field'], row['count']
        if t is None or f is None:
            continue
        if t not in monthly_trends:
            monthly_trends[t] = {}
        monthly_trends[t][f] = cnt

    # Wöchentlicher Trend
    cursor.execute('''
        SELECT strftime('%Y-W%W', c.timestamp) as time_unit, ch.field, COUNT(*) as count
        FROM comparisons c JOIN changes ch ON c.id = ch.comparison_id
        WHERE c.timestamp IS NOT NULL
          AND ch.field IS NOT NULL AND ch.field != ''
        GROUP BY time_unit, ch.field ORDER BY time_unit ASC
    ''')
    weekly_trends = {}
    for row in cursor.fetchall():
        t, f, cnt = row['time_unit'], row['field'], row['count']
        if t is None or f is None:
            continue
        if t not in weekly_trends:
            weekly_trends[t] = {}
        weekly_trends[t][f] = cnt
    
    conn.close()
    return {
        "monthly": monthly_changes,
        "categories": category_stats,
        "hotspots": hotspot_classes,
        "trends": {
            "monthly": monthly_trends,
            "weekly": weekly_trends
        }
    }

def get_all_classes():
    """Gibt eine Liste aller Klassen zurück, die in der Historie vorkommen."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT last_known_class FROM students 
        WHERE last_known_class IS NOT NULL AND last_known_class != '' 
        ORDER BY last_known_class ASC
    ''')
    classes = [row['last_known_class'] for row in cursor.fetchall()]
    conn.close()
    return classes

def get_class_analytics(class_name):
    """Gibt detaillierte Statistiken und die Historie für eine bestimmte Klasse zurück."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Kategorien-Verteilung für diese Klasse
    cursor.execute('''
        SELECT field, COUNT(*) as count 
        FROM changes ch
        JOIN students s ON ch.student_id = s.id
        WHERE s.last_known_class = ?
        GROUP BY field ORDER BY count DESC
    ''', (class_name,))
    categories = {row['field']: row['count'] for row in cursor.fetchall()}
    
    # 2. Zeitstrahl aller Änderungen in dieser Klasse
    cursor.execute('''
        SELECT c.timestamp, s.name, ch.field, ch.old_value, ch.new_value, s.id as student_id
        FROM changes ch
        JOIN comparisons c ON ch.comparison_id = c.id
        JOIN students s ON ch.student_id = s.id
        WHERE s.last_known_class = ?
        ORDER BY c.timestamp DESC
        LIMIT 100
    ''', (class_name,))
    timeline = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return {
        "categories": categories,
        "timeline": timeline
    }

def search_student_history(query):
    """Sucht nach einem Schüler und gibt die Historie zurück."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Suche nach ID oder Teil des Namens
    cursor.execute('''
        SELECT * FROM students 
        WHERE id = ? OR name LIKE ? 
        LIMIT 10
    ''', (query, f"%{query}%"))
    students = [dict(row) for row in cursor.fetchall()]
    
    results = []
    for student in students:
        cursor.execute('''
            SELECT c.timestamp, ch.field, ch.old_value, ch.new_value, c.file_b
            FROM changes ch
            JOIN comparisons c ON ch.comparison_id = c.id
            WHERE ch.student_id = ?
            ORDER BY c.timestamp DESC
        ''', (student['id'],))
        history = [dict(row) for row in cursor.fetchall()]
        results.append({
            "student": student,
            "timeline": history
        })
        
    conn.close()
    return results

def clear_history():
    """Löscht die gesamte Historie (Schuljahr-Reset)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM changes')
    cursor.execute('DELETE FROM comparisons')
    cursor.execute('DELETE FROM students')
    conn.commit()
    conn.close()

# Initialisierung bei Import
init_db()
