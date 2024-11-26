﻿import os
import sys

# Basisverzeichnis explizit zum Suchpfad hinzufügen, um relative Importe zu ermöglichen
base_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(base_dir)

import csv
import configparser
import webbrowser
import threading
import argparse
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from main import run, read_students, read_classes
from smtp import send_email
from compare import compare_student_changes

global warnings_cache, generated_emails_cache

app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))
warnings_cache = []  # Globaler Cache für die Zwischenspeicherung von Warnungen
generated_emails_cache = []  # Globaler Cache für generierte E-Mails

# Prüfen, ob die Konfigurationsdateien existieren, und sie bei Bedarf mit Standardwerten erstellen
def process_data():
    # Konfigurationsdatei einlesen
    config = configparser.ConfigParser()
    config.read('settings.ini')

    # Werte aus der Konfigurationsdatei laden
    use_abschlussdatum = config.getboolean('ProcessingOptions', 'use_abschlussdatum', fallback=False)
    create_second_file = config.getboolean('ProcessingOptions', 'create_second_file', fallback=False)
    warn_entlassdatum = config.getboolean('ProcessingOptions', 'warn_entlassdatum', fallback=True)
    warn_aufnahmedatum = config.getboolean('ProcessingOptions', 'warn_aufnahmedatum', fallback=True)
    warn_klassenwechsel = config.getboolean('ProcessingOptions', 'warn_klassenwechsel', fallback=True)

    print("Starting processing with the following options:")
    print(f"use_abschlussdatum: {use_abschlussdatum}")
    print(f"create_second_file: {create_second_file}")
    print(f"warn_entlassdatum: {warn_entlassdatum}")
    print(f"warn_aufnahmedatum: {warn_aufnahmedatum}")
    print(f"warn_klassenwechsel: {warn_klassenwechsel}")

    # Verarbeite die Daten
    all_warnings = run(
        use_abschlussdatum=use_abschlussdatum,
        create_second_file=create_second_file,
        warn_entlassdatum=warn_entlassdatum,
        warn_aufnahmedatum=warn_aufnahmedatum,
        warn_klassenwechsel=warn_klassenwechsel
    )
    print("Processing completed.")
    return all_warnings


def ensure_ini_files_exist():
    # Standard-Inhalt für die settings.ini zur Definition der Ordnerpfade
    default_classes_dir = "Klassendaten"
    default_teachers_dir = "Lehrerdaten"
    settings_ini_content = f"""# Einstellungen für Verzeichnisse
# Geben Sie die Pfade zu den benötigten Verzeichnissen an.
# Beispiele:
# classes_directory = ./Klassendaten
# teachers_directory = ./Lehrerdaten

[Directories]
classes_directory = ./{default_classes_dir}
teachers_directory = ./{default_teachers_dir}

[ProcessingOptions]
use_abschlussdatum = False
create_second_file = False
warn_entlassdatum = True
warn_aufnahmedatum = True
warn_klassenwechsel = True
"""
    # Standard-Inhalt für die email_settings.ini zur SMTP-Konfiguration
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

    # Prüfen, ob settings.ini existiert
    settings_ini_exists = os.path.exists("settings.ini")
    if not settings_ini_exists:
        with open("settings.ini", "w") as file:
            file.write(settings_ini_content)
        print("settings.ini wurde erstellt.")

    # Prüfen, ob email_settings.ini existiert
    if not os.path.exists("email_settings.ini"):
        with open("email_settings.ini", "w") as file:
            file.write(email_settings_ini_content)
        print("email_settings.ini wurde erstellt.")

    # Ordner für Klassendaten und Lehrerdaten nur erstellen, falls sie in settings.ini fehlen
    config = configparser.ConfigParser()
    if settings_ini_exists:
        config.read("settings.ini")

    classes_dir = config.get("Directories", "classes_directory", fallback=f"./{default_classes_dir}")
    teachers_dir = config.get("Directories", "teachers_directory", fallback=f"./{default_teachers_dir}")

    if classes_dir == f"./{default_classes_dir}" and not os.path.exists(default_classes_dir):
        os.makedirs(default_classes_dir)
        print(f"Ordner '{default_classes_dir}' wurde erstellt.")

    if teachers_dir == f"./{default_teachers_dir}" and not os.path.exists(default_teachers_dir):
        os.makedirs(default_teachers_dir)
        print(f"Ordner '{default_teachers_dir}' wurde erstellt.")

    # Sicherstellen, dass der Ordner für Importe existiert
    import_dir = "WebUntis Importe"
    if not os.path.exists(import_dir):
        os.makedirs(import_dir)
        print(f"Ordner '{import_dir}' wurde erstellt.")

