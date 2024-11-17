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
    # Standardpfade relativ zum Verzeichnis der .exe festlegen
    default_classes_dir = os.path.join(os.getcwd(), "Klassendaten")
    default_teachers_dir = os.path.join(os.getcwd(), "Lehrerdaten")

    # Standard-Inhalt für die settings.ini zur Definition der Ordnerpfade
    settings_ini_content = f"""# Einstellungen für Verzeichnisse
# Geben Sie die Pfade zu den benötigten Verzeichnissen an.
# Beispiele:
# classes_directory = {default_classes_dir} # Pfad zu den Klassendateien
# teachers_directory = {default_teachers_dir} # Pfad zu den Lehrerdaten

[Directories]
classes_directory = {default_classes_dir}  
teachers_directory = {default_teachers_dir}  
"""
    # Standard-Inhalt für die email_settings.ini zur SMTP-Konfiguration
    email_settings_ini_content = """# Einstellungen für den E-Mail-Versand
# Passen Sie diese Einstellungen an Ihren SMTP-Server an.
# Beispiele:
# smtp_server = smtp.gmail.com
# smtp_port = 587
# smtp_user = ihrbenutzer@gmail.com
# smtp_password = ihrpasswort
# smtp_encryption = starttls

[Email]
smtp_server = smtp.example.com  # SMTP-Server-Adresse
smtp_port = 587  # SMTP-Port (z. B. 587 für STARTTLS)
smtp_user = user@example.com  # Benutzername für SMTP
smtp_password = password  # Passwort für SMTP
smtp_encryption = starttls  # Verschlüsselungsmethode (starttls oder ssl)

# OAuth-Einstellungen (falls verwendet)
[OAuth]
use_oauth = False
credentials_path = ./config/credentials.json
"""

    # Prüfen, ob settings.ini existiert
    settings_ini_exists = os.path.exists("settings.ini")
    if not settings_ini_exists:
        # settings.ini erstellen
        with open("settings.ini", "w") as file:
            file.write(settings_ini_content)
        print("settings.ini wurde erstellt.")

    # Prüfen, ob email_settings.ini existiert
    if not os.path.exists("email_settings.ini"):
        with open("email_settings.ini", "w") as file:
            file.write(email_settings_ini_content)
        print("email_settings.ini wurde erstellt.")

    # Falls settings.ini existiert, lese die Konfiguration
    config = configparser.ConfigParser()
    if settings_ini_exists:
        config.read("settings.ini")

    # Ordner für Klassendaten und Lehrerdaten nur erstellen, falls sie in settings.ini fehlen
    classes_dir = config.get("Directories", "classes_directory", fallback=default_classes_dir)
    teachers_dir = config.get("Directories", "teachers_directory", fallback=default_teachers_dir)

    # Erstelle Standardordner für Klassendaten und Lehrerdaten, falls sie nicht existieren
    if classes_dir == default_classes_dir and not os.path.exists(default_classes_dir):
        os.makedirs(default_classes_dir)
        print(f"Ordner '{default_classes_dir}' wurde erstellt.")

    if teachers_dir == default_teachers_dir and not os.path.exists(default_teachers_dir):
        os.makedirs(default_teachers_dir)
        print(f"Ordner '{default_teachers_dir}' wurde erstellt.")

    # Sicherstellen, dass der Ordner für Importe existiert
    import_dir = "WebUntis Importe"
    if not os.path.exists(import_dir):
        os.makedirs(import_dir)
        print(f"Ordner '{import_dir}' wurde erstellt.")


@app.route('/', methods=['GET', 'POST'])
def index():
    global warnings_cache # Globaler Cache für die Zwischenspeicherung von Warnungen
    warnings = [] 
    confirmation = None  # Variable für Bestätigungsnachricht

    # Standardwerte für die Checkboxen definieren
    use_abschlussdatum = False
    create_second_file = False
    warn_entlassdatum = True
    warn_aufnahmedatum = True
    warn_klassenwechsel = True

    if request.method == 'POST':
        # Aktuelle Werte aus dem Formular lesen und die Auswahl des Benutzers speichern
        use_abschlussdatum = request.form.get('use_abschlussdatum') == 'on'
        create_second_file = request.form.get('create_second_file') == 'on'
        warn_entlassdatum = request.form.get('warn_entlassdatum') == 'on'
        warn_aufnahmedatum = request.form.get('warn_aufnahmedatum') == 'on'
        warn_klassenwechsel = request.form.get('warn_klassenwechsel') == 'on'

        # Übergebe die Auswahl an die Run-Funktion
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

    # Seite mit aktuellen Checkbox-Zuständen und Warnungen rendern
    return render_template(
        'index.html',
        warnings=warnings,
        confirmation=confirmation,
        use_abschlussdatum=use_abschlussdatum,
        create_second_file=create_second_file,
        warn_entlassdatum=warn_entlassdatum,
        warn_aufnahmedatum=warn_aufnahmedatum,
        warn_klassenwechsel=warn_klassenwechsel
    )

