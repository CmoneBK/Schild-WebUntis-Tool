import os  # Betriebssystemfunktionen wie Pfadoperationen
import sys  # Systemfunktionen und -parameter

# Basisverzeichnis explizit zum Suchpfad hinzufügen, um relative Importe zu ermöglichen
base_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(base_dir)

import csv  # Lesen und Schreiben von CSV-Dateien
import configparser  # Verarbeiten von Konfigurationsdateien im INI-Format
import webbrowser  # Öffnen von Webbrowsern
import threading  # Multithreading-Funktionen
import argparse  # Parsen von Kommandozeilenargumenten
import secrets  # Generieren sicherer Zufallswerte (z.B. für Secret Keys)
import winshell  # Interaktion mit der Windows-Shell (z.B. Erstellen von Verknüpfungen)
import pythoncom  # Python COM-Schnittstelle für Windows
import threading
from datetime import datetime  # Arbeiten mit Datum und Uhrzeit
from flask import Flask, render_template, request, jsonify, session  # Flask-Webframework
from main import run, read_students, read_classes, compare_timeframe_imports  # Import von Funktionen aus eigenen Modulen
from smtp import send_email  # Funktion zum Versenden von E-Mails aus eigenem Modul
from waitress import serve

# Globale Variablen für Warnungen und generierte E-Mails
global warnings_cache, generated_emails_cache


def resource_path(relative_path):
    """ Gibt den Pfad zu einer Ressource zurück, funktioniert für dev und bei PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Flask-App initialisieren
app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))
app.secret_key = secrets.token_hex(24) # Generierung eines zufälligen Secret Keys für die Session

# Globale Caches für Warnungen und generierte E-Mails
warnings_cache = []  # Cache für Warnungen
generated_emails_cache = []  # Cache für generierte E-Mails

# Prüfen, ob die Konfigurationsdateien existieren, und sie bei Bedarf mit Standardwerten erstellen
def process_data(no_log=False, no_xlsx=False):
    # Konfigurationsdatei einlesen
    config = configparser.ConfigParser()
    config.read('settings.ini')
    
    # Werte aus der Konfigurationsdatei laden
    use_abschlussdatum = config.getboolean('ProcessingOptions', 'use_abschlussdatum', fallback=False)
    create_second_file = config.getboolean('ProcessingOptions', 'create_second_file', fallback=False)
    warn_entlassdatum = config.getboolean('ProcessingOptions', 'warn_entlassdatum', fallback=True)
    warn_aufnahmedatum = config.getboolean('ProcessingOptions', 'warn_aufnahmedatum', fallback=True)
    warn_klassenwechsel = config.getboolean('ProcessingOptions', 'warn_klassenwechsel', fallback=True)
    
    # Aktuelle Einstellungen in der Konsole ausgeben
    print("Starting processing with the following options:")
    print(f"use_abschlussdatum: {use_abschlussdatum}")
    print(f"create_second_file: {create_second_file}")
    print(f"warn_entlassdatum: {warn_entlassdatum}")
    print(f"warn_aufnahmedatum: {warn_aufnahmedatum}")
    print(f"warn_klassenwechsel: {warn_klassenwechsel}")

    # Argumente aus der Kommandozeile (falls vorhanden)
    args = argparse.Namespace()
    no_log = args.no_log if hasattr(args, 'no_log') else False
    no_xlsx = args.no_xlsx if hasattr(args, 'no_xlsx') else False

    # Datenverarbeitung starten
    all_warnings = run(
        use_abschlussdatum=use_abschlussdatum,
        create_second_file=create_second_file,
        warn_entlassdatum=warn_entlassdatum,
        warn_aufnahmedatum=warn_aufnahmedatum,
        warn_klassenwechsel=warn_klassenwechsel,
        no_log=no_log,
        no_xlsx=no_xlsx
    )
    print("Processing completed.")
    return all_warnings


def ensure_ini_files_exist():
    # Standardverzeichnisse definieren
    default_classes_dir = "Klassendaten"
    default_teachers_dir = "Lehrerdaten"
    default_log_dir = "Logs"
    default_xlsx_dir = "ExcelExports"
    default_import_dir = "WebUntis Importe"

    # Standard-Inhalt für settings.ini vorbereiten
    settings_ini_content = f"""[Directories]
classes_directory = ./{default_classes_dir}
teachers_directory = ./{default_teachers_dir}
log_directory = ./{default_log_dir}
xlsx_directory = ./{default_xlsx_dir}
import_directory = ./{default_import_dir}

[ProcessingOptions]
use_abschlussdatum = False
create_second_file = False
warn_entlassdatum = True
warn_aufnahmedatum = True
warn_klassenwechsel = True
timeframe_hours = 24
"""
    # Standard-Inhalt für email_settings.ini vorbereiten
    email_settings_ini_content = """# Einstellungen für den E-Mail-Versand
# Passen Sie diese Einstellungen an Ihren SMTP-Server an.
# Beispiele:
# smtp_server = smtp.gmail.com # SMTP-Server-Adresse
# smtp_port = 587 # SMTP-Port (z. B. 587 für STARTTLS)
# smtp_user = ihrbenutzer@gmail.com # Benutzername für SMTP
# smtp_password = ihrpasswort # Passwort für SMTP
# smtp_encryption = starttls # Verschlüsselungsmethode (starttls oder ssl)
# admin_email = admin@example.com #E-Mail Adresse des Admins zum Erhalt spezieller Admin-Warnungen bei Nutzung über die Kommandozeile

