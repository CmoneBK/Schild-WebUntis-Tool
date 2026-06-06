import os  # Betriebssystemfunktionen wie Pfadoperationen
import sys  # Systemfunktionen und -parameter

# Basisverzeichnis explizit zum Suchpfad hinzufügen, um relative Importe zu ermöglichen
base_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(base_dir)

# Zwingend UTF-8 für die Standardausgabe konfigurieren, um Abstürze durch Emojis (wie ❌, ✅, ℹ️) auf veralteten Windows Konsolen in der .exe zu verhindern.
try:
    if sys.stdout and hasattr(sys.stdout, 'encoding') and sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

import csv  # Lesen und Schreiben von CSV-Dateien
import configparser  # Verarbeiten von Konfigurationsdateien im INI-Format
import webbrowser  # Öffnen von Webbrowsern
import threading  # Multithreading-Funktionen
import argparse  # Parsen von Kommandozeilenargumenten
import secrets
import traceback
import logging

# Logger konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import history_manager

from utils import safe_read_config

import winshell  # Interaktion mit der Windows-Shell (z.B. Erstellen von Verknüpfungen)
import pythoncom  # Python COM-Schnittstelle für Windows
import threading  # Multithreading-Funktionen
import werkzeug  # Werkzeug-Bibliothek für WSGI-Anwendungen (von Flask verwendet)
import tkinter as tk  # GUI-Toolkit für die Dateiauswahl-Dialoge
import colorama  # Ausgabe von farbigem Text in der Konsole
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.table import Table

_console = Console(highlight=False, legacy_windows=False)
from datetime import datetime  # Arbeiten mit Datum und Uhrzeit
from flask import Flask, render_template, request, jsonify, session, send_from_directory  # Flask-Webframework
from main import run, read_students, read_classes, compare_timeframe_imports, validate_imports, create_info_notifications, INFO_MAIL_AVAILABLE_FIELDS  # Funktionen aus eigenen Modulen importieren
from smtp import send_email  # Funktion zum Versenden von E-Mails aus eigenem Modul
from waitress import serve  # WSGI-Server zum Bereitstellen der Flask-Anwendung
from tkinter import filedialog  # Datei- und Verzeichnisauswahl-Dialoge
from werkzeug.utils import secure_filename  # Sichere Dateinamen-Verarbeitung
from colorama import Fore, Back, Style, init  # Farb- und Stildefinitionen für die Konsolenausgabe

# Colorama initialisieren
init(autoreset=True)

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

def print_section(title):
    """Gibt eine Abschnittsüberschrift aus – strukturelle Trennung, kein Emoji."""
    _console.rule(title, style="cyan")

def print_banner():
    import_dir  = get_directory('import_directory', './WebUntis Importe')
    log_dir     = get_directory('log_directory', './Logs')
    xlsx_dir    = get_directory('xlsx_directory', './ExcelLogs')

    content = Text()
    content.append("📂 Ausgabeverzeichnisse\n", style="bold cyan")
    content.append(f"   WebUntis-Import: {import_dir}\n", style="white")
    content.append(f"   Text-Logs:       {log_dir}\n", style="white")
    content.append(f"   Excel-Logs:      {xlsx_dir}", style="white")

    _console.print(Panel(
        content,
        title="[bold cyan]🚀 Schild-WebUntis-Tool v3.0[/]",
        border_style="cyan",
        padding=(0, 1),
    ))
    _console.print("")

def get_directory(key, default=None):
    # Hilfsfunktion zum Abrufen von Verzeichnispfaden aus der Konfigurationsdatei
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', key, fallback=default)



def resource_path(relative_path):
    # Gibt den Pfad zu einer Ressource zurück, funktioniert für dev und bei PyInstaller
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

# Globale Variablen für Warnungen und generierte E-Mails
global warnings_cache, generated_emails_cache, admin_warnings_cache

# Globale Caches für Warnungen und generierte E-Mails
warnings_cache = []             # Cache für Warn-E-Mails
generated_emails_cache = []     # Cache für generierte Warn-E-Mails
admin_warnings_cache = []
info_changes_cache = []         # Rohe Feldänderungen aus dem letzten Lauf (für Info-Mails)
generated_info_mails_cache = [] # Cache für generierte Info-Mails
last_foto_zip = None            # {'path': ..., 'name': ..., 'included': ..., 'missing': ...} — zuletzt erstelltes Foto-ZIP

# Start der Datenverarbeitung über das Kommandozeilen-Argument --process (nicht WebEnd-Button) heraus.
def process_data(no_log=False, no_xlsx=False):
    # Konfigurationsdatei einlesen
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    
    # Werte aus der Konfigurationsdatei laden, da in diesem Fall das WebEnd nicht immer geöffnet ist.
    use_abschlussdatum = config.getboolean('ProcessingOptions', 'use_abschlussdatum', fallback=False)
    create_second_file = config.getboolean('ProcessingOptions', 'create_second_file', fallback=False)
    create_class_size_file = config.getboolean('ProcessingOptions', 'create_class_size_file', fallback=True)
    enable_attestpflicht_column = config.getboolean('ProcessingOptions', 'enable_attestpflicht_column', fallback=False)
    enable_nachteilsausgleich_column = config.getboolean('ProcessingOptions', 'enable_nachteilsausgleich_column', fallback=False)
    disable_import_file_creation= config.getboolean('ProcessingOptions', 'disable_import_file_creation', fallback=False)
    disable_import_file_if_admin_warning= config.getboolean('ProcessingOptions', 'disable_import_file_if_admin_warning', fallback=False)
    warn_entlassdatum = config.getboolean('ProcessingOptions', 'warn_entlassdatum', fallback=True)
    warn_aufnahmedatum = config.getboolean('ProcessingOptions', 'warn_aufnahmedatum', fallback=True)
    warn_klassenwechsel = config.getboolean('ProcessingOptions', 'warn_klassenwechsel', fallback=True)
    warn_new_students = config.getboolean('ProcessingOptions', 'warn_new_students', fallback=True)
    warn_karteileichen = config.getboolean('ProcessingOptions', 'warn_karteileichen', fallback=False)
    
    # CLI Parameter für class_change_recipients hat Vorrang vor settings.ini, falls gesetzt
    global cli_args
    if cli_args and cli_args.get("class_change_recipients"):
        class_change_recipients = cli_args.get("class_change_recipients")
    else:
        class_change_recipients = config.get('ProcessingOptions', 'class_change_recipients', fallback='old')
    
    # Datenverarbeitung starten
    all_warnings, _ = run(                      #Hier wird die def_run aus der main.py mit den erfassten Einstellungen abgerufen und ausgeführt.
        use_abschlussdatum=use_abschlussdatum,
        create_second_file=create_second_file,
        enable_attestpflicht_column=enable_attestpflicht_column,
        create_class_size_file= create_class_size_file,
        disable_import_file_creation=disable_import_file_creation,
        disable_import_file_if_admin_warning=disable_import_file_if_admin_warning,
        warn_entlassdatum=warn_entlassdatum,
        warn_aufnahmedatum=warn_aufnahmedatum,
        warn_klassenwechsel=warn_klassenwechsel,
        warn_new_students=warn_new_students,
        warn_karteileichen=warn_karteileichen,
        class_change_recipients=class_change_recipients,
        no_log=no_log,
        no_xlsx=no_xlsx,
        admin_warnings_cache=admin_warnings_cache
    )
    print_success("Verarbeitung über die Konsole abgeschlossen.")
    return all_warnings

# Standard-Vorlagen für E-Mails
DEFAULT_TEMPLATES = {
    "entlassdatum": {
        "subject": "Webuntis-Hinweis: Entlassdatum-Problem bei $Vorname $Nachname",
        "body": "<p>Sehr geehrter/Sehr geehrte Herr/Frau $Klassenlehrkraft_1,</p><p>Es gibt ein Problem mit dem Entlassdatum des Schülers/der Schülerin <strong>$Vorname $Nachname</strong> aus der Klasse <strong>$Klasse</strong>.</p><p></p><p><strong>Neues Entlassdatum:</strong> $neues_entlassdatum</p><p><strong>Altes Entlassdatum:</strong> $altes_entlassdatum</p><p></p><p>$zeitraum_text</p><p></p><p>In dieser Zeit war der Schüler/die Schülerin nun offiziel teil der Klasse, jedoch nicht im digitalen Klassenbuch dokumentierbar. Dies muss nun nachgeholt werden.</p><p></p><p><strong>Klassenlehrkraft 1:</strong> $Klassenlehrkraft_1, E-Mail: $Klassenlehrkraft_1_Email</p><p><strong>Klassenlehrkraft 2:</strong> $Klassenlehrkraft_2, E-Mail: $Klassenlehrkraft_2_Email</p><p></p><p><strong>Hinweis:</strong> Es ist nicht möglich auf diese E-Mail Adresse zu antworten.</p><p></p><p>Mit freundlichen Grüßen,</p><p>Das WebUntis Team</p>"
    },
    "aufnahmedatum": {
        "subject": "Webuntis-Hinweis: Aufnahmedatum-Problem bei $Vorname $Nachname",
        "body": "<p>Sehr geehrter/Sehr geehrte Herr/Frau $Klassenlehrkraft_1,</p><p>Das Aufnahmedatum des Schülers/der Schülerin <strong>$Vorname $Nachname</strong> aus der Klasse <strong>$Klasse</strong> hat sich geändert.</p><p></p><p><strong>Neues Aufnahmedatum:</strong> $neues_aufnahmedatum</p><p><strong>Altes Aufnahmedatum:</strong> $altes_aufnahmedatum</p><p></p><p>$zeitraum_text</p><p></p><p>In dieser Zeit war der Schüler/die Schülerin nun offiziel teil der Klasse, jedoch nicht im digitalen Klassenbuch dokumentierbar. Dies muss nun nachgeholt werden.</p><p></p><p><strong>Klassenlehrkraft 1:</strong> $Klassenlehrkraft_1, E-Mail: $Klassenlehrkraft_1_Email</p><p><strong>Klassenlehrkraft 2:</strong> $Klassenlehrkraft_2, E-Mail: $Klassenlehrkraft_2_Email</p><p></p><p><strong>Hinweis:</strong> Es ist nicht möglich auf diese E-Mail Adresse zu antworten.</p><p></p><p>Mit freundlichen Grüßen,</p><p>Das WebUntis Team</p>"
    },
    "klassenwechsel": {
        "subject": "Webuntis-Hinweis: Klassenwechsel bei $Vorname $Nachname",
        "body": "<p>Sehr geehrte/r $anrede_global,</p><p>Es gab einen Klassenwechsel des Schülers/der Schülerin <strong>$Vorname $Nachname</strong>.</p><p>Sofern dieser Klassenwechsel nicht am heutigen Tag stattfand, informieren Sie bitte das WebUntis-Team über die Notwendigkeit einer Korrektur. </p><p>Liegt der Wechsel in der Vergangenheit müssen anschließend die Tage zwischen heute und diesem Wechsel nachdokumentiert werden.</p><p></p><p>$lehrkraefte_tabelle</p><p></p><p><strong>Hinweis:</strong> Es ist nicht möglich auf diese E-Mail Adresse zu antworten.</p><p></p><p>Mit freundlichen Grüßen,</p><p>Das WebUntis Team</p>"
    },
    "new_student": {
        "subject": "Webuntis-Hinweis: Neuer Schüler $Vorname $Nachname",
        "body": "<p>Sehr geehrte/r $Klassenlehrkraft_1,</p><p>Der Schüler/die Schülerin <strong>$Vorname $Nachname</strong> aus der Klasse <strong>$Klasse</strong> wurde als neu in den importierten Daten erkannt.</p><p>Bitte überprüfen Sie die Daten im digitalen Klassenbuch.</p><p>Mit freundlichen Grüßen,</p><p>Das WebUntis Team</p>"
    },
    "karteileiche": {
        "subject": "Webuntis-Hinweis: Schüler fehlt/gelöscht $Vorname $Nachname",
        "body": "<p>Sehr geehrte/r $Klassenlehrkraft_1,</p><p>Der Schüler/die Schülerin <strong>$Vorname $Nachname</strong> (Klasse <strong>$Klasse</strong>) taucht in den von SchILD importierten Daten (aktives Schuljahr) nicht mehr auf.</p><p>Dies wird dazu führen, dass seine Daten, darunter auch sein Entlassdatum, sein Status (inkl. von Aktiv nach Abschluss/Abgang) nicht mehr aktualisiert werden. Sofern das in Ordnung ist, ist keine weitere Aktion erforderlich. Falls nicht, prüfen Sie bitte den Verbleib des Schülers.</p><p>Mit freundlichen Grüßen,</p><p>Das WebUntis Team</p>"
    },
    "info_notification": {
        "subject": "WebUntis-Änderungsinfo: $Vorname $Nachname ($Klasse)",
        "body": "<p>Sehr geehrte/r $Klassenlehrkraft_1,</p><p>die folgenden Daten von <strong>$Vorname $Nachname</strong> (Klasse: <strong>$Klasse</strong>) wurden in der aktuellen WebUntis-Importdatei aktualisiert und werden mit dem nächsten Import wirksam:</p>$aenderungen_html$nachteilsausgleich_details<p>&nbsp;</p><p><strong>Hinweis:</strong> Es ist nicht möglich, auf diese E-Mail zu antworten.</p><p>Mit freundlichen Grüßen,<br>Das WebUntis Team</p>"
    },
    "ausbilder_kl_uebersicht": {
        # KL-Mail-Versand fuer den Ausbilder-Workflow (3.2): aktuelle Ausbilder-/
        # Betreuer-Daten je Klasse an die Klassenlehrkraft, zur Info + Kontrolle
        # (Korrektur in Schild via Sekretariat). Platzhalter: $Klasse,
        # $Klassenlehrer_Anrede, $Klassenlehrer_Name, $Klassenlehrer_E-Mail,
        # $Stand, $Schueler_Tabelle_HTML, $Schueler_Anzahl. Spiegelt die
        # Defaults aus ausbilder_processor.DEFAULT_KL_MAIL_SUBJECT/BODY.
        "subject": "Ausbilder-/Betreuer-Daten Ihrer Klasse $Klasse — Stand $Stand",
        "body": "<p>Sehr geehrte/r $Klassenlehrer_Anrede $Klassenlehrer_Name,</p><p>anbei die aktuell in Schild hinterlegten Ausbilder-/Betreuer-Daten Ihrer Klasse <strong>$Klasse</strong> (Stand $Stand). Diese werden in WebUntis übernommen, damit die Ausbilder die Fehlstunden ihrer Auszubildenden einsehen können.</p><p><strong>Bitte prüfen</strong> Sie die Daten und veranlassen Sie ggf. eine Korrektur über das Sekretariat in Schild. Eine Excel-Datei mit denselben Daten finden Sie zusätzlich im Anhang (zur Weiterleitung an das Sekretariat oder zur Bearbeitung).</p>$Schueler_Tabelle_HTML<p>Mit freundlichen Grüßen<br>Ihre WebUntis-Pflege</p>"
    },
    "erzieher_kl_uebersicht": {
        # KL-Mail-Versand fuer den Erzieher-Workflow (3.3): aktuelle
        # Erzieher-/Ansprechpartner-ROHDATEN je Klasse an die Klassenlehrkraft.
        # Eigene Platzhalter: $Erzieher_Tabelle_HTML (verschachtelte HTML-
        # Tabelle: Schueler -> mehrere Erzieher + mehrere Telefonnummern).
        # Spiegelt erzieher_processor.DEFAULT_ERZ_KL_MAIL_SUBJECT/BODY.
        "subject": "Erzieher-/Ansprechpartner-Daten Ihrer Klasse $Klasse — Stand $Stand",
        "body": "<p>Sehr geehrte/r $Klassenlehrer_Anrede $Klassenlehrer_Name,</p><p>anbei die aktuell in Schild hinterlegten Erzieher-/Ansprechpartner-Daten Ihrer Klasse <strong>$Klasse</strong> (Stand $Stand) — <em>Rohdaten</em>, also genau so, wie sie aus Schild kommen (ohne Smart-Match, Dummy-Fill o.&nbsp;ä.).</p><p><strong>Bitte prüfen</strong> Sie die Daten auf Vollständigkeit (insbesondere fehlende E-Mail-Adressen / fehlende zweite Elterndatensätze) und veranlassen Sie ggf. eine Korrektur über das Sekretariat in Schild. Eine Excel-Datei mit denselben Daten finden Sie zusätzlich im Anhang (zur Weiterleitung an das Sekretariat oder zur Bearbeitung).</p>$Erzieher_Tabelle_HTML<p>Mit freundlichen Grüßen<br>Ihre WebUntis-Pflege</p>"
    }
}

