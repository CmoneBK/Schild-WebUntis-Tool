# Schild-WebUntis-Tool
**Dieses Tool ist eine Weiterentwicklung des [SchildNRW-WebUntis-Umwandlers](https://github.com/CmoneBK/SchildNRW-WebUntis-Umwandler/tree/master)**

Ein Tool zur Umwandlung und Verwaltung von Schülerdaten aus SchildNRW für den Import nach WebUntis, inklusive benutzerdefinierter Warnungen und E-Mail-Benachrichtigungen.

Dieses Tool hilft dabei, Schülerdaten aus SchildNRW zu exportieren, für WebUntis aufzubereiten und Warnungen oder Benachrichtigungen basierend auf spezifischen Kriterien zu generieren. Es unterstützt Sie bei der Dokumentation und Kommunikation zwischen Lehrkräften, insbesondere bei kritischen Änderungen wie Entlassdaten, Aufnahmedaten oder Klassenwechseln.

## Funktionen
- **Datenumwandlung:** Automatische Anpassung von Schülerdaten aus SchildNRW für den WebUntis-Import.
- **Warnungen:** Generiert Warnungen für:
  - Entlassdaten, die in die Zukunft verschoben werden und zu einem nicht dokumentierten Zeitraum führen.
  - Aufnahmedaten, die in die Vergangenheit verschoben werden und Dokumentationslücken verursachen.
  - Klassenwechsel, die eine manuelle Nachbearbeitung in WebUntis erfordern.
- **E-Mail-Benachrichtigungen:** Automatisches Generieren und Versenden von E-Mails an Klassenlehrkräfte mit detaillierten Informationen zu den Warnungen.
- **Benutzerfreundliches Web-Interface:** Auswahl von Kriterien für Warnungen, Generieren von Berichten und Senden von E-Mails direkt über den Browser.
- **Automatische Konfiguration:** Erstellt die benötigten Ordner und .ini-Dateien bei der ersten Ausführung, falls diese fehlen.

## Voraussetzungen
### 1. Auswahlsfilter in SchildNRW und Export
- **Filtereinstellungen:**
  - Unten bei Laufbahninfo: `Schuljahr das aktuelle Schuljahr` auswählen
  - Oben rechts bei Status: `Aktiv`, `Abschluss` und `Abgänger` anwählen
  * Sie sollten diesen Filter speichern, damit Sie ihn später über "Auswahl - Vorhandene Filter laden" wieder verwenden können.
- **Ein Export aus SchildNRW als Text/Excel Export, jedoch unbedingt mit der manuell eingegebenen Dateiendung .csv.**
  - Als Seperator ist ";" zu wählen.
  - Erforderliche Daten (idealerweise auch in dieser Reihenfolge): Interne ID-Nummer, Nachname, Vorname, Klasse, Geburtsdatum, Geschlecht, vorrauss. Abschluss, Aufnahmedatum, Entlassdatum, Volljährig, Schulpflicht erfüllt, Status
  - Optionale Daten: E-mail (privat), Telefon-Nr., Fax-Nr., Straße, Postleitzahl, Ortsname

**Hinweise** Dies wird nicht funktionieren, wenn Sie die Datei als Excel-Datei exportieren und diese als .csv abspeichern. Ergänzen Sie stattdessen manuell die Endung .csv nachdem Sie als Exporttyp die Textdatei ausgewählt haben. Speichern Sie sich diese Exporteinstellung als Vorlage ab, um sie später schneller wieder verwenden zu können.

[Beispiel-Schild-Export](/Beispiel-Dateien/SchildExport.csv)

  
### 2. Ein in WebUntis korrekt konfigurierter Import
- Als Zeichensatz ist UTF-8 zu wählen.

  <img src="/Beispiel-Dateien/WebUntis%20Importeinstellungen.png" alt="Korrekt konfigurierter WebUntis Import" width="400" />

### 3. Optional: Stammdaten Exporte für Warnungs-Funktion
Falls die Warnungs-Funktion genutzt werden soll (z. B. E-Mail-Benachrichtigungen an Klassenleitungen), benötigen Sie:

- **Stammdaten-Export der Lehrkräfte:**  
  - In WebUntis unter `Stammdaten -> Lehrkräfte`.  
  - Scrollen Sie nach unten zur Seite, um `Berichte` anzuklicken und wählen Sie den CSV-Bericht bei "Lehrkräfte".  
  - **Wichtiger Hinweis:** Das Feld für die E-Mail-Adressen muss mit den Dienst-E-Mail-Adressen der Kollegen gefüllt sein, damit es nachher funktioniert.
  - [Beispiel-Lehrkräfte-Export](/Beispiel-Dateien/Teacher_20241006_1140%202.csv)
- **Stammdaten-Export der Klassen:**  
  - In WebUntis unter `Stammdaten -> Klassen`.  
  - Kopieren Sie die Tabelle in eine Excel-Datei mit folgenden Spalten in genau dieser Reihenfolge (nichts umbenennen):
    - `Auswahl`, `[eine Leere Spalte]`, `Klasse`, `Langname`, `Alias`, `Jahrgangsstufe`, `Text`, `Klassenlehrkraft`, `Klassenlehrkraft`, `Abteilung`, `Von`, `Bis`.
  
  Dies ist darauf ausgelegt, dass Sie die Tabelle aus WebUntis einfach dort reinkopieren können und nichts mehr ändern müssen.
  - Exportieren Sie diese Excel-Datei mit Excel anschließend als `.csv`.
  - [Beispiel-Klassen-Export](/Beispiel-Dateien/Klassen.csv)

**Hinweise:** Die generierten CSV-Dateien sollten im Ordner für Klassen- und Lehrerdaten gespeichert werden, der in der Datei `settings.ini` konfiguriert ist. Diese lässt sich mit dem Editor oder Notepad++ öffnen und bearbeiten. 
Wenn Sie das Verzeichnis so belassen wie es ist können Sie die Dateien in die generierten Ordner ablegen. Manche Schulen werden hierfür jedoch einen Ordner auf einem sicheren Netzlaufwerk bevorzugen.  
- **SMTP-Login-Daten Ihres E-Mail Anbieters:**

  Diese sollten Sie haben und bereithalten. Erstellen Sie am besten einen seperaten E-Mail Account speziell zum Versand der hier generierten E-Mails.

## Installation
1. Die .exe Dateie finden Sie unter: [Schild-WebUntis-Tool.exe](https://github.com/CmoneBK/Schild-WebUntis-Tool/blob/master/Schild_WebUntis_Tool/dist/Schild-WebUntis-Tool.exe) Dort gibt es oben rechts neben dem 'RAW' einen Download-Button. Laden Sie sie runter und platzieren Sie sie in einem leeren Ordner.
2. Platzieren Sie die `.csv`-Datei aus dem Schild-Export im selben Verzeichnis wie die ausführbare `Schild-WebUntis-Tool.exe`-Datei. 
Diese Datei sollte immer durch neue Exporte überschrieben werden, was am leichtesten gelingt, indem man die Schild Export Vorlage entsprechend speichert.
3. Starten Sie die `.exe`-Datei. Fehlende Konfigurationsdateien (.ini) und Ordner werden automatisch erstellt.
4. (Optional für den Fall, dass Sie die Warnungs- und E-Mail Funtkionen nutzen wollen)

   Passen Sie die generierten `.ini`-Dateien (`settings.ini` und `email_settings.ini`) an Ihre Umgebung an (zu öffnen mit Editor oder Notepad++):
   - `settings.ini` (Anpassung bei Bedarf. Es werden standardmäßig Order im Verzeichnis der .exe Datei erstellt und diese Pfade eingetragen):
     - Abweichende Wunsch-Ordnerpfade für Klassendaten (`classes_directory`) und Lehrerdaten (`teachers_directory`) können hier eingefügt werden.
   - `email_settings.ini` (Anpassung notwendig für E-Mail Versand):
     - SMTP-Konfiguration Ihrer Absender-Adresse für den E-Mail-Versand.
5. (Optional) Platzieren der Klassen und Lehrerdaten-Dateien in den Verzeichnissen.
6. Öffnen Sie die im Browser angezeigte Webseite, um das Tool zu nutzen.

## Verwendung
1. Das Programm wandelt bei einem Klick auf `Verarbeiten` aktuelle Schild-Export CSV in eine WebUntis geeignete CSV um und speichert sie im Order WebUntis Importe aktuellem Datum und Uhrzeit in der Datei. 
Dabei vergleicht das Programm diese Datei außerdem mit der zuletzt in dieses Verzeichnis exportierten Datei und stellt kritische Unterschiede als Warnungen dar.
2. Mit einem Klick auf `Emails Generieren` werden E-Mails an die Klassenlehrkräfte der von den Warnungen betroffenen Schülern/Klassen generiert.
3. Mit einem Klick auf `Emails Senden` werden diese E-Mails versendet. 
4. Durch Auswahloptionen haben Sie die Möglichkeit die Erstellung bestimmter Warnungsarten zu verhindern, sowie weitere nützliche Dateien zu erstellen, die auf WebUntis-kritische Fehler in den Stammdaten hindeuten und auch diese notdürftig abzufangen. 

## Hinweise
- **Warnungen:** Warnungen werden basierend auf Ihren Auswahlkriterien erstellt. Änderungen an Entlass- oder Aufnahmedaten, die zu Lücken in der Dokumentation führen, erfordern besondere Aufmerksamkeit.
- **E-Mails:** E-Mail-Inhalte basieren auf den generierten Warnungen und enthalten detaillierte Informationen sowie Aufforderungen zur Nachbearbeitung.
- **Testumgebung:** Nutzen Sie eine WebUntis-Spielwiese für Tests. Für Produktionsumgebungen sind keine Garantie oder Haftung gegeben.

## Update 2.0
### Änderungen:
- **Neue Warnungen:** 
  - Dokumentationslücken bei Aufnahmedatum und Entlassdatum.
  - Detaillierte Warnungsnachrichten mit betroffenen Zeiträumen.
- **E-Mail-Integration:** Vollständig generierte E-Mails für Warnungen direkt über das Tool versenden.
- **Flexibilität:** Benutzerdefinierte Auswahl, welche Warnungen erstellt oder ignoriert werden sollen.
- **Strukturverbesserungen:** Automatische Ordnererstellung für Klassendaten, Lehrerdaten und Importe.
