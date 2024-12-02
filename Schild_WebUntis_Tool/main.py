import os
import csv
import configparser
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

def run(use_abschlussdatum=True, create_second_file=True,
        warn_entlassdatum=True, warn_aufnahmedatum=True, warn_klassenwechsel=True,
        no_log=False, no_xlsx=False):
    # Hauptfunktion zur Verarbeitung der Daten und Generierung von Warnungen
    print(f'Inside your_script.py - use_abschlussdatum: {use_abschlussdatum}')  # Debug print
    warnings = []  # Liste für Warnungen
    class_change_warnings = []  # Liste für Klassenwechsel-Warnungen
    admission_date_warnings = []  # Liste für Aufnahmedatum-Warnungen

    # Konfigurationsdatei einlesen
    config = configparser.ConfigParser()
    config.read('settings.ini')
    classes_dir = config.get('Directories', 'classes_directory')
    teachers_dir = config.get('Directories', 'teachers_directory')

    # Daten einlesen und verarbeiten
    classes_by_name = read_classes(classes_dir, teachers_dir)
    output_data_students, students_by_id = read_students(use_abschlussdatum)

    # Warnungen erstellen basierend auf der Benutzerauswahl
    if warn_entlassdatum:
        warnings = create_warnings(classes_by_name, students_by_id)
    if warn_klassenwechsel:
        class_change_warnings = create_class_change_warnings(classes_by_name, students_by_id)
    if warn_aufnahmedatum:
        admission_date_warnings = create_admission_date_warnings(classes_by_name, students_by_id)

    # Alle Warnungen zusammenführen
    all_warnings = warnings + class_change_warnings + admission_date_warnings

    # Separate Konsolenausgabe der verschiedenen Warnungen
    print("==================== ENTLASSDATUM WARNUNGEN ====================")
    print_warnings(warnings)
    print("==================== KLASSENWECHSEL WARNUNGEN ==================")
    print_warnings(class_change_warnings)
    print("==================== AUFNAHMEDATUM WARNUNGEN ===================")
    print_warnings(admission_date_warnings)

    # Dateien speichern
    save_files(output_data_students, all_warnings, create_second_file)

    # Vergleiche die letzten beiden Dateien
    compare_latest_imports(no_log=no_log, no_xlsx=no_xlsx)

    return all_warnings

def get_directory(key, default=None):
    config = configparser.ConfigParser()
    config.read('settings.ini')
    return config.get('Directories', key, fallback=default)


def read_csv(file_path):
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
    except Exception as e:
        print(f"Fehler beim Lesen der Datei {file_path}: {e}")
    return data


def compare_latest_imports(no_log=False, no_xlsx=False):
    # Überspringen der Erstellung je nach Flags
    if no_log:
        print("Log-Datei-Erstellung wurde deaktiviert.")
    if no_xlsx:
        print("Excel-Datei-Erstellung wurde deaktiviert.")

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
    csv_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if len(csv_files) < 2:
        print(f"Nicht genügend Dateien im Verzeichnis {import_dir} vorhanden, um einen Vergleich durchzuführen.")
        return

    # Nach Erstellungszeit sortieren und die letzten beiden Dateien auswählen
    csv_files.sort(key=lambda f: os.path.getctime(os.path.join(import_dir, f)), reverse=True)
    latest_file = csv_files[0]
    previous_file = csv_files[1]

    print(f"Vergleiche Dateien: {previous_file} und {latest_file}")

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

    # Datum und Uhrzeit für Dateinamen
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f'ÄnderungsLog_{timestamp}.log')
    excel_file_path = os.path.join(xlsx_dir, f'ÄnderungsLog_{timestamp}.xlsx')

    # Log-Datei erstellen
    if not no_log:
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            for change in changes:
                log_file.write(f"Schüler: {change['name']} (ID: {change['student_id']})\n")
                for field, values in change['changes'].items():
                    log_file.write(f"  {field}: {values['old']} -> {values['new']}\n")
                log_file.write("\n")
        print(f"Log-Datei erstellt: {log_file_path}")

    # Excel-Datei erstellen
    if not no_xlsx and changes:
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
        print(f"Excel-Datei erstellt: {excel_file_path}")