# Prüfen, ob die Konfigurationsdateien existieren, und sie bei Bedarf mit Standardwerten erstellen. Die Funktion wird unmittlbar bei Start des Servers unter "if __name__ == "__main__":" abgerufen.
def ensure_ini_files_exist():
    # Standardverzeichnisse definieren
    default_classes_dir = "Klassendaten"
    default_teachers_dir = "Lehrerdaten"
    default_log_dir = "Logs"
    default_xlsx_dir = "ExcelLogs"
    default_import_dir = "WebUntis Importe"
    default_schildexport_dir = "."
    default_class_size_dir = "ClassSizes"
    default_attest_file_directory ="AttestpflichtDaten"
    default_nachteilsausgleich_file_directory ="NachteilsausgleichDaten"
    default_nachteilsausgleich_excel_directory ="NachteilsausgleichExcel"
    default_foto_directory ="SchuelerFotos"
    default_foto_zip_directory ="SchuelerFotosZips"
    default_erzieher_export_directory = "ErzieherExport"
    default_ansprechpartner_export_directory = "AnsprechpartnerExport"
    default_erzieher_output_directory = "ErzieherImporte"
    default_ausbilder_input_directory = "AusbilderInput"
    default_ausbilder_output_directory = "AusbilderImportDateien"

    # Standard-Inhalt für settings.ini vorbereiten
    settings_ini_content = f"""[Directories]
classes_directory = {default_classes_dir}
teachers_directory = {default_teachers_dir}
log_directory = {default_log_dir}
xlsx_directory = {default_xlsx_dir}
import_directory = {default_import_dir}
schildexport_directory = {default_schildexport_dir}
class_size_directory = {default_class_size_dir}
attest_file_directory = {default_attest_file_directory}
nachteilsausgleich_file_directory = {default_nachteilsausgleich_file_directory}
nachteilsausgleich_excel_directory = {default_nachteilsausgleich_excel_directory}
foto_directory = {default_foto_directory}
foto_zip_directory = {default_foto_zip_directory}
erzieher_export_directory = {default_erzieher_export_directory}
ansprechpartner_export_directory = {default_ansprechpartner_export_directory}
erzieher_output_directory = {default_erzieher_output_directory}
ausbilder_input_directory = {default_ausbilder_input_directory}
ausbilder_output_directory = {default_ausbilder_output_directory}

[FotoOptions]
# Vorlage fuer den ZIP-Dateinamen beim Foto-Export.
# Platzhalter: {{datum}} {{datetime}} {{zeit}} {{jahr}} {{monat}} {{tag}}
zip_name_template = Fotos_{{datum}}
# Vorlage fuer das Umbenennen beim Kopieren in den Unterordner.
# Platzhalter: {{id}} {{vorname}} {{nachname}} {{klasse}} {{status}} {{geschlecht}} {{geburtsdatum}}
rename_template = {{nachname}}_{{vorname}}_{{id}}
rename_subdir = Umbenannt

[ProcessingOptions]
use_abschlussdatum = False
create_second_file = False
warn_entlassdatum = True
warn_aufnahmedatum = True
warn_klassenwechsel = True
warn_new_students = True
warn_karteileichen = False
create_class_size_file = False
timeframe_hours = 24
enable_attestpflicht_column = False
enable_nachteilsausgleich_column = False
disable_import_file_creation = False
disable_import_file_if_admin_warning = False
treat_status_6_as_active = True

[InfoMailOptions]
selected_fields =

[SchildAPI]
# Optional: Schild 3.x SVWS-Server REST-API als Alternative zum CSV-Import.
# Wenn aktiv, werden Schueler-, Klassen- und Lehrerdaten direkt vom Server gelesen
# statt aus den CSV-Dateien. Schild 2.x: hier nichts ändern (use_api = False lassen).
use_api = False
server_url = https://localhost
schema = svwsdb
user =
password =
verify_ssl = False
fallback_to_csv = True
# Schuljahresabschnitt-Filter:
#   leer  = aktuell aktiver Abschnitt vom Server (empfohlen)
#   ID    = fester Abschnitt (z.B. fuer Tests, Vergangenheit)
abschnitt_id =
# Status-Whitelist (Schild-Statuswerte die abgerufen werden sollen).
# Default 2,6,8,9 entspricht dem Schild-Filter
# "Aktuelles Schuljahr - Aktive, Abgaenger und Abschluesse" + Externe.
#   0=Aufnahme, 1=Warteliste, 2=Aktiv, 3=Beurlaubt, 6=Extern,
#   8=Abschluss, 9=Abgang ohne Abschluss, 10=Ehemalige
allowed_statuses = 2,6,8,9
# Bezeichnung der Vermerkart in Schild fuer Attestpflicht / Nachteilsausgleich.
attest_vermerk_bezeichnung =
nachteilsausgleich_vermerk_bezeichnung =
# Quelle pro Vermerk: 'csv' = aus separater CSV-Datei (Voraussetzungen 4/5)
#                     'api' = direkt vom SVWS-Server (nur wirksam wenn use_api=True)
attest_source = csv
nachteilsausgleich_source = csv

[mail]
# Empfänger nur bei Klassenwechsel-Warnungen
# gültig: old | new | both
class_change_recipients = both

[Erzieher]
# Vorlage fuer den ZIP-Dateinamen beim Erzieher-Export.
# Platzhalter: {{datum}} {{datetime}} {{zeit}} {{jahr}} {{monat}} {{tag}}
zip_name_template = Erzieher_Import_{{datum}}
# Smart-Match: Anspr-Zeilen werden per Anschluss-Art (Mutter/Vater/...)
# an passende Erzieher-Slots zugewiesen — verhindert dass Vater versehentlich
# Mutters Telefon bekommt. False = altes positional-Matching.
smart_match = True
# Volljaehrig-Filter: Schueler mit Erzieher-Art "Schueler/in ist volljaehrig"
# (Self-Ansprechpartner) werden nicht in den Erzieher-Import uebernommen.
filter_volljaehrig = False
# E-Mail-Pflicht: Erzieher ohne E-Mail-Adresse werden nicht exportiert
# (sie koennen sich in WebUntis ohnehin nicht anmelden).
require_email = False
# Dummy-Fill: leere Erzieher-Felder werden mit eindeutigen Dummy-Werten
# (DUMMY / dummy@invalid.local / 000) gefuellt, damit Pflichtfelder belegt sind
# und Dummies nachtraeglich in WebUntis filterbar bleiben.
fill_dummies = False
# Lift-Limit: Limit von 2 Erziehern pro Schueler aufheben. Ueberzaehlige
# Telefon-Zeilen aus dem Ansprechpartner-Export landen in Erzieher_3.csv,
# Erzieher_4.csv ... (Stammdaten ggf. Dummy, wenn fill_dummies aktiv).
lift_limit = False
# Telefon-Quelle: Telefonnummer aus dem Erzieher-Export (Spalten
# 'Telefon-Nummern: ...') wird als prioritaere Pseudo-Ansprechpartner-Zeile
# behandelt; Duplikate gegenueber dem Ansprechpartner-Export werden gefiltert.
phone_from_erz_first = True
# Eltern-IDs: jedem Erzieher wird eine schulweit eindeutige ID zugewiesen
# (persistent in eltern_ids.json), damit WebUntis denselben Erzieher ueber
# Geschwister hinweg als denselben Account erkennt.
assign_eltern_ids = False
# Klassen-Whitelist (Komma-getrennt, analog Ausbilder). Leer = alle Klassen
# werden uebernommen. Sentinel '__NONE__' = explizit keine Klasse aktiv
# (nichts wird exportiert — fuer 'Alle abwaehlen' im UI).
class_filter =
# Single-File-Konsolidierung (3.2): nutzt den Schueler-Export aus dem
# 'Schild Exporte'-Hauptverzeichnis (Setting schildexport_directory) auch
# als Erzieher-Quelle (gleiche 'Erzieher 1/2: ...' und 'Telefon-Nummern: ...'-
# Spalten wie der separate Erzieher-Export). Werte:
#   off      — Default, ignoriert Schueler-Export
#   fallback — nur wenn erzieher_export_directory leer ist
#   always   — Schueler-Export hat IMMER Vorrang
# Limit: max. 2 Erzieher pro Schueler, max. 1 Telefon pro Schueler.
schueler_export_mode = off
# KL-Mail-Versand fuer den Erzieher-Workflow (3.3): aktuelle Erzieher-/
# Ansprechpartner-ROHDATEN an die Klassenlehrkraefte mailen (zur Info +
# Kontrolle, Korrektur ueber das Sekretariat in Schild).
kl_mail_respect_class_whitelist = True
kl_mail_only_minor = False
kl_mail_include_stv_kl = True
kl_mail_subject_suffix =

[Ausbilder]
# Vorlage fuer den Dateinamen der Ausbilder-Import-CSV.
# Platzhalter: {{datum}} {{datetime}} {{zeit}} {{jahr}} {{monat}} {{tag}}
output_name_template = WebUntis_Ausbilder_Import_{{datetime}}
# Whitelist der Klassen (Komma-getrennt). Leer = alle Klassen werden uebernommen.
class_filter =
# Blacklist der Schueler-IDs (Komma-getrennt). Diese Schueler werden NICHT exportiert
# (z.B. weil sie der Datenverarbeitung nicht zugestimmt haben).
blacklist_ids =
# Modus fuer den Firma-Filter: 'whitelist' (nur diese Firmen exportieren) oder
# 'blacklist' (diese Firmen nie exportieren). Es ist immer nur einer aktiv.
firma_filter_mode = blacklist
# Whitelist / Blacklist der Firmen (JSON-Liste). Leer = keine Beschraenkung.
# JSON, weil Firmen-Namen Kommas enthalten koennen.
firma_whitelist = []
firma_blacklist = []
# KL-Mail-Versand (3.2): Optionen fuer den Funktion 'Aktuelle Ausbilder-Daten
# an Klassenlehrkraefte mailen'. Defaults gespiegelt vom WebUntis-Export
# (Datensparsamkeit: was nicht in den Export wandert, geht auch nicht an die KL).
kl_mail_respect_class_whitelist = True
kl_mail_respect_blacklist = True
kl_mail_respect_firma_filter = True
kl_mail_include_stv_kl = True
kl_mail_subject_suffix =
# Single-File-Konsolidierung (3.2): nutzt den Schueler-Export aus dem
# 'Schild Exporte'-Hauptverzeichnis (Setting schildexport_directory) auch
# als Ausbilder-Quelle. Werte:
#   off      — Default, ignoriert Schueler-Export (liest aus ausbilder_input_directory)
#   fallback — nur wenn ausbilder_input_directory leer ist
#   always   — Schueler-Export hat IMMER Vorrang
schueler_export_mode = off
"""

    # Standard-Inhalt für email_settings.ini vorbereiten
    email_settings_ini_content = f"""# Einstellungen für den E-Mail-Versand
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
# Verwenden Sie Platzhalter wie {{Vorname}}, {{Nachname}}, {{Klasse}}, {{neues_entlassdatum}}, etc.

[Templates]
subject_entlassdatum = {DEFAULT_TEMPLATES['entlassdatum']['subject']}
body_entlassdatum = {DEFAULT_TEMPLATES['entlassdatum']['body']}
subject_aufnahmedatum = {DEFAULT_TEMPLATES['aufnahmedatum']['subject']}
body_aufnahmedatum = {DEFAULT_TEMPLATES['aufnahmedatum']['body']}
subject_klassenwechsel = {DEFAULT_TEMPLATES['klassenwechsel']['subject']}
body_klassenwechsel = {DEFAULT_TEMPLATES['klassenwechsel']['body']}
subject_new_student = {DEFAULT_TEMPLATES['new_student']['subject']}
body_new_student = {DEFAULT_TEMPLATES['new_student']['body']}
subject_karteileiche = {DEFAULT_TEMPLATES['karteileiche']['subject']}
body_karteileiche = {DEFAULT_TEMPLATES['karteileiche']['body']}
subject_info_notification = {DEFAULT_TEMPLATES['info_notification']['subject']}
body_info_notification = {DEFAULT_TEMPLATES['info_notification']['body']}
subject_ausbilder_kl_uebersicht = {DEFAULT_TEMPLATES['ausbilder_kl_uebersicht']['subject']}
body_ausbilder_kl_uebersicht = {DEFAULT_TEMPLATES['ausbilder_kl_uebersicht']['body']}
subject_erzieher_kl_uebersicht = {DEFAULT_TEMPLATES['erzieher_kl_uebersicht']['subject']}
body_erzieher_kl_uebersicht = {DEFAULT_TEMPLATES['erzieher_kl_uebersicht']['body']}
[WebUntisAPI]
use_api = False
server_url = https://neptun.webuntis.com/WebUntis/jsonrpc.do
school = schoolname
user = user
password = password
client_name = Schild-WebUntis-Tool
"""

    # Prüfen, ob settings.ini existiert, und ggf. erstellen
    settings_ini_exists = os.path.exists("settings.ini")
    if not settings_ini_exists:
        with open("settings.ini", "w", encoding="utf-8-sig") as file:
            file.write(settings_ini_content)
        print_success("Standard-Konfigurationsdatei 'settings.ini' wurde erstellt.")
    else:
        # Bestehende Konfiguration patchen (neue Felder hinzufügen)
        config = configparser.ConfigParser()
        if safe_read_config(config, "settings.ini"):
            updated = False
            # ProcessingOptions
            if not config.has_option('ProcessingOptions', 'warn_karteileichen'):
                config.set('ProcessingOptions', 'warn_karteileichen', 'False')
                updated = True
            if not config.has_option('ProcessingOptions', 'treat_status_6_as_active'):
                config.set('ProcessingOptions', 'treat_status_6_as_active', 'True')
                updated = True

            # SchildAPI-Section (Schild 3.x)
            if not config.has_section('SchildAPI'):
                config.add_section('SchildAPI')
                updated = True
            for key, default in [
                ('use_api', 'False'),
                ('server_url', 'https://localhost'),
                ('schema', 'svwsdb'),
                ('user', ''),
                ('password', ''),
                ('verify_ssl', 'False'),
                ('fallback_to_csv', 'True'),
                ('abschnitt_id', ''),
                ('allowed_statuses', '2,6,8,9'),
                ('attest_vermerk_bezeichnung', ''),
                ('nachteilsausgleich_vermerk_bezeichnung', ''),
                ('attest_source', 'csv'),
                ('nachteilsausgleich_source', 'csv'),
            ]:
                if not config.has_option('SchildAPI', key):
                    config.set('SchildAPI', key, default)
                    updated = True

            # Directories
            if not config.has_option('Directories', 'nachteilsausgleich_excel_directory'):
                config.set('Directories', 'nachteilsausgleich_excel_directory', default_nachteilsausgleich_excel_directory)
                updated = True
            if not config.has_option('Directories', 'foto_directory'):
                config.set('Directories', 'foto_directory', default_foto_directory)
                updated = True
            if not config.has_option('Directories', 'foto_zip_directory'):
                config.set('Directories', 'foto_zip_directory', default_foto_zip_directory)
                updated = True
            if not config.has_option('Directories', 'erzieher_export_directory'):
                config.set('Directories', 'erzieher_export_directory', default_erzieher_export_directory)
                updated = True
            if not config.has_option('Directories', 'ansprechpartner_export_directory'):
                config.set('Directories', 'ansprechpartner_export_directory', default_ansprechpartner_export_directory)
                updated = True
            if not config.has_option('Directories', 'erzieher_output_directory'):
                config.set('Directories', 'erzieher_output_directory', default_erzieher_output_directory)
                updated = True
            if not config.has_option('Directories', 'ausbilder_input_directory'):
                config.set('Directories', 'ausbilder_input_directory', default_ausbilder_input_directory)
                updated = True
            if not config.has_option('Directories', 'ausbilder_output_directory'):
                config.set('Directories', 'ausbilder_output_directory', default_ausbilder_output_directory)
                updated = True
            # FotoOptions
            if not config.has_section('FotoOptions'):
                config.add_section('FotoOptions')
                updated = True
            if not config.has_option('FotoOptions', 'zip_name_template'):
                config.set('FotoOptions', 'zip_name_template', 'Fotos_{datum}')
                updated = True
            if not config.has_option('FotoOptions', 'rename_template'):
                config.set('FotoOptions', 'rename_template', '{nachname}_{vorname}_{id}')
                updated = True
            if not config.has_option('FotoOptions', 'rename_subdir'):
                config.set('FotoOptions', 'rename_subdir', 'Umbenannt')
                updated = True

            # Erzieher (Phase 2 — aktiv)
            if not config.has_section('Erzieher'):
                config.add_section('Erzieher')
                updated = True
            # Veralteten "status = In Vorbereitung"-Eintrag entfernen, falls vorhanden
            if config.has_option('Erzieher', 'status') and config.get('Erzieher', 'status', fallback='').strip().startswith('In Vorbereitung'):
                config.remove_option('Erzieher', 'status')
                updated = True
            if not config.has_option('Erzieher', 'zip_name_template'):
                config.set('Erzieher', 'zip_name_template', 'Erzieher_Import_{datum}')
                updated = True
            if not config.has_option('Erzieher', 'smart_match'):
                config.set('Erzieher', 'smart_match', 'True')
                updated = True
            if not config.has_option('Erzieher', 'filter_volljaehrig'):
                config.set('Erzieher', 'filter_volljaehrig', 'False')
                updated = True
            if not config.has_option('Erzieher', 'require_email'):
                config.set('Erzieher', 'require_email', 'False')
                updated = True
            if not config.has_option('Erzieher', 'fill_dummies'):
                config.set('Erzieher', 'fill_dummies', 'False')
                updated = True
            if not config.has_option('Erzieher', 'lift_limit'):
                config.set('Erzieher', 'lift_limit', 'False')
                updated = True
            if not config.has_option('Erzieher', 'phone_from_erz_first'):
                config.set('Erzieher', 'phone_from_erz_first', 'True')
                updated = True
            if not config.has_option('Erzieher', 'assign_eltern_ids'):
                config.set('Erzieher', 'assign_eltern_ids', 'False')
                updated = True
            if not config.has_option('Erzieher', 'class_filter'):
                config.set('Erzieher', 'class_filter', '')
                updated = True
            # Single-File-Konsolidierung (3.2): default = 'off' (bestehende
            # Installationen veraendern ihr Verhalten nicht stillschweigend —
            # User muss in der UI explizit auf 'fallback' oder 'always' wechseln).
            if not config.has_option('Erzieher', 'schueler_export_mode'):
                config.set('Erzieher', 'schueler_export_mode', 'off')
                updated = True
            # KL-Mail-Versand (3.3) — pro Setting einzeln (alte Configs erben Defaults).
            for _k, _v in (
                ('kl_mail_respect_class_whitelist', 'True'),
                ('kl_mail_only_minor',              'False'),
                ('kl_mail_include_stv_kl',          'True'),
                ('kl_mail_subject_suffix',          ''),
            ):
                if not config.has_option('Erzieher', _k):
                    config.set('Erzieher', _k, _v)
                    updated = True

            # Ausbilder (Phase 3 — aktiv)
            if not config.has_section('Ausbilder'):
                config.add_section('Ausbilder')
                updated = True
            # Veralteten "status = In Vorbereitung"-Eintrag entfernen, falls vorhanden
            if config.has_option('Ausbilder', 'status') and config.get('Ausbilder', 'status', fallback='').strip().startswith('In Vorbereitung'):
                config.remove_option('Ausbilder', 'status')
                updated = True
            if not config.has_option('Ausbilder', 'output_name_template'):
                config.set('Ausbilder', 'output_name_template', 'WebUntis_Ausbilder_Import_{datetime}')
                updated = True
            if not config.has_option('Ausbilder', 'class_filter'):
                config.set('Ausbilder', 'class_filter', '')
                updated = True
            if not config.has_option('Ausbilder', 'blacklist_ids'):
                config.set('Ausbilder', 'blacklist_ids', '')
                updated = True
            if not config.has_option('Ausbilder', 'firma_whitelist'):
                config.set('Ausbilder', 'firma_whitelist', '[]')
                updated = True
            if not config.has_option('Ausbilder', 'firma_blacklist'):
                config.set('Ausbilder', 'firma_blacklist', '[]')
                updated = True
            if not config.has_option('Ausbilder', 'firma_filter_mode'):
                config.set('Ausbilder', 'firma_filter_mode', 'blacklist')
                updated = True
            # Single-File-Konsolidierung (3.2) auch fuer Ausbilder — default 'off',
            # damit bestehende Workflows ihre Quelle nicht stillschweigend wechseln.
            if not config.has_option('Ausbilder', 'schueler_export_mode'):
                config.set('Ausbilder', 'schueler_export_mode', 'off')
                updated = True
            # KL-Mail-Versand (3.2): pro Setting einzeln pruefen, damit alte
            # Configs nahtlos die Defaults erben.
            for _k, _v in (
                ('kl_mail_respect_class_whitelist', 'True'),
                ('kl_mail_respect_blacklist',       'True'),
                ('kl_mail_respect_firma_filter',    'True'),
                ('kl_mail_include_stv_kl',          'True'),
                ('kl_mail_subject_suffix',          ''),
            ):
                if not config.has_option('Ausbilder', _k):
                    config.set('Ausbilder', _k, _v)
                    updated = True

            if updated:
                with open("settings.ini", "w", encoding="utf-8-sig") as configfile:
                    config.write(configfile)
                print_info("settings.ini wurde um fehlende Einträge aktualisiert (Auto-Patcher).")

    # Prüfen, ob email_settings.ini existiert, und ggf. erstellen
    email_settings_ini_exists = os.path.exists("email_settings.ini")
    if not email_settings_ini_exists:
        with open("email_settings.ini", "w", encoding="utf-8-sig") as file:
            file.write(email_settings_ini_content)
        print_success("Standard-Konfigurationsdatei 'email_settings.ini' wurde erstellt.")
    else:
        # Bestehende Konfiguration patchen (neue Felder hinzufügen)
        config = configparser.ConfigParser()
        if safe_read_config(config, "email_settings.ini"):
            updated = False
            # Templates
            if not config.has_option('Templates', 'subject_karteileiche'):
                config.set('Templates', 'subject_karteileiche', 'Webuntis-Hinweis: Schüler fehlt/gelöscht $Vorname $Nachname')
                updated = True
            if not config.has_option('Templates', 'body_karteileiche'):
                config.set('Templates', 'body_karteileiche', DEFAULT_TEMPLATES['karteileiche']['body'])
                updated = True
            
            # Ensure other templates are also present (Silent Update)
            for t_type in ['entlassdatum', 'aufnahmedatum', 'klassenwechsel', 'new_student', 'info_notification', 'ausbilder_kl_uebersicht', 'erzieher_kl_uebersicht']:
                if not config.has_option('Templates', f'subject_{t_type}'):
                    config.set('Templates', f'subject_{t_type}', DEFAULT_TEMPLATES[t_type]['subject'])
                    updated = True
                if not config.has_option('Templates', f'body_{t_type}'):
                    config.set('Templates', f'body_{t_type}', DEFAULT_TEMPLATES[t_type]['body'])
                    updated = True

            # Spezielles Update für Klassenwechsel (Force Update auf neues Tabellen-Format)
            if config.has_option('Templates', 'body_klassenwechsel'):
                current_body = config.get('Templates', 'body_klassenwechsel')
                if "$lehrkraefte_tabelle" not in current_body:
                    config.set('Templates', 'body_klassenwechsel', DEFAULT_TEMPLATES['klassenwechsel']['body'])
                    updated = True

            # Spezielles Update für Info-Notification (Nachteilsausgleich-Details Platzhalter)
            if config.has_option('Templates', 'body_info_notification'):
                current_body = config.get('Templates', 'body_info_notification')
                if "$nachteilsausgleich_details" not in current_body:
                    config.set('Templates', 'body_info_notification', DEFAULT_TEMPLATES['info_notification']['body'])
                    updated = True
            
            if not config.has_section('WebUntisAPI'):
                config.add_section('WebUntisAPI')
                config.set('WebUntisAPI', 'use_api', 'False')
                config.set('WebUntisAPI', 'server_url', 'https://neptun.webuntis.com/WebUntis/jsonrpc.do')
                config.set('WebUntisAPI', 'school', 'schoolname')
                config.set('WebUntisAPI', 'user', 'user')
                config.set('WebUntisAPI', 'password', 'password')
                config.set('WebUntisAPI', 'client_name', 'Schild-WebUntis-Tool')
                updated = True
            
            if updated:
                with open("email_settings.ini", "w", encoding="utf-8-sig") as configfile:
                    config.write(configfile)
                print_info("email_settings.ini wurde um fehlende Einträge aktualisiert (Auto-Patcher).")

    # Sicherstellen, dass die in settings.ini definierten Ordner existieren
    config = configparser.ConfigParser()
    if settings_ini_exists:
        safe_read_config(config, "settings.ini")

    directories = {
        "classes_directory": default_classes_dir,
        "teachers_directory": default_teachers_dir,
        "log_directory": default_log_dir,
        "xlsx_directory": default_xlsx_dir,
        "schildexport_directory": default_schildexport_dir,
        "class_size_directory": default_class_size_dir,
        "import_directory": default_import_dir,
        "attest_file_directory": default_attest_file_directory,
        "nachteilsausgleich_file_directory": default_nachteilsausgleich_file_directory,
        "nachteilsausgleich_excel_directory": default_nachteilsausgleich_excel_directory,
        "foto_directory": default_foto_directory,
        "foto_zip_directory": default_foto_zip_directory,
        "erzieher_export_directory": default_erzieher_export_directory,
        "ansprechpartner_export_directory": default_ansprechpartner_export_directory,
        "erzieher_output_directory": default_erzieher_output_directory,
        "ausbilder_input_directory": default_ausbilder_input_directory,
        "ausbilder_output_directory": default_ausbilder_output_directory,
    }

    print_section("Verzeichnisse")
    for key, default_path in directories.items():
        directory = config.get("Directories", key, fallback=default_path, raw=True)
        directory = os.path.normpath(directory)
        if not os.path.isabs(directory):
            directory = os.path.abspath(directory)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
                print_creation(f"  Erstellt: '{directory}'")
            except (FileNotFoundError, OSError) as e:
                print_warning(f"  Nicht erreichbar: '{directory}' – {e}")


    global admin_warnings_cache
    admin_warnings_cache = []