@app.route('/generate_emails', methods=['POST'])
def generate_emails():
    global warnings_cache, generated_emails_cache
    generated_emails_cache = []  # Globaler Cache für generierte E-Mails
    if warnings_cache:
        # Generiere E-Mails basierend auf den vorhandenen Warnungen und speichere sie im Cache
        for warning in warnings_cache:
            # Dynamische Einbindung des Zeitraums (falls vorhanden)
            zeitraum_text = (
                f"<p><strong>Zeitraum nicht dokumentiert:</strong> {warning.get('Zeitraum_nicht_dokumentiert', 'N/A')}</p>"
                if 'Zeitraum_nicht_dokumentiert' in warning
                else ""
            )
            
            if 'neues_entlassdatum' in warning:
                subject = f"Webuntis-Warnung: Entlassdatum-Problem bei {warning.get('Vorname', 'N/A')} {warning.get('Nachname', 'N/A')}"
                body = (
                    f"<p>Sehr geehrter/Sehr geehrte Herr/Frau {warning.get('Klassenlehrkraft_1', '').split()[-1]},</p>"
                    f"<p>Es gibt ein Problem mit dem Entlassdatum des Schülers/der Schülerin <strong>{warning.get('Vorname', 'N/A')} {warning.get('Nachname', 'N/A')}</strong> "
                    f"aus der Klasse <strong>{warning.get('Klasse', 'N/A')}</strong>.</p>"
                    f"<p><strong>Neues Entlassdatum:</strong> {warning.get('neues_entlassdatum', 'N/A')}<br>"
                    f"<strong>Altes Entlassdatum:</strong> {warning.get('altes_entlassdatum', 'N/A')}</p>"
                    f"{zeitraum_text}"
                    f"<p>Dies führt nun dazu, dass der Zeitraum dazwischen nachdokumentiert werden muss. Bitte nehmen Sie in WebUntis die entsprechenden Eintragungen vor.</p>"
                    f"<p><strong>Klassenlehrkraft 1:</strong> {warning.get('Klassenlehrkraft_1', 'N/A')}, E-Mail: {warning.get('Klassenlehrkraft_1_Email', 'N/A')}<br>"
                    f"<strong>Klassenlehrkraft 2:</strong> {warning.get('Klassenlehrkraft_2', 'N/A')}, E-Mail: {warning.get('Klassenlehrkraft_2_Email', 'N/A')}</p>"
                    f"<p>Mit freundlichen Grüßen,<br>Das WebUntis Team</p>"
                )
            elif 'neues_aufnahmedatum' in warning:
                subject = f"Webuntis-Warnung: Aufnahmedatum-Problem bei {warning.get('Vorname', 'N/A')} {warning.get('Nachname', 'N/A')}"
                body = (
                    f"<p>Sehr geehrter/Sehr geehrte Herr/Frau {warning.get('Klassenlehrkraft_1', '').split()[-1]},</p>"
                    f"<p>Das Aufnahmedatum des Schülers/der Schülerin <strong>{warning.get('Vorname', 'N/A')} {warning.get('Nachname', 'N/A')}</strong> "
                    f"aus der Klasse <strong>{warning.get('Klasse', 'N/A')}</strong> hat sich geändert.</p>"
                    f"<p><strong>Neues Aufnahmedatum:</strong> {warning['neues_aufnahmedatum']}<br>"
                    f"<strong>Altes Aufnahmedatum:</strong> {warning['altes_aufnahmedatum']}</p>"
                    f"{zeitraum_text}"
                    f"<p>Dies führt nun dazu, dass der Zeitraum dazwischen nachdokumentiert werden muss. Bitte nehmen Sie in WebUntis die entsprechenden Eintragungen vor.</p>"
                    f"<p><strong>Klassenlehrkraft 1:</strong> {warning.get('Klassenlehrkraft_1', 'N/A')}, E-Mail: {warning.get('Klassenlehrkraft_1_Email', 'N/A')}<br>"
                    f"<strong>Klassenlehrkraft 2:</strong> {warning.get('Klassenlehrkraft_2', 'N/A')}, E-Mail: {warning.get('Klassenlehrkraft_2_Email', 'N/A')}</p>"
                    f"<p>Mit freundlichen Grüßen,<br>Das WebUntis Team</p>"
                )
            elif 'neue_klasse' in warning:
                subject = f"Webuntis-Warnung: Klassenwechsel bei {warning.get('Vorname', 'N/A')} {warning.get('Nachname', 'N/A')}"
                body = (
                    f"<p>Sehr geehrter/Sehr geehrte Herr/Frau {warning.get('Klassenlehrkraft_1', '').split()[-1]},</p>"
                    f"<p>Es gab einen Klassenwechsel des Schülers/der Schülerin <strong>{warning.get('Vorname', 'N/A')} {warning.get('Nachname', 'N/A')}</strong>.</p>"
                    f"<p><strong>Alte Klasse:</strong> {warning.get('alte_klasse', 'N/A')}<br>"
                    f"<strong>Neue Klasse:</strong> {warning.get('neue_klasse', 'N/A')}</p>"
                    f"<p>Sofern das heutige Datum nicht das Datum ist, an dem die Klasse gewechselt wurde, muss dies manuell im Digitalen Klassenbuch korrigiert werden, da die Änderung ab dem aktuellen Tag gilt.<br>Bitte informieren Sie in diesem Fall Ihre Abteilungsleitung, damit diese die Änderung in den Schülerstammdaten in WebUntis vornehmen kann.</p>"
                    f"<p><strong>Klassenlehrkraft 1:</strong> {warning.get('Klassenlehrkraft_1', 'N/A')}, E-Mail: {warning.get('Klassenlehrkraft_1_Email', 'N/A')}<br>"
                    f"<strong>Klassenlehrkraft 2:</strong> {warning.get('Klassenlehrkraft_2', 'N/A')}, E-Mail: {warning.get('Klassenlehrkraft_2_Email', 'N/A')}</p>"
                    f"<p>Mit freundlichen Grüßen,<br>Das WebUntis Team</p>"
                )
            else:
                continue  # Überspringt, wenn der Warnungstyp nicht erkannt wird

            # Fügt die generierte E-Mail dem Cache hinzu
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