from smtp import send_email
def compare_timeframe_imports(no_log=False, no_xlsx=False):

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
        print("Keine Admin-E-Mail-Adresse in der email_settings.ini definiert. E-Mail-Versand deaktiviert.")
        send_log_email = False

    os.makedirs(import_dir, exist_ok=True)
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(xlsx_dir, exist_ok=True)

    # Überprüfung des letzten E-Mail-Versands
    email_log_path = os.path.join(log_dir, "last_email_sent.log")
    if os.path.exists(email_log_path):
        with open(email_log_path, "r") as email_log:
            last_email_time = datetime.strptime(email_log.read().strip(), "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_email_time < timedelta(hours=timeframe_hours):
            print("Eine E-Mail wurde bereits innerhalb des definierten Zeitrahmens gesendet. Kein neuer Versand.")
            return
    else:
        last_email_time = None


    cutoff_time = datetime.now() - timedelta(hours=timeframe_hours)
    # Dateien im Zeitrahmen finden
    csv_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]

    # Dateien sortieren
    csv_files.sort(key=lambda f: os.path.getctime(os.path.join(import_dir, f)), reverse=True)

    # Datei suchen, die älter als der Zeitrahmen ist
    previous_file = next(
        (f for f in csv_files if datetime.fromtimestamp(os.path.getmtime(os.path.join(import_dir, f))) < cutoff_time),
        None
    )

    # Neueste Datei finden
    latest_file = csv_files[0] if csv_files else None

    if not latest_file:
        print("Keine Dateien gefunden.")
        return

    if not previous_file:
        print(f"Keine Dateien gefunden, die älter als {timeframe_hours} Stunden sind.")
        return

    print(f"Vergleiche Dateien: {previous_file} und {latest_file}")

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
        print("Keine Änderungen festgestellt.")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_dir, f'ÄnderungsLog_{timestamp}.log')
    excel_file_path = os.path.join(xlsx_dir, f'ÄnderungsLog_{timestamp}.xlsx')

    if not no_log:
        with open(log_file_path, 'w', encoding='utf-8') as log_file:
            for change in changes:
                log_file.write(f"Schüler: {change['name']} (ID: {change['student_id']})\n")
                for field, values in change['changes'].items():
                    log_file.write(f"  {field}: {values['old']} -> {values['new']}\n")
                log_file.write("\n")
        print(f"Log-Datei erstellt: {log_file_path}")

    if not no_xlsx:
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
        print(f"Excel-Datei erstellt: {excel_file_path}")

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

        # Generiere die Tabelle
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
            print(f"E-Mail mit Änderungen an {admin_email} gesendet.")

            # Zeitstempel des E-Mail-Versands speichern
            with open(email_log_path, "w") as email_log:
                email_log.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        except Exception as e:
            print(f"Fehler beim Senden der E-Mail: {e}")