# Generieren der Admin-Warnungen bei für den Fall inkonsistenter Daten. Wird ebenfalls direkt beim Start des Servers unter "if __name__ == "__main__":" abegerufen, sofern kein --skip-admin-warnings verwendet wurde.
def admin_warnings(send_email_flag=False):

    # Admin-Warnungen werden erstellt
    print_info("Erstelle Admin-Warnungen...")

    # Haupt-Import-Datei einlesen
    students_output, students_by_id = read_students(use_abschlussdatum=False)

    # Konfigurationsdatei einlesen
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
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

    # Im SVWS-API-Modus (Schild 3.x) kommen die Klassendaten direkt vom Server —
    # die zweite Warnungsstufe (Klassenlehrer-Check direkt aus der Klassen-CSV)
    # entfaellt dann.
    use_schild_api = config.getboolean('SchildAPI', 'use_api', fallback=False)
    if use_schild_api:
        print_info("SVWS-API-Modus: überspringe Klassen-CSV-basierte Klassenlehrer-Prüfung (Daten kommen vom Server).")
        return admin_warnings_cache

    # Überprüfen, ob CSV-Dateien im Klassenverzeichnis vorhanden sind
    if not os.path.exists(classes_dir):
        print_admin_warning(f"Warnung: Klassenverzeichnis '{classes_dir}' nicht erreichbar (Laufwerk nicht verfügbar?).")
        return admin_warnings_cache
    class_csv_files = [f for f in os.listdir(classes_dir) if f.endswith('.csv')]
    if not class_csv_files:
        print_admin_warning(f"Warnung: Keine Klassen-CSV-Dateien im Ordner '{classes_dir}' für die Erstellung von Admin-Warnungen gefunden.")
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
    if admin_warnings_cache:
        print_section("Admin-Warnungen")
        for warning in admin_warnings_cache:
            print_admin_warning(f"  {warning['Typ']}: {warning['Details']}")
        print_warningtext("Klassen- und Lehrerdaten sollten aktualisiert werden.")
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


#(Get) Route und Funktion zum Öffnen der Webseite, Reinladen der Daten, Initialisieren von Caches für Warnungen, Fehlermeldungen etc., 
#(Post) sowie auch Ausführung der def_run aus der main.py bei Klick auf den Verarbeiten-Button
@app.route('/test')
def test_route(): return 'TEST OK', 200

_PANEL_LABELS = {
    'settingsPanel':                 'Einstellungspanel',
    'emailEditor':                   'E-Mail-Editor',
    'emailEditorAusbilderKlMail':    'E-Mail-Editor (Ausbilder: KL-Mail)',
    'emailEditorErzieherKlMail':     'E-Mail-Editor (Erzieher: KL-Mail)',
    'shortcutCreator':               'Shortcut-Tool',
    'uploadArea':                    'Datei-Upload',
    'historyPanel':                  'Historie',
    'warningsPanel':                 'Warnungen',
    'dashboardPanel':                'Dashboard',
    'adminPanel':                    'Admin-Check',
    'infoMailPanel':                 'Info-Mails',
}

@app.route('/api/panel_opened', methods=['POST'])
def panel_opened():
    panel_key = request.json.get('panel', '') if request.json else ''
    label = _PANEL_LABELS.get(panel_key, panel_key)
    print_info(f"🌐 Weboberfläche: {label} geöffnet.")
    return jsonify({"status": "ok"})

@app.route('/test_api', methods=['POST'])
def test_api():
    from webuntis_api import WebUntisClient
    data = request.json
    client = WebUntisClient(
        server_url=data.get('server_url'),
        school=data.get('school'),
        user=data.get('user'),
        password=data.get('password'),
        client_name=data.get('client_name', 'Schild-WebUntis-Tool')
    )
    success, message = client.test_connection()
    return jsonify({'success': success, 'message': message})

@app.route('/', methods=['GET', 'POST'])
def index():
    global warnings_cache  # Globaler Cache für die Zwischenspeicherung von Warnungen
    warnings = warnings_cache or []
    confirmation = None  # Variable für Bestätigungsnachricht
    errors = []  # Liste für Fehlermeldungen
    warnings_messages = []  # Liste für nicht-blockierende Warnungen

    if request.method == 'GET':
        print_info("🌐 Weboberfläche: Schüler-Verarbeitung geöffnet.")

    # Zugriff auf die globalen CLI-Argumente
    global cli_args
    no_log = cli_args.get("no_log", False)
    no_xlsx = cli_args.get("no_xlsx", False)

    # Werte aus der settings.ini laden
    config = configparser.ConfigParser()
    safe_read_config(config, "settings.ini")
    use_abschlussdatum = config.getboolean('ProcessingOptions', 'use_abschlussdatum', fallback=False)
    create_second_file = config.getboolean('ProcessingOptions', 'create_second_file', fallback=False)
    warn_entlassdatum = config.getboolean('ProcessingOptions', 'warn_entlassdatum', fallback=True)
    warn_aufnahmedatum = config.getboolean('ProcessingOptions', 'warn_aufnahmedatum', fallback=True)
    warn_klassenwechsel = config.getboolean('ProcessingOptions', 'warn_klassenwechsel', fallback=True)
    class_change_recipients = config.get('ProcessingOptions', 'class_change_recipients', fallback='old')
    warn_new_students = config.getboolean('ProcessingOptions', 'warn_new_students', fallback=True)
    warn_karteileichen = config.getboolean('ProcessingOptions', 'warn_karteileichen', fallback=False)
    create_class_size_file = config.getboolean('ProcessingOptions', 'create_class_size_file', fallback=True) 
    enable_attestpflicht_column = config.getboolean('ProcessingOptions', 'enable_attestpflicht_column', fallback=False) 
    enable_nachteilsausgleich_column= config.getboolean('ProcessingOptions', 'enable_nachteilsausgleich_column', fallback=False)
    disable_import_file_creation = config.getboolean('ProcessingOptions', 'disable_import_file_creation', fallback=False)
    disable_import_file_if_admin_warning = config.getboolean('ProcessingOptions', 'disable_import_file_if_admin_warning', fallback=False)

    # Werte aus der email_settings.ini laden
    config = configparser.ConfigParser()
    config.read("email_settings.ini", encoding='utf-8-sig')

    # Vorlagenwerte laden
    subject_entlassdatum = config.get("Templates", "subject_entlassdatum", fallback="")
    body_entlassdatum = config.get("Templates", "body_entlassdatum", fallback="")
    subject_aufnahmedatum = config.get("Templates", "subject_aufnahmedatum", fallback="")
    body_aufnahmedatum = config.get("Templates", "body_aufnahmedatum", fallback="")
    subject_klassenwechsel = config.get("Templates", "subject_klassenwechsel", fallback="")
    body_klassenwechsel = config.get("Templates", "body_klassenwechsel", fallback="")
    subject_karteileiche = config.get("Templates", "subject_karteileiche", fallback="")
    body_karteileiche = config.get("Templates", "body_karteileiche", fallback="")

    # Einstellungen laden
    config = configparser.ConfigParser()
    safe_read_config(config, "settings.ini")
    classes_dir = config.get("Directories", "classes_directory", fallback="./Klassendaten")
    teachers_dir = config.get("Directories", "teachers_directory", fallback="./Lehrerdaten")
    use_schild_api = config.getboolean('SchildAPI', 'use_api', fallback=False)
    fallback_to_csv = config.getboolean('SchildAPI', 'fallback_to_csv', fallback=True)

    # Im SVWS-API-Modus (Schild 3.x) kommen die Daten direkt vom Server — die
    # CSV-Exports sind dann nur noch optionaler Fallback. Pruefchecks daher
    # entsprechend abschwaechen: fehlende CSV nur als Warnung, wenn ein Fallback
    # ausdruecklich erwartet wird; sonst gar nichts melden.
    if not use_schild_api:
        # Haupt-CSV pruefen — nur im CSV-Modus harter Blocker
        schildexport_dir = get_directory('schildexport_directory', default='.')
        if schildexport_dir in ('.', '', None):
            schildexport_dir = os.getcwd()
        main_csv_exists = any(
            f.endswith('.csv') for f in os.listdir(schildexport_dir) if not os.path.isdir(os.path.join(schildexport_dir, f))
        )
        if not main_csv_exists:
            errors.append("Die Haupt-CSV-Datei fehlt im Hauptverzeichnis und wird für die Verarbeitung benötigt.")
            print_error("Fehler: Haupt-CSV-Datei fehlt im Hauptverzeichnis und wird für die Verarbeitung benötigt.")

        # Klassen-/Lehrer-CSVs nur im CSV-Modus pruefen
        if not os.path.exists(classes_dir) or not any(f.endswith('.csv') for f in os.listdir(classes_dir)):
            warnings_messages.append("Die Klassendaten fehlen oder es sind keine CSV-Dateien im konfigurierten Ordner vorhanden.")
            print_warning(f"Warnung: Keine Klassendaten im Ordner '{classes_dir}' zur Vorbereitung der Warnungen gefunden.")
        if not os.path.exists(teachers_dir) or not any(f.endswith('.csv') for f in os.listdir(teachers_dir)):
            warnings_messages.append("Die Lehrerdaten fehlen oder es sind keine CSV-Dateien im konfigurierten Ordner vorhanden.")
            print_warning(f"Warnung: Keine Lehrerdaten im Ordner '{teachers_dir}' zur Vorbereitung der Warnungen gefunden.")
    elif fallback_to_csv:
        # API aktiv, aber CSV als Fallback gewuenscht — pruefe nur, ob ein Fallback
        # ueberhaupt verfuegbar waere; alles nur als Warnung, nicht als Blocker.
        schildexport_dir = get_directory('schildexport_directory', default='.')
        if schildexport_dir in ('.', '', None):
            schildexport_dir = os.getcwd()
        main_csv_exists = any(
            f.endswith('.csv') for f in os.listdir(schildexport_dir) if not os.path.isdir(os.path.join(schildexport_dir, f))
        )
        if not main_csv_exists:
            warnings_messages.append("SVWS-API-Modus aktiv mit fallback_to_csv=True, aber keine Haupt-CSV im Schild-Export-Verzeichnis. Bei API-Ausfall ist kein CSV-Fallback möglich.")

    if request.method == 'POST' and not errors:
        # Aktuelle Werte aus dem Formular auf im WebEnd lesen und die Auswahl des Benutzers speichern (Standardwerte werden für den Prozess überschrieben)
        use_abschlussdatum = request.form.get('use_abschlussdatum') == 'on'
        create_second_file = request.form.get('create_second_file') == 'on'
        warn_entlassdatum = request.form.get('warn_entlassdatum') == 'on'
        warn_aufnahmedatum = request.form.get('warn_aufnahmedatum') == 'on'
        warn_klassenwechsel = request.form.get('warn_klassenwechsel') == 'on'
        class_change_recipients = request.form.get('class_change_recipients', class_change_recipients)
        warn_new_students = request.form.get('warn_new_students') == 'on'
        warn_karteileichen = request.form.get('warn_karteileichen') == 'on'
        create_class_size_file = request.form.get('create_class_size_file') == 'on'
        enable_attestpflicht_column = request.form.get('enable_attestpflicht_column') == 'on'
        enable_nachteilsausgleich_column = request.form.get('enable_nachteilsausgleich_column') == 'on'
        disable_import_file_creation = request.form.get('disable_import_file_creation') == 'on'
        disable_import_file_if_admin_warning = request.form.get('disable_import_file_if_admin_warning') == 'on'

        # Übergebe die Auswahl an die Run-Funktion
        try:
            # Datenverarbeitung basierend auf den Benutzereinstellungen
            print_info("🌐 Dashboard-Aktion: Manueller Daten-Import durch Benutzer gestartet.")
            print_section("Verarbeitung via Weboberfläche")
            warnings, info_changes = run(
                use_abschlussdatum=use_abschlussdatum,
                create_second_file=create_second_file,
                warn_entlassdatum=warn_entlassdatum,
                warn_aufnahmedatum=warn_aufnahmedatum,
                warn_klassenwechsel=warn_klassenwechsel,
                warn_new_students=warn_new_students,
                warn_karteileichen=warn_karteileichen,
                class_change_recipients=class_change_recipients,
                no_log=no_log,
                no_xlsx=no_xlsx,
                create_class_size_file=create_class_size_file,
                enable_attestpflicht_column=enable_attestpflicht_column,
                enable_nachteilsausgleich_column=enable_nachteilsausgleich_column,
                disable_import_file_creation=disable_import_file_creation,
                disable_import_file_if_admin_warning=disable_import_file_if_admin_warning,
                admin_warnings_cache=admin_warnings_cache
            )
            for w in warnings:
                w['status'] = 'offen'
            warnings_cache = warnings
            global info_changes_cache
            info_changes_cache = info_changes or []

            # Setzt eine Bestätigungsnachricht nach erfolgreicher Ausführung
            confirmation = "Verarbeitung erfolgreich abgeschlossen."
            print_success("Verarbeitung über die Weboberfläche erfolgreich abgeschlossen.")
        except Exception as e:
            errors.append(f"Fehler während der Verarbeitung: {str(e)}")
            print_error(f"Fehler während der Verarbeitung über die Weboberfläche: {str(e)}")
        print_info("=" * 50)

    # Seite mit aktuellen Checkbox-Zuständen, Warnungen, Fehlern und Bestätigung rendern
    return render_template(
        'index.html',
        warnings=warnings,
        admin_warnings=admin_warnings_cache,
        confirmation=confirmation,
        errors=errors,
        warnings_messages=warnings_messages,
        use_abschlussdatum=use_abschlussdatum,
        create_second_file=create_second_file,
        warn_entlassdatum=warn_entlassdatum,
        warn_aufnahmedatum=warn_aufnahmedatum,
        warn_klassenwechsel=warn_klassenwechsel,
        class_change_recipients=class_change_recipients,
        warn_new_students=warn_new_students,
        warn_karteileichen=warn_karteileichen,
        create_class_size_file=create_class_size_file,
        enable_attestpflicht_column = enable_attestpflicht_column,
        enable_nachteilsausgleich_column = enable_nachteilsausgleich_column,
        disable_import_file_creation=disable_import_file_creation,
        disable_import_file_if_admin_warning=disable_import_file_if_admin_warning,
        subject_entlassdatum=subject_entlassdatum,
        body_entlassdatum=body_entlassdatum,
        subject_aufnahmedatum=subject_aufnahmedatum,
        body_aufnahmedatum=body_aufnahmedatum,
        subject_klassenwechsel=subject_klassenwechsel,
        body_klassenwechsel=body_klassenwechsel,
        subject_karteileiche=subject_karteileiche,
        body_karteileiche=body_karteileiche,
        no_directory_change=cli_args.get("no_directory_change", False),
        enable_upload=cli_args.get("enable_upload", False),
        initial_validation=validate_imports(),
        info_mail_fields=INFO_MAIL_AVAILABLE_FIELDS,
        info_changes_count=len(info_changes_cache),
    )


from string import Template

