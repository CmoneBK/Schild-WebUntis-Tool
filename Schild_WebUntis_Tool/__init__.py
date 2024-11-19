import os
import sys

# Basisverzeichnis explizit zum Suchpfad hinzufügen, um relative Importe zu ermöglichen
base_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(base_dir)

import csv
import configparser
import webbrowser
import threading
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from main import run
from smtp import send_email

app = Flask(__name__,
            template_folder=os.path.join(base_dir, 'templates'),
            static_folder=os.path.join(base_dir, 'static'))
warnings_cache = []  # Globaler Cache für die Zwischenspeicherung von Warnungen
generated_emails_cache = []  # Globaler Cache für generierte E-Mails

# Prüfen, ob die Konfigurationsdateien existieren, und sie bei Bedarf mit Standardwerten erstellen
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
classes_directory = ./{default_classes_dir}  # Pfad zu den Klassendateien
teachers_directory = ./{default_teachers_dir}  # Pfad zu den Lehrerdaten
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

[Email]
smtp_server = smtp.example.com  
smtp_port = 587  
smtp_user = user@example.com  
smtp_password = password  
smtp_encryption = starttls  

# OAuth-Einstellungen (falls verwendet)
[OAuth]
use_oauth = False
credentials_path = ./config/credentials.json

# Vorlagen für generierte E-Mails
# Verwenden Sie Platzhalter wie {Vorname}, {Nachname}, {Klasse}, {neues_entlassdatum}, etc.

[Templates]
subject_entlassdatum = Webuntis-Warnung: Entlassdatum-Problem bei $Vorname $Nachname
body_entlassdatum = <p>Sehr geehrter/Sehr geehrte Herr/Frau $Klassenlehrkraft_1,</p><p>Es gibt ein Problem mit dem Entlassdatum des Schülers/der Schülerin <strong>$Vorname $Nachname</strong> aus der Klasse <strong>$Klasse</strong>.</p><p><strong>Neues Entlassdatum:</strong> $neues_entlassdatum<br><strong>Altes Entlassdatum:</strong> $altes_entlassdatum</p><p>$zeitraum_text</p><p><strong>Klassenlehrkraft 1:</strong> $Klassenlehrkraft_1, E-Mail: $Klassenlehrkraft_1_Email<br><strong>Klassenlehrkraft 2:</strong> $Klassenlehrkraft_2, E-Mail: $Klassenlehrkraft_2_Email</p><p>Mit freundlichen Grüßen,<br>Das WebUntis Team</p>

subject_aufnahmedatum = Webuntis-Warnung: Aufnahmedatum-Problem bei $Vorname $Nachname
body_aufnahmedatum = <p>Sehr geehrter/Sehr geehrte Herr/Frau $Klassenlehrkraft_1,</p><p>Das Aufnahmedatum des Schülers/der Schülerin <strong>$Vorname $Nachname</strong> aus der Klasse <strong>$Klasse</strong> hat sich geändert.</p><p><strong>Neues Aufnahmedatum:</strong> $neues_aufnahmedatum<br><strong>Altes Aufnahmedatum:</strong> $altes_aufnahmedatum</p><p>$zeitraum_text</p><p><strong>Klassenlehrkraft 1:</strong> $Klassenlehrkraft_1, E-Mail: $Klassenlehrkraft_1_Email<br><strong>Klassenlehrkraft 2:</strong> $Klassenlehrkraft_2, E-Mail: $Klassenlehrkraft_2_Email</p><p>Mit freundlichen Grüßen,<br>Das WebUntis Team</p>

subject_klassenwechsel = Webuntis-Warnung: Klassenwechsel bei $Vorname $Nachname
body_klassenwechsel = <p>Sehr geehrter/Sehr geehrte Herr/Frau $Klassenlehrkraft_1,</p><p>Es gab einen Klassenwechsel des Schülers/der Schülerin <strong>$Vorname $Nachname</strong>.</p><p><strong>Alte Klasse:</strong> $alte_klasse<br><strong>Neue Klasse:</strong> $neue_klasse</p><p><strong>Klassenlehrkraft 1:</strong> $Klassenlehrkraft_1, E-Mail: $Klassenlehrkraft_1_Email<br><strong>Klassenlehrkraft 2:</strong> $Klassenlehrkraft_2, E-Mail: $Klassenlehrkraft_2_Email</p><p>Mit freundlichen Grüßen,<br>Das WebUntis Team</p>
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



@app.route('/', methods=['GET', 'POST'])
def index():
    global warnings_cache  # Globaler Cache für die Zwischenspeicherung von Warnungen
    warnings = []
    confirmation = None  # Variable für Bestätigungsnachricht
    errors = []  # Liste für Fehlermeldungen
    warnings_messages = []  # Liste für nicht-blockierende Warnungen

    # Standardwerte für die Checkboxen definieren
    use_abschlussdatum = False
    create_second_file = False
    warn_entlassdatum = True
    warn_aufnahmedatum = True
    warn_klassenwechsel = True

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
        warn_klassenwechsel=warn_klassenwechsel
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

            # Lade Vorlagen aus der .ini-Datei
            subject_template = config.get("Templates", f"subject_{warning_type}", fallback="")
            body_template = config.get("Templates", f"body_{warning_type}", fallback="")

            # Verwende Template-System zur Verarbeitung der Vorlagen
            subject = Template(subject_template).substitute(warning)
            body = Template(body_template).substitute(
                warning,
                zeitraum_text=zeitraum_text  # Zusatzwert für Zeitraum
            )

            # E-Mail zur Liste hinzufügen
            generated_emails_cache.append({
                'subject': subject,
                'body': body,
                'to': [warning.get('Klassenlehrkraft_1_Email', 'N/A'), warning.get('Klassenlehrkraft_2_Email', 'N/A')]
            })

        return jsonify({"message": "Die E-Mails wurden erfolgreich generiert.", "emails": generated_emails_cache})
    else:
        return jsonify({"message": "Keine Warnungen verfügbar, um E-Mails zu generieren."})




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
    ensure_ini_files_exist()  # Prüfe und erstelle .ini-Dateien bei Bedarf

    if os.environ.get('FLASK_SERVER_STARTED') != '1':
        os.environ['FLASK_SERVER_STARTED'] = '1'
        browser_thread = threading.Timer(1, open_browser)
        browser_thread.start()

    app.run(debug=True)
    try:
        app.run(debug=True)
    except Exception as e:
        print(f"Fehler: {e}")
    input("Drücke eine Taste, um die Konsole zu schließen...")