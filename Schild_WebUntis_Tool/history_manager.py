import sqlite3
import os
from datetime import datetime

DB_PATH = 'history.db'

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
        # Vergleich registrieren
        cursor.execute('INSERT INTO comparisons (timestamp, file_a, file_b) VALUES (?, ?, ?)', 
                       (timestamp, file_a, file_b))
        comp_id = cursor.lastrowid
        
        for change in changes_list:
            student_id = change.get('student_id')
            student_name = change.get('name')
            
            # Student aktualisieren oder anlegen
            cursor.execute('''
                INSERT INTO students (id, name) VALUES (?, ?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name
            ''', (student_id, student_name))
            
            # Einzelne Feldänderungen speichern
            for field, values in change.get('changes', {}).items():
                cursor.execute('''
                    INSERT INTO changes (comparison_id, student_id, field, old_value, new_value)
                    VALUES (?, ?, ?, ?, ?)
                ''', (comp_id, student_id, field, values['old'], values['new']))
                
                # Wenn es ein Klassenwechsel ist, die last_known_class beim Studenten aktualisieren
                if field == 'Klasse':
                    cursor.execute('UPDATE students SET last_known_class = ? WHERE id = ?', 
                                   (values['new'], student_id))
        
        conn.commit()
    except Exception as e:
        if conn: conn.rollback()
        print(f"Fehler beim Speichern der Historie: {e}")
    finally:
        if conn: conn.close()

import re
def reindex_logs(log_dir):
    """Parst vorhandene .log Dateien im Verzeichnis und importiert sie in die DB."""
    if not os.path.exists(log_dir):
        return 0
    
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log') and 'ÄnderungsLog' in f]
    count = 0
    
    for filename in log_files:
        filepath = os.path.join(log_dir, filename)
        # Zeitstempel aus Dateiname extrahieren (Format: ÄnderungsLog_YYYY-MM-DD_HH-MM-SS.log)
        match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', filename)
        timestamp = match.group(1).replace('_', ' ') if match else datetime.fromtimestamp(os.path.getctime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Zerlege Inhalt nach Schüler-Blöcken
            student_blocks = content.split('Schüler: ')
            changes_for_db = []
            
            for block in student_blocks:
                if not block.strip(): continue
                lines = block.split('\n')
                # Erste Zeile enthält Name und ID: "Name (ID: 123)"
                header = lines[0]
                match_header = re.search(r'(.*) \(ID: (.*)\)', header)
                if not match_header: continue
                
                name = match_header.group(1).strip()
                student_id = match_header.group(2).strip()
                
                student_changes = {}
                for line in lines[1:]:
                    if ' -> ' in line:
                        # Format: "  Feld: alt -> neu"
                        parts = line.split(': ', 1)
                        if len(parts) < 2: continue
                        field = parts[0].strip()
                        values = parts[1].split(' -> ')
                        if len(values) < 2: continue
                        student_changes[field] = {"old": values[0].strip(), "new": values[1].strip()}
                
                if student_changes:
                    changes_for_db.append({
                        "student_id": student_id,
                        "name": name,
                        "changes": student_changes
                    })
            
            if changes_for_db:
                record_changes(changes_for_db, timestamp=timestamp, file_b=filename)
                count += 1
                
        except Exception as e:
            print(f"Fehler beim Parsen von {filename}: {e}")
            
    return count

def get_dashboard_stats():
    """Aggregiert Statistiken für das Dashboard."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Änderungen pro Monat (für Liniendiagramm)
    cursor.execute('''
        SELECT strftime('%Y-%m', timestamp) as month, COUNT(*) as count 
        FROM comparisons c
        JOIN changes ch ON c.id = ch.comparison_id
        GROUP BY month ORDER BY month ASC
    ''')
    monthly_changes = {row['month']: row['count'] for row in cursor.fetchall()}
    
    # 2. Häufigste Änderungsarten (Kategorien)
    cursor.execute('''
        SELECT field, COUNT(*) as count FROM changes 
        GROUP BY field ORDER BY count DESC LIMIT 10
    ''')
    category_stats = {row['field']: row['count'] for row in cursor.fetchall()}
    
    # 3. Top-Klassen mit den meisten Änderungen (Fehler-Hotspots)
    cursor.execute('''
        SELECT s.last_known_class as class, COUNT(*) as count 
        FROM changes ch
        JOIN students s ON ch.student_id = s.id
        WHERE class IS NOT NULL AND class != ''
        GROUP BY class ORDER BY count DESC LIMIT 5
    ''')
    hotspot_classes = {row['class']: row['count'] for row in cursor.fetchall()}
    
    conn.close()
    return {
        "monthly": monthly_changes,
        "categories": category_stats,
        "hotspots": hotspot_classes
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