# Route und Funktion hinter dem Button "E-Mails Generieren". Sie generiert die E-Mails zur Vorschau im WebEnd (view_emails.html).
@app.route('/generate_emails', methods=['POST'])
def generate_emails():
    global warnings_cache, generated_emails_cache
    generated_emails_cache = []  # Globaler Cache für generierte E-Mails

    if warnings_cache:
        print_info("🌐 Dashboard-Aktion: E-Mail-Generierung angefordert.")
        print_info("Generiere E-Mails basierend auf den vorhandenen Warnungen...")
        # E-Mail-Einstellungen laden
        config = configparser.ConfigParser()
        safe_read_config(config, 'email_settings.ini')

        for i, warning in enumerate(warnings_cache):
            # Bestimme den Typ der Warnung
            if 'neues_entlassdatum' in warning:
                warning_type = "entlassdatum"
            elif 'neues_aufnahmedatum' in warning:
                warning_type = "aufnahmedatum"
            elif 'neue_klasse' in warning:
                warning_type = "klassenwechsel"
            elif 'new_student' in warning and warning['new_student']:
                warning_type = "new_student"
            elif 'karteileiche' in warning and warning['karteileiche']:
                warning_type = "karteileiche"
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
                print_error(error_message)
                return jsonify({"message": f"⚠️ Vorlage für {warning_type} fehlt in der Konfigurationsdatei."}), 400

            # Verwende Template-System zur Verarbeitung der Vorlagen
            try:
                subject = Template(subject_template).substitute(**warning)
                body = Template(body_template).substitute(
                    **warning,
                    zeitraum_text=zeitraum_text  # Zusatzwert für Zeitraum
                )
            except KeyError as e:
                error_message = f"Fehlender Platzhalter: {e} in der Vorlage für {warning_type}"
                print_error(error_message)
                return jsonify({"message": f"⚠️ Fehlender Platzhalter: {e} in der Vorlage für {warning_type}"}), 400

            # E-Mail zur Liste hinzufügen
            recipients = warning.get('recipients_list')
            if not recipients:
                recipients = [warning.get('Klassenlehrkraft_1_Email', 'N/A'), warning.get('Klassenlehrkraft_2_Email', 'N/A')]

            generated_emails_cache.append({
                'subject': subject,
                'body': body,
                'to': recipients,
                'warning_index': i
            })
        print_success("E-Mails wurden erfolgreich generiert.")
        return jsonify({"message": "✅ Die E-Mails wurden erfolgreich generiert.", "emails": generated_emails_cache})
    else:
        print_info("Keine Warnungen vorhanden, um E-Mails zu generieren.")
        return jsonify({"message": "ℹ️ Keine Warnungen verfügbar, um E-Mails zu generieren."})

# Abruf der generierten E-Mails im, WebEnd mittels der view_emails.html
@app.route('/view_generated_emails', methods=['GET'])
def view_generated_emails():
    global generated_emails_cache
    print_info("Anzeige der generierten E-Mails im Webinterface...")
    # Rendert die Seite zum Anzeigen der generierten E-Mails
    return render_template('view_emails.html', emails=generated_emails_cache)

# Route zum Abrufen der Dateihistorie (Logs & Excels)
@app.route('/api/history', methods=['GET'])
def get_history():
    print_info("Lade Historie-Daten...")
    config = configparser.ConfigParser()
    config.read("settings.ini", encoding='utf-8-sig')
    log_dir = config.get("Directories", "log_directory", fallback="Logs")
    xlsx_dir = config.get("Directories", "xlsx_directory", fallback="ExcelLogs")

    history_dict = {}
    
    import re
    date_pattern = re.compile(r'_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})\.')

    def scan_dir(directory, extension, key_name):
        if not os.path.exists(directory): return
        for f in os.listdir(directory):
            if f.endswith(extension):
                match = date_pattern.search(f)
                if match:
                    timestamp = match.group(1)
                    if timestamp not in history_dict:
                        # Format timestamp for display nicely
                        display_time = timestamp.replace('_', ' ').replace('-', ':', 2)
                        # Quick fix: original format is YYYY-MM-DD_HH-MM-SS
                        # We want YYYY-MM-DD HH:MM:SS
                        parts = timestamp.split('_')
                        if len(parts) == 2:
                            display_time = f"{parts[0]} {parts[1][:2]}:{parts[1][3:5]}:{parts[1][6:]}"

                        history_dict[timestamp] = {
                            "timestamp": timestamp,
                            "display_time": display_time,
                            "log_file": None,
                            "xlsx_file": None
                        }
                    history_dict[timestamp][key_name] = f

    scan_dir(log_dir, '.log', 'log_file')
    scan_dir(xlsx_dir, '.xlsx', 'xlsx_file')

    # Convert to list and sort descending by timestamp
    history_list = list(history_dict.values())
    history_list.sort(key=lambda x: x["timestamp"], reverse=True)

    # Apply limit
    limit = request.args.get('limit', default=30, type=int)
    if limit > 0:
        history_list = history_list[:limit]

    return jsonify(history_list)


# Route zum Anzeigen des Datei-Inhalts einer .log-Datei im WeUI Modal
@app.route('/api/log_content/<path:filename>', methods=['GET'])
def get_log_content(filename):
    config = configparser.ConfigParser()
    config.read("settings.ini", encoding='utf-8-sig')
    log_dir = config.get("Directories", "log_directory", fallback="Logs")
    
    # Path-Traversal Protection
    safe_filename = os.path.basename(filename)
    print_info(f"📄 Historie: Text-Log wird angezeigt – {safe_filename}")
    file_path = os.path.join(log_dir, safe_filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "Datei nicht gefunden"}), 404
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except Exception as e:
        # Fallback falls es anderes Encoding hat
        try:
            with open(file_path, 'r', encoding='utf-16') as f:
                content = f.read()
                return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
        except Exception as e2:
            return jsonify({"error": f"Dateiformat kann nicht gelesen werden: {str(e2)}"}), 500

# Route zum Anzeigen des Inhalts einer Excel-Log-Datei im WeUI Modal (Konvertierung in HTML-Tabelle)
@app.route('/api/xlsx_view/<path:filename>', methods=['GET'])
def view_xlsx(filename):
    from openpyxl import load_workbook
    config = configparser.ConfigParser()
    config.read("settings.ini", encoding='utf-8-sig')
    xlsx_dir = config.get("Directories", "xlsx_directory", fallback="ExcelLogs")

    # Pfad-Sicherheitsprüfung
    safe_filename = os.path.basename(filename)
    print_info(f"📊 Historie: Excel-Log wird angezeigt – {safe_filename}")

    # Pfad absolut machen
    if not os.path.isabs(xlsx_dir):
        xlsx_dir = os.path.abspath(xlsx_dir)
    file_path = os.path.join(xlsx_dir, safe_filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "Excel-Datei nicht gefunden"}), 404

    try:
        wb = load_workbook(file_path, data_only=True)
        ws = wb.active

        # HTML-Tabelle generieren
        html = '<div class="table-responsive"><table class="table table-sm table-bordered table-striped">'
        for row in ws.iter_rows(values_only=True):
            html += '<tr>'
            for cell in row:
                # Zellinhalt sicher als String behandeln
                cell_val = str(cell) if cell is not None else ""
                # Stil wie im Excel (rote Markierung bei "->")
                style = ' style="background-color: #FFCCCC;"' if "->" in cell_val else ""
                html += f'<td{style}>{cell_val}</td>'
            html += '</tr>'
        html += '</table></div>'

        return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return jsonify({"error": f"Excel konnte nicht gelesen werden: {str(e)}"}), 500


@app.route('/api/refresh_admin_warnings', methods=['POST'])
def refresh_admin_warnings():
    print_info("🌐 Dashboard-Aktion: Admin-Warnungen (System-Check) manuell neu gestartet.")
    global admin_warnings_cache
    admin_warnings_cache.clear()
    admin_warnings()
    return jsonify({"success": True, "count": len(admin_warnings_cache), "warnings": admin_warnings_cache})

# Route zum Herunterladen einer Excel-Log-Datei aus dem ExcelLogs-Verzeichnis
@app.route('/api/xlsx_download/<path:filename>', methods=['GET'])
def download_xlsx(filename):
    config = configparser.ConfigParser()
    config.read("settings.ini", encoding='utf-8-sig')
    xlsx_dir = config.get("Directories", "xlsx_directory", fallback="ExcelLogs")
    
    # Pfad-Sicherheitsprüfung
    safe_filename = os.path.basename(filename)
    print_info(f"⬇️  Historie: Excel-Log wird heruntergeladen – {safe_filename}")
    # Sicherstellen, dass das Verzeichnis absolut ist, falls nötig
    if not os.path.isabs(xlsx_dir):
        xlsx_dir = os.path.abspath(xlsx_dir)
        
    if not os.path.exists(os.path.join(xlsx_dir, safe_filename)):
        return jsonify({"error": "Excel-Datei nicht gefunden"}), 404
        
    return send_from_directory(xlsx_dir, safe_filename, as_attachment=True)
# Route und Funktion zum Abruf der E-Mail Inhalte des Vorlagen-Email-Editors im WebEnd. 
@app.route('/get_templates', methods=['GET'])
def get_templates():
    config = configparser.ConfigParser()
    try:
        config.read('email_settings.ini', encoding='utf-8-sig')
        templates = {
            "subject_entlassdatum": config.get("Templates", "subject_entlassdatum", fallback=""),
            "body_entlassdatum": config.get("Templates", "body_entlassdatum", fallback=""),
            "subject_aufnahmedatum": config.get("Templates", "subject_aufnahmedatum", fallback=""),
            "body_aufnahmedatum": config.get("Templates", "body_aufnahmedatum", fallback=""),
            "subject_klassenwechsel": config.get("Templates", "subject_klassenwechsel", fallback=""),
            "body_klassenwechsel": config.get("Templates", "body_klassenwechsel", fallback=""),
            "subject_new_student": config.get("Templates", "subject_new_student", fallback=""),
            "body_new_student": config.get("Templates", "body_new_student", fallback=""),
            "subject_karteileiche": config.get("Templates", "subject_karteileiche", fallback=""),
            "body_karteileiche": config.get("Templates", "body_karteileiche", fallback=""),
            "subject_info_notification": config.get("Templates", "subject_info_notification", fallback=""),
            "body_info_notification": config.get("Templates", "body_info_notification", fallback=""),
            # KL-Mail-Vorlage (3.2/3.3) — Ausbilder-Workflow-spezifisch, wird im
            # eigenen Editor im Ausbilder-Modul-Bereich angezeigt + editiert.
            "subject_ausbilder_kl_uebersicht": config.get("Templates", "subject_ausbilder_kl_uebersicht", fallback=""),
            "body_ausbilder_kl_uebersicht": config.get("Templates", "body_ausbilder_kl_uebersicht", fallback=""),
            # KL-Mail-Vorlage (3.3) — Erzieher-Workflow-spezifisch, analog zur
            # Ausbilder-Variante, im eigenen Editor im Erzieher-Modul-Bereich.
            "subject_erzieher_kl_uebersicht": config.get("Templates", "subject_erzieher_kl_uebersicht", fallback=""),
            "body_erzieher_kl_uebersicht": config.get("Templates", "body_erzieher_kl_uebersicht", fallback=""),
        }
        return jsonify(templates)
    except Exception as e:
        print_error(f"Fehler beim Laden der E-Mail-Vorlagen: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Route und Funktion zum Speichern der Inhalte des Vorlagen-Email-Editors im WebEnd. 
@app.route('/update_templates', methods=['POST'])
def update_templates():
    # Aktualisiert die E-Mail-Vorlagen basierend auf den vom Benutzer gesendeten Daten
    print_info("Aktualisiere E-Mail-Vorlagen in 'email_settings.ini'...")
    try:
        # E-Mail-Einstellungen laden
        email_config = configparser.ConfigParser()
        safe_read_config(email_config, 'email_settings.ini')

        # Vorlagen mit den bereitgestellten Daten aktualisieren
        email_config['Templates']['subject_entlassdatum'] = request.form.get('subject_entlassdatum', '')
        email_config['Templates']['body_entlassdatum'] = request.form.get('body_entlassdatum', '')
        email_config['Templates']['subject_aufnahmedatum'] = request.form.get('subject_aufnahmedatum', '')
        email_config['Templates']['body_aufnahmedatum'] = request.form.get('body_aufnahmedatum', '')
        email_config['Templates']['subject_klassenwechsel'] = request.form.get('subject_klassenwechsel', '')
        email_config['Templates']['body_klassenwechsel'] = request.form.get('body_klassenwechsel', '')
        email_config['Templates']['subject_new_student'] = request.form.get('subject_new_student', '')
        email_config['Templates']['body_new_student'] = request.form.get('body_new_student', '')
        email_config['Templates']['subject_karteileiche'] = request.form.get('subject_karteileiche', '')
        email_config['Templates']['body_karteileiche'] = request.form.get('body_karteileiche', '')
        email_config['Templates']['subject_info_notification'] = request.form.get('subject_info_notification', '')
        email_config['Templates']['body_info_notification'] = request.form.get('body_info_notification', '')

        # Änderungen in die Datei schreiben
        with open('email_settings.ini', 'w', encoding='utf-8-sig') as configfile:
            email_config.write(configfile)
        print_success("E-Mail-Vorlagen wurden erfolgreich aktualisiert.")
        return jsonify({'message': '✅ E-Mail-Vorlagen erfolgreich gespeichert!'})
    except Exception as e:
        error_message = f'Fehler beim Speichern der E-Mail-Vorlagen: {str(e)}'
        print_error(error_message)
        return jsonify({'message': f'❌ Fehler beim Speichern der E-Mail-Vorlagen: {str(e)}'}), 500

@app.route('/api/templates/default/<template_type>', methods=['GET'])
def get_default_template(template_type):
    if template_type in DEFAULT_TEMPLATES:
        return jsonify(DEFAULT_TEMPLATES[template_type])
    return jsonify({"error": "Template type not found"}), 404


@app.route('/api/ausbilder/update_kl_mail_template', methods=['POST'])
def ausbilder_update_kl_mail_template():
    """Speichert NUR die KL-Mail-Vorlage (subject + body) in
    [Templates].subject_ausbilder_kl_uebersicht / body_ausbilder_kl_uebersicht.

    Bewusst eigene Route (nicht /update_templates), weil der bestehende
    Bulk-Endpoint alle Templates aus den Form-Feldern uebernimmt — fehlende
    Felder wuerden andere Vorlagen leerschreiben. Hier ist nur dieses eine
    Paar wirksam, die anderen Vorlagen bleiben unangetastet."""
    print_info("Aktualisiere KL-Mail-Vorlage in 'email_settings.ini'...")
    try:
        email_config = configparser.ConfigParser()
        safe_read_config(email_config, 'email_settings.ini')
        if not email_config.has_section('Templates'):
            email_config.add_section('Templates')
        subject = request.form.get('subject_ausbilder_kl_uebersicht', '')
        body    = request.form.get('body_ausbilder_kl_uebersicht', '')
        email_config['Templates']['subject_ausbilder_kl_uebersicht'] = subject
        email_config['Templates']['body_ausbilder_kl_uebersicht']    = body
        with open('email_settings.ini', 'w', encoding='utf-8-sig') as f:
            email_config.write(f)
        print_success("KL-Mail-Vorlage gespeichert.")
        return jsonify({'message': '✅ KL-Mail-Vorlage erfolgreich gespeichert!'})
    except Exception as e:
        msg = f"Fehler beim Speichern der KL-Mail-Vorlage: {e}"
        print_error(msg)
        return jsonify({'message': f'❌ {msg}'}), 500


# Route und Funktion hinter dem "E-Mails Senden" Button im WebEnd zum Senden der E-Mails auf Grundlage der generierten Warnugen und gespeicherten Einstellungen 
@app.route('/send_emails', methods=['POST'])
def send_emails():
    global generated_emails_cache, warnings_cache
    if generated_emails_cache:
        print_info("Beginne mit dem Senden der generierten E-Mails...")
        # Verwende den Cache zum Senden der E-Mails
        for email in generated_emails_cache:
            # Filtere N/A Adressen vor dem Senden
            actual_recipients = [r for r in email['to'] if r and r.lower() != 'n/a']
            
            if not actual_recipients:
                print_warning(f"Überspringe E-Mail für '{email['subject']}', da keine gültigen Empfänger vorhanden sind.")
                continue

            try:
                send_email(
                    subject=email['subject'],
                    body=email['body'],
                    to_addresses=actual_recipients
                )
                print_success(f"✅ E-Mail an {actual_recipients} erfolgreich gesendet.")
                
                # Status der Warnung aktualisieren
                idx = email.get('warning_index')
                if idx is not None and idx < len(warnings_cache):
                    warnings_cache[idx]['status'] = 'versendet'
                
                # Kurze Pause um Rate-Limiting zu vermeiden (z.B. bei Strato)
                import time
                time.sleep(2)
            except Exception as e:
                print_error(f"❌ ❌ ❌ Fehler beim Senden an {actual_recipients}: {str(e)}")
                
        print_success("--- Alle E-Mails wurden verarbeitet ---")
        return jsonify({"message": "📧 Die Verarbeitung der E-Mails ist abgeschlossen."})
    else:
        print_warning("Keine generierten E-Mails zum Senden vorhanden.")
        return jsonify({"message": " ⚠️Keine generierten E-Mails verfügbar, um sie zu versenden."})

# API-Route zum Abrufen der aktuellen Warnungen mit ihrem Status
@app.route('/api/get_warnings', methods=['GET'])
def get_warnings():
    global warnings_cache
    return jsonify(warnings_cache)

# API-Route zum Abrufen der rohen Feldänderungen für Info-Mails
@app.route('/api/info_changes', methods=['GET'])
def get_info_changes():
    global info_changes_cache
    # Liefert vereinfachte Übersicht (ohne interne row-Daten)
    result = [
        {
            "student_id":    c["student_id"],
            "name":          c["name"],
            "current_class": c["current_class"],
            "changes":       c["changes"],
        }
        for c in info_changes_cache
    ]
    return jsonify(result)

# Route zum Laden/Speichern der Info-Mail Feldauswahl in settings.ini
@app.route('/api/info_mail_fields', methods=['GET'])
def get_info_mail_fields():
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    raw = config.get('InfoMailOptions', 'selected_fields', fallback='')
    fields = [f.strip() for f in raw.split(',') if f.strip()]
    return jsonify({"selected_fields": fields})

@app.route('/api/info_mail_fields', methods=['POST'])
def save_info_mail_fields():
    data = request.json or {}
    fields = data.get('selected_fields', [])
    config = configparser.ConfigParser()
    safe_read_config(config, 'settings.ini')
    if 'InfoMailOptions' not in config:
        config['InfoMailOptions'] = {}
    config['InfoMailOptions']['selected_fields'] = ', '.join(fields)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)
    return jsonify({"status": "ok"})

# Route zum Testen der SVWS-API-Verbindung (Schild 3.x)
@app.route('/api/schild_api/test', methods=['POST'])
def test_schild_api():
    data = request.json or {}
    try:
        from schild_api import SVWSClient
        client = SVWSClient(
            server_url=data.get('server_url', ''),
            schema=data.get('schema', ''),
            user=data.get('user', ''),
            password=data.get('password', ''),
            verify_ssl=str(data.get('verify_ssl', 'False')).lower() in ('true', '1', 'yes'),
        )
        ok, msg = client.test_connection()
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "message": f"Fehler: {e}"})

# Route zum Holen der Vermerkarten (für Datalist im UI)
@app.route('/api/schild_api/vermerkarten', methods=['POST'])
def list_schild_vermerkarten():
    data = request.json or {}
    try:
        from schild_api import SVWSClient
        client = SVWSClient(
            server_url=data.get('server_url', ''),
            schema=data.get('schema', ''),
            user=data.get('user', ''),
            password=data.get('password', ''),
            verify_ssl=str(data.get('verify_ssl', 'False')).lower() in ('true', '1', 'yes'),
        )
        vermerkarten = client.get_vermerkarten()
        return jsonify({"success": True, "vermerkarten": vermerkarten})
    except Exception as e:
        return jsonify({"success": False, "message": f"Fehler: {e}", "vermerkarten": []})