def read_classes(classes_dir, teachers_dir, return_teachers=False):
    # Normalisiere Pfade
    classes_dir = os.path.normpath(classes_dir)
    teachers_dir = os.path.normpath(teachers_dir)

    # Prüfen, ob der Ordner für Klassendaten existiert
    if not os.path.exists(classes_dir):
        print(f"Warnung: Der Ordner '{classes_dir}' existiert nicht.")
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
        print(f"Warnung: Keine Klassen-CSV-Dateien im Ordner '{classes_dir}' gefunden.")
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

    # Prüfen, ob der Ordner für Lehrerdaten existiert
    if not os.path.exists(teachers_dir):
        print(f"Warnung: Der Ordner '{teachers_dir}' existiert nicht.")
        teachers = {
            "dummy_teacher_1": {"email": "lehrer1@example.com", "forename": "Anna", "longname": "Lehrkraft"},
            "dummy_teacher_2": {"email": "lehrer2@example.com", "forename": "Tom", "longname": "Muster"},
        }
    else:
        # Neueste Lehrkräfte-CSV-Datei finden
        teacher_csv_files = [f for f in os.listdir(teachers_dir) if f.endswith('.csv')]
        if not teacher_csv_files:
            print(f"Warnung: Keine Lehrkräfte-CSV-Dateien im Ordner '{teachers_dir}' gefunden.")
            teachers = {
                "dummy_teacher_1": {"email": "lehrer1@example.com", "forename": "Anna", "longname": "Lehrkraft"},
                "dummy_teacher_2": {"email": "lehrer2@example.com", "forename": "Tom", "longname": "Muster"},
            }
        else:
            newest_teacher_file = max(teacher_csv_files, key=lambda f: os.path.getctime(os.path.join(teachers_dir, f)))

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
                print(f"Fehler beim Einlesen der Lehrkräfte-Datei: {e}")
                teachers = {}  # Fallback auf leere Lehrer-Daten

    # Klassen-CSV-Datei einlesen und Lehrkräfte-Emails zuordnen
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

    return (classes_by_name, teachers) if return_teachers else classes_by_name





