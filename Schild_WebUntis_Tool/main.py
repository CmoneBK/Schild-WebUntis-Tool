import os
import csv
import configparser
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import colorama
from colorama import Fore, Style, init
import threading

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

def print_warningtext(message):
    thread_safe_print(Fore.MAGENTA, f"👾 {message}")

def print_success(message):
    thread_safe_print(Fore.GREEN, f"✅ {message}")

def print_info(message):
    thread_safe_print(Fore.CYAN, f"ℹ️ {message}")

def print_creation(message):
    thread_safe_print(Fore.WHITE, f"✨ {message}")

def run(use_abschlussdatum=True, create_second_file=True,
        warn_entlassdatum=True, warn_aufnahmedatum=True, warn_klassenwechsel=True, warn_new_students=True,
        no_log=False, no_xlsx=False, create_class_size_file=False, enable_attestpflicht_column=False):
    # Hauptfunktion zur Verarbeitung der Daten und Generierung von Warnungen
    print_info("Starte Hauptverarbeitung mit den folgenden Optionen:")
    print_info(f"  Verwende Abschlussdatum: {use_abschlussdatum}")
    print_info(f"  Erstelle zweite Datei: {create_second_file}")
    print_info(f"  Erstelle Klassengrößen-Auswertung: {create_class_size_file}")
    print_info(f"  Attestpflicht-Spalte hinzufügen: {enable_attestpflicht_column}")
    print_info(f"  Warnung für Entlassdatum: {warn_entlassdatum}")
    print_info(f"  Warnung für Aufnahmedatum: {warn_aufnahmedatum}")
    print_info(f"  Warnung für Klassenwechsel: {warn_klassenwechsel}")
    print_info(f"  Warnung für neue Schüler: {warn_new_students}")
    print_info(f"  Log-Dateien erstellen: {'Nein' if no_log else 'Ja'}")
    print_info(f"  Excel-Dateien erstellen: {'Nein' if no_xlsx else 'Ja'}")

    warnings = []  # Liste für Entlassdatum-Warnungen
    class_change_warnings = []  # Liste für Klassenwechsel-Warnungen
    admission_date_warnings = []  # Liste für Aufnahmedatum-Warnungen
    new_student_warnings = []

    # Konfigurationsdatei einlesen
    print_info("Lese 'settings.ini' Konfigurationsdatei ein...")
    config = configparser.ConfigParser()
    config.read('settings.ini')
    classes_dir = config.get('Directories', 'classes_directory')
    teachers_dir = config.get('Directories', 'teachers_directory')
    print_info(f"Klassendatenverzeichnis: {classes_dir}")
    print_info(f"Lehrerdatenverzeichnis: {teachers_dir}")

    # Daten einlesen und verarbeiten
    print_info("Lese Klassen- und Schülerdaten ein...")
    classes_by_name = read_classes(classes_dir, teachers_dir)
    output_data_students, students_by_id = read_students(use_abschlussdatum)

    # Warnungen erstellen basierend auf der Benutzerauswahl
    if warn_entlassdatum:
        warnings = create_warnings(classes_by_name, students_by_id)
    if warn_klassenwechsel:
        class_change_warnings = create_class_change_warnings(classes_by_name, students_by_id)
    if warn_aufnahmedatum:
        admission_date_warnings = create_admission_date_warnings(classes_by_name, students_by_id)
    if warn_new_students:
        new_student_warnings = create_new_student_warnings(classes_by_name, students_by_id)

    # Alle Warnungen zusammenführen
    all_warnings = warnings + class_change_warnings + admission_date_warnings+ new_student_warnings

    # Separate Konsolenausgabe der verschiedenen Warnungen
    print_warning("==================== ENTLASSDATUM WARNUNGEN ====================")
    print_warnings(warnings)
    print_warning("==================== KLASSENWECHSEL WARNUNGEN ==================")
    print_warnings(class_change_warnings)
    print_warning("==================== AUFNAHMEDATUM WARNUNGEN ===================")
    print_warnings(admission_date_warnings)
    print_warning("==================== Neue SCHÜLER WARNUNGEN ===================")
    print_warnings(new_student_warnings)

    # Dateien speichern
    save_files(output_data_students, all_warnings, create_second_file, enable_attestpflicht_column)

    if create_class_size_file:
     create_class_sizes_file(students_by_id)

    # Vergleiche die letzten beiden Dateien
    print_info("Initialisiere Log-Erstellung")
    compare_latest_imports(no_log=no_log, no_xlsx=no_xlsx)

    print_success("Hauptverarbeitung abgeschlossen.")
    return all_warnings

def get_directory(key, default=None):
    # Hilfsfunktion zum Abrufen von Verzeichnispfaden aus der Konfigurationsdatei
    config = configparser.ConfigParser()
    config.read('settings.ini')
    return config.get('Directories', key, fallback=default)