# Route zum Holen der verfügbaren Schuljahresabschnitte (für Dropdown im UI)
@app.route('/api/schild_api/abschnitte', methods=['POST'])
def list_schild_abschnitte():
    data = request.json or {}
    try:
        from schild_api import SVWSClient
        client = SVWSClient(
            server_url=data.get('server_url', ''),
            schema=data.get('schema', ''),
            user=data.get('user', ''),
            password=data.get('password', ''),
            verify_ssl=str(data.get('verify_ssl', 'False')).lower() in ('true', '1', 'yes'),
        )
        active_id, abschnitte = client.get_schuljahresabschnitte()
        return jsonify({"success": True, "active_id": active_id, "abschnitte": abschnitte})
    except Exception as e:
        return jsonify({"success": False, "message": f"Fehler: {e}", "abschnitte": []})

# ====================== Inline-Hilfe ======================

@app.route('/api/help/<key>', methods=['GET'])
def api_help_single(key):
    """Liefert einen einzelnen Hilfe-Eintrag."""
    import help_content
    entry = help_content.get_help(key)
    if not entry:
        return jsonify({"error": f"Hilfe-Eintrag '{key}' nicht gefunden."}), 404
    return jsonify({"key": key, **entry})


@app.route('/api/help', methods=['GET'])
def api_help_all():
    """Liefert alle Hilfe-Einträge (für den Glossar-Modus)."""
    import help_content
    return jsonify(help_content.get_all_help())


# ====================== Foto-Verwaltung ======================

def _current_students_with_status():
    """Liefert {id: status_str} der aktuellen Schüler (CSV oder API, je nach Konfig)."""
    try:
        _, students_by_id = read_students()
        return {sid: str(s.get('Status', '')).strip() for sid, s in students_by_id.items()}, students_by_id
    except Exception:
        return {}, {}


@app.route('/api/fotos/list', methods=['GET'])
def fotos_list():
    """Listet alle Fotos im foto_directory + Match-Info gegen aktuelle Schüler."""
    import foto_manager
    fotos = foto_manager.list_fotos(include_archive=True)
    status_by_id, students_by_id = _current_students_with_status()
    out = []
    for f in fotos:
        sid = f['id']
        student = students_by_id.get(sid)
        out.append({
            **f,
            'in_import': sid in status_by_id,
            'status': status_by_id.get(sid, ''),
            'name': (f"{student.get('Vorname','')} {student.get('Nachname','')}".strip()
                     if student else ''),
            'klasse': (student.get('Klasse', '') if student else ''),
        })
    # Status-Übersicht für die UI: welche Stati kommen im aktuellen Import vor
    present_statuses = sorted({st for st in status_by_id.values() if st})
    return jsonify({
        'foto_directory': foto_manager.get_foto_directory(),
        'zip_name_template': foto_manager.get_zip_name_template(),
        'rename_template': foto_manager.get_rename_template(),
        'rename_subdir': foto_manager.get_rename_subdir(),
        'fotos': out,
        'student_count': len(students_by_id),
        'present_statuses': present_statuses,
    })


@app.route('/api/fotos/image/<path:student_id>', methods=['GET'])
def fotos_image(student_id):
    """Liefert das Foto eines Schülers (für Dashboard / Vorschau)."""
    import foto_manager
    archived = request.args.get('archived') == '1'
    foto_dir = foto_manager.get_foto_directory()
    if archived:
        foto_dir = os.path.join(foto_dir, foto_manager.ARCHIVE_SUBDIR)
    path = foto_manager.get_foto_path(student_id, foto_dir)
    if not path or not os.path.isfile(path):
        return '', 404
    # send_from_directory loest relative Verzeichnisse gegen app.root_path
    # (= Schild_WebUntis_Tool/) auf, NICHT gegen cwd — und die settings.ini
    # liefert das Foto-Verzeichnis typischerweise cwd-relativ ('SchuelerFotos').
    # Ohne abspath() schlagen alle Foto-Auslieferungen mit 404 fehl, sobald
    # das Foto-Verzeichnis nicht zufaellig unter Schild_WebUntis_Tool/ liegt
    # (Bug bis 3.2 Beta, siehe auch analoge Stelle im xlsx-Download).
    directory = os.path.abspath(os.path.dirname(path))
    return send_from_directory(directory, os.path.basename(path))


@app.route('/api/fotos/zip/create', methods=['POST'])
def fotos_zip_create():
    """Erstellt ein Foto-ZIP und speichert es im foto_zip_directory.
       Body: {statuses: [..] | null, name_template: str | null}. statuses=null → alle im Import."""
    global last_foto_zip
    import foto_manager
    data = request.json or {}
    statuses = data.get('statuses')
    name_template = (data.get('name_template') or '').strip() or None

    # Vorlage persistent speichern
    if name_template:
        try:
            foto_manager.save_zip_name_template(name_template)
        except Exception:
            pass

    status_by_id, _ = _current_students_with_status()
    if statuses:
        wanted = {str(s).strip() for s in statuses}
        ids = [sid for sid, st in status_by_id.items() if st in wanted]
    else:
        ids = list(status_by_id.keys())

    if not ids:
        return jsonify({"error": "Keine passenden Schüler gefunden."}), 400

    try:
        zip_path, zip_name, included, missing = foto_manager.create_zip_file(
            ids, name_template=name_template)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Erstellen: {e}"}), 500
    if included == 0:
        return jsonify({"error": f"Keine Fotos gefunden (0 von {len(ids)} Schülern haben ein Foto)."}), 400

    last_foto_zip = {'path': zip_path, 'name': zip_name, 'included': included, 'missing': missing}
    return jsonify({
        "success": True,
        "name": zip_name,
        "path": zip_path,
        "directory": foto_manager.get_zip_directory(),
        "included": included,
        "missing": missing,
        "total": len(ids),
    })


@app.route('/api/fotos/zip/download', methods=['GET'])
def fotos_zip_download():
    """Lädt das zuletzt erstellte Foto-ZIP herunter."""
    from flask import send_file
    if not last_foto_zip or not os.path.isfile(last_foto_zip.get('path', '')):
        return jsonify({"error": "Es wurde noch kein ZIP erstellt (oder die Datei wurde verschoben/gelöscht)."}), 404
    return send_file(
        last_foto_zip['path'],
        mimetype='application/zip',
        as_attachment=True,
        download_name=last_foto_zip['name'],
    )


@app.route('/api/fotos/rename-copy', methods=['POST'])
def fotos_rename_copy():
    """Kopiert die Fotos der passenden Schüler umbenannt in einen Unterordner.
       Body: {statuses: [..] | null, template: str | null, subdir: str | null}."""
    import foto_manager
    data = request.json or {}
    statuses = data.get('statuses')
    template = (data.get('template') or '').strip() or None
    subdir = (data.get('subdir') or '').strip() or None

    # Vorlage + Unterordner persistent speichern
    if template or subdir:
        try:
            foto_manager.save_rename_settings(template=template, subdir=subdir)
        except Exception:
            pass

    status_by_id, students_by_id = _current_students_with_status()
    if statuses:
        wanted = {str(s).strip() for s in statuses}
        students_list = [s for sid, s in students_by_id.items() if status_by_id.get(sid) in wanted]
    else:
        students_list = list(students_by_id.values())

    if not students_list:
        return jsonify({"error": "Keine passenden Schüler gefunden."}), 400

    try:
        target_dir, copied, missing = foto_manager.copy_renamed_fotos(
            students_list, template=template, target_subdir=subdir)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Kopieren: {e}"}), 500

    if copied == 0:
        return jsonify({"error": f"Keine Fotos kopiert (0 von {len(students_list)} Schülern haben ein Foto)."}), 400

    return jsonify({
        "success": True,
        "target_dir": target_dir,
        "copied": copied,
        "missing": missing,
        "total": len(students_list),
    })


@app.route('/api/fotos/archive', methods=['POST'])
def fotos_archive():
    """Verschiebt Fotos verwaister Schüler (nicht mehr im Import) in den Archiv-Unterordner."""
    import foto_manager
    status_by_id, _ = _current_students_with_status()
    if not status_by_id:
        return jsonify({"error": "Keine aktuellen Schülerdaten verfügbar — bitte zuerst eine Verarbeitung durchführen."}), 400
    moved = foto_manager.archive_orphan_fotos(list(status_by_id.keys()))
    return jsonify({"moved": moved, "count": len(moved)})


@app.route('/api/fotos/restore', methods=['POST'])
def fotos_restore():
    """Holt eine archivierte Foto-Datei zurück ins Hauptverzeichnis."""
    import foto_manager
    data = request.json or {}
    filename = (data.get('filename') or '').strip()
    if not filename:
        return jsonify({"error": "Dateiname fehlt."}), 400
    ok = foto_manager.restore_archived_foto(filename)
    return jsonify({"ok": ok})


# ====================== Erzieher-Workflow (Phase 2) ======================

last_erzieher_zip = None  # {'path', 'name', 'stats'}


@app.route('/api/erzieher/status', methods=['GET'])
def erzieher_status():
    """Liefert Info über die aktuell erkannten Eingabedateien + Konfig."""
    import erzieher_processor
    info = erzieher_processor.status_info()
    info['last_zip'] = last_erzieher_zip
    return jsonify(info)


@app.route('/api/erzieher/preview', methods=['GET'])
def erzieher_preview():
    """Liefert eine Vorschau der Schueler-Erzieher-Zuordnungen + Feld-Mapping
    fuer die UI (kein ZIP wird erzeugt)."""
    import erzieher_processor
    try:
        data = erzieher_processor.preview()
        return jsonify(data)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Fehler bei der Vorschau: {e}"}), 500


@app.route('/api/erzieher/raw_source', methods=['GET'])
def erzieher_raw_source():
    """Liefert die Roh-Inhalte beider Quell-CSVs als Tabular-Daten fuer die UI."""
    import erzieher_processor
    try:
        max_rows = int(request.args.get('max', '500'))
    except Exception:
        max_rows = 500
    max_rows = max(10, min(5000, max_rows))
    try:
        return jsonify(erzieher_processor.raw_source(max_rows=max_rows))
    except Exception as e:
        return jsonify({"error": f"Fehler beim Laden der Quelldateien: {e}"}), 500


@app.route('/api/erzieher/process', methods=['POST'])
def erzieher_process():
    """Verarbeitet Erzieher- und Ansprechpartner-Export, schreibt ZIP ins Ausgabeverzeichnis."""
    global last_erzieher_zip
    import erzieher_processor
    data = request.json or {}
    name_template = (data.get('name_template') or '').strip() or None

    if name_template:
        try:
            erzieher_processor.save_zip_name_template(name_template)
        except Exception:
            pass

    try:
        result_files, stats = erzieher_processor.process()
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Fehler bei der Verarbeitung: {e}"}), 500

    if not result_files:
        return jsonify({"error": "Es wurden keine Erzieher gefunden."}), 400

    try:
        zip_path, zip_name = erzieher_processor.write_zip(result_files, name_template=name_template)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Schreiben des ZIP: {e}"}), 500

    last_erzieher_zip = {'path': zip_path, 'name': zip_name, 'stats': stats}
    return jsonify({
        "success":   True,
        "name":      zip_name,
        "path":      zip_path,
        "directory": erzieher_processor.get_output_dir(),
        "stats":     stats,
    })


@app.route('/api/erzieher/download', methods=['GET'])
def erzieher_download():
    """Lädt das zuletzt erstellte Erzieher-ZIP herunter."""
    from flask import send_file
    if not last_erzieher_zip or not os.path.isfile(last_erzieher_zip.get('path', '')):
        return jsonify({"error": "Es wurde noch kein ZIP erstellt (oder die Datei wurde verschoben/gelöscht)."}), 404
    return send_file(
        last_erzieher_zip['path'],
        mimetype='application/zip',
        as_attachment=True,
        download_name=last_erzieher_zip['name'],
    )


# Klassenweise Auswertung: minderjaehrige Schueler ohne Erzieher-Daten
last_erzieher_missing_zip = None  # {'path', 'name'}


@app.route('/api/erzieher/missing_report', methods=['GET'])
def erzieher_missing_report():
    """Liefert die Klassen-Auswertung minderjaehriger Schueler nach den
    angegebenen Kriterien. Query: ?criteria=a,b,c&mode=any|all"""
    import erzieher_processor
    crit_str = request.args.get('criteria', '').strip()
    criteria = [c.strip() for c in crit_str.split(',') if c.strip()] if crit_str else None
    mode = (request.args.get('mode') or 'any').strip().lower()
    if mode not in ('any', 'all'):
        mode = 'any'
    try:
        return jsonify(erzieher_processor.missing_erzieher_report(
            criteria=criteria, match_mode=mode))
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Fehler beim Erstellen des Reports: {e}"}), 500


@app.route('/api/erzieher/missing_export', methods=['POST'])
def erzieher_missing_export():
    """Schreibt CSVs (eine pro ausgewaehlter Klasse) als ZIP ins Ausgabeverzeichnis."""
    global last_erzieher_missing_zip
    import erzieher_processor
    data = request.json or {}
    classes = data.get('classes')  # Liste oder None
    criteria = data.get('criteria')  # Liste oder None
    mode = (data.get('mode') or 'any').strip().lower()
    if mode not in ('any', 'all'):
        mode = 'any'
    try:
        zip_path, zip_name, counts = erzieher_processor.write_missing_report_zip(
            classes, criteria=criteria, match_mode=mode)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Fehler beim Schreiben des ZIP: {e}"}), 500
    last_erzieher_missing_zip = {'path': zip_path, 'name': zip_name}
    return jsonify({
        "success":   True,
        "name":      zip_name,
        "path":      zip_path,
        "directory": erzieher_processor.get_output_dir(),
        "counts":    counts,
    })


@app.route('/api/erzieher/save_class_filter', methods=['POST'])
def erzieher_save_class_filter():
    """Speichert die Klassen-Whitelist (analog Ausbilder). Erwartet
    `{'classes': [klassen-namen]}`; leerer Array = alle Klassen aktiv,
    `['__NONE__']` = explizit keine."""
    import erzieher_processor
    data = request.json or {}
    classes = data.get('classes', [])
    if not isinstance(classes, list):
        return jsonify({"error": "Feld 'classes' muss eine Liste sein."}), 400
    try:
        erzieher_processor.save_class_filter(classes)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True, "class_filter": erzieher_processor.get_class_filter()})


@app.route('/api/erzieher/save_schueler_export_mode', methods=['POST'])
def erzieher_save_schueler_export_mode():
    """Speichert den Quell-Modus fuer den Erzieher-Workflow (Single-File-
    Konsolidierung). Erwartet `{'mode': 'off'|'fallback'|'always'}`."""
    import erzieher_processor
    data = request.json or {}
    mode = (data.get('mode') or '').strip().lower()
    try:
        erzieher_processor.save_schueler_export_mode(mode)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True,
                    "schueler_export_mode": erzieher_processor.get_schueler_export_mode()})


@app.route('/api/erzieher/eltern_ids/status', methods=['GET'])
def erzieher_eltern_ids_status():
    """Statistik der persistenten Eltern-ID-Datenbank."""
    import eltern_id_manager
    return jsonify(eltern_id_manager.stats())


@app.route('/api/erzieher/eltern_ids/reset', methods=['POST'])
def erzieher_eltern_ids_reset():
    """Loescht die Eltern-ID-Datenbank komplett (irreversibel)."""
    import eltern_id_manager
    removed = eltern_id_manager.reset()
    return jsonify({"success": True, "removed": removed,
                    "stats": eltern_id_manager.stats()})


@app.route('/api/erzieher/missing_download', methods=['GET'])
def erzieher_missing_download():
    """Lädt das zuletzt erstellte 'Fehlende Erzieher'-ZIP herunter."""
    from flask import send_file
    if not last_erzieher_missing_zip or not os.path.isfile(last_erzieher_missing_zip.get('path', '')):
        return jsonify({"error": "Es wurde noch kein Missing-ZIP erstellt."}), 404
    return send_file(
        last_erzieher_missing_zip['path'],
        mimetype='application/zip',
        as_attachment=True,
        download_name=last_erzieher_missing_zip['name'],
    )


# ====================== Ausbilder-Workflow (Phase 3) ======================
# DSGVO/VO DVI: Ausbilder duerfen nur Fehlstunden derjenigen Azubis sehen, die
# der Datenverarbeitung zugestimmt haben. Tool filtert Schild-Export nach
# Klassen-Whitelist UND Blacklist (keine Einwilligung) -> WebUntis-Import-CSV.

last_ausbilder_csv = None  # {'path', 'name', 'rows_in', 'rows_out'}


@app.route('/api/ausbilder/students', methods=['GET'])
def ausbilder_students():
    """Liefert Liste der Schueler aus der neuesten Schild-CSV inkl. Klassen/Blacklist/Filter."""
    import ausbilder_processor
    data = ausbilder_processor.list_students()
    data['last_csv'] = last_ausbilder_csv
    return jsonify(data)


@app.route('/api/ausbilder/save_filter', methods=['POST'])
def ausbilder_save_filter():
    """Speichert die Klassen-Whitelist persistent in settings.ini."""
    import ausbilder_processor
    data = request.json or {}
    classes = data.get('classes', [])
    if not isinstance(classes, list):
        return jsonify({"error": "Feld 'classes' muss eine Liste sein."}), 400
    try:
        ausbilder_processor.save_class_filter(classes)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True, "class_filter": ausbilder_processor.get_class_filter()})


@app.route('/api/ausbilder/save_schueler_export_mode', methods=['POST'])
def ausbilder_save_schueler_export_mode():
    """Speichert den Quell-Modus fuer den Ausbilder-Workflow (Single-File-
    Konsolidierung, symmetrisch zum Erzieher-Workflow). Erwartet
    `{'mode': 'off'|'fallback'|'always'}`."""
    import ausbilder_processor
    data = request.json or {}
    mode = (data.get('mode') or '').strip().lower()
    try:
        ausbilder_processor.save_schueler_export_mode(mode)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True,
                    "schueler_export_mode": ausbilder_processor.get_schueler_export_mode()})


@app.route('/api/ausbilder/save_blacklist', methods=['POST'])
def ausbilder_save_blacklist():
    """Speichert die komplette Blacklist (Liste von Schueler-IDs)."""
    import ausbilder_processor
    data = request.json or {}
    ids = data.get('ids', [])
    if not isinstance(ids, list):
        return jsonify({"error": "Feld 'ids' muss eine Liste sein."}), 400
    try:
        ausbilder_processor.save_blacklist(ids)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True, "blacklist": sorted(ausbilder_processor.get_blacklist())})


@app.route('/api/ausbilder/save_firma_whitelist', methods=['POST'])
def ausbilder_save_firma_whitelist():
    """Speichert die Firma-Whitelist (JSON-Liste)."""
    import ausbilder_processor
    data = request.json or {}
    firms = data.get('firms', [])
    if not isinstance(firms, list):
        return jsonify({"error": "Feld 'firms' muss eine Liste sein."}), 400
    try:
        ausbilder_processor.save_firma_whitelist(firms)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True, "firma_whitelist": ausbilder_processor.get_firma_whitelist()})


@app.route('/api/ausbilder/save_firma_blacklist', methods=['POST'])
def ausbilder_save_firma_blacklist():
    """Speichert die Firma-Blacklist (JSON-Liste)."""
    import ausbilder_processor
    data = request.json or {}
    firms = data.get('firms', [])
    if not isinstance(firms, list):
        return jsonify({"error": "Feld 'firms' muss eine Liste sein."}), 400
    try:
        ausbilder_processor.save_firma_blacklist(firms)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True, "firma_blacklist": ausbilder_processor.get_firma_blacklist()})