def admin_warnings(send_email_flag=False):
    global admin_warnings_cache
    admin_warnings_cache = []

    # Haupt-Import-Datei einlesen
    students_output, students_by_id = read_students(use_abschlussdatum=False)

    # Klassen- und Lehrkräfte-Daten einlesen
    config = configparser.ConfigParser()
    config.read('settings.ini')
    classes_dir = config.get('Directories', 'classes_directory')
    teachers_dir = config.get('Directories', 'teachers_directory')

    # Klassen- und Lehrkräfte-Daten einlesen
    classes_by_name, teachers = read_classes(classes_dir, teachers_dir, return_teachers=True)

    # Lehrer-Daten aus der Lehrerdatei extrahieren (Spalte "name")
    teacher_names = set(teachers.keys())

    # Warnungen für fehlende Klassen in der Klassen-Datei
    for student in students_by_id.values():
        klasse = student.get('Klasse', '').strip().lower()
        if klasse not in classes_by_name:
            admin_warnings_cache.append({
                'Typ': 'Fehlende Klasse in der Klassen-Datei',
                'Details': f"Die Klasse '{klasse}' aus der Haupt-Import-Datei existiert nicht in der Klassen-Datei.",
                'Schüler': f"{student.get('Vorname', '')} {student.get('Nachname', '')}"
            })

    # Warnungen für fehlende Klassenlehrkräfte in der Lehrkräfte-Datei
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
        print(f"Warnung: Keine Klassen-CSV-Dateien im Ordner '{classes_dir}' gefunden. Es werden Dummy-Daten verwendet.")
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

    # Überprüfen, ob die Klassendaten verfügbar sind
    if not os.path.exists(classes_dir) or not any(f.endswith('.csv') for f in os.listdir(classes_dir)):
        warnings_messages.append("Die Klassendaten fehlen oder es sind keine CSV-Dateien im konfigurierten Ordner vorhanden.")

    # Überprüfen, ob die Lehrerdaten verfügbar sind
    if not os.path.exists(teachers_dir) or not any(f.endswith('.csv') for f in os.listdir(teachers_dir)):
        warnings_messages.append("Die Lehrerdaten fehlen oder es sind keine CSV-Dateien im konfigurierten Ordner vorhanden.")

    if request.method == 'POST' and not errors:
        # Aktuelle Werte aus dem Formular lesen und die Auswahl des Benutzers speichern
        use_abschlussdatum = request.form.get('use_abschlussdatum') == 'on'
        create_second_file = request.form.get('create_second_file') == 'on'
        warn_entlassdatum = request.form.get('warn_entlassdatum') == 'on'
        warn_aufnahmedatum = request.form.get('warn_aufnahmedatum') == 'on'
        warn_klassenwechsel = request.form.get('warn_klassenwechsel') == 'on'

        # Übergebe die Auswahl an die Run-Funktion
        try:
            warnings = run(
                use_abschlussdatum=use_abschlussdatum,
                create_second_file=create_second_file,
                warn_entlassdatum=warn_entlassdatum,
                warn_aufnahmedatum=warn_aufnahmedatum,
                warn_klassenwechsel=warn_klassenwechsel
            )
            warnings_cache = warnings  # Speichert Warnungen zur späteren Nutzung

            # Setzt eine Bestätigungsnachricht nach erfolgreicher Ausführung
            confirmation = "Erledigt!"
        except Exception as e:
            errors.append(f"Fehler während der Verarbeitung: {str(e)}")

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
                return jsonify({"message": f"Vorlage für {warning_type} fehlt in der Konfigurationsdatei."}), 400

            # Verwende Template-System zur Verarbeitung der Vorlagen
            try:
                subject = Template(subject_template).substitute(**warning)
                body = Template(body_template).substitute(
                    **warning,
                    zeitraum_text=zeitraum_text  # Zusatzwert für Zeitraum
                )
            except KeyError as e:
                return jsonify({"message": f"Fehlender Platzhalter: {e} in der Vorlage für {warning_type}"}), 400

            # E-Mail zur Liste hinzufügen
            generated_emails_cache.append({
                'subject': subject,
                'body': body,
                'to': [warning.get('Klassenlehrkraft_1_Email', 'N/A'), warning.get('Klassenlehrkraft_2_Email', 'N/A')]
            })
        return jsonify({"message": "Die E-Mails wurden erfolgreich generiert.", "emails": generated_emails_cache})
    else:
        return jsonify({"message": "Keine Warnungen verfügbar, um E-Mails zu generieren."})


