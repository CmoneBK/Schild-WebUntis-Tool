# Schild-WebUntis-Tool

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
#### Hinweise
  - Es wird nicht funktionieren, wenn Sie die Datei als Excel-Datei exportieren und diese als .csv abspeichern.
  - Speichern Sie sich diese Exporteinstellung als Vorlage ab, um sie später schneller wieder verwenden zu können.
  
### 2. Ein in WebUntis korrekt konfigurierter Import
- Als Zeichensatz ist UTF-8 zu wählen.
![Korrekt konfigurierter WebUntis Import](/WebUntis%20Importeinstellungen.png)

### 3. Optional: Stammdaten Exporte für Warnungs-Funktion
Falls die Warnungs-Funktion genutzt werden soll (z. B. E-Mail-Benachrichtigungen an Klassenleitungen), benötigen Sie:

- **Stammdaten-Export der Lehrkräfte:**  
  - In WebUntis unter `Stammdaten -> Lehrkräfte`.  
  - Scrollen Sie nach unten zur Seite `Berichte` und wählen Sie den CSV-Bericht bei "Lehrkräfte".  
  - **Hinweis:** Das Feld für die E-Mail-Adressen muss mit den Dienst-E-Mail-Adressen der Kollegen gefüllt sein.

- **Stammdaten-Export der Klassen:**  
  - In WebUntis unter `Stammdaten -> Klassen`.  
  - Kopieren Sie die Tabelle in eine Excel-Datei mit den Spalten:
    - `Klasse`, `Langname`, `Alias`, `Jahrgangsstufe`, `Text`, `Klassenlehrkraft`, `Klassenlehrkraft`, `Abteilung`, `Von`, `Bis`.
  - Exportieren Sie diese Excel-Datei anschließend als `.csv`.

**Hinweis:** Die generierten CSV-Dateien sollten im Ordner für Klassen- und Lehrerdaten gespeichert werden, der in der Datei `settings.ini` konfiguriert ist. Diese lässt sich mit dem Editor oder Notepad++ öffnen und bearbeiten. 
Wenn Sie das Verzeichnis so belassen wie es ist können Sie die Dateien in die generierten Ordner ablegen. Manche Schulen werden hierfür jedoch einen Ordner auf einem sicheren Netzlaufwerk bevorzugen.  

## Installation
1. Platzieren Sie die `.csv`-Datei im selben Verzeichnis wie die ausführbare `.exe`-Datei.
2. Starten Sie die `.exe`-Datei. Fehlende Konfigurationsdateien (.ini) und Ordner werden automatisch erstellt.
3. Passen Sie die generierten `.ini`-Dateien (`settings.ini` und `email_settings.ini`) an Ihre Umgebung an:
   - `settings.ini`:
     - Ordnerpfade für Klassendaten (`classes_directory`) und Lehrerdaten (`teachers_directory`).
   - `email_settings.ini`:
     - SMTP-Konfiguration für den E-Mail-Versand.
4. Öffnen Sie die im Browser angezeigte Webseite, um das Tool zu nutzen.

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