@app.route('/api/ausbilder/firma_invert', methods=['POST'])
def ausbilder_firma_invert():
    """Invertiert die aktive Firma-Liste in das Gegenteil und schaltet den Modus um.

    Beispiel: war vorher Blacklist mit 28 von 30 Firmen aktiv, ist nachher
    eine Whitelist mit den 2 verbleibenden Firmen aktiv. Berechnungsbasis ist
    die Menge aller Firmen in der aktuell geladenen Schueler-CSV.

    Die nicht-aktive Liste vor dem Switch (z.B. eine Whitelist, die im
    Blacklist-Modus passiv war) bleibt unangetastet — der Caller bekommt
    durch das Mode-Toggle direkt das invertierte Set, kann aber durch
    nochmaliges Mode-Toggle den Original-Stand wiederherstellen."""
    import ausbilder_processor
    try:
        # Aktuelle CSV einlesen, um alle Firmen zu erhalten — gleicher Pfad
        # wie das Frontend bei /api/ausbilder/students verwendet.
        data = ausbilder_processor.list_students()
        all_firms = set(data.get('firms', []))
        if not all_firms:
            return jsonify({"error": "Keine Firmen in der aktuellen CSV gefunden — "
                                     "Invertierung ohne Bezugsmenge nicht möglich."}), 400
        mode = ausbilder_processor.get_firma_filter_mode()
        if mode == 'whitelist':
            active = set(ausbilder_processor.get_firma_whitelist())
            new_list = sorted(all_firms - active)
            ausbilder_processor.save_firma_blacklist(new_list)
            new_mode = 'blacklist'
        else:
            active = set(ausbilder_processor.get_firma_blacklist())
            new_list = sorted(all_firms - active)
            ausbilder_processor.save_firma_whitelist(new_list)
            new_mode = 'whitelist'
        ausbilder_processor.save_firma_filter_mode(new_mode)
        return jsonify({
            'success':            True,
            'old_mode':           mode,
            'new_mode':           new_mode,
            # Aktive Firmen, die wirklich in der CSV vorkommen (stale-Eintraege
            # im persistenten List koennten sonst die Counts verzerren).
            'old_count':          len(active & all_firms),
            'new_count':          len(new_list),
            'total_firms_in_csv': len(all_firms),
        })
    except Exception as e:
        return jsonify({"error": f"Fehler beim Invertieren: {e}"}), 500


@app.route('/api/ausbilder/blacklist/toggle', methods=['POST'])
def ausbilder_blacklist_toggle():
    """Fuegt eine Schueler-ID zur Blacklist hinzu oder entfernt sie."""
    import ausbilder_processor
    data = request.json or {}
    sid = str(data.get('id', '')).strip()
    add = bool(data.get('add', True))
    if not sid:
        return jsonify({"error": "Feld 'id' fehlt."}), 400
    current = ausbilder_processor.get_blacklist()
    if add:
        current.add(sid)
    else:
        current.discard(sid)
    try:
        ausbilder_processor.save_blacklist(current)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True, "blacklisted": sid in current, "blacklist": sorted(current)})


@app.route('/api/ausbilder/process', methods=['POST'])
def ausbilder_process():
    """Filtert die Schild-CSV nach Klassen-Whitelist + Blacklist und schreibt die WebUntis-Import-CSV."""
    global last_ausbilder_csv
    import ausbilder_processor
    data = request.json or {}
    name_template = (data.get('name_template') or '').strip() or None

    if name_template:
        try:
            ausbilder_processor.save_output_name_template(name_template)
        except Exception:
            pass

    try:
        out_path, out_name, rows_in, rows_out = ausbilder_processor.filter_and_write(name_template=name_template)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Fehler bei der Verarbeitung: {e}"}), 500

    last_ausbilder_csv = {'path': out_path, 'name': out_name, 'rows_in': rows_in, 'rows_out': rows_out}
    return jsonify({
        "success":   True,
        "name":      out_name,
        "path":      out_path,
        "directory": ausbilder_processor.get_output_dir(),
        "rows_in":   rows_in,
        "rows_out":  rows_out,
    })


@app.route('/api/ausbilder/download', methods=['GET'])
def ausbilder_download():
    """Laedt die zuletzt erstellte Ausbilder-Import-CSV herunter."""
    from flask import send_file
    if not last_ausbilder_csv or not os.path.isfile(last_ausbilder_csv.get('path', '')):
        return jsonify({"error": "Es wurde noch keine CSV erstellt (oder die Datei wurde verschoben/gelöscht)."}), 404
    return send_file(
        last_ausbilder_csv['path'],
        mimetype='text/csv',
        as_attachment=True,
        download_name=last_ausbilder_csv['name'],
    )


# =========================================================================
# KL-Mail-Versand (3.2): aktuelle Ausbilder-/Betreuer-Daten an Klassenlehr-
# kraefte mailen, zur Info + Kontrolle (Korrektur via Sekretariat in Schild).
# =========================================================================
# Backend-Logik komplett in ausbilder_processor; hier nur Glue + KL-Lookup
# via read_classes() (identisch zu admin_warnings).

def _kl_mail_load_templates():
    """Liest Subject- und Body-Template aus email_settings.ini. Liefert die
    Defaults aus ausbilder_processor, falls die Datei oder die Section
    nicht existiert. Wird sowohl von Preview als auch Send genutzt."""
    import ausbilder_processor
    cfg = configparser.ConfigParser()
    safe_read_config(cfg, 'email_settings.ini')
    subject = cfg.get('Templates', 'subject_ausbilder_kl_uebersicht',
                      fallback=ausbilder_processor.DEFAULT_KL_MAIL_SUBJECT)
    body    = cfg.get('Templates', 'body_ausbilder_kl_uebersicht',
                      fallback=ausbilder_processor.DEFAULT_KL_MAIL_BODY)
    return subject, body


def _kl_mail_classes_by_name():
    """Wrapper um main.read_classes(), damit Routes nicht direkt main
    importieren muessen (verhindert Zyklen) und einfache Fehlerbehandlung
    bei nicht erreichbaren CSV-Verzeichnissen."""
    from main import read_classes
    cfg = configparser.ConfigParser()
    safe_read_config(cfg, 'settings.ini')
    classes_dir  = cfg.get('Directories', 'classes_directory',  fallback='Klassendaten')
    teachers_dir = cfg.get('Directories', 'teachers_directory', fallback='Lehrerdaten')
    try:
        classes_by_name, _teachers = read_classes(classes_dir, teachers_dir, return_teachers=True)
        return classes_by_name
    except Exception:
        return {}


@app.route('/api/ausbilder/kl_mail/preview', methods=['GET'])
def ausbilder_kl_mail_preview():
    """Liefert Pro-Klasse-Vorschau aller KL-Mails (Subject, Body-HTML,
    Empfaenger, Schueler-Tabelle) — KEIN Versand. UI rendert daraus die
    Auswahl-Liste pro Klasse + Vorschau auf Klick."""
    import ausbilder_processor
    try:
        classes_by_name = _kl_mail_classes_by_name()
        data = ausbilder_processor.build_kl_mail_data(classes_by_name=classes_by_name)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Fehler beim Aufbau der KL-Mail-Daten: {e}"}), 500
    subject_tpl, body_tpl = _kl_mail_load_templates()
    stand_date = datetime.now().strftime('%d.%m.%Y')
    suffix = (data.get('options_used') or {}).get('subject_suffix', '')
    out_classes = []
    for c in data['classes']:
        subject, body = ausbilder_processor.render_kl_mail(
            c, subject_template=subject_tpl, body_template=body_tpl,
            stand_date=stand_date, subject_suffix=suffix)
        recipients = [c['kl_email']] if c['kl_email'] else []
        cc = [c['stv_kl_email']] if c.get('stv_kl_email') else []
        out_classes.append({
            'klasse':         c['klasse'],
            'kl_name':        c['kl_name'],
            'kl_email':       c['kl_email'],
            'stv_kl_name':    c['stv_kl_name'],
            'stv_kl_email':   c['stv_kl_email'],
            'recipients':     recipients,
            'cc':             cc,
            'subject':        subject,
            'body_html':      body,
            'students_count': len(c['students']),
            'xlsx_filename':  f"KL_Mail_{ausbilder_processor.safe_class_filename(c['klasse'])}.xlsx",
        })
    return jsonify({
        'csv_path':     data['csv_path'],
        'stand':        stand_date,
        'classes':      out_classes,
        'stats':        data['stats'],
        'options_used': data['options_used'],
        'kl_mail_settings': {
            'kl_mail_respect_class_whitelist': ausbilder_processor.get_kl_mail_respect_class_whitelist(),
            'kl_mail_respect_blacklist':       ausbilder_processor.get_kl_mail_respect_blacklist(),
            'kl_mail_respect_firma_filter':    ausbilder_processor.get_kl_mail_respect_firma_filter(),
            'kl_mail_include_stv_kl':          ausbilder_processor.get_kl_mail_include_stv_kl(),
            'kl_mail_subject_suffix':          ausbilder_processor.get_kl_mail_subject_suffix(),
        },
    })


@app.route('/api/ausbilder/kl_mail/download_xlsx', methods=['GET'])
def ausbilder_kl_mail_download_xlsx():
    """Excel-Anhang einer einzelnen Klasse zum Vorschau-Check (vor dem Versand).
    Query: ?klasse=DI24a"""
    import ausbilder_processor
    from flask import send_file
    import io
    klasse = (request.args.get('klasse') or '').strip()
    if not klasse:
        return jsonify({"error": "Parameter 'klasse' fehlt."}), 400
    try:
        classes_by_name = _kl_mail_classes_by_name()
        data = ausbilder_processor.build_kl_mail_data(classes_by_name=classes_by_name)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Fehler beim Aufbau der KL-Mail-Daten: {e}"}), 500
    target = next((c for c in data['classes'] if c['klasse'] == klasse), None)
    if not target:
        return jsonify({"error": f"Klasse {klasse} ist in den aktuellen Daten nicht enthalten."}), 404
    xlsx_bytes = ausbilder_processor.build_kl_mail_xlsx(target, stand_date=datetime.now().strftime('%d.%m.%Y'))
    fname = f"KL_Mail_{ausbilder_processor.safe_class_filename(klasse)}.xlsx"
    return send_file(
        io.BytesIO(xlsx_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=fname,
    )


# Letzte KL-Mail-Versand-Stats (fuer das Frontend-Result-Feld nach Versand)
last_kl_mail_send = None  # {sent: int, failed: int, skipped: int, details: [...]}


@app.route('/api/ausbilder/kl_mail/send', methods=['POST'])
def ausbilder_kl_mail_send():
    """Versendet die ausgewaehlten KL-Mails inkl. Excel-Anhang pro Klasse.
    Body: {"classes": ["DI24a", "DI24b", ...]} — leere/fehlende Liste = alle
    Klassen mit gueltiger KL-E-Mail.

    Schreibt die xlsx-Anhaenge ins ausbilder_output_directory unter dem
    Unterordner 'KL_Mails/' — dient gleichzeitig als Versand-Nachweis."""
    import ausbilder_processor
    global last_kl_mail_send
    data_req = request.json or {}
    selected = data_req.get('classes')
    selected_set = set(selected) if isinstance(selected, list) else None  # None = alle
    try:
        classes_by_name = _kl_mail_classes_by_name()
        data = ausbilder_processor.build_kl_mail_data(classes_by_name=classes_by_name)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Fehler beim Aufbau der KL-Mail-Daten: {e}"}), 500
    subject_tpl, body_tpl = _kl_mail_load_templates()
    stand_date = datetime.now().strftime('%d.%m.%Y')
    suffix = (data.get('options_used') or {}).get('subject_suffix', '')
    out_dir = ausbilder_processor.get_output_dir()
    kl_mail_dir = os.path.join(out_dir, 'KL_Mails', datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(kl_mail_dir, exist_ok=True)

    sent = 0
    failed = 0
    skipped = 0
    details = []
    for c in data['classes']:
        if selected_set is not None and c['klasse'] not in selected_set:
            continue
        if not c['kl_email']:
            skipped += 1
            details.append({'klasse': c['klasse'], 'status': 'skipped',
                            'reason': 'Keine KL-E-Mail aufgeloesst.'})
            continue
        try:
            subject, body = ausbilder_processor.render_kl_mail(
                c, subject_template=subject_tpl, body_template=body_tpl,
                stand_date=stand_date, subject_suffix=suffix)
            xlsx_bytes = ausbilder_processor.build_kl_mail_xlsx(c, stand_date=stand_date)
            fname = f"KL_Mail_{ausbilder_processor.safe_class_filename(c['klasse'])}.xlsx"
            xlsx_path = os.path.join(kl_mail_dir, fname)
            with open(xlsx_path, 'wb') as f:
                f.write(xlsx_bytes)
            to_addrs = [c['kl_email']]
            if c.get('stv_kl_email'):
                to_addrs.append(c['stv_kl_email'])
            send_email(subject, body, to_addrs, attachment_path=xlsx_path)
            sent += 1
            details.append({'klasse': c['klasse'], 'status': 'sent',
                            'recipients': to_addrs, 'xlsx_path': xlsx_path,
                            'students_count': len(c['students'])})
        except Exception as e:
            failed += 1
            details.append({'klasse': c['klasse'], 'status': 'failed',
                            'error': str(e)})
    last_kl_mail_send = {'sent': sent, 'failed': failed, 'skipped': skipped,
                         'xlsx_directory': kl_mail_dir, 'details': details}
    return jsonify({'success': True, **last_kl_mail_send})


@app.route('/api/ausbilder/kl_mail/save_settings', methods=['POST'])
def ausbilder_kl_mail_save_settings():
    """Speichert die KL-Mail-Filter-/Optionen-Settings bulk. Erwartet alle
    Felder im Body (UI sendet sie zusammen, da auto-save per Toggle)."""
    import ausbilder_processor
    data = request.json or {}
    try:
        ausbilder_processor.save_kl_mail_settings(data)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True,
                    "kl_mail_settings": {
                        'kl_mail_respect_class_whitelist': ausbilder_processor.get_kl_mail_respect_class_whitelist(),
                        'kl_mail_respect_blacklist':       ausbilder_processor.get_kl_mail_respect_blacklist(),
                        'kl_mail_respect_firma_filter':    ausbilder_processor.get_kl_mail_respect_firma_filter(),
                        'kl_mail_include_stv_kl':          ausbilder_processor.get_kl_mail_include_stv_kl(),
                        'kl_mail_subject_suffix':          ausbilder_processor.get_kl_mail_subject_suffix(),
                    }})


# =========================================================================
# KL-Mail-Versand fuer den Erzieher-Workflow (3.3) — symmetrisch zur
# Ausbilder-Variante oben. Backend in erzieher_processor; hier nur Glue +
# Template-Loading aus email_settings.ini.
# =========================================================================

def _erz_kl_mail_load_templates():
    """Liest Subject- und Body-Template aus email_settings.ini. Defaults
    aus erzieher_processor als Fallback."""
    import erzieher_processor
    cfg = configparser.ConfigParser()
    safe_read_config(cfg, 'email_settings.ini')
    subject = cfg.get('Templates', 'subject_erzieher_kl_uebersicht',
                      fallback=erzieher_processor.DEFAULT_ERZ_KL_MAIL_SUBJECT)
    body    = cfg.get('Templates', 'body_erzieher_kl_uebersicht',
                      fallback=erzieher_processor.DEFAULT_ERZ_KL_MAIL_BODY)
    return subject, body


@app.route('/api/erzieher/kl_mail/preview', methods=['GET'])
def erzieher_kl_mail_preview():
    """Vorschau aller KL-Mails fuer den Erzieher-Workflow (Subject + Body-HTML
    + Empfaenger + Schueler-/Erzieher-/Telefon-Daten). KEIN Versand."""
    import erzieher_processor
    try:
        classes_by_name = _kl_mail_classes_by_name()  # reuse aus Ausbilder
        data = erzieher_processor.build_kl_mail_data(classes_by_name=classes_by_name)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Fehler beim Aufbau der KL-Mail-Daten: {e}"}), 500
    subject_tpl, body_tpl = _erz_kl_mail_load_templates()
    stand_date = datetime.now().strftime('%d.%m.%Y')
    suffix = (data.get('options_used') or {}).get('subject_suffix', '')
    out_classes = []
    for c in data['classes']:
        subject, body = erzieher_processor.render_kl_mail(
            c, subject_template=subject_tpl, body_template=body_tpl,
            stand_date=stand_date, subject_suffix=suffix)
        recipients = [c['kl_email']] if c['kl_email'] else []
        cc = [c['stv_kl_email']] if c.get('stv_kl_email') else []
        # Mail-Adress-Counts fuer die UI-Anzeige (im Vorschau-Listing).
        # 'alle' = ohne Vollj.-Filter, 'minderj' = mit. Die Verteiler sind seit
        # 3.3 in die Excel integriert (Sheets 'Mailverteiler (alle)' +
        # 'Mailverteiler (nur Minderj.)') — kein separater .txt-Anhang mehr.
        email_count_all     = len(erzieher_processor._collect_parent_emails(c, exclude_volljaehrige=False))
        email_count_minderj = len(erzieher_processor._collect_parent_emails(c, exclude_volljaehrige=True))
        out_classes.append({
            'klasse':         c['klasse'],
            'kl_name':        c['kl_name'],
            'kl_email':       c['kl_email'],
            'stv_kl_name':    c['stv_kl_name'],
            'stv_kl_email':   c['stv_kl_email'],
            'recipients':     recipients,
            'cc':             cc,
            'subject':        subject,
            'body_html':      body,
            'students_count': len(c['students']),
            'xlsx_filename':  f"KL_Mail_Erzieher_{erzieher_processor.safe_class_filename(c['klasse'])}.xlsx",
            'email_count_all':     email_count_all,
            'email_count_minderj': email_count_minderj,
        })
    return jsonify({
        'csv_path':     data['csv_path'],
        'anspr_path':   data['anspr_path'],
        'stand':        stand_date,
        'classes':      out_classes,
        'stats':        data['stats'],
        'options_used': data['options_used'],
        'kl_mail_settings': {
            'kl_mail_respect_class_whitelist': erzieher_processor.get_kl_mail_respect_class_whitelist(),
            'kl_mail_only_minor':              erzieher_processor.get_kl_mail_only_minor(),
            'kl_mail_include_stv_kl':          erzieher_processor.get_kl_mail_include_stv_kl(),
            'kl_mail_subject_suffix':          erzieher_processor.get_kl_mail_subject_suffix(),
        },
    })


@app.route('/api/erzieher/kl_mail/download_xlsx', methods=['GET'])
def erzieher_kl_mail_download_xlsx():
    """Excel-Anhang einer einzelnen Klasse zum Vorschau-Check (vor dem Versand).
    Query: ?klasse=DI24a"""
    import erzieher_processor
    from flask import send_file
    import io
    klasse = (request.args.get('klasse') or '').strip()
    if not klasse:
        return jsonify({"error": "Parameter 'klasse' fehlt."}), 400
    try:
        classes_by_name = _kl_mail_classes_by_name()
        data = erzieher_processor.build_kl_mail_data(classes_by_name=classes_by_name)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Fehler beim Aufbau der KL-Mail-Daten: {e}"}), 500
    target = next((c for c in data['classes'] if c['klasse'] == klasse), None)
    if not target:
        return jsonify({"error": f"Klasse {klasse} ist in den aktuellen Daten nicht enthalten."}), 404
    xlsx_bytes = erzieher_processor.build_kl_mail_xlsx(target, stand_date=datetime.now().strftime('%d.%m.%Y'))
    fname = f"KL_Mail_Erzieher_{erzieher_processor.safe_class_filename(klasse)}.xlsx"
    return send_file(
        io.BytesIO(xlsx_bytes),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=fname,
    )