@app.route('/get_templates', methods=['GET'])
def get_templates():
    config = configparser.ConfigParser()
    config.read('email_settings.ini')
    return jsonify({
        "subject_entlassdatum": config.get("Templates", "subject_entlassdatum"),
        "body_entlassdatum": config.get("Templates", "body_entlassdatum"),
        "subject_aufnahmedatum": config.get("Templates", "subject_aufnahmedatum"),
        "body_aufnahmedatum": config.get("Templates", "body_aufnahmedatum"),
        "subject_klassenwechsel": config.get("Templates", "subject_klassenwechsel"),
        "body_klassenwechsel": config.get("Templates", "body_klassenwechsel")
    })

@app.route('/update_templates', methods=['POST'])
def update_templates():
    save_to_ini = request.form.get('saveToIni') == 'on'

    templates = {
        "subject_entlassdatum": request.form.get("subject_entlassdatum", ""),
        "body_entlassdatum": request.form.get("body_entlassdatum", ""),
        "subject_aufnahmedatum": request.form.get("subject_aufnahmedatum", ""),
        "body_aufnahmedatum": request.form.get("body_aufnahmedatum", ""),
        "subject_klassenwechsel": request.form.get("subject_klassenwechsel", ""),
        "body_klassenwechsel": request.form.get("body_klassenwechsel", "")
    }

    if save_to_ini:
        # Aktualisiere die .ini-Datei
        config = configparser.ConfigParser()
        config.read('email_settings.ini')

        if not config.has_section("Templates"):
            config.add_section("Templates")

        for key, value in templates.items():
            config.set("Templates", key, str(value))  # Konvertiere alle Werte in Strings

        with open('email_settings.ini', 'w') as configfile:
            config.write(configfile)
        return jsonify({"message": "Vorlagen dauerhaft gespeichert."})
    else:
        # Speichere Vorlagen temporär in der Session
        for key, value in templates.items():
            session[key] = str(value)  # Speichere alle Werte als Strings in der Session

        return jsonify({"message": "Vorlagen temporär gespeichert."})


@app.route('/send_emails', methods=['POST'])
def send_emails():
    global generated_emails_cache
    if generated_emails_cache:
        # Verwende den Cache zum Senden der E-Mails und überprüfe, ob welche vorhanden sind
        for email in generated_emails_cache:
            send_email(
                subject=email['subject'],
                body=email['body'],
                to_addresses=email['to']
            )
        return jsonify({"message": "Die E-Mails wurden erfolgreich versendet."})
    else:
        return jsonify({"message": "Keine generierten E-Mails verfügbar, um sie zu versenden."})


@app.route('/view_generated_emails', methods=['GET'])
def view_generated_emails():
    global generated_emails_cache
    return render_template('view_emails.html', emails=generated_emails_cache)

# Öffnet den Standardbrowser automatisch auf die lokale URL
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    ensure_ini_files_exist()
    # Parser für CLI-Argumente
    parser = argparse.ArgumentParser(description="Command-line interface for processing data.")
    parser.add_argument('--process', action='store_true', help="Run the main processing task.")
    parser.add_argument('--generate-emails', action='store_true', help="Generate warning emails.")
    parser.add_argument('--send-emails', action='store_true', help="Send generated warning emails.")
    parser.add_argument('--send-admin-warnings', action='store_true', help="Send admin warnings via email.")
    parser.add_argument('--no-web', action='store_true', help="Prevent opening the web interface.")
    parser.add_argument('--skip-admin-warnings', action='store_true', help="Skip the generation of admin warnings.")
    args = parser.parse_args()

    # Initialisiere globale Caches
    warnings_cache = []
    generated_emails_cache = []

    # Standardmäßig Admin-Warnungen ausführen, falls nicht übersprungen
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':  # Verhindert doppelte Ausführung im Debug-Modus
        if not args.skip_admin_warnings:
            admin_warnings()

    # Senden von Admin-Warnugen
    if args.send_admin_warnings:
        admin_warnings(send_email_flag=True)

    # Verarbeitung starten
    if args.process:
        print("Processing data...")
        warnings_cache = process_data()  # Ergebnisse des Prozesses speichern
        print("Data processed successfully.")

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

    # Web-App starten, falls keine Optionen gewählt wurden
    if not args.no_web and not any([args.process, args.generate_emails, args.send_emails]):
        ensure_ini_files_exist()  # Sicherstellen, dass .ini-Dateien vorhanden sind

        if os.environ.get('FLASK_SERVER_STARTED') != '1':
            os.environ['FLASK_SERVER_STARTED'] = '1'

            # Browser in einem separaten Thread öffnen
            browser_thread = threading.Timer(1, open_browser)
            browser_thread.start()

        try:
            app.run(debug=True)
        except Exception as e:
            print(f"Fehler: {e}")
        input("Drücke eine Taste, um die Konsole zu schließen...")

    elif args.no_web:
        print("Weboberfläche wurde deaktiviert.")