[Email]
smtp_server = smtp.example.com  
smtp_port = 587  
smtp_user = user@example.com  
smtp_password = password  
smtp_encryption = starttls
admin_email = admin@example.com

# OAuth-Einstellungen (falls verwendet)
[OAuth]
use_oauth = False
credentials_path = ./config/credentials.json

# Vorlagen für generierte E-Mails
# Verwenden Sie Platzhalter wie {Vorname}, {Nachname}, {Klasse}, {neues_entlassdatum}, etc.

[Templates]
subject_entlassdatum = Webuntis-Hinweis: Entlassdatum-Problem bei $Vorname $Nachname
body_entlassdatum = <p>Sehr geehrter/Sehr geehrte Herr/Frau $Klassenlehrkraft_1,</p><p>Es gibt ein Problem mit dem Entlassdatum des Schülers/der Schülerin <strong>$Vorname $Nachname</strong> aus der Klasse <strong>$Klasse</strong>.</p><p></p><p><strong>Neues Entlassdatum:</strong> $neues_entlassdatum</p><p><strong>Altes Entlassdatum:</strong> $altes_entlassdatum</p><p></p><p>$zeitraum_text</p><p></p><p>In dieser Zeit war der Schüler/die Schülerin nun offiziel teil der Klasse, jedoch nicht im digitalen Klassenbuch dokumentierbar. Dies muss nun nachgeholt werden.</p><p></p><p><strong>Klassenlehrkraft 1:</strong> $Klassenlehrkraft_1, E-Mail: $Klassenlehrkraft_1_Email</p><p><strong>Klassenlehrkraft 2:</strong> $Klassenlehrkraft_2, E-Mail: $Klassenlehrkraft_2_Email</p><p></p><p><strong>Hinweis:</strong> Es ist nicht möglich auf diese E-Mail Adresse zu antworten.</p><p></p><p>Mit freundlichen Grüßen,</p><p>Das WebUntis Team</p>
subject_aufnahmedatum = Webuntis-Hinweis: Aufnahmedatum-Problem bei $Vorname $Nachname
body_aufnahmedatum = <p>Sehr geehrter/Sehr geehrte Herr/Frau $Klassenlehrkraft_1,</p><p>Das Aufnahmedatum des Schülers/der Schülerin <strong>$Vorname $Nachname</strong> aus der Klasse <strong>$Klasse</strong> hat sich geändert.</p><p></p><p><strong>Neues Aufnahmedatum:</strong> $neues_aufnahmedatum</p><p><strong>Altes Aufnahmedatum:</strong> $altes_aufnahmedatum</p><p></p><p>$zeitraum_text</p><p></p><p>In dieser Zeit war der Schüler/die Schülerin nun offiziel teil der Klasse, jedoch nicht im digitalen Klassenbuch dokumentierbar. Dies muss nun nachgeholt werden.</p><p></p><p><strong>Klassenlehrkraft 1:</strong> $Klassenlehrkraft_1, E-Mail: $Klassenlehrkraft_1_Email</p><p><strong>Klassenlehrkraft 2:</strong> $Klassenlehrkraft_2, E-Mail: $Klassenlehrkraft_2_Email</p><p></p><p><strong>Hinweis:</strong> Es ist nicht möglich auf diese E-Mail Adresse zu antworten.</p><p></p><p>Mit freundlichen Grüßen,</p><p>Das WebUntis Team</p>
subject_klassenwechsel = Webuntis-Hinweis: Klassenwechsel bei $Vorname $Nachname
body_klassenwechsel = <p>Sehr geehrter/Sehr geehrte Herr/Frau $Klassenlehrkraft_1,</p><p>Es gab einen Klassenwechsel des Schülers/der Schülerin <strong>$Vorname $Nachname</strong>.</p><p>Sofern dieser Klassenwechsel nicht am heutigen Tag stattfand, informieren Sie bitte das WebUntis-Team über die Notwendigkeit einer Korrektur. </p><p>Liegt der Wechsel in der Vergangenheit müssen anschließend die Tage zwischen heute und diesem Wechsel nachdokumentiert werden.</p><p></p><p><strong>Alte Klasse:</strong> $alte_klasse</p><p><strong>Neue Klasse:</strong> $neue_klasse</p><p></p><p><strong>Klassenlehrkraft 1:</strong> $Klassenlehrkraft_1, E-Mail: $Klassenlehrkraft_1_Email</p><p><strong>Klassenlehrkraft 2:</strong> $Klassenlehrkraft_2, E-Mail: $Klassenlehrkraft_2_Email</p><p></p><p><strong>Hinweis:</strong> Es ist nicht möglich auf diese E-Mail Adresse zu antworten.</p><p></p><p>Mit freundlichen Grüßen,</p><p>Das WebUntis Team</p>
"""

    # Prüfen, ob settings.ini existiert, und ggf. erstellen
    settings_ini_exists = os.path.exists("settings.ini")
    if not settings_ini_exists:
        with open("settings.ini", "w") as file:
            file.write(settings_ini_content)
        print("settings.ini wurde erstellt.")

    # Prüfen, ob email_settings.ini existiert, und ggf. erstellen
    if not os.path.exists("email_settings.ini"):
        with open("email_settings.ini", "w") as file:
            file.write(email_settings_ini_content)
        print("email_settings.ini wurde erstellt.")

    # Sicherstellen, dass die in settings.ini definierten Ordner existieren
    config = configparser.ConfigParser()
    if settings_ini_exists:
        config.read("settings.ini")

    directories = {
        "classes_directory": f"./{default_classes_dir}",
        "teachers_directory": f"./{default_teachers_dir}",
        "log_directory": f"./{default_log_dir}",
        "xlsx_directory": f"./{default_xlsx_dir}",
    }

    for key, default_path in directories.items():
        directory = config.get("Directories", key, fallback=default_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Ordner '{directory}' wurde erstellt.")

    # Sicherstellen, dass der Import-Ordner existiert
    import_dir = "WebUntis Importe"
    if not os.path.exists(import_dir):
        os.makedirs(import_dir)
        print(f"Ordner '{import_dir}' wurde erstellt.")

def admin_warnings(send_email_flag=False):
    global admin_warnings_cache
    admin_warnings_cache = []

    # Admin-Warnungen werden erstellt
    print("Erstelle Admin-Warnungen...")

    # Haupt-Import-Datei einlesen
    students_output, students_by_id = read_students(use_abschlussdatum=False)

    # Einstellungen aus settings.ini einlesen
    config = configparser.ConfigParser()
    config.read('settings.ini')
    classes_dir = config.get('Directories', 'classes_directory')
    teachers_dir = config.get('Directories', 'teachers_directory')

    # Klassen- und Lehrkräfte-Daten einlesen
    classes_by_name, teachers = read_classes(classes_dir, teachers_dir, return_teachers=True)

    # Lehrer-Daten aus der Lehrerdatei extrahieren (Spalte "name")
    teacher_names = set(teachers.keys())

    # Überprüfung auf fehlende Klassen in der Klassen-Datei
    for student in students_by_id.values():
        klasse = student.get('Klasse', '').strip().lower()
        if klasse not in classes_by_name:
            admin_warnings_cache.append({
                'Typ': 'Fehlende Klasse in der Klassen-Datei',
                'Details': f"Die Klasse '{klasse}' aus der Haupt-Import-Datei existiert nicht in der Klassen-Datei.",
                'Schüler': f"{student.get('Vorname', '')} {student.get('Nachname', '')}"
            })

    # Überprüfung auf fehlende Klassenlehrkräfte in der Lehrkräfte-Datei
    for student in students_by_id.values():
        klassenlehrer = student.get('Klassenlehrer', '').strip()  # Klassenlehrer aus Haupt-Import        
        if klassenlehrer:  # Nur prüfen, wenn der Wert vorhanden ist
            if klassenlehrer not in teacher_names:  # Vergleich mit Lehrkräfte-Datei
                admin_warnings_cache.append({
                    'Typ': 'Fehlender Klassenlehrer in Lehrerdatei',
                    'Details': f"Der Klassenlehrer '{klassenlehrer}' aus der Haupt-Import-Datei existiert nicht in der Lehrkräfte-Datei.",
                    'Schüler': f"{student.get('Vorname', '')} {student.get('Nachname', '')}"
                })

    # Überprüfen, ob CSV-Dateien im Klassenverzeichnis vorhanden sind
    class_csv_files = [f for f in os.listdir(classes_dir) if f.endswith('.csv')]
    if not class_csv_files:
        print(f"Warnung: Keine Klassen-CSV-Dateien im Ordner '{classes_dir}' gefunden.")
        return admin_warnings_cache  # Gibt leere Warnungsliste zurück oder handle dies mit Dummy-Daten

    # Neueste Klassen-CSV-Datei bestimmen
    newest_class_file = max(class_csv_files, key=lambda f: os.path.getctime(os.path.join(classes_dir, f)))

    # Warnungen für fehlende Klassenlehrkräfte in der Klassen-Datei (Spalten 8 und 9)
    with open(os.path.join(classes_dir, newest_class_file), 'r', newline='', encoding='utf-8-sig') as class_file:
        class_reader = csv.reader(class_file, delimiter=';')
        header = next(class_reader)
        for row in class_reader:
            for idx in [7, 8]:  # Indizes für Klassenlehrkräfte
                teacher_name = row[idx].strip()
                if teacher_name and teacher_name not in teacher_names:
                    admin_warnings_cache.append({
                        'Typ': 'Fehlender Klassenlehrer in Lehrerdatei',
                        'Details': f"Der Klassenlehrer '{teacher_name}' aus der Klassen-Datei existiert nicht in der Lehrkräfte-Datei."
                    })

    # Admin-Warnungen in der Konsole ausgeben
    print("Admin-Warnungen:")
    for warning in admin_warnings_cache:
        print(f"Typ: {warning['Typ']}, Details: {warning['Details']}")
    else:
        print("Keine Admin-Warnungen gefunden.")

    # E-Mail senden, falls das Kommandozeilenargument verwendet wurde
    if send_email_flag and admin_warnings_cache:
        config.read('email_settings.ini')
        admin_email = config.get('Email', 'admin_email', fallback=None)
        if not admin_email:
            print("Admin-E-Mail-Adresse fehlt in email_settings.ini.")
            return admin_warnings_cache

        subject = "Admin-Warnungen von WebUntis"
        body = "<p>Folgende Admin-Warnungen wurden generiert:</p><ul>"
        for warning in admin_warnings_cache:
            body += f"<li><strong>{warning['Typ']}:</strong> {warning['Details']}</li>"
        body += "</ul><p>Mit freundlichen Grüßen,<br>Ihr System</p>"

        try:
            send_email(subject, body, [admin_email])
            print(f"Admin-Warnungen wurden erfolgreich an {admin_email} gesendet.")
        except Exception as e:
            print(f"Fehler beim Senden der Admin-Warnungen: {e}")

    return admin_warnings_cache


@app.route('/', methods=['GET', 'POST'])
def index():
    global warnings_cache  # Globaler Cache für die Zwischenspeicherung von Warnungen
    warnings = []
    confirmation = None  # Variable für Bestätigungsnachricht
    errors = []  # Liste für Fehlermeldungen
    warnings_messages = []  # Liste für nicht-blockierende Warnungen

    # Zugriff auf die globalen CLI-Argumente
    global cli_args
    no_log = cli_args.get("no_log", False)
    no_xlsx = cli_args.get("no_xlsx", False)

    # Werte aus der settings.ini laden
    config = configparser.ConfigParser()
    config.read("settings.ini")
    use_abschlussdatum = config.getboolean('ProcessingOptions', 'use_abschlussdatum', fallback=False)
    create_second_file = config.getboolean('ProcessingOptions', 'create_second_file', fallback=False)
    warn_entlassdatum = config.getboolean('ProcessingOptions', 'warn_entlassdatum', fallback=True)
    warn_aufnahmedatum = config.getboolean('ProcessingOptions', 'warn_aufnahmedatum', fallback=True)
    warn_klassenwechsel = config.getboolean('ProcessingOptions', 'warn_klassenwechsel', fallback=True)

    # Werte aus der email_settings.ini laden
    config = configparser.ConfigParser()
    config.read("email_settings.ini")

    # Vorlagenwerte laden
    subject_entlassdatum = config.get("Templates", "subject_entlassdatum", fallback="")
    body_entlassdatum = config.get("Templates", "body_entlassdatum", fallback="")
    subject_aufnahmedatum = config.get("Templates", "subject_aufnahmedatum", fallback="")
    body_aufnahmedatum = config.get("Templates", "body_aufnahmedatum", fallback="")
    subject_klassenwechsel = config.get("Templates", "subject_klassenwechsel", fallback="")
    body_klassenwechsel = config.get("Templates", "body_klassenwechsel", fallback="")

    # Lese die Konfigurationspfade aus der settings.ini
    config = configparser.ConfigParser()
    config.read("settings.ini")
    classes_dir = config.get("Directories", "classes_directory", fallback="./Klassendaten")
    teachers_dir = config.get("Directories", "teachers_directory", fallback="./Lehrerdaten")

    # Überprüfen, ob die Haupt-CSV-Datei vorhanden ist
    main_csv_exists = any(f.endswith('.csv') for f in os.listdir('.') if not os.path.isdir(f))
    if not main_csv_exists:
        errors.append("Die Haupt-CSV-Datei fehlt im Hauptverzeichnis und wird für die Verarbeitung benötigt.")
        print("Fehler: Haupt-CSV-Datei fehlt im Hauptverzeichnis.")

    # Überprüfen, ob die Klassendaten verfügbar sind
    if not os.path.exists(classes_dir) or not any(f.endswith('.csv') for f in os.listdir(classes_dir)):
        warnings_messages.append("Die Klassendaten fehlen oder es sind keine CSV-Dateien im konfigurierten Ordner vorhanden.")
        print(f"Warnung: Keine Klassendaten im Ordner '{classes_dir}' gefunden.")

    # Überprüfen, ob die Lehrerdaten verfügbar sind
    if not os.path.exists(teachers_dir) or not any(f.endswith('.csv') for f in os.listdir(teachers_dir)):
        warnings_messages.append("Die Lehrerdaten fehlen oder es sind keine CSV-Dateien im konfigurierten Ordner vorhanden.")
        print(f"Warnung: Keine Lehrerdaten im Ordner '{teachers_dir}' gefunden.")

    if request.method == 'POST' and not errors:
        # Aktuelle Werte aus dem Formular lesen und die Auswahl des Benutzers speichern
        use_abschlussdatum = request.form.get('use_abschlussdatum') == 'on'
        create_second_file = request.form.get('create_second_file') == 'on'
        warn_entlassdatum = request.form.get('warn_entlassdatum') == 'on'
        warn_aufnahmedatum = request.form.get('warn_aufnahmedatum') == 'on'
        warn_klassenwechsel = request.form.get('warn_klassenwechsel') == 'on'

        # Übergebe die Auswahl an die Run-Funktion
        try:
            # Datenverarbeitung basierend auf den Benutzereinstellungen
            print("Starte Verarbeitung über die Weboberfläche...")
            warnings = run(
                use_abschlussdatum=use_abschlussdatum,
                create_second_file=create_second_file,
                warn_entlassdatum=warn_entlassdatum,
                warn_aufnahmedatum=warn_aufnahmedatum,
                warn_klassenwechsel=warn_klassenwechsel,
                no_log=no_log,
                no_xlsx=no_xlsx
            )
            warnings_cache = warnings  # Speichert Warnungen zur späteren Nutzung

            # Setzt eine Bestätigungsnachricht nach erfolgreicher Ausführung
            confirmation = "Verarbeitung erfolgreich abgeschlossen."
            print("Verarbeitung über die Weboberfläche erfolgreich abgeschlossen.")
        except Exception as e:
            errors.append(f"Fehler während der Verarbeitung: {str(e)}")
            print(f"Fehler während der Verarbeitung über die Weboberfläche: {str(e)}")

    # Seite mit aktuellen Checkbox-Zuständen, Warnungen, Fehlern und Bestätigung rendern
    return render_template(
        'index.html',
        warnings=warnings,
        confirmation=confirmation,
        errors=errors,
        warnings_messages=warnings_messages,
        use_abschlussdatum=use_abschlussdatum,
        create_second_file=create_second_file,
        warn_entlassdatum=warn_entlassdatum,
        warn_aufnahmedatum=warn_aufnahmedatum,
        warn_klassenwechsel=warn_klassenwechsel,
        subject_entlassdatum=subject_entlassdatum,
        body_entlassdatum=body_entlassdatum,
        subject_aufnahmedatum=subject_aufnahmedatum,
        body_aufnahmedatum=body_aufnahmedatum,
        subject_klassenwechsel=subject_klassenwechsel,
        body_klassenwechsel=body_klassenwechsel
    )

from string import Template

@app.route('/generate_emails', methods=['POST'])
def generate_emails():
    global warnings_cache, generated_emails_cache
    generated_emails_cache = []  # Globaler Cache für generierte E-Mails

    if warnings_cache:
        print("Generiere E-Mails basierend auf den vorhandenen Warnungen...")
        # Lade die Vorlagen aus der email_settings.ini
        config = configparser.ConfigParser()
        config.read("email_settings.ini")

        for warning in warnings_cache:
            # Bestimme den Typ der Warnung
            if 'neues_entlassdatum' in warning:
                warning_type = "entlassdatum"
            elif 'neues_aufnahmedatum' in warning:
                warning_type = "aufnahmedatum"
            elif 'neue_klasse' in warning:
                warning_type = "klassenwechsel"
            else:
                continue  # Unbekannter Warnungstyp wird übersprungen

            # Dynamische Einbindung des Zeitraums (falls vorhanden)
            zeitraum_text = (
                f"<p><strong>Zeitraum nicht dokumentiert:</strong> {warning.get('Zeitraum_nicht_dokumentiert', 'N/A')}</p>"
                if 'Zeitraum_nicht_dokumentiert' in warning
                else ""
            )

            # Prüfen, ob "Volljaehrig" verwendet wird, und den Wert dynamisch bereitstellen
            if 'Volljährig' not in warning:
                warning['Volljaehrig'] = warning.get('Volljaehrig', 'Unbekannt')

            # Lade Vorlagen aus der .ini-Datei
            try:
                subject_template = config.get("Templates", f"subject_{warning_type}")
                body_template = config.get("Templates", f"body_{warning_type}")
            except configparser.NoOptionError:
                error_message = f"Vorlage für {warning_type} fehlt in der Konfigurationsdatei."
                print(error_message)
                return jsonify({"message": f"Vorlage für {warning_type} fehlt in der Konfigurationsdatei."}), 400

            # Verwende Template-System zur Verarbeitung der Vorlagen
            try:
                subject = Template(subject_template).substitute(**warning)
                body = Template(body_template).substitute(
                    **warning,
                    zeitraum_text=zeitraum_text  # Zusatzwert für Zeitraum
                )
            except KeyError as e:
                error_message = f"Fehlender Platzhalter: {e} in der Vorlage für {warning_type}"
                print(error_message)
                return jsonify({"message": f"Fehlender Platzhalter: {e} in der Vorlage für {warning_type}"}), 400

            # E-Mail zur Liste hinzufügen
            generated_emails_cache.append({
                'subject': subject,
                'body': body,
                'to': [warning.get('Klassenlehrkraft_1_Email', 'N/A'), warning.get('Klassenlehrkraft_2_Email', 'N/A')]
            })
        print("E-Mails wurden erfolgreich generiert.")
        return jsonify({"message": "Die E-Mails wurden erfolgreich generiert.", "emails": generated_emails_cache})
    else:
        print("Keine Warnungen vorhanden, um E-Mails zu generieren.")
        return jsonify({"message": "Keine Warnungen verfügbar, um E-Mails zu generieren."})


@app.route('/get_templates', methods=['GET'])
def get_templates():
    # Lädt die E-Mail-Vorlagen aus der Konfigurationsdatei
    print("Lade E-Mail-Vorlagen aus 'email_settings.ini'...")
    config = configparser.ConfigParser()
    try:
        config.read('email_settings.ini')
        return jsonify({
            "subject_entlassdatum": config.get("Templates", "subject_entlassdatum", fallback=""),
            "body_entlassdatum": config.get("Templates", "body_entlassdatum", fallback=""),
            "subject_aufnahmedatum": config.get("Templates", "subject_aufnahmedatum", fallback=""),
            "body_aufnahmedatum": config.get("Templates", "body_aufnahmedatum", fallback=""),
            "subject_klassenwechsel": config.get("Templates", "subject_klassenwechsel", fallback=""),
            "body_klassenwechsel": config.get("Templates", "body_klassenwechsel", fallback="")
        })
        print("E-Mail-Vorlagen erfolgreich geladen.")
    except Exception as e:
        error_message = f"Fehler beim Laden der E-Mail-Vorlagen: {str(e)}"
        print(error_message)
        return jsonify({"error": str(e)}), 500
@app.route('/update_templates', methods=['POST'])
def update_templates():
    # Aktualisiert die E-Mail-Vorlagen basierend auf den vom Benutzer gesendeten Daten
    print("Aktualisiere E-Mail-Vorlagen in 'email_settings.ini'...")
    try:
        # E-Mail-Einstellungen laden
        email_config = configparser.ConfigParser()
        email_config.read('email_settings.ini')

        # Vorlagen mit den bereitgestellten Daten aktualisieren
        email_config['Templates']['subject_entlassdatum'] = request.form.get('subject_entlassdatum', '')
        email_config['Templates']['body_entlassdatum'] = request.form.get('body_entlassdatum', '')
        email_config['Templates']['subject_aufnahmedatum'] = request.form.get('subject_aufnahmedatum', '')
        email_config['Templates']['body_aufnahmedatum'] = request.form.get('body_aufnahmedatum', '')
        email_config['Templates']['subject_klassenwechsel'] = request.form.get('subject_klassenwechsel', '')
        email_config['Templates']['body_klassenwechsel'] = request.form.get('body_klassenwechsel', '')

        # Änderungen in die Datei schreiben
        with open('email_settings.ini', 'w') as configfile:
            email_config.write(configfile)
        print("E-Mail-Vorlagen wurden erfolgreich aktualisiert.")
        return jsonify({'message': 'E-Mail-Vorlagen erfolgreich gespeichert!'})
    except Exception as e:
        error_message = f'Fehler beim Speichern der E-Mail-Vorlagen: {str(e)}'
        print(error_message)
        return jsonify({'message': f'Fehler beim Speichern der E-Mail-Vorlagen: {str(e)}'}), 500



@app.route('/send_emails', methods=['POST'])
def send_emails():
    global generated_emails_cache
    if generated_emails_cache:
        print("Beginne mit dem Senden der generierten E-Mails...")
        # Verwende den Cache zum Senden der E-Mails
        for email in generated_emails_cache:
            try:
                send_email(
                    subject=email['subject'],
                    body=email['body'],
                    to_addresses=email['to']
                )
                print(f"E-Mail an {email['to']} erfolgreich gesendet.")
            except Exception as e:
                print(f"Fehler beim Senden der E-Mail an {email['to']}: {str(e)}")
        print("Alle E-Mails wurden verarbeitet.")
        return jsonify({"message": "Die E-Mails wurden erfolgreich versendet."})
    else:
        print("Keine generierten E-Mails zum Senden vorhanden.")
        return jsonify({"message": "Keine generierten E-Mails verfügbar, um sie zu versenden."})
@app.route('/view_generated_emails', methods=['GET'])
def view_generated_emails():
    global generated_emails_cache
    print("Anzeige der generierten E-Mails im Webinterface...")
    # Rendert die Seite zum Anzeigen der generierten E-Mails
    return render_template('view_emails.html', emails=generated_emails_cache)

@app.route('/load-settings', methods=['GET'])
def load_settings():
    print("Lade Einstellungen aus 'settings.ini' und 'email_settings.ini'...")
    settings = {}
    # settings.ini laden
    config = configparser.ConfigParser()
    config.read("settings.ini")
    for section in config.sections():
        if section not in settings:
            settings[section] = {}
        settings[section].update({key: config.get(section, key, fallback="") for key in config[section]})

    # email_settings.ini laden
    email_config = configparser.ConfigParser()
    email_config.read("email_settings.ini")
    for section in email_config.sections():
        if section not in settings:
            settings[section] = {}
        settings[section].update({key: email_config.get(section, key, fallback="") for key in email_config[section]})
    print("Einstellungen erfolgreich geladen.")
    return jsonify(settings)

def save_to_settings_ini(settings):
    # Funktion zum Speichern der Einstellungen in die Datei 'settings.ini'
    print("Speichere Einstellungen in 'settings.ini'...")
    config = configparser.ConfigParser()
    config.read("settings.ini")
    for section, values in settings.items():
        if not config.has_section(section):
            config.add_section(section)
            print(f"Abschnitt '{section}' hinzugefügt.")
        for key, value in values.items():
            # Ersetze Backslashes durch Forward Slashes für Pfade
            if "directory" in key:
                value = value.replace("\\", "/")
                print(f"Pfad angepasst für '{key}': {value}")
            config.set(section, key, str(value))
            print(f"Einstellung gesetzt: [{section}] {key} = {value}")
    with open("settings.ini", "w") as configfile:
        config.write(configfile)
    print("Einstellungen wurden erfolgreich in 'settings.ini' gespeichert.")

def save_to_email_settings_ini(settings):
    # Funktion zum Speichern der E-Mail-Einstellungen in 'email_settings.ini'
    print("Speichere E-Mail-Einstellungen in 'email_settings.ini'...")
    config = configparser.ConfigParser()
    config.read("email_settings.ini")
    # Bestehende Abschnitte beibehalten
    existing_sections = config.sections()
    # Aktualisiere nur die bereitgestellten Abschnitte
    for section, values in settings.items():
        print(f"Aktualisiere Abschnitt '{section}'...")
        if section in existing_sections:
            for key, value in values.items():
                config.set(section, key, str(value))
                print(f"Einstellung aktualisiert: [{section}] {key} = {value}")
        else:
            print(f"Füge neuen Abschnitt '{section}' hinzu...")
            config[section] = values
            for key, value in values.items():
                print(f"Einstellung hinzugefügt: [{section}] {key} = {value}")
    # Einstellungen in die Datei schreiben
    with open("email_settings.ini", "w") as configfile:
        config.write(configfile)
    print("E-Mail-Einstellungen wurden erfolgreich in 'email_settings.ini' gespeichert.")

@app.route('/save-settings', methods=['POST'])
def save_settings():
    print("Speichere Einstellungen in 'settings.ini' und 'email_settings.ini'...")
    settings = request.json.get('settings', {})
    settings_ini_data = {}
    email_settings_ini_data = {}

    # Definiere, welche Abschnitte zu email_settings.ini gehören
    email_sections = ['Email', 'OAuth', 'Templates']

    # Aufteilen der Einstellungen in die entsprechenden Dateien
    for section, values in settings.items():
        if section in email_sections:
            if section not in email_settings_ini_data:
                email_settings_ini_data[section] = {}
            email_settings_ini_data[section].update(values)
        else:
            if section not in settings_ini_data:
                settings_ini_data[section] = {}
            settings_ini_data[section].update(values)
    # Einstellungen speichern
    if settings_ini_data:
        save_to_settings_ini(settings_ini_data)
    if email_settings_ini_data:
        save_to_email_settings_ini(email_settings_ini_data)

    print("Einstellungen wurden erfolgreich gespeichert.")
    return jsonify({"status": "success"})

@app.route('/process-directory', methods=['POST'])
def process_directory():
    print("Verarbeite ausgewähltes Verzeichnis...")
    directory_name = request.form.get("directoryName")
    if not directory_name:
        error_message = "Verzeichnisname ist erforderlich."
        print(f"Fehler: {error_message}")
        return jsonify({"error": error_message}), 400

    # Beispiel: Verarbeite das Verzeichnis (Anpassung an Ihr System erforderlich)
    full_path = os.path.abspath(directory_name)

    # Konvertiere Backslashes zu Forward Slashes für INI-Kompatibilität
    formatted_path = full_path.replace("\\", "/")

    return jsonify({"fullPath": formatted_path})




@app.route('/get-arguments', methods=['GET'])
def get_arguments():
    # Route zum Abrufen der verfügbaren Kommandozeilenargumente mit ihren Beschreibungen
    # Diese Funktion wird vom Frontend aufgerufen, um die Argumente für den Verknüpfungsersteller bereitzustellen
    print("Bereite Liste der verfügbaren Kommandozeilenargumente vor...")
    # Liste der Argumente mit Beschreibungen
    arguments = [
        {"name": "--process", "description": "Führt den Hauptprozess aus (Verarbeitung des Schild-Exports, Erstellungen von Warnungen, Erstellung der Log-Dateien)."},
        {"name": "--generate-emails --send-emails", "description": "Generiert und sendet die Warn-Emails auf Grundlage der gespeicherten Einstellungen. (Davor ist --process erforderlich.)"},
        {"name": "--send-admin-warnings", "description": "Sendet Admin-Warnungen per Email an die hinterlegte Admin Email-Adresse, wenn im SchildExport Klassen oder Klassenlehrkräfte vorkommen, die in den Klassen- oder Lehrkraftdaten fehlen."},
        {"name": "--no-web", "description": "Verhindert das Öffnen des Web-Interfaces."},
        {"name": "--send-log-email", "description": "Sendet eine tabellarische Übersicht (html) und die den Excel-Änderungslog (im Anhang) für einen definierten Zeitraum an die hinterlegte Admin Email-Adresse."},
        {"name": "--skip-admin-warnings", "description": "Überspringt die Erstellung von Admin-Warnungen. (Darf nicht mit --send admin-warnings kombiniert werden.)"},
        {"name": "--no-log", "description": "Verhindert die Erstellung der .log Logdateien."},
        {"name": "--no-xlsx", "description": "Verhindert die Erstellung der Excel Logdateien. (Darf nicht mit --send-log-email kombiniert werden.)"}
    ]
    print("Liste der verfügbaren Kommandozeilenargumente wurde erstellt.")
    return jsonify({"success": True, "arguments": arguments})
@app.route('/get-executable-path', methods=['GET'])
def get_executable_path():
    # Route zum Abrufen des Pfads der ausführbaren Datei
    print("Bestimme den Pfad der ausführbaren Datei...")
    # Bestimmen des Pfads der ausführbaren Datei
    if getattr(sys, 'frozen', False):
        # Wenn die Anwendung eingefroren ist (in eine .exe kompiliert mit PyInstaller)
        exe_path = sys.executable
        print(f"Anwendung ist eingefroren. Pfad der ausführbaren Datei: {exe_path}")
    else:
        # Wenn die Anwendung in einer Standard-Python-Umgebung läuft
        exe_path = os.path.abspath(sys.argv[0])
        print(f"Anwendung läuft in der Python-Umgebung. Pfad der ausführbaren Datei: {exe_path}")
    return jsonify({"exePath": exe_path})
@app.route('/create-shortcut', methods=['POST'])
def create_shortcut():
    # Route zum Erstellen einer Desktop-Verknüpfung für die Anwendung mit den angegebenen Argumenten
    print("Erstelle Desktop-Verknüpfung...")
    data = request.json
    exe_path = data.get('exePath')
    args = data.get('args', '')

    # Empfangenen Pfad und Argumente ausgeben
    print(f"Empfangener exe_path: {exe_path}")
    print(f"Empfangene Argumente: {args}")
    print(f"Existiert exe_path? {os.path.exists(exe_path)}")

    if not exe_path or not os.path.exists(exe_path):
        error_message = f"Pfad der ausführbaren Datei nicht gefunden: {exe_path}"
        print(f"Fehler: {error_message}")
        return jsonify({"success": False, "error": error_message})

    try:
        # COM-Bibliothek initialisieren
        import pythoncom
        pythoncom.CoInitialize()  # Initialize COM
        print("COM-Bibliothek initialisiert.")
        
        # Desktop-Pfad abrufen
        import winshell
        desktop = winshell.desktop()
        print(f"Desktop-Pfad: {desktop}")

        # Pfad für die Verknüpfung festlegen
        shortcut_path = os.path.join(desktop, "Schild-WebUntis-Tool.lnk")
        print(f"Verknüpfungspfad: {shortcut_path}")

        # Verknüpfung erstellen
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = exe_path
            shortcut.arguments = args
            shortcut.description = "Shortcut for Schild-WebUntis-Tool"
        print("Verknüpfung erfolgreich erstellt.")
        return jsonify({"success": True})
    except Exception as e:
        error_message = f"Fehler beim Erstellen der Verknüpfung: {str(e)}"
        print(error_message)
        return jsonify({"success": False, "error": error_message})
    finally:
        # COM-Bibliothek deinitialisieren
        pythoncom.CoUninitialize()
        print("COM-Bibliothek deinitialisiert.")

# Öffnet den Standardbrowser automatisch auf die lokale URL
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

# Globale Variable für CLI-Argumente
cli_args = {}

if __name__ == "__main__":


    ensure_ini_files_exist()

    # Parser für Kommandozeilenargumente
    parser = argparse.ArgumentParser(description="Command-line interface for processing data.")
    parser.add_argument('--process', action='store_true', help="Run the main processing task.")
    parser.add_argument('--generate-emails', action='store_true', help="Generate warning emails.")
    parser.add_argument('--send-emails', action='store_true', help="Send generated warning emails.")
    parser.add_argument('--send-admin-warnings', action='store_true', help="Send admin warnings via email.")
    parser.add_argument('--no-web', action='store_true', help="Prevent opening the web interface.")
    parser.add_argument('--skip-admin-warnings', action='store_true', help="Skip the generation of admin warnings.")
    parser.add_argument('--no-log', action='store_true', help="Prevent the creation of the log file.")
    parser.add_argument('--no-xlsx', action='store_true', help="Prevent the creation of the Excel file.")
    parser.add_argument('--send-log-email', action='store_true', help="Send the log and Excel comparison via email.")
    args = parser.parse_args()

    # Speichern der CLI-Argumente in der globalen Variable
    cli_args = {
        "process": args.process,
        "generate_emails": args.generate_emails,
        "send_emails": args.send_emails,
        "send_admin_warnings": args.send_admin_warnings,
        "no_web": args.no_web,
        "skip_admin_warnings": args.skip_admin_warnings,
        "no_log": args.no_log,
        "no_xlsx": args.no_xlsx,
        "send_log_email": args.send_log_email,
    }


    # Initialisiere globale Caches
    warnings_cache = []
    generated_emails_cache = []

    # Admin-Warnungen erstellen, falls nicht übersprungen
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':  # Verhindert doppelte Ausführung im Debug-Modus
        if not args.skip_admin_warnings:
            admin_warnings()

    # Senden von Admin-Warnugen
    if args.send_admin_warnings:
        admin_warnings(send_email_flag=True)

    # Verarbeitung starten
    if args.process:
        print("Starte Datenverarbeitung...")
        # Übergabe der Argumente no_log und no_xlsx an process_data
        warnings_cache = process_data(
            no_log=args.no_log,
            no_xlsx=args.no_xlsx
        )
        print("Datenverarbeitung erfolgreich abgeschlossen.")

    # Timeframe-Import vergleichen und ggf. E-Mail versenden
    if args.send_log_email:
        print("Vergleiche Import-Dateien basierend auf dem definierten Zeitrahmen...")
        compare_timeframe_imports(
            no_log=args.no_log,
            no_xlsx=args.no_xlsx
        )
        print("Vergleich abgeschlossen.")

    # E-Mails generieren
    if args.generate_emails:
        if not warnings_cache:
            print("Es sind zum Generieren von E-Mails keine Warnungen im Cache vorhanden.")
        else:
            print("Generiere E-Mails...")
            from flask import current_app
            with app.app_context():
                generate_emails()
            print("E-Mails erfolgreich generiert.")

    # E-Mails senden
    if args.send_emails:
        if not generated_emails_cache:
            print("Es sind keine generierten E-Mails zum Senden im Cache vorhanden.")
        else:
            print("Sende E-Mails...")
            for email in generated_emails_cache:
                send_email(email['subject'], email['body'], email['to'])
            print("E-Mails erfolgreich gesendet.")


    # Starten des WSGI-Servers mit Waitress
    if not args.no_web:
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.start()
    try:
        serve(app, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"Fehler beim Starten des WSGI-Servers: {e}")