last_erz_kl_mail_send = None


@app.route('/api/erzieher/kl_mail/send', methods=['POST'])
def erzieher_kl_mail_send():
    """Versendet die ausgewaehlten Erzieher-KL-Mails inkl. Excel-Anhang.
    Excel-Anhaenge zusaetzlich im erzieher_output_directory/KL_Mails/
    <Zeitstempel>/ als Versand-Nachweis."""
    import erzieher_processor
    global last_erz_kl_mail_send
    data_req = request.json or {}
    selected = data_req.get('classes')
    selected_set = set(selected) if isinstance(selected, list) else None
    try:
        classes_by_name = _kl_mail_classes_by_name()
        data = erzieher_processor.build_kl_mail_data(classes_by_name=classes_by_name)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Fehler beim Aufbau der KL-Mail-Daten: {e}"}), 500
    subject_tpl, body_tpl = _erz_kl_mail_load_templates()
    stand_date = datetime.now().strftime('%d.%m.%Y')
    suffix = (data.get('options_used') or {}).get('subject_suffix', '')
    out_dir = erzieher_processor.get_output_dir()
    kl_mail_dir = os.path.join(out_dir, 'KL_Mails', datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))
    os.makedirs(kl_mail_dir, exist_ok=True)

    sent = failed = skipped = 0
    details = []
    for c in data['classes']:
        if selected_set is not None and c['klasse'] not in selected_set:
            continue
        if not c['kl_email']:
            skipped += 1
            details.append({'klasse': c['klasse'], 'status': 'skipped',
                            'reason': 'Keine KL-E-Mail aufgeloesst.'})
            continue
        try:
            subject, body = erzieher_processor.render_kl_mail(
                c, subject_template=subject_tpl, body_template=body_tpl,
                stand_date=stand_date, subject_suffix=suffix)
            # Anhang: Excel (enthaelt seit 3.3 zusaetzlich die zwei Mailverteiler-
            # Sheets — kein separater .txt-Anhang mehr).
            xlsx_bytes = erzieher_processor.build_kl_mail_xlsx(c, stand_date=stand_date)
            xlsx_name  = f"KL_Mail_Erzieher_{erzieher_processor.safe_class_filename(c['klasse'])}.xlsx"
            xlsx_path  = os.path.join(kl_mail_dir, xlsx_name)
            with open(xlsx_path, 'wb') as f:
                f.write(xlsx_bytes)
            to_addrs = [c['kl_email']]
            if c.get('stv_kl_email'):
                to_addrs.append(c['stv_kl_email'])
            send_email(subject, body, to_addrs, attachment_path=xlsx_path)
            sent += 1
            details.append({'klasse': c['klasse'], 'status': 'sent',
                            'recipients': to_addrs, 'xlsx_path': xlsx_path,
                            'students_count': len(c['students'])})
        except Exception as e:
            failed += 1
            details.append({'klasse': c['klasse'], 'status': 'failed',
                            'error': str(e)})
    last_erz_kl_mail_send = {'sent': sent, 'failed': failed, 'skipped': skipped,
                             'xlsx_directory': kl_mail_dir, 'details': details}
    return jsonify({'success': True, **last_erz_kl_mail_send})


@app.route('/api/erzieher/kl_mail/save_settings', methods=['POST'])
def erzieher_kl_mail_save_settings():
    """Speichert die KL-Mail-Settings bulk (Filter-Booleans + Suffix)."""
    import erzieher_processor
    data = request.json or {}
    try:
        erzieher_processor.save_kl_mail_settings(data)
    except Exception as e:
        return jsonify({"error": f"Fehler beim Speichern: {e}"}), 500
    return jsonify({"success": True,
                    "kl_mail_settings": {
                        'kl_mail_respect_class_whitelist': erzieher_processor.get_kl_mail_respect_class_whitelist(),
                        'kl_mail_only_minor':              erzieher_processor.get_kl_mail_only_minor(),
                        'kl_mail_include_stv_kl':          erzieher_processor.get_kl_mail_include_stv_kl(),
                        'kl_mail_subject_suffix':          erzieher_processor.get_kl_mail_subject_suffix(),
                    }})


@app.route('/api/erzieher/update_kl_mail_template', methods=['POST'])
def erzieher_update_kl_mail_template():
    """Speichert NUR die Erzieher-KL-Mail-Vorlage in
    [Templates].subject_erzieher_kl_uebersicht / body_erzieher_kl_uebersicht.
    Symmetrisch zu /api/ausbilder/update_kl_mail_template (Begruendung dort)."""
    print_info("Aktualisiere Erzieher-KL-Mail-Vorlage in 'email_settings.ini'...")
    try:
        email_config = configparser.ConfigParser()
        safe_read_config(email_config, 'email_settings.ini')
        if not email_config.has_section('Templates'):
            email_config.add_section('Templates')
        subject = request.form.get('subject_erzieher_kl_uebersicht', '')
        body    = request.form.get('body_erzieher_kl_uebersicht', '')
        email_config['Templates']['subject_erzieher_kl_uebersicht'] = subject
        email_config['Templates']['body_erzieher_kl_uebersicht']    = body
        with open('email_settings.ini', 'w', encoding='utf-8-sig') as f:
            email_config.write(f)
        print_success("Erzieher-KL-Mail-Vorlage gespeichert.")
        return jsonify({'message': '✅ Erzieher-KL-Mail-Vorlage erfolgreich gespeichert!'})
    except Exception as e:
        msg = f"Fehler beim Speichern der Erzieher-KL-Mail-Vorlage: {e}"
        print_error(msg)
        return jsonify({'message': f'❌ {msg}'}), 500


# Route zum Generieren von Info-Mails aus den Feldänderungen des letzten Laufs
@app.route('/generate_info_mails', methods=['POST'])
def generate_info_mails():
    global info_changes_cache, generated_info_mails_cache
    generated_info_mails_cache = []

    data = request.json or {}
    selected_fields = [f.strip() for f in data.get('selected_fields', []) if f.strip()]

    if not info_changes_cache:
        return jsonify({"message": "ℹ️ Keine Änderungsdaten verfügbar. Bitte zuerst eine Verarbeitung durchführen."})
    if not selected_fields:
        return jsonify({"message": "⚠️ Keine Felder ausgewählt. Bitte mindestens ein Feld wählen."})

    print_info(f"🌐 Dashboard-Aktion: Info-Mails werden generiert (Felder: {', '.join(selected_fields)}).")
    notifications = create_info_notifications(info_changes_cache, selected_fields)

    if not notifications:
        return jsonify({"message": "ℹ️ Keine Feldänderungen für die gewählten Felder gefunden."})

    config = configparser.ConfigParser()
    safe_read_config(config, 'email_settings.ini')
    subject_tpl = config.get("Templates", "subject_info_notification", fallback=DEFAULT_TEMPLATES['info_notification']['subject'])
    body_tpl    = config.get("Templates", "body_info_notification",    fallback=DEFAULT_TEMPLATES['info_notification']['body'])

    for i, n in enumerate(notifications):
        try:
            subject = Template(subject_tpl).substitute(**n)
            body    = Template(body_tpl).substitute(**n)
        except KeyError as e:
            return jsonify({"message": f"⚠️ Fehlender Platzhalter {e} in der Info-Mail-Vorlage."}), 400

        recipients = [n.get('Klassenlehrkraft_1_Email', 'N/A'), n.get('Klassenlehrkraft_2_Email', 'N/A')]
        generated_info_mails_cache.append({
            'subject':                    subject,
            'body':                       body,
            'to':                         recipients,
            'notification_index':         i,
            'student':                    f"{n['Vorname']} {n['Nachname']}",
            'klasse':                     n['Klasse'],
            'felder':                     n['aenderungen_felder'],
            'nachteilsausgleich_details': n.get('nachteilsausgleich_details', ''),
        })

    print_success(f"{len(generated_info_mails_cache)} Info-Mail(s) generiert.")
    return jsonify({
        "message": f"✅ {len(generated_info_mails_cache)} Info-Mail(s) erfolgreich generiert.",
        "count":   len(generated_info_mails_cache),
        "emails":  generated_info_mails_cache,
    })

# Route zum Versenden der generierten Info-Mails
@app.route('/send_info_mails', methods=['POST'])
def send_info_mails():
    global generated_info_mails_cache
    if not generated_info_mails_cache:
        return jsonify({"message": "⚠️ Keine generierten Info-Mails zum Senden vorhanden."})

    data = request.json or {}
    indices = data.get('indices', None)
    if indices is not None:
        emails_to_send = [generated_info_mails_cache[i] for i in indices if 0 <= i < len(generated_info_mails_cache)]
    else:
        emails_to_send = generated_info_mails_cache

    import time
    print_info(f"Sende Info-Mails ({len(emails_to_send)} von {len(generated_info_mails_cache)})...")
    sent, skipped = 0, 0
    for email in emails_to_send:
        actual_recipients = [r for r in email['to'] if r and r.lower() != 'n/a']
        if not actual_recipients:
            print_warning(f"Überspringe Info-Mail für '{email['subject']}': keine gültigen Empfänger.")
            skipped += 1
            continue
        try:
            send_email(subject=email['subject'], body=email['body'], to_addresses=actual_recipients)
            print_success(f"✅ Info-Mail an {actual_recipients} gesendet.")
            sent += 1
            time.sleep(2)
        except Exception as e:
            print_error(f"❌ Fehler beim Senden der Info-Mail an {actual_recipients}: {str(e)}")

    print_success(f"Info-Mails abgeschlossen: {sent} gesendet, {skipped} übersprungen.")
    return jsonify({"message": f"📧 Info-Mails verarbeitet: {sent} gesendet, {skipped} übersprungen."})

# API-Route zum Durchführen eines Vorab-Checks der Import-Dateien
@app.route('/api/validate_imports', methods=['GET'])
def api_validate_imports():
    report = validate_imports()
    return jsonify(report)

# API-Route zum Prüfen, ob bereits E-Mails generiert wurden
@app.route('/api/check_emails_status', methods=['GET'])
def check_emails_status():
    global generated_emails_cache
    return jsonify({"has_emails": len(generated_emails_cache) > 0})

# --- Dashboard & Historie API ---

@app.route('/api/history/stats', methods=['GET'])
def get_history_stats():
    field_filter = request.args.get('field')
    hotspot_limit = request.args.get('hotspot_limit', 5)
    try:
        hotspot_limit = max(1, int(hotspot_limit))
    except (ValueError, TypeError):
        hotspot_limit = 5
    stats = history_manager.get_dashboard_stats(field_filter=field_filter, hotspot_limit=hotspot_limit)
    return jsonify(stats)

@app.route('/api/history/classes', methods=['GET'])
def get_history_classes():
    classes = history_manager.get_all_classes()
    return jsonify(classes)

@app.route('/api/history/class_stats/<class_name>', methods=['GET'])
def get_class_stats(class_name):
    print_info(f"🏫 Dashboard: Klassendetails abgerufen – {class_name}")
    stats = history_manager.get_class_analytics(class_name)
    return jsonify(stats)

@app.route('/api/history/export/excel', methods=['GET'])
def export_history_excel():
    import io
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from flask import send_file
    
    export_type = request.args.get('type') # 'student' or 'class'
    identifier = request.args.get('id')
    
    if not export_type or not identifier:
        return jsonify({"error": "Missing parameters"}), 400

    type_label = "Schüler" if export_type == 'student' else "Klasse"
    print_info(f"⬇️  Dashboard: Historienexport ({type_label}) wird erstellt – {identifier}")

    wb = Workbook()
    ws = wb.active
    ws.title = "Historie"
    
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    
    if export_type == 'student':
        data = history_manager.search_student_history(identifier)
        if not data: return "No data", 404
        student = data[0]['student']
        timeline = data[0]['timeline']
        ws.append(["Datum", "Feld", "Alter Wert", "Neuer Wert", "Quelle"])
        for t in timeline:
            ws.append([t['timestamp'], t['field'], t['old_value'], t['new_value'], t['file_b']])
        filename = f"Historie_{student['name']}_{identifier}.xlsx"
    else:
        stats = history_manager.get_class_analytics(identifier)
        timeline = stats['timeline']
        ws.append(["Datum", "Schüler Name", "Schüler ID", "Feld", "Alter Wert", "Neuer Wert"])
        for t in timeline:
            ws.append([t['timestamp'], t['name'], t['student_id'], t['field'], t['old_value'], t['new_value']])
        filename = f"Klassen_Historie_{identifier}.xlsx"

    # Spaltenbreite und Styling
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column].width = max_length + 3

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/history/sync', methods=['POST'])
def sync_history_classes():
    print_info("🌐 Dashboard-Aktion: Klassendaten-Synchronisierung mit aktuellen Schülerdaten gestartet.")
    import main
    success = main.sync_student_classes_from_latest()
    if success:
        print_success("Klassendaten-Synchronisierung abgeschlossen.")
        return jsonify({"success": True, "message": "Synchronisierung erfolgreich abgeschlossen."})
    else:
        print_warning("Klassendaten-Synchronisierung fehlgeschlagen oder keine Quelldaten gefunden.")
        return jsonify({"success": False, "message": "Synchronisierung fehlgeschlagen oder keine Quelldaten gefunden."}), 500

@app.route('/api/history/search', methods=['GET'])
def search_history():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    print_info(f"🔍 Dashboard: Schüleranalyse – Suche nach '{query}'")
    results = history_manager.search_student_history(query)
    return jsonify(results)

@app.route('/api/history/reset', methods=['POST'])
def reset_history():
    print_warning("🌐 Dashboard-Aktion: Historie-Datenbank wird vollständig zurückgesetzt!")
    history_manager.clear_history()
    print_success("Historie-Datenbank erfolgreich zurückgesetzt.")
    return jsonify({"message": "✅ Historie erfolgreich zurückgesetzt."})

@app.route('/api/history/reindex', methods=['POST'])
def reindex_history():
    config = configparser.ConfigParser()
    from utils import safe_read_config
    safe_read_config(config, 'settings.ini')
    log_dir = config.get("Directories", "log_directory", fallback="./Logs")
    count = history_manager.reindex_logs(log_dir)
    if count == 0:
        msg = "ℹ️ Keine neuen Log-Dateien gefunden (alle bereits importiert oder Verzeichnis leer)."
    else:
        msg = f"✅ {count} neue Log-Datei(en) erfolgreich in die Datenbank importiert."
    return jsonify({"message": msg})

# Route und Funktion zum Abrufen und Reinladen der Einstellungen des Einstellungs-Panels im WebEnd aus den verschiedenen .ini Dateien
@app.route('/load-settings', methods=['GET'])
def load_settings():
    settings = {}
    # settings.ini laden
    config = configparser.ConfigParser()
    safe_read_config(config, "settings.ini")
    for section in config.sections():
        if section not in settings:
            settings[section] = {}
        settings[section].update({key: config.get(section, key, fallback="") for key in config[section]})

    # email_settings.ini laden
    email_config = configparser.ConfigParser()
    safe_read_config(email_config, "email_settings.ini")
    for section in email_config.sections():
        if section not in settings:
            settings[section] = {}
        settings[section].update({key: email_config.get(section, key, fallback="") for key in email_config[section]})
    return jsonify(settings)

# Route und Funktion zum Speichern der geänderten Einstellungen aus dem Einstellungs-Panel im WebEnd in die verschiedenen .ini Dateien. 
# Hier wird zunächst sortiert, welche Daten in welche Datei gehören.
_SECTION_LABELS = {
    'ProcessingOptions': 'Verarbeitungsoptionen',
    'Directories':       'Verzeichnisse',
    'Email':             'E-Mail-Einstellungen',
    'OAuth':             'OAuth-Konfiguration',
    'Templates':         'E-Mail-Vorlagen',
    'Settings':          'Allgemeine Einstellungen',
    'InfoMailOptions':   'Info-Mail-Optionen',
}

@app.route('/save-settings', methods=['POST'])
def save_settings():
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

    # If directory change is disabled, remove the Directories section or ignore changes to directories
    if cli_args.get("no_directory_change", False):
        if 'Directories' in settings_ini_data:
            del settings_ini_data['Directories']

    # Einstellungen speichern
    if settings_ini_data:
        save_to_settings_ini(settings_ini_data)
    if email_settings_ini_data:
        save_to_email_settings_ini(email_settings_ini_data)

    # Zusammenfassung als rich Panel ausgeben
    all_saved = {**settings_ini_data, **email_settings_ini_data}
    summary = Table(box=None, show_header=False, pad_edge=False, padding=(0, 2, 0, 0))
    summary.add_column(style="cyan dim", no_wrap=True)
    summary.add_column(style="white")
    for section, values in all_saved.items():
        label = _SECTION_LABELS.get(section, section)
        summary.add_row(label, f"{len(values)} Feld(er)")
    _console.print(Panel(summary, title="[bold cyan]Einstellungen gespeichert[/]", border_style="cyan", padding=(0, 1)))

    # Verzeichnisse neu prüfen/anlegen, falls Pfade geändert wurden
    ensure_ini_files_exist()
    return jsonify({"status": "success"})


# Funktion zum Speichern der Einstellungen in die Datei 'settings.ini'
def save_to_settings_ini(settings):
    config = configparser.ConfigParser()
    safe_read_config(config, "settings.ini")
    for section, values in settings.items():
        if not config.has_section(section):
            config.add_section(section)
        for key, value in values.items():
            if "directory" in key:
                value = os.path.normpath(value)
            config.set(section, key, str(value))
    with open("settings.ini", "w", encoding="utf-8-sig") as configfile:
        config.write(configfile)

# Funktion zum Speichern der E-Mail-Einstellungen in 'email_settings.ini'
def save_to_email_settings_ini(settings):
    config = configparser.ConfigParser()
    safe_read_config(config, "email_settings.ini")
    existing_sections = config.sections()
    for section, values in settings.items():
        if section in existing_sections:
            for key, value in values.items():
                config.set(section, key, str(value))
        else:
            config[section] = values
    with open("email_settings.ini", "w", encoding="utf-8-sig") as configfile:
        config.write(configfile)


# Route und Funktion für den Durchsuchen-Button zur Angabe und Speicherung vollständiger absoluter Verzeichnispfade
@app.route('/process-directory', methods=['POST'])
def process_directory():
    print_info("Verarbeite ausgewähltes Verzeichnis...")
    directory_name = request.form.get("directoryName")
    if not directory_name:
        error_message = "Verzeichnisname ist erforderlich."
        print_error(f"Fehler: {error_message}")
        return jsonify({"error": error_message}), 400

    # Beispiel: Verarbeite das Verzeichnis (Anpassung an Ihr System erforderlich)
    full_path = os.path.abspath(directory_name)

    # Konvertiere Backslashes zu Forward Slashes für INI-Kompatibilität
    formatted_path = full_path.replace("\\", "/")

    return jsonify({"fullPath": formatted_path})

