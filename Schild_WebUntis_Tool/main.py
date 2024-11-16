import os
import csv
import configparser
from datetime import datetime

def run(use_abschlussdatum=True, create_second_file=True,
        warn_entlassdatum=True, warn_aufnahmedatum=True, warn_klassenwechsel=True):
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

    return all_warnings


def read_classes(classes_dir, teachers_dir):
    # Neueste Klassen-CSV-Datei finden
    class_csv_files = [f for f in os.listdir(classes_dir) if f.endswith('.csv')]
    if not class_csv_files:
        print("Keine Klassen-CSV-Dateien im angegebenen Verzeichnis gefunden.")
        return {}
    newest_class_file = max(class_csv_files, key=lambda f: os.path.getctime(os.path.join(classes_dir, f)))

    # Neueste Lehrkräfte-CSV-Datei finden
    teacher_csv_files = [f for f in os.listdir(teachers_dir) if f.endswith('.csv')]
    if not teacher_csv_files:
        print("Keine Lehrkräfte-CSV-Dateien im angegebenen Verzeichnis gefunden.")
        return {}
    newest_teacher_file = max(teacher_csv_files, key=lambda f: os.path.getctime(os.path.join(teachers_dir, f)))

    # Lehrkräfte in ein Dictionary einlesen
    teachers = {}
    with open(os.path.join(teachers_dir, newest_teacher_file), 'r', newline='', encoding='utf-8-sig') as teacher_file:
        teacher_reader = csv.DictReader(teacher_file, delimiter='\t')
        for row in teacher_reader:
            teacher_name = row['name']
            teachers[teacher_name] = {
            'email': row.get('address.email', ''),
            'forename': row.get('foreName', ''),
            'longname': row.get('longName', '')
        }

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

    return classes_by_name

def read_students(use_abschlussdatum):
    import_dir = os.path.join(os.getcwd(), 'WebUntis Importe')
    if not os.path.exists(import_dir):
        os.makedirs(import_dir)

    # Überprüfen, ob .csv Dateien im aktuellen Verzeichnis vorhanden sind
    csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not csv_files:
        print("Keine CSV-Dateien im aktuellen Verzeichnis gefunden.")
        return [], {}

    newest_file = max(csv_files, key=os.path.getctime)

    # Definierte Spalten
    columns_to_filter = ['Interne ID-Nummer', 'Nachname', 'Vorname', 'Geburtsdatum', 'Klasse', 'Geschlecht', 'Entlassdatum', 'Aufnahmedatum', 'vorauss. Abschlussdatum', 'Schulpflicht erfüllt', 'Volljährig', 'E-Mail (privat)', 'Telefon-Nr.', 'Fax-Nr.', 'Straße', 'Postleitzahl', 'Ortsname']
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
            output_data_students.append([filtered_row.get(col, '') for col in output_columns])
            students_by_id[filtered_row['Interne ID-Nummer']] = filtered_row

    return output_data_students, students_by_id

def create_warnings(classes_by_name, students_by_id):
    warnings = []
    import_dir = os.path.join(os.getcwd(), 'WebUntis Importe')
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
                                'Zeitraum_nicht_dokumentiert': f"{previous_entlassdatum} bis {now_date.strftime('%d.%m.%Y')}",
                                'Klassenlehrkraft_1': klassen_info.get('Klassenlehrkraft_1', 'N/A'),
                                'Klassenlehrkraft_1_Email': klassen_info.get('Klassenlehrkraft_1_Email', 'N/A'),
                                'Klassenlehrkraft_2': klassen_info.get('Klassenlehrkraft_2', 'N/A'),
                                'Klassenlehrkraft_2_Email': klassen_info.get('Klassenlehrkraft_2_Email', 'N/A'),
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
    import_dir = os.path.join(os.getcwd(), 'WebUntis Importe')
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
                            'warning_message': "Klassenwechsel muss im Digitalen Klassenbuch manuell korrigiert werden, da die Änderung im System ab dem aktuellen Tag gilt."
                        })
    return warnings

def create_admission_date_warnings(classes_by_name, students_by_id):
    warnings = []
    import_dir = os.path.join(os.getcwd(), 'WebUntis Importe')
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
                            klasse = row.get('Klasse', 'N/A').strip().lower()
                            klassen_info = classes_by_name.get(klasse, {})

                            warnings.append({
                                'Nachname': row['Nachname'],
                                'Vorname': row['Vorname'],
                                'Klasse': row.get('Klasse', 'N/A'),
                                'neues_aufnahmedatum': new_admission_date,
                                'altes_aufnahmedatum': previous_admission_date,
                                'Zeitraum_nicht_dokumentiert': f"{new_admission_date} bis {previous_admission_date}",
                                'Klassenlehrkraft_1': klassen_info.get('Klassenlehrkraft_1', 'N/A'),
                                'Klassenlehrkraft_1_Email': klassen_info.get('Klassenlehrkraft_1_Email', 'N/A'),
                                'Klassenlehrkraft_2': klassen_info.get('Klassenlehrkraft_2', 'N/A'),
                                'Klassenlehrkraft_2_Email': klassen_info.get('Klassenlehrkraft_2_Email', 'N/A'),
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
    import_dir = os.path.join(os.getcwd(), 'WebUntis Importe')
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





