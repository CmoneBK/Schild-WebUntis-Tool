import os
import csv
import configparser
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import colorama
from colorama import Fore, Style, init
import threading
from main import read_students, read_classes, send_email
from utils import safe_read_config

# Thread-sicherer Zugriff
console_lock = threading.Lock()

def thread_safe_print(color, message):
    with console_lock:
        print(f"{color}{message}{Style.RESET_ALL}", flush=True)


# Hilfsfunktionen
def print_error(message):
    thread_safe_print(Fore.RED, f"❌ {message}")

def print_warning(message):
    thread_safe_print(Fore.YELLOW, f"⚠️ {message}")

def print_admin_warning(message):
    thread_safe_print(Fore.LIGHTRED_EX, f"❗ {message}")

def print_warningtext(message):
    thread_safe_print(Fore.MAGENTA, f"👾 {message}")

def print_success(message):
    thread_safe_print(Fore.GREEN, f"✅ {message}")

def print_info(message):
    thread_safe_print(Fore.CYAN, f"ℹ️ {message}")

def print_creation(message):
    thread_safe_print(Fore.WHITE, f"✨ {message}")



# Generieren der Admin-Warnungen bei für den Fall inkonsistenter Daten. Wird ebenfalls direkt beim Start des Servers unter "if __name__ == "__main__":" abegerufen, sofern kein --skip-admin-warnings verwendet wurde.
def admin_warnings(send_email_flag=False):
    global admin_warnings_cache
    admin_warnings_cache = []

    # Admin-Warnungen werden erstellt
    print_info("Erstelle Admin-Warnungen...")

    # Haupt-Import-Datei einlesen
    students_output, students_by_id = read_students(use_abschlussdatum=False)

    # Einstellungen aus settings.ini einlesen
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    classes_dir = config.get('Directories', 'classes_directory')
    teachers_dir = config.get('Directories', 'teachers_directory')

    # Klassen- und Lehrkräfte-Daten einlesen
    classes_by_name, teachers = read_classes(classes_dir, teachers_dir, return_teachers=True)

    # Lehrer-Daten aus der Lehrerdatei extrahieren (Spalte "name")
    teacher_names = set(teachers.keys())

    # Sets für Deduplizierung der Warnungen
    warned_classes = set()
    warned_teachers_students = set()
    warned_teachers_classes = set()

    # Überprüfung auf fehlende Klassen in der Klassen-Datei
    for student in students_by_id.values():
        klasse = student.get('Klasse', '').strip().lower()
        if klasse and klasse not in classes_by_name:
            if klasse not in warned_classes:
                warned_classes.add(klasse)
                admin_warnings_cache.append({
                    'Typ': 'Fehlende Klasse in der Klassen-Datei',
                    'Details': f"Die Klasse '{klasse}' aus der Haupt-Import-Datei existiert nicht in der Klassen-Datei.",
                    'Schüler': f"{student.get('Vorname', '')} {student.get('Nachname', '')} (und ggf. weitere)"
                })

    # Überprüfung auf fehlende Klassenlehrkräfte in der Lehrkräfte-Datei
    for student in students_by_id.values():
        klassenlehrer = student.get('Klassenlehrer', '').strip()  # Klassenlehrer aus Haupt-Import        
        if klassenlehrer:  # Nur prüfen, wenn der Wert vorhanden ist
            if klassenlehrer not in teacher_names:  # Vergleich mit Lehrkräfte-Datei
                if klassenlehrer not in warned_teachers_students:
                    warned_teachers_students.add(klassenlehrer)
                    admin_warnings_cache.append({
                        'Typ': 'Fehlender Klassenlehrer in Lehrerdatei',
                        'Details': f"Der Klassenlehrer '{klassenlehrer}' aus der Haupt-Import-Datei existiert nicht in der Lehrkräfte-Datei.",
                        'Schüler': f"{student.get('Vorname', '')} {student.get('Nachname', '')} (und ggf. weitere)"
                    })

    # Überprüfen, ob CSV-Dateien im Klassenverzeichnis vorhanden sind
    class_csv_files = []
    if os.path.exists(classes_dir):
        class_csv_files = [f for f in os.listdir(classes_dir) if f.endswith('.csv')]
    
    # Falls wir API-Daten haben, brauchen wir die CSV nicht zwingend für weitere Warnungen
    is_api_data = any(c.get('api_data') for c in classes_by_name.values())

    if not class_csv_files:
        if is_api_data:
            print_info("Nutze API-Daten für Admin-Warnungen, überspringe CSV-spezifische Prüfungen.")
        else:
            print_admin_warning(f"Warnung: Keine Klassen-CSV-Dateien im Ordner '{classes_dir}' für die Erstellung von Admin-Warnungen gefunden.")
        return admin_warnings_cache

    # Neueste Klassen-CSV-Datei bestimmen
    newest_class_file = max(class_csv_files, key=lambda f: os.path.getctime(os.path.join(classes_dir, f)))

    # Warnungen für fehlende Klassenlehrkräfte in der Klassen-Datei (Spalten 8 und 9)
    with open(os.path.join(classes_dir, newest_class_file), 'r', newline='', encoding='utf-8-sig') as class_file:
        class_reader = csv.reader(class_file, delimiter=';')
        header = next(class_reader)
        for row in class_reader:
            for idx in [7, 8]:  # Indizes für Klassenlehrkräfte
                teacher_name = row[idx].strip() if len(row) > idx else ''
                if teacher_name and teacher_name not in teacher_names:
                    if teacher_name not in warned_teachers_classes:
                        warned_teachers_classes.add(teacher_name)
                        admin_warnings_cache.append({
                            'Typ': 'Fehlender Klassenlehrer in Lehrerdatei',
                            'Details': f"Der Klassenlehrer '{teacher_name}' aus der Klassen-Datei existiert nicht in der Lehrkräfte-Datei."
                        })

    # Admin-Warnungen in der Konsole ausgeben
    if admin_warnings_cache:
        print_admin_warning("Admin-Warnungen:")
        for warning in admin_warnings_cache:
            print_admin_warning(f"Typ: {warning['Typ']}, Details: {warning['Details']}")
        print_warningtext("Für die korrekte Funktion Warn-Funktionalität sollten Sie Ihre Klassen- und Lehrerdaten aktualisieren.")
    else:
        print_success("Keine Admin-Warnungen gefunden.")

    # E-Mail senden, falls das Kommandozeilenargument verwendet wurde
    if send_email_flag and admin_warnings_cache:
        config.read('email_settings.ini', encoding='utf-8-sig')
        admin_email = config.get('Email', 'admin_email', fallback=None)
        if not admin_email:
            print_error("Admin-E-Mail-Adresse fehlt in email_settings.ini.")
            return admin_warnings_cache

        subject = "Admin-Warnungen von WebUntis"
        body = "<p>Folgende Admin-Warnungen wurden generiert:</p><ul>"
        for warning in admin_warnings_cache:
            body += f"<li><strong>{warning['Typ']}:</strong> {warning['Details']}</li>"
        body += "</ul><p>Mit freundlichen Grüßen,<br>Ihr System</p>"

        try:
            send_email(subject, body, [admin_email])
            print_success(f"Admin-Warnungen wurden erfolgreich an {admin_email} gesendet.")
        except Exception as e:
            print_error(f"Fehler beim Senden der Admin-Warnungen: {e}")

    return admin_warnings_cache