# Route und Funktion für den Durchsuchen-Button zur Angabe und Speicherung vollständiger absoluter Verzeichnispfade
@app.route('/select-directory', methods=['POST'])
def select_directory():
    print_info("Öffne Dateiauswahl zur Auswahl eines Verzeichnisses...")

    # Variable zum Speichern des Ergebnisses
    result = {'directory': None}
    
    def open_dialog():
        try:
            root = tk.Tk()
            root.withdraw()  # Hauptfenster ausblenden
            root.wm_attributes('-topmost', 1)  # Setzt das Fenster in den Vordergrund
            directory = filedialog.askdirectory()
            root.destroy()
            if directory:
                print_info(f"Verzeichnis ausgewählt: {directory}")
                result['directory'] = directory
            else:
                print_warning("Keine Auswahl getroffen.")
        except Exception as e:
            error_message = f"Fehler beim Öffnen der Dateiauswahl: {str(e)}"
            print_error(error_message)

    thread = threading.Thread(target=open_dialog)
    thread.start()
    thread.join()

    if result['directory']:
        return jsonify({"selected_directory": result['directory']})
    else:
        return jsonify({"selected_directory": None})


# Route und Funktion zum Abrufen der verfügbaren Kommandozeilenargumente mit ihren Beschreibungen, um die Argumente für den Befehl- und Verknüpfungsersteller bereitzustellen
@app.route('/get-arguments', methods=['GET'])
def get_arguments():
    # Liste der Argumente mit Beschreibungen
    arguments = [
        {"name": "--process", "description": "Führt den Hauptprozess aus: Verarbeitung des Schild-Exports, Erstellung von Warnungen sowie .log- und Excel-Logdateien."},
        {"name": "--generate-emails --send-emails", "description": "Generiert und sendet die Warn-E-Mails auf Grundlage der gespeicherten Einstellungen. Setzt voraus, dass --process zuvor ausgeführt wurde."},
        {"name": "--send-admin-warnings", "description": "Führt den Admin-Check durch und sendet das Ergebnis per E-Mail an die hinterlegte Admin-E-Mail-Adresse. Meldet fehlende Klassen oder Klassenlehrkräfte in den Stammdaten."},
        {"name": "--no-web", "description": "Verhindert das automatische Öffnen des Browsers beim Start. Der Server läuft weiterhin und ist manuell erreichbar."},
        {"name": "--send-log-email", "description": "Vergleicht Import-Dateien im konfigurierten Zeitrahmen (timeframe_hours in settings.ini) und sendet eine tabellarische HTML-Übersicht sowie den Excel-Änderungslog als Anhang an die Admin-E-Mail-Adresse."},
        {"name": "--skip-admin-warnings", "description": "Überspringt die Erstellung von Admin-Warnungen beim Start. Darf nicht mit --send-admin-warnings kombiniert werden."},
        {"name": "--no-log", "description": "Verhindert die Erstellung der .log-Textdateien."},
        {"name": "--no-xlsx", "description": "Verhindert die Erstellung der Excel-Logdateien."},
        {"name": "--no-directory-change", "description": "Sperrt die Verzeichnisverwaltung im WebEnd: Der Einstellungs-Tab wird ausgeblendet und Änderungen an Verzeichnissen werden serverseitig blockiert."},
        {"name": "--no-directory-change --enable-upload", "description": "Sperrt die Verzeichnisverwaltung und aktiviert zusätzlich den Datei-Upload in die konfigurierten Verzeichnisse. ⚠️ --enable-upload sollte ausschließlich zusammen mit --no-directory-change verwendet werden."},
        {"name": "--host", "description": "IP-Adresse, auf der der Server lauscht (Standard: 0.0.0.0 = alle Interfaces)."},
        {"name": "--port", "description": "Port, auf dem der Server lauscht (Standard: 5000)."},
    ]
    return jsonify({"success": True, "arguments": arguments})

# Route und Funktion zum Abrufen des Pfads der ausführbaren Datei
@app.route('/get-executable-path', methods=['GET'])
def get_executable_path():
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
    else:
        exe_path = os.path.abspath(sys.argv[0])
    return jsonify({"exePath": exe_path})

# Route und Funktion zum Erstellen einer Desktop-Verknüpfung für die Anwendung mit den angegebenen Argumenten
@app.route('/create-shortcut', methods=['POST'])
def create_shortcut():
    data = request.json
    exe_path = data.get('exePath')
    args = data.get('args', '')

    if not exe_path or not os.path.exists(exe_path):
        error_message = f"Pfad der ausführbaren Datei nicht gefunden: {exe_path}"
        print_error(f"Fehler: {error_message}")
        return jsonify({"success": False, "error": error_message})

    try:
        # COM-Bibliothek initialisieren
        import pythoncom
        pythoncom.CoInitialize()
        import winshell
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "Schild-WebUntis-Tool.lnk")

        # Verknüpfung erstellen
        with winshell.shortcut(shortcut_path) as shortcut:
            shortcut.path = exe_path
            shortcut.arguments = args
            shortcut.description = "Shortcut for Schild-WebUntis-Tool"
        print_success("Verknüpfung erfolgreich erstellt.")
        return jsonify({"success": True})
    except Exception as e:
        error_message = f"Fehler beim Erstellen der Verknüpfung: {str(e)}"
        print_error(error_message)
        return jsonify({"success": False, "error": error_message})
    finally:
        # COM-Bibliothek deinitialisieren
        pythoncom.CoUninitialize()
        print_info("COM-Bibliothek deinitialisiert.")

# Route und Funktion zum Hochladen von Dateien in die Quelldaten-Verzeichnisse 
@app.route('/upload-files', methods=['POST'])
def upload_files():
    print_info("Empfange Dateien zum Hochladen...")
    # Get directories from settings.ini
    config = configparser.ConfigParser()
    config.read("settings.ini", encoding='utf-8-sig')
    classes_dir = config.get("Directories", "classes_directory", fallback="./Klassendaten")
    teachers_dir = config.get("Directories", "teachers_directory", fallback="./Lehrerdaten")
    schildexport_dir = config.get("Directories", "schildexport_directory", fallback=".")

    # Create directories if they do not exist
    os.makedirs(classes_dir, exist_ok=True)
    os.makedirs(teachers_dir, exist_ok=True)
    os.makedirs(schildexport_dir, exist_ok=True)

    # Process uploaded files
    uploaded_files = request.files
    success_messages = []
    error_messages = []

    # Handle class data files
    class_data_files = request.files.getlist("class_data_files")
    for file in class_data_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if validate_class_data_file(file):
                # File is valid, save it
                save_path = os.path.join(classes_dir, filename)
                file.stream.seek(0)  # Ensure stream is at the beginning before saving
                file.save(save_path)
                success_messages.append(f"'{filename}' in Klassendaten hochgeladen.")
                print_info(f"Datei '{filename}' in '{classes_dir}' gespeichert.")
            else:
                error_messages.append(f"Ungültiges Dateiformat oder Inhalt: {file.filename}")
                print_warning(f"Ungültiges Dateiformat oder Inhalt: {file.filename}")
        else:
            error_messages.append(f"Ungültige Datei: {file.filename}")
            print_warning(f"Ungültige Datei: {file.filename}")

    # Handle teacher data files
    teacher_data_files = request.files.getlist("teacher_data_files")
    for file in teacher_data_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            if validate_teacher_data_file(file):
                # File is valid, save it
                save_path = os.path.join(teachers_dir, filename)
                file.stream.seek(0)  # Ensure stream is at the beginning before saving
                file.save(save_path)
                success_messages.append(f"'{filename}' in Lehrerdaten hochgeladen.")
                print_info(f"Datei '{filename}' in '{teachers_dir}' gespeichert.")
            else:
                error_messages.append(f"Ungültiges Dateiformat oder Inhalt: {file.filename}")
                print_warning(f"Ungültiges Dateiformat oder Inhalt: {file.filename}")
        else:
            error_messages.append(f"Ungültige Datei: {file.filename}")
            print_warning(f"Ungültige Datei: {file.filename}")

    # Schild-Export Dateien (falls notwendig, hier ohne zusätzliche Validierung)
    schild_export_files = request.files.getlist("schild_export_files")
    for file in schild_export_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(schildexport_dir, filename)
            file.save(save_path)
            success_messages.append(f"'{filename}' in Schild-Export hochgeladen.")
            print_info(f"Datei '{filename}' in '{schildexport_dir}' gespeichert.")
        else:
            error_messages.append(f"Ungültige Datei: {file.filename}")
            print_warning(f"Ungültige Datei: {file.filename}")

    # Prepare response message
    message = ""
    if success_messages:
        message += "Erfolgreich hochgeladen:\n" + "\n".join(success_messages)
    if error_messages:
        message += "\nFehler beim Hochladen:\n" + "\n".join(error_messages)

    return jsonify({"message": message})
# Funktion zum determinieren, welche Dateiformate erlaubt sind
def allowed_file(filename):
    # Allow only certain file extensions
    allowed_extensions = {'csv'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
#Funktion zum Überprüfen der Hochgeladenden Klassendatei auf das Vorhandensein aller erwarteter Spalten und des korrekten Seperators (;)
def validate_class_data_file(file):
    expected_columns = ["Auswahl", "", "Klasse", "Langname", "Alias", "Jahrgangsstufe", "Text", "Klassenlehrkraft", "Klassenlehrkraft", "Abteilung", "Von", "Bis"]
    expected_separator = ';'
    possible_separators = [',', ';', '\t']

    try:
        # Zurück zum Anfang der Datei
        file.stream.seek(0)
        # Erste Zeile (Header) einlesen
        first_line = file.stream.readline().decode('utf-8-sig').strip()

        # Zuerst mit dem erwarteten Separator testen
        headers = first_line.split(expected_separator)
        if headers == expected_columns:
            # Validierung erfolgreich
            file.stream.seek(0)  # Stream-Position zurücksetzen
            return True
        else:
            # Prüfen, ob ein anderer Separator das Problem verursacht
            for sep in possible_separators:
                if sep == expected_separator:
                    continue  # Bereits getestet
                headers = first_line.split(sep)
                if headers == expected_columns:
                    # Falscher Separator gefunden
                    print_warning(f"Falscher Separator in der Klassendatei '{file.filename}'. Erwartet: '{expected_separator}', gefunden: '{sep}'")
                    return False
            # Wenn kein passender Separator gefunden wurde
            print_warning(f"Ungültige Spalten oder Separator in der Klassendatei '{file.filename}'. Erwartete Spalten: {expected_columns}")
            return False
    except Exception as e:
        print_warning(f"Fehler beim Validieren der Klassendatei '{file.filename}': {e}")
        return False
#Funktion zum Überprüfen der Hochgeladenden Lehrkräftedatei auf das Vorhandensein aller erwarteter Spalten und des korrekten Seperators (Tab)
def validate_teacher_data_file(file):
    expected_columns = ["name", "longName", "foreName", "title", "birthDate", "pnr", "address.email", "address.phone", "address.mobile", "address.street", "address.postCode", "address.city"]
    expected_separator = '\t'
    possible_separators = [',', ';', '\t']

    try:
        file.stream.seek(0)
        first_line = file.stream.readline().decode('utf-8-sig').strip()

        headers = first_line.split(expected_separator)
        if headers == expected_columns:
            file.stream.seek(0)
            return True
        else:
            # Prüfen, ob ein anderer Separator das Problem verursacht
            for sep in possible_separators:
                if sep == expected_separator:
                    continue  # Bereits getestet
                headers = first_line.split(sep)
                if headers == expected_columns:
                    # Falscher Separator gefunden
                    print_warning(f"Falscher Separator in der Lehrerdaten-Datei '{file.filename}'. Erwartet: '{expected_separator}', gefunden: '{sep}'")
                    return False
            # Wenn kein passender Separator gefunden wurde
            print_warning(f"Ungültige Spalten oder Separator in der Lehrerdaten-Datei '{file.filename}'. Erwartete Spalten: {expected_columns}")
            return False
    except Exception as e:
        print_warning(f"Fehler beim Validieren der Lehrerdaten-Datei '{file.filename}': {e}")
        return False





# Funktion zum Öffnen des Standardbrowsers, automatisch auf die lokale URL, wird beim Start des Servers ausgeführt sofern nicht mit --no-web unterbunden.
def open_browser():
    host = cli_args.get("host", "127.0.0.1")
    port = cli_args.get("port", 5000)
    # Wenn der Host '0.0.0.0' ist, setzen wir ihn auf '127.0.0.1' für die Browser-URL
    if host == '0.0.0.0':
        display_host = '127.0.0.1'
    else:
        display_host = host
    url = f"http://{display_host}:{port}/"
    webbrowser.open_new(url)

# Globale Variable für CLI-Argumente
cli_args = {}

if __name__ == "__main__":
    # Banner beim Start ausgeben
    print_banner()

    ensure_ini_files_exist()

    # Parser für Kommandozeilenargumente
    parser = argparse.ArgumentParser(description="Command-line interface for processing data.")
    parser.add_argument('--process', action='store_true', help="Führt den Hauptprozess aus (Verarbeitung des Schild-Exports, Erstellungen von Warnungen, Erstellung der Log-Dateien).")
    parser.add_argument('--generate-emails', action='store_true', help="Generiert die Warn-E-Mails auf Grundlage der gespeicherten Einstellungen. (Davor ist --process erforderlich.)")
    parser.add_argument('--send-emails', action='store_true', help="Sendet die Warn-E-Mails auf Grundlage der gespeicherten Einstellungen. (Davor sind --process und --generate-emails erforderlich.)")
    parser.add_argument('--send-admin-warnings', action='store_true', help="Sendet Admin-Warnungen per E-Mail an die hinterlegte Admin E-Mail-Adresse, wenn im SchildExport Klassen oder Klassenlehrkräfte vorkommen, die in den Klassen- oder Lehrkraftdaten fehlen.")
    parser.add_argument('--no-web', action='store_true', help="Verhindert das Öffnen des Web-Interfaces.")
    parser.add_argument('--skip-admin-warnings', action='store_true', help="Überspringt die Erstellung von Admin-Warnungen. (Darf nicht mit --send admin-warnings kombiniert werden.)")
    parser.add_argument('--class-change-recipients', type=str, choices=['old', 'new', 'both'], help="Legt den Empfänger der Klassenwechsel-Warnung fest (old, new oder both). Überschreibt die ini-Konfiguration.")
    parser.add_argument('--no-log', action='store_true', help="Verhindert die Erstellung der .log Logdateien.")
    parser.add_argument('--no-xlsx', action='store_true', help="Verhindert die Erstellung der Excel Logdateien. (Darf nicht mit --send-log-email kombiniert werden.)")
    parser.add_argument('--send-log-email', action='store_true', help="Sendet eine tabellarische Übersicht (html) und die den Excel-Änderungslog (im Anhang) für einen definierten Zeitraum an die hinterlegte Admin E-Mail-Adresse.")
    parser.add_argument('--no-directory-change', action='store_true', help="Verhindert, dass Verzeichnisse über das WebEnd geändert werden können. Dazu wird der Tab in den Einstellungen entfernt und im BackEnd Funktionen blockiert.")
    parser.add_argument('--enable-upload', action='store_true', help="Ermöglicht einen Upload von Dateien in die Verzeichnisse.\n⚠️ Aus Sicherheitsgründen sollte --enable-upload niemals ohne --no-directory-change verwendet werden!⚠️")
    parser.add_argument('--host', type=str, default='0.0.0.0', help="IP-Adresse, auf der der Server laufen soll (Standard: 0.0.0.0)")
    parser.add_argument('--port', type=int, default=5000, help="Port, auf dem der Server laufen soll (Standard: 5000)")

    args = parser.parse_args()

    # Speichern der CLI-Argumente in der globalen Variable
    cli_args = {
        "process": args.process,
        "generate_emails": args.generate_emails,
        "send_emails": args.send_emails,
        "send_admin_warnings": args.send_admin_warnings,
        "no_web": args.no_web,
        "skip_admin_warnings": args.skip_admin_warnings,
        "class_change_recipients": args.class_change_recipients,
        "no_log": args.no_log,
        "no_xlsx": args.no_xlsx,
        "send_log_email": args.send_log_email,
        "no_directory_change": args.no_directory_change,
        "enable_upload": args.enable_upload,
        "host": args.host,
        "port": args.port,
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
        print_info("Starte Datenverarbeitung...")
        # Übergabe der Argumente no_log und no_xlsx an process_data
        warnings_cache = process_data(
            no_log=args.no_log,
            no_xlsx=args.no_xlsx
        )
        print_success("Datenverarbeitung erfolgreich abgeschlossen.")

    # Timeframe-Import vergleichen und ggf. E-Mail versenden
    if args.send_log_email:
        print_info("Vergleiche Import-Dateien basierend auf dem definierten Zeitrahmen...")
        compare_timeframe_imports(
            no_log=args.no_log,
            no_xlsx=args.no_xlsx
        )
        print_success("Vergleich abgeschlossen.")

    # E-Mails generieren
    if args.generate_emails:
        if not warnings_cache:
            print_info("Es sind zum Generieren von E-Mails keine Warnungen im Cache vorhanden.")
        else:
            print_info("Generiere E-Mails...")
            from flask import current_app
            with app.app_context():
                generate_emails()
            print_success("E-Mails erfolgreich generiert.")

    # E-Mails senden
    if args.send_emails:
        if not generated_emails_cache:
            print_info("Es sind keine generierten E-Mails zum Senden im Cache vorhanden.")
        else:
            print_info("Sende E-Mails...")
            for email in generated_emails_cache:
                send_email(email['subject'], email['body'], email['to'])
            print_success("E-Mails erfolgreich gesendet.")


    # Prüfen, ob eine rein aufgabenspezifische CLI-Zugehörigkeit vorliegt und der Server übergangen werden soll.
    if any([args.process, args.generate_emails, args.send_emails, args.send_admin_warnings, args.send_log_email]):
        print_success("CLI-Verarbeitung abgeschlossen. Beende das Skript.")
        sys.exit(0)

    # Starten des WSGI-Servers mit Waitress
    if not args.no_web:
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.start()

    try:
        # Initialer Check der Historie
        import sqlite3
        import history_manager
        import configparser
        conn = sqlite3.connect('history.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comparisons'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM comparisons")
            count = cursor.fetchone()[0]
            if count == 0:
                print_info("✨ Historie ist leer. Starte automatische Indizierung vorhandener Logs...")
                config = configparser.ConfigParser()
                from utils import safe_read_config
                safe_read_config(config, 'settings.ini')
                log_dir = config.get("Directories", "log_directory", fallback="./Logs")
                reindexed = history_manager.reindex_logs(log_dir)
                if reindexed > 0:
                    print_success(f"✅ {reindexed} historische Log-Dateien wurden automatisch indiziert.")
            else:
                print_success(f"📦 Historien-Datenbank bereit ({count} Vergleiche geladen).")
        conn.close()
    except Exception as e:
        print_warning(f"Hinweis zur Historie-Initialisierung: {e}")

    try:
        import socket
        host = cli_args.get("host", "0.0.0.0")
        port = cli_args.get("port", 5000)
        # Tatsächliche IP ermitteln
        try:
            display_ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            display_ip = "127.0.0.1"
        if host not in ("0.0.0.0", ""):
            display_ip = host
        print_success(f"Server gestartet – erreichbar unter http://{display_ip}:{port}")
        # Waitress-Logger unterdrücken
        logging.getLogger("waitress").setLevel(logging.ERROR)
        logging.getLogger("waitress.queue").setLevel(logging.ERROR)
        serve(app, host=host, port=port, threads=8)
    except Exception as e:
        print_error(f"Fehler beim Starten des WSGI-Servers: {e}")



__all__ = ['admin_warnings_cache','admin_warnings']





