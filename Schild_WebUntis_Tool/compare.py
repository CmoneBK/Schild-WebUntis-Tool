import os
import csv
from datetime import datetime

def compare_student_changes():
    # Verzeichnis für Importe erstellen, falls es nicht existiert
    import_dir = os.path.join(os.getcwd(), 'WebUntis Importe')
    if not os.path.exists(import_dir):
        print("Import directory does not exist.")
        return

    # Neueste Export-Datei finden
    csv_files = [f for f in os.listdir(import_dir) if f.endswith('.csv')]
    if not csv_files:
        print("No export files to compare changes.")
        return
    
    # Sortiere die Dateien nach Datum der letzten Änderung und nehme die neueste
    csv_files.sort(key=lambda f: os.path.getctime(os.path.join(import_dir, f)), reverse=True)
    previous_file = csv_files[0]
    
    # Aktuelle Datei simulieren (neue Exportdaten generieren, ohne Abschlussdatum zu übernehmen)
    output_data_students, students_by_id = read_students(use_abschlussdatum=False)
    
    # Vorherige Datei einlesen
    previous_data = read_csv(os.path.join(import_dir, previous_file))
    
    # Vergleiche die Daten pro Schüler
    changes = []
    class_changes = []
    for student_id, latest_student in students_by_id.items():
        previous_student = previous_data.get(student_id)
        if not previous_student:
            continue  # Schüler ist neu hinzugefügt worden

        student_changes = []
        for field in latest_student.keys():
            new_value = latest_student.get(field, '').strip()
            old_value = previous_student.get(field, '').strip()

            # Spezielle Handhabung für Telefonnummern, um führende Nullen zu berücksichtigen
            if field in ['Telefon-Nr.', 'Fax-Nr.']:
                new_value = new_value.replace(' ', '').replace('-', '').replace('/', '')
                old_value = old_value.replace(' ', '').replace('-', '').replace('/', '')
                if new_value == old_value:
                    continue

            # Spezielle Handhabung für 'Schulpflicht erfüllt', umgekehrt dargestellt
            if field == 'Schulpflicht erfüllt' or field == 'Schulpflicht':
                if (new_value == 'Ja' and old_value == 'Nein') or (new_value == 'Nein' and old_value == 'Ja'):
                    continue

            # Spezielle Handhabung für Datumsangaben, um sicherzustellen, dass sie gleich formatiert sind
            if field in ['Geburtsdatum', 'Entlassdatum', 'vorauss. Abschlussdatum']:
                try:
                    old_value_date = datetime.strptime(old_value, '%d.%m.%Y').date() if old_value else None
                    new_value_date = datetime.strptime(new_value, '%d.%m.%Y').date() if new_value else None
                    if old_value_date == new_value_date:
                        continue
                except ValueError:
                    pass

            if old_value != new_value:
                student_changes.append(f"{field}: {old_value} -> {new_value}")

            # Spezielle Handhabung für Klassenänderungen
            if field == 'Klasse' and old_value != new_value:
                class_changes.append({
                    'student_id': student_id,
                    'name': f"{latest_student.get('Vorname', '')} {latest_student.get('Nachname', '')}",
                    'old_class': old_value,
                    'new_class': new_value,
                    'warning': "Klassenwechsel muss im Digitalen Klassenbuch manuell korrigiert werden"
                })
        
        if student_changes:
            changes.append({
                'student_id': student_id,
                'name': f"{latest_student.get('Vorname', '')} {latest_student.get('Nachname', '')}",
                'changes': student_changes
            })
    
    # Änderungen tabellarisch anzeigen
    for change in changes:
        print(f"Schüler: {change['name']} (ID: {change['student_id']})")
        for change_detail in change['changes']:
            print(f"  {change_detail}")
        print("\n")

    # Klassenänderungen anzeigen
    for class_change in class_changes:
        print(f"Klassenänderung: Schüler: {class_change['name']} (ID: {class_change['student_id']})")
        print(f"  Alte Klasse: {class_change['old_class']} -> Neue Klasse: {class_change['new_class']}")
        print(f"  Warnung: {class_change['warning']}")
        print("\n")

    # Speichere alle Änderungen und Klassenänderungen für die Anzeige im Web-End
    save_warnings_for_web(changes, class_changes)

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

    # Mapping für Status-Werte
    status_mapping = {
        '2': 'Aktiv',
        '8': 'Abgang',
        '9': 'Abschluss'
    }

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

            # Datumskonvertierung für Entlassdatum (nur wenn use_abschlussdatum True ist)
            entlassdatum = filtered_row.get('Entlassdatum', '')
            abschlussdatum = filtered_row.get('vorauss. Abschlussdatum', '')
            if use_abschlussdatum:
                if entlassdatum and abschlussdatum:
                    try:
                        entlassdatum_date = datetime.strptime(entlassdatum, '%d.%m.%Y')
                        abschlussdatum_date = datetime.strptime(abschlussdatum, '%d.%m.%Y')
                        if abschlussdatum_date < entlassdatum_date:
                            entlassdatum = abschlussdatum
                    except ValueError:
                        pass
                elif not entlassdatum and abschlussdatum:
                    entlassdatum = abschlussdatum
            filtered_row['Entlassdatum'] = entlassdatum

            # Mapping des Status
            filtered_row['Status_Text'] = status_mapping.get(row.get('Status', ''), 'Unbekannt')

            # Schüler als aktiv markieren
            filtered_row['Aktiv'] = 'Ja' if row['Status'] == '2' else 'Nein'
            output_data_students.append([filtered_row.get(col, '') for col in output_columns])
            students_by_id[filtered_row['Interne ID-Nummer']] = filtered_row
        return output_data_students, students_by_id

def read_csv(file_path):
    data = {}
    with open(file_path, 'r', newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        for row in reader:
            student_id = row.get('Interne ID-Nummer')
            if student_id:
                data[student_id] = row
    return data

def save_warnings_for_web(changes, class_changes):
    web_data_dir = os.path.join(os.getcwd(), 'web_data')
    if not os.path.exists(web_data_dir):
        os.makedirs(web_data_dir)
    
    # Speichern der allgemeinen Änderungen
    with open(os.path.join(web_data_dir, 'changes.csv'), 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        # Ergänzung der neuen Spalte "Volljährig"
        writer.writerow(['student_id', 'name', 'volljährig', 'changes'])
        for change in changes:
            writer.writerow([
                change['student_id'], 
                change['name'], 
                change.get('Volljährig', 'Unbekannt'),  # Sicherstellen, dass der Schlüssel existiert
                " | ".join(change['changes'])
            ])
    
    # Speichern der Klassenänderungen
    with open(os.path.join(web_data_dir, 'class_changes.csv'), 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        # Ergänzung der neuen Spalte "Volljährig"
        writer.writerow(['student_id', 'name', 'volljährig', 'old_class', 'new_class', 'warning'])
        for class_change in class_changes:
            writer.writerow([
                class_change['student_id'], 
                class_change['name'], 
                class_change.get('Volljährig', 'Unbekannt'),  # Sicherstellen, dass der Schlüssel existiert
                class_change['old_class'], 
                class_change['new_class'], 
                class_change['warning']
            ])

if __name__ == "__main__":
    compare_student_changes()