def read_students(use_abschlussdatum):
    import_dir = get_directory('import_directory', './WebUntis Importe')
    if not os.path.exists(import_dir):
        os.makedirs(import_dir)

    # Überprüfen, ob .csv Dateien im aktuellen Verzeichnis vorhanden sind
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files:
        print("Keine CSV-Dateien im aktuellen Verzeichnis gefunden.")
        return [], {}

    newest_file = max(csv_files, key=os.path.getctime)

    # Definierte Spalten
    columns_to_filter = ['Interne ID-Nummer', 'Nachname', 'Vorname', 'Geburtsdatum', 'Klasse', 'Klassenlehrer', 'Geschlecht', 'Entlassdatum', 'Aufnahmedatum', 'vorauss. Abschlussdatum', 'Schulpflicht erfüllt', 'Volljährig', 'E-Mail (privat)', 'Telefon-Nr.', 'Fax-Nr.', 'Straße', 'Postleitzahl', 'Ortsname']
    output_columns = ['Interne ID-Nummer', 'Nachname', 'Vorname', 'Geburtsdatum', 'Klasse', 'Geschlecht', 'Entlassdatum', 'Aufnahmedatum', 'vorauss. Abschlussdatum', 'Schulpflicht', 'Volljährig', 'E-Mail (privat)', 'Telefon-Nr.', 'Fax-Nr.', 'Straße', 'Postleitzahl', 'Ortsname', 'Aktiv']

    output_data_students = []
    students_by_id = {}
    with open(newest_file, 'r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        header = [column for column in reader.fieldnames if column in columns_to_filter]
        header.append('Schulpflicht')
        header.append('Aktiv')
        output_data_students.append(output_columns)
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
                except ValueError:
                    pass
            elif not entlassdatum and abschlussdatum and use_abschlussdatum:
                entlassdatum = abschlussdatum
            filtered_row['Entlassdatum'] = entlassdatum

            # Schüler als aktiv markieren
            filtered_row['Aktiv'] = 'Ja' if row['Status'] == '2' else 'Nein'

            # Klassenlehrer verarbeiten
            if 'Klassenlehrer' in reader.fieldnames:
                filtered_row['Klassenlehrer'] = row.get('Klassenlehrer', '').strip()
            else:
                filtered_row['Klassenlehrer'] = ''  # Standardwert, falls die Spalte fehlt

            output_data_students.append([filtered_row.get(col, '') for col in output_columns])
            students_by_id[filtered_row['Interne ID-Nummer']] = filtered_row

    return output_data_students, students_by_id

def create_warnings(classes_by_name, students_by_id):
    warnings = []
    import_dir = get_directory('import_directory', './WebUntis Importe')
    output_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if output_files:
        newest_output_file = max(output_files, key=lambda f: os.path.getctime(os.path.join(import_dir, f)))
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
                                print(f"Klasse '{klasse}' nicht in Klasseninformationen gefunden.")

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
                    except ValueError:
                        pass  # Ignoriere ungültige Datumsangaben
    return warnings

def create_class_change_warnings(classes_by_name, students_by_id):
    warnings = []
    import_dir = get_directory('import_directory', './WebUntis Importe')
    output_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if output_files:
        newest_output_file = max(output_files, key=lambda f: os.path.getctime(os.path.join(import_dir, f)))
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
                            print(f"Klasse '{klasse}' nicht in Klasseninformationen gefunden.")

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
    return warnings

def create_admission_date_warnings(classes_by_name, students_by_id):
    warnings = []
    import_dir = get_directory('import_directory', './WebUntis Importe')
    output_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if output_files:
        newest_output_file = max(output_files, key=lambda f: os.path.getctime(os.path.join(import_dir, f)))
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
                    except ValueError:
                        pass  # Ignoriere ungültige Datumsangaben
    return warnings

def print_warnings(warnings):
    for warning in warnings:
        print("===================== WARNUNG =====================")
        print(f"Nachname: {warning['Nachname']}")
        print(f"Vorname: {warning['Vorname']}")
        if 'neues_aufnahmedatum' in warning:
            print(f"Klasse: {warning.get('Klasse', 'N/A')}")
            print(f"Neues Aufnahmedatum: {warning['neues_aufnahmedatum']}")
            print(f"Altes Aufnahmedatum: {warning['altes_aufnahmedatum']}")
        if 'neues_entlassdatum' in warning:
            print(f"Klasse: {warning.get('Klasse', 'N/A')}")
            print(f"Neues Entlassdatum: {warning['neues_entlassdatum']}")
            print(f"Altes Entlassdatum: {warning['altes_entlassdatum']}")
        if 'neue_klasse' in warning:
            print(f"Alte Klasse: {warning['alte_klasse']}")
            print(f"Neue Klasse: {warning['neue_klasse']}")
        # Einheitliche Ausgabe der Warnungsnachricht
        if 'warning_message' in warning:
            print(f"Warnung: {warning['warning_message']}")
        print(f"Klassenlehrkraft 1: {warning['Klassenlehrkraft_1']}")
        print(f"Klassenlehrkraft 1 Email: {warning['Klassenlehrkraft_1_Email']}")
        print(f"Klassenlehrkraft 2: {warning['Klassenlehrkraft_2']}")
        print(f"Klassenlehrkraft 2 Email: {warning['Klassenlehrkraft_2_Email']}")
        print("====================================================")

def save_files(output_data_students, warnings, create_second_file):
    # Verzeichnis für Ausgabedateien
    import_dir = get_directory('import_directory', './WebUntis Importe')
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = os.path.join(import_dir, f'WebUntis Import {now}.csv')
    second_output_file = os.path.join(import_dir, f'WebUntis Import {now}_Fehlende Entlassdatumsangaben.csv')

    # Ausgabedatei speichern
    os.makedirs(import_dir, exist_ok=True)  # Sicherstellen, dass das Ausgabeverzeichnis existiert
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerows(output_data_students)

    # Zweite Ausgabedatei speichern, falls gewünscht
    if create_second_file:
        second_output_columns = ['Interne ID-Nummer', 'Nachname', 'Vorname', 'Geburtsdatum', 'Klasse', 'Geschlecht', 'Entlassdatum']
        second_output_data = []

        # Suche die neueste Datei im Hauptverzeichnis
        csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
        if not csv_files:
            print("Fehler: Keine CSV-Dateien im Hauptverzeichnis gefunden.")
            return

        # Daten für zweite Datei extrahieren
        newest_file = max(csv_files, key=os.path.getctime)
        with open(newest_file, 'r', newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                if row['Status'] != '2' and not row.get('Entlassdatum'):
                    filtered_row = {k: v for k, v in row.items() if k in second_output_columns}
                    second_output_data.append([filtered_row.get(col, '') for col in second_output_columns])

        with open(second_output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(second_output_columns)  # Header für die zweite Datei
            writer.writerows(second_output_data)
        print(f'Second output file name: {second_output_file}')