def read_csv(file_path):
    # Funktion zum Einlesen einer CSV-Datei und Rückgabe eines Dictionaries mit den Daten
    print_info(f"Lese CSV-Datei: {file_path}")
    data = {}
    try:
        with open(file_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                # Entfernt unsichtbare Zeichen und Leerzeichen
                cleaned_row = {key: value.strip().replace('\u00a0', '') for key, value in row.items()}
                student_id = cleaned_row.get('Interne ID-Nummer')  # oder anderer eindeutiger Schlüssel
                if student_id:
                    data[student_id] = cleaned_row
        print_info(f"CSV-Datei erfolgreich eingelesen. Anzahl Datensätze: {len(data)}")
    except Exception as e:
        print_error(f"Fehler beim Lesen der Datei {file_path}: {e}")
    return data


def compare_latest_imports(no_log=False, no_xlsx=False):
    # Funktion zum Vergleichen der neuesten Importdateien und Erfassen von Änderungen
    print_info("Prüfe Einstellungen zu gewünschten Log-Dateien...")
    # Überspringen der Erstellung je nach Flags
    if no_log:
        print_info("Log-Datei-Erstellung wurde deaktiviert.")
    if no_xlsx:
        print_info("Excel-Datei-Erstellung wurde deaktiviert.")
    # Abbruch, wenn sowohl no_log als auch no_xlsx aktiviert sind
    if no_log and no_xlsx:
        print_warning("Vergleich abgebrochen: Sowohl Log- als auch Excel-Datei-Erstellung wurden deaktiviert.")
        return

    # Verzeichnisse definieren
    import_dir = get_directory('import_directory', './WebUntis Importe')
    config = configparser.ConfigParser()
    config.read("settings.ini")

    # Verzeichnisse für Log- und Excel-Dateien aus der settings.ini lesen
    log_dir = config.get("Directories", "log_directory", fallback="./Logs")
    xlsx_dir = config.get("Directories", "xlsx_directory", fallback="./ExcelExports")

    # Sicherstellen, dass die Verzeichnisse existieren
    os.makedirs(import_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(xlsx_dir, exist_ok=True)

    # Neueste zwei Dateien im Importverzeichnis finden
    print_info("Suchen der zwei neuesten Dateien im Importverzeichnis...")
    csv_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if len(csv_files) < 2:
        print_warning(f"Nicht genügend Dateien im Verzeichnis {import_dir} vorhanden, um einen Vergleich durchzuführen. Abbruch der Log-Erstellung.")
        return

    # Nach Erstellungszeit sortieren und die letzten beiden Dateien auswählen
    csv_files.sort(key=lambda f: os.path.getctime(os.path.join(import_dir, f)), reverse=True)
    latest_file = csv_files[0]
    previous_file = csv_files[1]

    print_info(f"Vergleiche Dateien:\n {previous_file} und\n {latest_file}")

    # Dateien einlesen
    previous_data = read_csv(os.path.join(import_dir, previous_file))
    latest_data = read_csv(os.path.join(import_dir, latest_file))

    # Änderungen erfassen
    changes = []
    for student_id, latest_student in latest_data.items():
        previous_student = previous_data.get(student_id)
        if not previous_student:
            continue  # Neuer Schüler, keine Änderung

        row_changed = False
        updated_row = latest_student.copy()
        change_details = {}
        for field, new_value in latest_student.items():
            old_value = previous_student.get(field, '').strip().replace('\u00a0', '')
            new_value = new_value.strip().replace('\u00a0', '')

            if old_value != new_value:
                row_changed = True
                updated_row[field] = f"{old_value} -> {new_value}"
                change_details[field] = {"old": old_value, "new": new_value}

        if row_changed:
            changes.append({"student_id": student_id, "name": f"{latest_student.get('Vorname', '')} {latest_student.get('Nachname', '')}", "changes": change_details, "row": updated_row})
    if not changes:
        print_warning("Keine Änderungen zwischen den Dateien festgestellt. Abbruch der Log-Erstellung.")
        print_warningtext("Prüfen Sie, ob Sie die selbe Schild-Export Datei zwei mal verarbeitet haben.")
        return

    # Datum und Uhrzeit für Dateinamen
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f'ÄnderungsLog_{timestamp}.log')
    excel_file_path = os.path.join(xlsx_dir, f'ÄnderungsLog_{timestamp}.xlsx')

    # Log-Datei erstellen
    if not no_log:
        print_creation(f"Erstelle Log-Datei: {log_file_path}")
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            for change in changes:
                log_file.write(f"Schüler: {change['name']} (ID: {change['student_id']})\n")
                for field, values in change['changes'].items():
                    log_file.write(f"  {field}: {values['old']} -> {values['new']}\n")
                log_file.write("\n")
        print_success(".log Log-Datei erfolgreich erstellt.")

    # Excel-Datei erstellen
    if not no_xlsx and changes:
        print_creation(f"Erstelle Excel-Datei: {excel_file_path}")
        wb = Workbook()
        ws = wb.active
        ws.title = "Änderungen"

        # Kopfzeile schreiben
        headers = list(changes[0]["row"].keys())
        ws.append(headers)

        # Daten schreiben
        for change in changes:
            row = []
            for header in headers:
                value = change["row"].get(header, "")
                row.append(value)
            ws.append(row)

        # Spaltenbreite automatisch anpassen
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter  # Hol den Buchstaben der Spalte
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = max_length + 2
            ws.column_dimensions[column].width = adjusted_width

        # Änderungen farblich hervorheben
        red_fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                if "->" in str(cell.value):
                    cell.fill = red_fill

        wb.save(excel_file_path)
        print_success("Excel-Log-Datei erfolgreich erstellt.")
    print_success("Vergleich der neuesten Importdateien abgeschlossen.")

from smtp import send_email
def compare_timeframe_imports(no_log=False, no_xlsx=False):
    # Funktion zum Vergleichen von Importdateien innerhalb eines bestimmten Zeitrahmens und Senden von E-Mails bei Änderungen
    print_info("Starte Vergleich der Importdateien im definierten Zeitrahmen...")

    # Verzeichnisse und Einstellungen
    config = configparser.ConfigParser()
    config.read("settings.ini")
    email_config = configparser.ConfigParser()
    email_config.read("email_settings.ini")

    timeframe_hours = config.getint("ProcessingOptions", "timeframe_hours", fallback=24)
    import_dir = config.get("Directories", "import_directory", fallback="./WebUntis Importe")
    log_dir = config.get("Directories", "log_directory", fallback="./Logs")
    xlsx_dir = config.get("Directories", "xlsx_directory", fallback="./ExcelExports")
    admin_email = email_config.get("Email", "admin_email", fallback=None)

    if not admin_email:
        print_warning("Keine Admin-E-Mail-Adresse in der email_settings.ini definiert. E-Mail-Versand deaktiviert.")
        send_log_email = False

    os.makedirs(import_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(xlsx_dir, exist_ok=True)

    # Überprüfung des letzten E-Mail-Versands
    print_info(f"Überprüfe, ob in den letzten {timeframe_hours} Stunden schon eine Log-E-Mail versendet wurde...")
    email_log_path = os.path.join(log_dir, "last_email_sent.log")
    if os.path.exists(email_log_path):
        with open(email_log_path, "r") as email_log:
            last_email_time = datetime.strptime(email_log.read().strip(), "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_email_time < timedelta(hours=timeframe_hours):
            print_warning("Eine E-Mail wurde bereits innerhalb des definierten Zeitrahmens gesendet. Kein neuer Versand.")
            return
    else:
        last_email_time = None


    cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)
    # Dateien im Zeitrahmen finden
    csv_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]

    # Dateien sortieren
    csv_files.sort(key=lambda f: os.path.getctime(os.path.join(import_dir, f)), reverse=True)

    # Datei suchen, die älter als der Zeitrahmen ist
    print_info(f"Suche neueste WebUntis-Import-Datei mit einem Mintestalter von {timeframe_hours} Stunden.")
    previous_file = next(
        (f for f in csv_files if datetime.fromtimestamp(os.path.getmtime(os.path.join(import_dir, f))) < cutoff_time),
        None
    )

    # Neueste Datei finden
    print_info(f"Suche neuste WebUntis-Import-Datei.")
    latest_file = csv_files[0] if csv_files else None

    if not latest_file:
        print_warning("Keine Dateien gefunden.")
        return

    if not previous_file:
        print_warning(f"Keine Dateien gefunden, die älter als {timeframe_hours} Stunden sind.")
        return

    print_info(f"Vergleiche Dateien:\n {previous_file} und\n {latest_file}")

    previous_data = read_csv(os.path.join(import_dir, previous_file)) if previous_file else {}
    latest_data = read_csv(os.path.join(import_dir, latest_file))

    changes = []
    for student_id, latest_student in latest_data.items():
        previous_student = previous_data.get(student_id)
        if not previous_student:
            continue

        row_changed = False
        updated_row = latest_student.copy()
        change_details = {}
        for field, new_value in latest_student.items():
            old_value = previous_student.get(field, '').strip()
            new_value = new_value.strip()

            if old_value != new_value:
                row_changed = True
                updated_row[field] = f"{old_value} -> {new_value}"
                change_details[field] = {"old": old_value, "new": new_value}

        if row_changed:
            changes.append({"student_id": student_id, "name": f"{latest_student.get('Vorname', '')} {latest_student.get('Nachname', '')}", "changes": change_details, "row": updated_row})

    if not changes:
        print_warning("Keine Änderungen festgestellt.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f'ÄnderungsLog_{timestamp}.log')
    excel_file_path = os.path.join(xlsx_dir, f'ÄnderungsLog_{timestamp}.xlsx')

    # Log-Datei erstellen
    if not no_log:
        print_creation(f"Erstelle Log-Datei: {log_file_path}")
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            for change in changes:
                log_file.write(f"Schüler: {change['name']} (ID: {change['student_id']})\n")
                for field, values in change['changes'].items():
                    log_file.write(f"  {field}: {values['old']} -> {values['new']}\n")
                log_file.write("\n")
        print_success(".log Log-Datei erfolgreich erstellt.")

    # Excel-Datei erstellen
    if not no_xlsx:
        print_creation(f"Erstelle Excel-Datei: {excel_file_path}")
        wb = Workbook()
        ws = wb.active
        ws.title = "Änderungen"

        headers = list(changes[0]["row"].keys())
        ws.append(headers)

        for change in changes:
            row = []
            for header in headers:
                value = change["row"].get(header, "")
                row.append(value)
            ws.append(row)

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            ws.column_dimensions[column].width = max_length + 2

        red_fill = PatternFill(start_color="FFCCCC", end_color="FFCCCC", fill_type="solid")
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                if "->" in str(cell.value):
                    cell.fill = red_fill

        wb.save(excel_file_path)
        print_success("Excel-Log-Datei erfolgreich erstellt.")

    # E-Mail mit den Änderungen senden
    print_info(f"Erstelle und sende E-Mails mit HTML-Tabelle und Excel-Datei im Anhang...")
    if changes:
        subject = "Änderungen im WebUntis Import"
        body = f"""
        <p>Die Dateien <strong>{previous_file}</strong> und <strong>{latest_file}</strong> wurden verglichen.</p>
        <p>Folgende Änderungen wurden festgestellt:</p>
        <table border="1" cellpadding="5" cellspacing="0" style="border-collapse: collapse; width: 100%;">
            <thead>
                <tr>
                    {"".join(f"<th>{header}</th>" for header in headers)}
                </tr>
            </thead>
            <tbody>
        """

        # Generiere die Tabelle mit den Änderungen
        for change in changes:
            body += "<tr>"
            for header in headers:
                value = change["row"].get(header, "")
                if "->" in value:  # Markiere Zellen mit Änderungen
                    body += f"<td style='background-color: #FFCCCC;'>{value}</td>"
                else:
                    body += f"<td>{value}</td>"
            body += "</tr>"

        body += """
            </tbody>
        </table>
        <p>Die vollständige Excel-Datei mit den Änderungen ist im Anhang enthalten.</p>
        """

        try:
            send_email(
                subject=subject,
                body=body,
                to_addresses=[admin_email],
                attachment_path=excel_file_path
            )
            print_success(f"E-Mail mit Änderungen an {admin_email} gesendet.")

            # Zeitstempel des E-Mail-Versands speichern
            print_info(f"Schreiben des Zeitstempels des Versands in {email_log_path} zur Verhinderung weiter E-Mails innerhalb der nächsten {timeframe_hours} Stunden...")
            with open(email_log_path, "w") as email_log:
                email_log.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            print_success(f"Zeit [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]notiert.")
        except Exception as e:
            print_error(f"Fehler beim Senden der E-Mail: {e}")


def read_classes(classes_dir, teachers_dir, return_teachers=False):
    # Funktion zum Einlesen der Klassen- und Lehrerdaten
    print_info("Lese Klassen- und Lehrerdaten ein...")

    # Prüfen, ob der Ordner für Klassendaten existiert
    if not os.path.exists(classes_dir):
        print_warning(f"Warnung: Der Ordner '{classes_dir}' existiert nicht.")
        dummy_classes = {
            "dummy_class_1": {
                "Klassenlehrkraft_1": "Max Muster",
                "Klassenlehrkraft_1_Email": "max.muster@example.com",
                "Klassenlehrkraft_2": "Erika Beispiel",
                "Klassenlehrkraft_2_Email": "erika.beispiel@example.com",
            }
        }
        return (dummy_classes, {}) if return_teachers else dummy_classes

    # Neueste Klassen-CSV-Datei finden
    class_csv_files = [f for f in os.listdir(classes_dir) if f.endswith('.csv')]
    if not class_csv_files:
        print_warning(f"Warnung: Keine Klassen-CSV-Dateien im Ordner '{classes_dir}' gefunden.")
        dummy_classes = {
            "dummy_class_1": {
                "Klassenlehrkraft_1": "Max Muster",
                "Klassenlehrkraft_1_Email": "max.muster@example.com",
                "Klassenlehrkraft_2": "Erika Beispiel",
                "Klassenlehrkraft_2_Email": "erika.beispiel@example.com",
            }
        }
        return (dummy_classes, {}) if return_teachers else dummy_classes

    newest_class_file = max(class_csv_files, key=lambda f: os.path.getctime(os.path.join(classes_dir, f)))
    print_info(f"Verwende Klassen-Datei: {newest_class_file}")

    # Prüfen, ob der Ordner für Lehrerdaten existiert
    if not os.path.exists(teachers_dir):
        print_warning(f"Warnung: Der Ordner '{teachers_dir}' existiert nicht.")
        teachers = {
            "dummy_teacher_1": {"email": "lehrer1@example.com", "forename": "Anna", "longname": "Lehrkraft"},
            "dummy_teacher_2": {"email": "lehrer2@example.com", "forename": "Tom", "longname": "Muster"},
        }
    else:
        # Neueste Lehrkräfte-CSV-Datei finden
        teacher_csv_files = [f for f in os.listdir(teachers_dir) if f.endswith('.csv')]
        if not teacher_csv_files:
            print_warning(f"Warnung: Keine Lehrkräfte-CSV-Dateien im Ordner '{teachers_dir}' gefunden.")
            teachers = {
                "dummy_teacher_1": {"email": "lehrer1@example.com", "forename": "Anna", "longname": "Lehrkraft"},
                "dummy_teacher_2": {"email": "lehrer2@example.com", "forename": "Tom", "longname": "Muster"},
            }
        else:
            newest_teacher_file = max(teacher_csv_files, key=lambda f: os.path.getctime(os.path.join(teachers_dir, f)))
            print_info(f"Verwende Lehrkräfte-Datei: {newest_teacher_file}")

            # Lehrkräfte in ein Dictionary einlesen
            teachers = {}
            try:
                with open(os.path.join(teachers_dir, newest_teacher_file), 'r', newline='', encoding='utf-8-sig') as teacher_file:
                    teacher_reader = csv.DictReader(teacher_file, delimiter='\t')
                    for row in teacher_reader:
                        teacher_name = row['name']
                        teachers[teacher_name] = {
                            'email': row.get('address.email', ''),
                            'forename': row.get('foreName', ''),
                            'longname': row.get('longName', '')
                        }
            except Exception as e:
                print_error(f"Fehler beim Einlesen der Lehrkräfte-Datei: {e}")
                teachers = {}  # Fallback auf leere Lehrer-Daten

    # Klassen-CSV-Datei einlesen und Lehrkräfte-Emails zuordnen
    print_info("Verarbeite Klassen-CSV-Datei und ordne Lehrkräfte zu...")
    classes_by_name = {}
    with open(os.path.join(classes_dir, newest_class_file), 'r', newline='', encoding='utf-8-sig') as class_file:
        class_reader = csv.reader(class_file, delimiter=';')
        header = next(class_reader)

        # Die beiden Klassenlehrkraft-Spalten anhand ihrer Position (8. und 9. Spalte) identifizieren
        class_teacher_columns = [7, 8]  # 0-basierter Index: 8. und 9. Spalte

        for row in class_reader:
            emails = [teachers.get(row[idx], 'Keine E-Mail gefunden') for idx in class_teacher_columns]
            row.extend(emails)

            # Klasseninformationen speichern
            classes_by_name[row[2].strip().lower()] = {
                'Klassenlehrkraft_1': f"{teachers.get(row[7], {}).get('forename', '')} {teachers.get(row[7], {}).get('longname', '')}",
                'Klassenlehrkraft_1_Email': teachers.get(row[7], {}).get('email', 'Keine E-Mail gefunden'),
                'Klassenlehrkraft_2': f"{teachers.get(row[8], {}).get('forename', '')} {teachers.get(row[8], {}).get('longname', '')}",
                'Klassenlehrkraft_2_Email': teachers.get(row[8], {}).get('email', 'Keine E-Mail gefunden')
            }
    print_success("Klassen- und Lehrerdaten erfolgreich eingelesen.")
    return (classes_by_name, teachers) if return_teachers else classes_by_name


def read_students(use_abschlussdatum):
    # Funktion zum Einlesen der Schülerdaten aus der neuesten CSV-Datei im aktuellen Verzeichnis
    print_info("Lese Schülerdaten ein...")
    import_dir = get_directory('import_directory', './WebUntis Importe')
    # Überprüfen, ob das Importverzeichnis existiert, falls nicht, erstellen
    if not os.path.exists(import_dir):
        os.makedirs(import_dir)
        print_success(f"Importverzeichnis '{import_dir}' wurde erstellt.")

    # Überprüfen, ob .csv Dateien im aktuellen Verzeichnis vorhanden sind
    schildexport_dir = get_directory('schildexport_directory', default='.')
    if schildexport_dir in ('.', '', None):
        schildexport_dir = os.getcwd()
    csv_files = [f for f in os.listdir(schildexport_dir) if f.endswith('.csv')]

    if not csv_files:
        print_error("Keine CSV-Dateien im aktuellen Verzeichnis gefunden.")
        return [], {}

    # Neueste CSV-Datei bestimmen
    newest_file = max(csv_files, key=os.path.getctime)

    # Definierte Spalten, die gefiltert werden sollen
    columns_to_filter = ['Interne ID-Nummer', 'Nachname', 'Vorname', 'Geburtsdatum', 'Klasse', 'Klassenlehrer', 'Geschlecht', 'Entlassdatum', 'Aufnahmedatum', 'vorauss. Abschlussdatum', 'Schulpflicht erfüllt', 'Volljährig', 'E-Mail (privat)', 'Telefon-Nr.', 'Fax-Nr.', 'Straße', 'Postleitzahl', 'Ortsname']
    # Spalten für die Ausgabe
    output_columns = ['Interne ID-Nummer', 'Nachname', 'Vorname', 'Geburtsdatum', 'Klasse', 'Geschlecht', 'Entlassdatum', 'Aufnahmedatum', 'vorauss. Abschlussdatum', 'Schulpflicht', 'Volljährig', 'E-Mail (privat)', 'Telefon-Nr.', 'Fax-Nr.', 'Straße', 'Postleitzahl', 'Ortsname', 'Aktiv']

    output_data_students = [] # Liste für die Ausgabe der Schülerdaten
    students_by_id = {} # Dictionary für den schnellen Zugriff auf Schülerdaten per ID

    # Öffnen der neuesten CSV-Datei und Einlesen der Daten
    with open(newest_file, 'r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        # Überprüfen, ob die notwendigen Spalten vorhanden sind
        header = [column for column in reader.fieldnames if column in columns_to_filter]
        header.append('Schulpflicht')
        header.append('Aktiv')
        output_data_students.append(output_columns)
        print_info("Beginne mit dem Verarbeiten der Schülerdaten...")
        for row in reader:
            filtered_row = {k: v for k, v in row.items() if k in columns_to_filter}

            # Schulpflicht-Logik (umkehren von 'Ja'/'Nein')
            if 'Schulpflicht erfüllt' in filtered_row:
                if filtered_row['Schulpflicht erfüllt'] == 'Ja':
                    filtered_row['Schulpflicht'] = 'Nein'
                elif filtered_row['Schulpflicht erfüllt'] == 'Nein':
                    filtered_row['Schulpflicht'] = 'Ja'

            # Datumskonvertierung für Entlassdatum
            entlassdatum = filtered_row.get('Entlassdatum', '')
            abschlussdatum = filtered_row.get('vorauss. Abschlussdatum', '')
            if entlassdatum and abschlussdatum:
                try:
                    entlassdatum_date = datetime.strptime(entlassdatum, '%d.%m.%Y')
                    abschlussdatum_date = datetime.strptime(abschlussdatum, '%d.%m.%Y')
                    if use_abschlussdatum and abschlussdatum_date < entlassdatum_date:
                        entlassdatum = abschlussdatum
                        print_info(f"Entlassdatum für Schüler {filtered_row['Nachname']}, {filtered_row['Vorname']} auf Abschlussdatum aktualisiert.")
                except ValueError:
                    print_error(f"Fehler beim Konvertieren von Datumsangaben für Schüler {filtered_row['Nachname']}, {filtered_row['Vorname']}.")
                    pass # Ignoriere ungültige Datumsangaben
            elif not entlassdatum and abschlussdatum and use_abschlussdatum:
                entlassdatum = abschlussdatum
                print_creation(f"Entlassdatum für Schüler {filtered_row['Nachname']}, {filtered_row['Vorname']} gesetzt auf Abschlussdatum.")

            filtered_row['Entlassdatum'] = entlassdatum
            
            # Schüler als aktiv markieren basierend auf dem Status
            filtered_row['Aktiv'] = 'Ja' if row['Status'] == '2' else 'Nein'

            # Klassenlehrer verarbeiten
            if 'Klassenlehrer' in reader.fieldnames:
                filtered_row['Klassenlehrer'] = row.get('Klassenlehrer', '').strip()
            else:
                filtered_row['Klassenlehrer'] = ''  # Standardwert, falls die Spalte fehlt

            # Füge die Daten zur Ausgabeliste hinzu
            output_data_students.append([filtered_row.get(col, '') for col in output_columns])
            # Speichere den Schüler im Dictionary nach Interner ID
            students_by_id[filtered_row['Interne ID-Nummer']] = filtered_row

    print_success("Schülerdaten erfolgreich eingelesen und verarbeitet.")
    return output_data_students, students_by_id

def create_warnings(classes_by_name, students_by_id):
    # Funktion zum Erstellen von Warnungen bei Änderungen des Entlassdatums
    print_info("Erstelle Entlassdatum-Warnungen...")
    warnings = []
    import_dir = get_directory('import_directory', './WebUntis Importe')

    # Vorherige Importdatei finden
    output_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if output_files:
        newest_output_file = max(output_files, key=lambda f: os.path.getctime(os.path.join(import_dir, f)))
        print_info(f"Vergleiche mit vorheriger Importdatei:\n {newest_output_file}")
        with open(os.path.join(import_dir, newest_output_file), 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                interne_id = row.get('Interne ID-Nummer')
                if interne_id in students_by_id:
                    # Vergleiche Entlassdatum
                    previous_entlassdatum = row.get('Entlassdatum')
                    new_entlassdatum = students_by_id[interne_id].get('Entlassdatum')
                    try:
                        previous_date = datetime.strptime(previous_entlassdatum, '%d.%m.%Y').date() if previous_entlassdatum else None
                        new_date = datetime.strptime(new_entlassdatum, '%d.%m.%Y').date() if new_entlassdatum else None
                        now_date = datetime.now().date()  # Importdatum ist aktuelles Datum

                        # Fall 1: Entlassdatum wird in die Zukunft verschoben und Importdatum liegt nach altem Entlassdatum
                        if previous_date and new_date and previous_date < new_date and now_date > previous_date:
                            if now_date < new_date:
                                undokumentierter_zeitraum_bis = now_date
                            else:
                                undokumentierter_zeitraum_bis = new_date

                            klasse = row['Klasse'].strip().lower()
                            klassen_info = classes_by_name.get(klasse, {})
                            if not klassen_info:
                                print_warning(f"Klasse '{klasse}' nicht in Klasseninformationen gefunden.")

                            # Warnung hinzufügen
                            warnings.append({
                                'Nachname': row['Nachname'],
                                'Vorname': row['Vorname'],
                                'Klasse': row.get('Klasse', 'N/A'),
                                'neues_entlassdatum': new_entlassdatum,
                                'altes_entlassdatum': previous_entlassdatum,
                                'Zeitraum_nicht_dokumentiert': f"{previous_entlassdatum} bis {undokumentierter_zeitraum_bis.strftime('%d.%m.%Y')}",
                                'Klassenlehrkraft_1': klassen_info.get('Klassenlehrkraft_1', 'N/A'),
                                'Klassenlehrkraft_1_Email': klassen_info.get('Klassenlehrkraft_1_Email', 'N/A'),
                                'Klassenlehrkraft_2': klassen_info.get('Klassenlehrkraft_2', 'N/A'),
                                'Klassenlehrkraft_2_Email': klassen_info.get('Klassenlehrkraft_2_Email', 'N/A'),
                                'Volljaehrig': students_by_id[interne_id].get('Volljährig', 'Unbekannt'),  # Volljaehrig Schlüssel hinzufügen
                                'Status': students_by_id[interne_id].get('Status_Text', 'Unbekannt'),  # Status Schlüssel hinzufügen
                                'warning_message': (
                                    "Das Entlassdatum wurde in die Zukunft verschoben, "
                                    "und es gibt einen nicht dokumentierten Zeitraum."
                                )
                            })
                            print_info(f"Warnung erstellt für Schüler {row['Nachname']}, {row['Vorname']}: Entlassdatum verschoben.")
                    except ValueError:
                        print_error(f"Ungültiges Datum für Schüler {row['Nachname']}, {row['Vorname']}. Warnung nicht erstellt.")
                        pass  # Ignoriere ungültige Datumsangaben
    else:
        print_warning("Keine vorherige Importdatei zum Vergleich gefunden.")
    print_info(f"Anzahl der erstellten Entlassdatum-Warnungen: {len(warnings)}")
    return warnings


def create_new_student_warnings(classes_by_name, current_students_by_id):
    print_info("Erstelle Warnungen für neue Schüler...")
    warnings = []
    import_dir = get_directory('import_directory', './WebUntis Importe')
    
    # Alle CSV-Dateien aus dem Importverzeichnis ermitteln
    output_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    
    # Wähle als Vergleichsdatei:
    if len(output_files) >= 1:
        # Sortiere absteigend nach Erstellungszeit und wähle die neueste Datei
        output_files.sort(key=lambda f: os.path.getctime(os.path.join(import_dir, f)), reverse=True)
        previous_file = output_files[0]
    else:
        print_warning("Keine Importdatei gefunden.")
        return warnings

    print_info(f"Vergleiche mit Vergleichsdatei für neue Schüler:\n {previous_file}")
    
    # Lese die Vergleichsdatei ein und sammle alle Schüler-IDs (normalisiert)
    previous_students = {}
    try:
        with open(os.path.join(import_dir, previous_file), 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                student_id = row.get('Interne ID-Nummer')
                if student_id:
                    previous_students[student_id.strip()] = row
    except Exception as e:
        print_error(f"Fehler beim Einlesen der Vergleichsdatei: {e}")
        return warnings

    # Vergleiche die aktuellen Schülerdaten (students_by_id) mit denen der Vergleichsdatei
    for student_id, student in current_students_by_id.items():
        key = student_id.strip() if isinstance(student_id, str) else str(student_id)
        if key not in previous_students:
            klasse = student.get('Klasse', 'N/A').strip().lower()
            klassen_info = classes_by_name.get(klasse, {})
            warnings.append({
                'Nachname': student.get('Nachname', ''),
                'Vorname': student.get('Vorname', ''),
                'Klasse': student.get('Klasse', 'N/A'),
                'Aufnahmedatum': student.get('Aufnahmedatum', ''),
                'warning_message': "Neuer Schüler in den importierten Daten entdeckt.",
                'Klassenlehrkraft_1': klassen_info.get('Klassenlehrkraft_1', 'N/A'),
                'Klassenlehrkraft_1_Email': klassen_info.get('Klassenlehrkraft_1_Email', 'N/A'),
                'Klassenlehrkraft_2': klassen_info.get('Klassenlehrkraft_2', 'N/A'),
                'Klassenlehrkraft_2_Email': klassen_info.get('Klassenlehrkraft_2_Email', 'N/A'),
                'new_student': True
            })
            print_info(f"Warnung erstellt für neuen Schüler {student.get('Nachname', '')}, {student.get('Vorname', '')}.")
    
    print_info(f"Anzahl der erstellten Warnungen für neue Schüler: {len(warnings)}")
    return warnings




def create_class_change_warnings(classes_by_name, students_by_id):
    # Funktion zum Erstellen von Warnungen bei Klassenwechseln
    print_info("Erstelle Klassenwechsel-Warnungen...")
    warnings = []
    import_dir = get_directory('import_directory', './WebUntis Importe')

    # Vorherige Importdatei finden
    output_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if output_files:
        newest_output_file = max(output_files, key=lambda f: os.path.getctime(os.path.join(import_dir, f)))
        print_info(f"Vergleiche mit vorheriger Importdatei:\n {newest_output_file}")
        with open(os.path.join(import_dir, newest_output_file), 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                interne_id = row.get('Interne ID-Nummer')
                if interne_id in students_by_id:
                    # Vergleiche Klasse
                    previous_class = row.get('Klasse')
                    new_class = students_by_id[interne_id].get('Klasse')
                    if previous_class and new_class and previous_class != new_class:
                        klasse = previous_class.strip().lower()
                        klassen_info = classes_by_name.get(klasse, {})
                        if not klassen_info:
                            print_warning(f"Klasse '{klasse}' nicht in Klasseninformationen gefunden.")

                        # Warnung hinzufügen
                        warnings.append({
                            'Nachname': row['Nachname'],
                            'Vorname': row['Vorname'],
                            'alte_klasse': previous_class,
                            'neue_klasse': new_class,
                            'Klassenlehrkraft_1': klassen_info.get('Klassenlehrkraft_1', 'N/A'),
                            'Klassenlehrkraft_1_Email': klassen_info.get('Klassenlehrkraft_1_Email', 'N/A'),
                            'Klassenlehrkraft_2': klassen_info.get('Klassenlehrkraft_2', 'N/A'),
                            'Klassenlehrkraft_2_Email': klassen_info.get('Klassenlehrkraft_2_Email', 'N/A'),
                            'Volljaehrig': students_by_id[interne_id].get('Volljährig', 'Unbekannt'),  # Volljaehrig hinzufügen
                            'Status': students_by_id[interne_id].get('Status_Text', 'Unbekannt'),  # Status Schlüssel hinzufügen
                            'warning_message': "Klassenwechsel muss im Digitalen Klassenbuch manuell korrigiert werden, da die Änderung im System ab dem aktuellen Tag gilt."
                        })
                        print_info(f"Warnung erstellt für Schüler {row['Nachname']}, {row['Vorname']}: Klassenwechsel von {previous_class} zu {new_class}.")
    else:
        print_warning("Keine vorherige Importdatei zum Vergleich gefunden.")
    print_info(f"Anzahl der erstellten Klassenwechsel-Warnungen: {len(warnings)}")
    return warnings

def create_admission_date_warnings(classes_by_name, students_by_id):
    # Funktion zum Erstellen von Warnungen bei Änderungen des Aufnahmedatums
    print_info("Erstelle Aufnahmedatum-Warnungen...")
    warnings = []
    import_dir = get_directory('import_directory', './WebUntis Importe')

    # Vorherige Importdatei finden
    output_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if output_files:
        newest_output_file = max(output_files, key=lambda f: os.path.getctime(os.path.join(import_dir, f)))
        print_info(f"Vergleiche mit vorheriger Importdatei:\n {newest_output_file}")
        with open(os.path.join(import_dir, newest_output_file), 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                interne_id = row.get('Interne ID-Nummer')
                if interne_id in students_by_id:
                    # Prüfen, ob sich das Aufnahmedatum geändert hat
                    previous_admission_date = row.get('Aufnahmedatum')
                    new_admission_date = students_by_id[interne_id].get('Aufnahmedatum')
                    try:
                        # Konvertiere Datumsangaben zu `date`-Objekten
                        prev_date_obj = datetime.strptime(previous_admission_date, '%d.%m.%Y').date() if previous_admission_date else None
                        new_date_obj = datetime.strptime(new_admission_date, '%d.%m.%Y').date() if new_admission_date else None
                        now_date = datetime.now().date()  # Importdatum ist aktuelles Datum

                        # Fall 2: Aufnahmedatum wird in die Vergangenheit verschoben und Importdatum liegt nach dem neuen Aufnahmedatum
                        if prev_date_obj and new_date_obj and new_date_obj < prev_date_obj and now_date > new_date_obj:
                            if now_date < prev_date_obj:
                                undokumentierter_zeitraum_bis = now_date
                            else:
                                undokumentierter_zeitraum_bis = prev_date_obj
                            klasse = row.get('Klasse', 'N/A').strip().lower()
                            klassen_info = classes_by_name.get(klasse, {})

                            # Warnung hinzufügen
                            warnings.append({
                                'Nachname': row['Nachname'],
                                'Vorname': row['Vorname'],
                                'Klasse': row.get('Klasse', 'N/A'),
                                'neues_aufnahmedatum': new_admission_date,
                                'altes_aufnahmedatum': previous_admission_date,
                                'Zeitraum_nicht_dokumentiert': f"{new_admission_date} bis {undokumentierter_zeitraum_bis.strftime('%d.%m.%Y')}",
                                'Klassenlehrkraft_1': klassen_info.get('Klassenlehrkraft_1', 'N/A'),
                                'Klassenlehrkraft_1_Email': klassen_info.get('Klassenlehrkraft_1_Email', 'N/A'),
                                'Klassenlehrkraft_2': klassen_info.get('Klassenlehrkraft_2', 'N/A'),
                                'Klassenlehrkraft_2_Email': klassen_info.get('Klassenlehrkraft_2_Email', 'N/A'),
                                'Volljaehrig': students_by_id[interne_id].get('Volljährig', 'Unbekannt'),  # Volljaehrig hinzufügen
                                'Status': students_by_id[interne_id].get('Status_Text', 'Unbekannt'),  # Status Schlüssel hinzufügen
                                'warning_message': (
                                    "Das Aufnahmedatum wurde in die Vergangenheit verschoben, "
                                    "und es gibt einen nicht dokumentierten Zeitraum."
                                )
                            })
                            print_info(f"Warnung erstellt für Schüler {row['Nachname']}, {row['Vorname']}: Aufnahmedatum geändert.")
                    except ValueError:
                        print_error(f"Ungültiges Datum für Schüler {row['Nachname']}, {row['Vorname']}. Warnung nicht erstellt.")
                        pass  # Ignoriere ungültige Datumsangaben
    else:
        print_warning("Keine vorherige Importdatei zum Vergleich gefunden.")
    print_info(f"Anzahl der erstellten Aufnahmedatum-Warnungen: {len(warnings)}")
    return warnings

def print_warnings(warnings):
    # Funktion zur Ausgabe der Warnungen in der Konsole
    for warning in warnings:
        print_warning("===================== WARNUNG =====================")
        print_warning(f"Nachname: {warning['Nachname']}")
        print_warning(f"Vorname: {warning['Vorname']}")
        if 'neues_aufnahmedatum' in warning:
            print_warning(f"Klasse: {warning.get('Klasse', 'N/A')}")
            print_warning(f"Neues Aufnahmedatum: {warning['neues_aufnahmedatum']}")
            print_warning(f"Altes Aufnahmedatum: {warning['altes_aufnahmedatum']}")
        if 'neues_entlassdatum' in warning:
            print_warning(f"Klasse: {warning.get('Klasse', 'N/A')}")
            print_warning(f"Neues Entlassdatum: {warning['neues_entlassdatum']}")
            print_warning(f"Altes Entlassdatum: {warning['altes_entlassdatum']}")
        if 'neue_klasse' in warning:
            print_warning(f"Alte Klasse: {warning['alte_klasse']}")
            print_warning(f"Neue Klasse: {warning['neue_klasse']}")
        # Einheitliche Ausgabe der Warnungsnachricht
        if 'warning_message' in warning:
            print_warning(f"Warnung: {warning['warning_message']}")
        print_warning(f"Klassenlehrkraft 1: {warning['Klassenlehrkraft_1']}")
        print_warning(f"Klassenlehrkraft 1 E-Mail: {warning['Klassenlehrkraft_1_Email']}")
        print_warning(f"Klassenlehrkraft 2: {warning['Klassenlehrkraft_2']}")
        print_warning(f"Klassenlehrkraft 2 E-Mail: {warning['Klassenlehrkraft_2_Email']}")
        print_warning("====================================================")

def save_files(output_data_students, warnings, create_second_file, enable_attestpflicht_column=False):
    # Funktion zum Speichern der Ausgabedateien
    print_info("Speichere Ausgabedateien...")
    config = configparser.ConfigParser()
    config.read('settings.ini')
    import_dir = get_directory('import_directory', './WebUntis Importe')
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Falls Attestpflicht-Spalte gewünscht
    if enable_attestpflicht_column:
        print_info("Füge Attestpflicht-Spalte hinzu...")
        attest_ids = read_attest_ids_from_latest_file()

        # Beispiel: Wir fügen eine neue Spalte 'Attestpflicht' an.
        headers = output_data_students[0]
        if "Attestpflicht" not in headers:
            headers.append("Attestpflicht")

        id_index = headers.index("Interne ID-Nummer")

        for row_i in range(1, len(output_data_students)):
            row = output_data_students[row_i]
            student_id = row[id_index]
            row.append("Ja" if student_id in attest_ids else "Nein")

    output_file = os.path.join(import_dir, f'WebUntis Import {now}.csv')
    second_output_file = os.path.join(import_dir, f'WebUntis Import {now}_Fehlende Entlassdatumsangaben.csv')

    # Sicherstellen, dass das Importverzeichnis existiert
    os.makedirs(import_dir, exist_ok=True)
    print_info(f"Importverzeichnis '{import_dir}' ist vorhanden oder wurde erstellt.")

    # Hauptausgabedatei speichern
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerows(output_data_students)
    print_creation(f"Hauptausgabedatei (Neue WebUntis-Import_Datei) gespeichert:\n {output_file}")

    # Zweite Ausgabedatei speichern, falls gewünscht
    if create_second_file:
        print_info("Erstelle zweite Ausgabedatei für fehlende Entlassdatumsangaben...")
        second_output_columns = ['Interne ID-Nummer', 'Nachname', 'Vorname', 'Geburtsdatum', 'Klasse', 'Geschlecht', 'Entlassdatum']
        second_output_data = []

        # Suche die neueste Datei im Hauptverzeichnis
        schildexport_dir = get_directory('schildexport_directory', default='.')
        if schildexport_dir in ('.', '', None):
            schildexport_dir = os.getcwd()
        csv_files = [f for f in os.listdir(schildexport_dir) if f.endswith('.csv')]

        if not csv_files:
            print_error("Fehler: Keine CSV-Dateien im Hauptverzeichnis gefunden.")
            return

        # Daten für zweite Datei extrahieren
        newest_file = max(
            [os.path.join(schildexport_dir, f) for f in csv_files], 
            key=os.path.getctime
        )
        print_info(f"Verwende Datei für zweite Ausgabe:\n {newest_file}")
        with open(newest_file, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                if row['Status'] != '2' and not row.get('Entlassdatum'):
                    filtered_row = {k: v for k, v in row.items() if k in second_output_columns}
                    second_output_data.append([filtered_row.get(col, '') for col in second_output_columns])
        if second_output_data:
            with open(second_output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(second_output_columns)  # Header für die zweite Datei
                writer.writerows(second_output_data)
            print_creation(f"Zweite Ausgabedatei gespeichert:\n {second_output_file}")
        else:
            print_warning("Keine Daten für die zweite Ausgabedatei gefunden.")
    else:
        print_info("Keine zweite Ausgabedatei da die Erstellung der zweiten Ausgabedatei deaktiviert wurde.")

    
def read_attest_ids_from_latest_file():
    """
    Sucht im 'attest_file_directory' (aus settings.ini) nach der neuesten .csv-Datei,
    liest daraus alle 'Interne ID-Nummer' Einträge in ein Set und gibt dieses zurück.
    """
    config = configparser.ConfigParser()
    config.read('settings.ini')
    attest_dir = config.get('Directories', 'attest_file_directory', fallback='./AttestpflichtDaten')

    if not os.path.exists(attest_dir):
        print(Fore.YELLOW + f"⚠️ Attest-Verzeichnis '{attest_dir}' existiert nicht. Keine Attestdaten vorhanden." + Style.RESET_ALL)
        return set()

    # Alle CSV-Dateien ermitteln
    csv_files = [f for f in os.listdir(attest_dir) if f.endswith('.csv')]
    if not csv_files:
        print(Fore.YELLOW + "⚠️ Keine CSV-Dateien im Attest-Verzeichnis gefunden. Keine Attestdaten vorhanden." + Style.RESET_ALL)
        return set()

    # Neueste CSV-Datei bestimmen
    csv_files.sort(key=lambda x: os.path.getctime(os.path.join(attest_dir, x)), reverse=True)
    latest_file = csv_files[0]
    full_path = os.path.join(attest_dir, latest_file)

    # IDs einlesen
    return read_attest_ids(full_path)
def read_attest_ids(attest_file_path):
    """
    Liest alle Interne ID-Nummern aus der gegebenen Attest-CSV-Datei und gibt sie als Set zurück.
    Beispielhafte Spalte: 'Interne ID-Nummer'
    """
    ids = set()
    print(Fore.CYAN + f"ℹ️ Lese Attestpflicht-Datei: {attest_file_path}" + Style.RESET_ALL)
    try:
        with open(attest_file_path, 'r', encoding='utf-8-sig', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                sid = row.get("Interne ID-Nummer", "").strip()
                if sid:
                    ids.add(sid)
    except Exception as e:
        print(Fore.RED + f"❌ Fehler beim Lesen der Attestpflicht-Datei {attest_file_path}: {e}" + Style.RESET_ALL)
    print(Fore.CYAN + f"ℹ️ Attestpflicht-Datei eingelesen. Anzahl IDs: {len(ids)}" + Style.RESET_ALL)
    return ids

from collections import defaultdict
def create_class_sizes_file(students_by_id):
    """
    Erzeugt eine CSV mit den Spalten:
      Klasse, Schüler (männlich), Schüler (weiblich), Schüler (divers), Schüler (gesamt)
    und berücksichtigt nur Schüler mit Status == '2' (also Aktiv == 'Ja').
    Die Datei wird in das class_size_directory aus den settings.ini abgelegt.
    """
    print_info("Erstelle Klassengrößen-Auswertung...")

    # 1) Lese aus settings.ini das Verzeichnis
    config = configparser.ConfigParser()
    config.read('settings.ini')
    class_size_dir = config.get('Directories', 'class_size_directory', fallback="./ClassSizes")

    # Stelle sicher, dass der Ordner existiert
    os.makedirs(class_size_dir, exist_ok=True)

    # 2) Aggregation: { klasse_name: {"m": 0, "w": 0, "d": 0} }
    class_counts = defaultdict(lambda: {"m": 0, "w": 0, "d": 0})

    for student_id, student_data in students_by_id.items():
        # Nur Schüler mit Status=2 => 'Aktiv' == 'Ja'
        if student_data.get("Aktiv") == "Ja":
            klasse = (student_data.get("Klasse") or "").strip()
            geschlecht = (student_data.get("Geschlecht") or "").lower()  # 'm', 'w', 'd'
            if geschlecht in ("m", "w", "d"):
                class_counts[klasse][geschlecht] += 1

    # 3) CSV-Datei schreiben
    now_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file_path = os.path.join(class_size_dir, f"Klassengroessen_{now_str}.csv")
    headers = ["Klasse", "Schüler (männlich)", "Schüler (weiblich)", "Schüler (divers)", "Schüler (gesamt)"]

    try:
        with open(output_file_path, "w", newline="", encoding="utf-8-sig") as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(headers)

            # Sortiere Klassen wahlweise alphabetisch
            for klasse in sorted(class_counts.keys()):
                counts = class_counts[klasse]
                male = counts["m"]
                female = counts["w"]
                diverse = counts["d"]
                total = male + female + diverse
                writer.writerow([klasse, male, female, diverse, total])
        print_success(f"Klassengrößen-Datei erstellt: {output_file_path}")
    except Exception as e:
        print_error(f"Fehler beim Erstellen der Klassengrößen-Datei: {e}")
