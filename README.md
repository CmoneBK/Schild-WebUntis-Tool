# Schild-WebUntis-Tool
**Dieses Tool ist eine Weiterentwicklung des [SchildNRW-WebUntis-Umwandlers](https://github.com/CmoneBK/SchildNRW-WebUntis-Umwandler/tree/master)**

Dieses Tool hilft dabei, Schülerdaten aus SchildNRW zu exportieren, für WebUntis aufzubereiten* und Warnungen oder Benachrichtigungen basierend auf spezifischen Kriterien zu generieren. Es unterstützt Sie bei der Dokumentation und Kommunikation zwischen Lehrkräften, insbesondere bei kritischen Änderungen wie Entlassdaten, Aufnahmedaten oder Klassenwechseln.

*Darunter auch insbesondere solche Daten, die im Schild-Export nicht kompatibel mit WebUntis sind (Status, Schulpflicht,...).

## Funktionen
- **Datenumwandlung:** Automatische Anpassung von Schülerdaten aus SchildNRW für den WebUntis-Import.
- **Warnungen:** Generiert (auf Wunsch) Warnungen für:
  - Entlassdaten, die in die Zukunft verschoben werden und zu einem nicht dokumentierten Zeitraum führen.
  - Aufnahmedaten, die in die Vergangenheit verschoben werden und Dokumentationslücken verursachen.
  - Klassenwechsel, die eine manuelle Nachbearbeitung in WebUntis erfordern.
- **E-Mail-Benachrichtigungen:** Automatisches Generieren und Versenden von (anpassbaren) E-Mails an Klassenlehrkräfte mit detaillierten Informationen zu den Warnungen.
- **Benutzerfreundliches Web-Interface:** Auswahl von Kriterien für Warnungen, Generieren von Berichten, Senden von E-Mails und Editieren der E-Mail Vorlagen sowie allen anderen Einstellungen direkt über den Browser.
- **Automatische Konfiguration:** Erstellt die benötigten Ordner und .ini-Dateien bei der ersten Ausführung, falls diese fehlen.
- **Admin Warnungen:** Der Nutzer erhält per Konsole (optional Mail) Meldungen, wenn in den Schild-Daten (plötzlich) Klassen oder Klassenlehrkräfte vorkommen die in den bereitgestellten Klassen- und Lehrkräftedaten noch fehlen.
- **Änderungs-Log-Dateien:** Nach jeder Datenumwandlung wird die aktuelle Import-Datei mit der zuvor erstellten Import-Datei vergleichen und die Unterschiede in Änderungs-Log Dateien festgehalten.
- **Kommandozeilen-Modus:** Auf Wunsch kann die gesammte Funktion zur besseren Automatisierung auch per Kommandozeile ausgeführt werden. Dabei gibt es auch nützliche Zusatzfunktionen wie den Log-Versand per E-mail.

## Voraussetzungen
<details>
<summary><b>1. Auswahlsfilter in SchildNRW und Export</b></summary>

- **Filtereinstellungen:**
  - Unten bei Laufbahninfo: `Schuljahr das aktuelle Schuljahr` auswählen
  - Oben rechts bei Status: `Aktiv`, `Abschluss` und `Abgänger` anwählen
  - Sie sollten diesen Filter speichern, damit Sie ihn später über "Auswahl - Vorhandene Filter laden" wieder verwenden können.
- **Ein Export aus SchildNRW als Text/Excel Export, jedoch unbedingt mit der manuell eingegebenen Dateiendung .csv.**
  - Als Seperator ist ";" zu wählen.
  - Erforderliche Daten (idealerweise auch in dieser Reihenfolge): Interne ID-Nummer, Nachname, Vorname, Klasse, Klassenlehrer, Geburtsdatum, Geschlecht, vorrauss. Abschluss, Aufnahmedatum, Entlassdatum, Volljährig, Schulpflicht erfüllt, Status
  - Optionale Daten: E-mail (privat), Telefon-Nr., Fax-Nr., Straße, Postleitzahl, Ortsname

**Hinweise:** Dies wird nicht funktionieren, wenn Sie die Datei als Excel-Datei exportieren und diese als .csv abspeichern. Ergänzen Sie stattdessen manuell die Endung .csv nachdem Sie als Exporttyp die Textdatei ausgewählt haben. Speichern Sie sich diese Exporteinstellung als Vorlage ab, um sie später schneller wieder verwenden zu können.

[Beispiel-Schild-Export](/Beispiel-Dateien/SchildExport.csv)

</details>
<details>
<summary><b>2. Ein in WebUntis korrekt konfigurierter Import</b></summary>

- Als Zeichensatz ist UTF-8 zu wählen.

  <img src="/Beispiel-Dateien/WebUntis%20Importeinstellungen.png" alt="Korrekt konfigurierter WebUntis Import" width="400" />

</details>
<details>
<summary><b>3. Optional: Stammdaten Exporte für Warnungs-Funktion</b></summary>

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

**Hinweise:**  
Die generierten CSV-Dateien sollten im Ordner für Klassen- und Lehrerdaten gespeichert werden, die Sie durch die Installation des Programms angelegt und ggf. durch Sie angepasst wurden.
Wenn Sie das Verzeichnis so belassen habne wie sie waren, können Sie die Dateien jetzt schon in die generierten Ordner ablegen. Manche Schulen werden hierfür jedoch einen Ordner auf einem sicheren Netzlaufwerk bevorzugen.  

- **SMTP-Login-Daten Ihres E-Mail Anbieters:**
  Diese sollten Sie haben und bereithalten. Erstellen Sie am besten einen separaten E-Mail Account speziell zum Versand der hier generierten E-Mails. Weiteres unter 'Installation'.

</details>


## Installation
1. Die .exe Dateien finden Sie unter: </br>[Schild-WebUntis-Tool.exe](https://github.com/CmoneBK/Schild-WebUntis-Tool/blob/master/Schild_WebUntis_Tool/dist/Schild-WebUntis-Tool.exe) (für Test-Umgebung, wird nicht mehr aktualisiert) </br>[Schild-WebUntis-Tool-WServer.exe](https://github.com/CmoneBK/Schild-WebUntis-Tool/blob/master/Schild_WebUntis_Tool/dist/Schild-WebUntis-Tool-WServer.exe) (für Produktions-Umgebung).</br>
Dort gibt es oben rechts neben dem 'RAW' einen Download-Button. Laden Sie sie runter und platzieren Sie sie in einem leeren Ordner.
  
   ⚠️Derzeit kommte es zu falsch Positiv Meldungen (Win64:Evo-gen [Trj]) von Norton und ggf. auch anderen.</br>
   Ich bin an der Sache dran und habe die Datei zur Neubewertung nach Norton geschickt. </br>
   https://safeweb.norton.com/file_dispute; Prüfnummer: 8e0216e5-e864-4b46-8597-d306649b0879 </br>
   Nutzen Sie in der Zwischenzeit https://nordvpn.com/de/file-checker/⚠️
   
3. Platzieren Sie die `.csv`-Datei aus dem Schild-Export im selben Verzeichnis wie die ausführbare `Schild-WebUntis-Tool.exe`-Datei. 
Diese Datei sollte immer durch neue Exporte überschrieben werden, was am leichtesten gelingt, indem man die Schild Export Vorlage entsprechend speichert.
4. Starten Sie die `.exe`-Datei. Fehlende Konfigurationsdateien (.ini) und Ordner werden automatisch erstellt.
<details>
<summary><b>4. (Optional für den Fall, dass Sie die Warnungs- und E-Mail Funktionen nutzen wollen)</b></summary>
<br>
  
Passen Sie im Browser Ihre Standard-Einstellungen im Bereich `⚙️ Einstellungen` an Ihre Umgebung an:

- Wählen Sie ein Wunsch-Verzeichnis für die Klassendaten 🏫. Sie werden zur Identifkation der Klassenlehrkräfte genutzt.
- Wählen Sie ein Wunsch-Verzeichnis für die Lehrerdaten 🧑‍🏫. Sie werden zur Identifkation der Namen und E-Mail Adressen der Klassenlehrkräfte genutzt.
- Wählen Sie unter `⚠️ Warnungen`, welche Warnungen standardmäßig generiert werden sollen.
- Geben Sie unter `📤 SMTP` die Server- und Logindaten der E-Mail Adresse ein, von der aus die Warnungen gesendet werden sollen.
- Falls Sie die sichere Authentifizierung O-Auth nutzen, geben Sie die entsprechenden Daten im Feld `🔐 O-Auth` ein.
- Falls Sie außerdem Admin-Warnungen und Änderungs-Logs erhalten wollen, geben die bevorzugete Empfangsadresse unter `📧 Admin-Kontakt` ein.
- Falls Sie für den Versand der Änderungs-Logs einen Zeitraum definieren möchten, in dem sie unabhägig davon wie oft der Import ausgeführt wird keine zweite E-Mail erhalten möchten, geben Sie den Zeitraum unter `🎛️Konsole` ein. Dies ist nur wirksam, wenn das Programm über die Kommandozeile gesteuert wird.

Platzieren Sie schließlich die Klassen- und Lehrerdaten-Dateien in den Verzeichnissen. 

<details><summary>Alternativ lassen sich diese Einstellungen auch direkt in den .ini Dateien anpassen</summary>
  
- **`settings.ini`** (Anpassung bei Bedarf. Es werden standardmäßig Ordner im Verzeichnis der `.exe`-Datei erstellt und diese Pfade eingetragen):
  - Abweichende Wunsch-Ordnerpfade für Klassendaten (`classes_directory`) und Lehrerdaten (`teachers_directory`), sowie auch Logfiles (`log_directory`, `xlsx_directory`) können hier eingefügt werden.
  - Für die Nutzung über die Kommandozeile kann hier außerdem ein Zeitintervall (`timeframe_hours`) festgelegt werden wie alt die zuvor geneierte ImportDatei mindestens sein muss für einen Änderungs-Vergleich und Log-Versand per Email relevant zu sein und in welchem kein zweiter Mail-Versand stattfinden kann.
  - Außerdem können Sie hier die Standard-Einstellungen zur Verarbeitung im WebEnd bzw. in der Kommandozeile anpassen.
    
- **`email_settings.ini`** (Anpassung notwendig für E-Mail Versand):
  - SMTP-Konfiguration Ihrer Absender-Adresse für den E-Mail-Versand.
  - Option zur Hinterlegung einer Admin-Email-Adresse für den Versand/Erhalt der Admin-Warnungen und Änderungs-Logs.
  - Email-Vorlagen können hier alternativ zum WebEnd-Editor auch per Coding angepasst werden.
    
</details>
</details>

5. Öffnen Sie die im Browser angezeigte Webseite, um das Tool zu nutzen.

## Verwendung
Hauptfunktion:
1. Das Programm wandelt bei einem Klick auf `Verarbeiten` die aktuelle Schild-Export CSV in eine WebUntis geeignete CSV um und speichert sie im Unterorder `WebUntis Importe` mit dem aktuellem Datum und Uhrzeit im Dateinamen. 
Dabei vergleicht das Programm diese Datei außerdem mit der zuletzt in dieses Verzeichnis exportierten Datei und stellt kritische Unterschiede als Warnungen dar.

<details>
<summary>E-Mail-Funktion:</summary>

2. Mit einem Klick auf `Emails Generieren` werden E-Mails an die Klassenlehrkräfte der von den Warnungen betroffenen Schülern/Klassen generiert.

3. Mit einem Klick auf `Emails Senden` werden diese E-Mails versendet.

</details>

Optionen: 
- Durch Auswahloptionen haben Sie die Möglichkeit die Erstellung bestimmter Warnungsarten zu verhindern, sowie weitere nützliche Dateien zu erstellen, die auf WebUntis-kritische Fehler in den Stammdaten hindeuten und auch diese notdürftig abzufangen.
- Auf der außerdem geöffneten Konsole können Sie den Verarbeitungsprozess beobachten. Dort werden auch spezielle Admin-Warnungen angezeigt, falls in der importierten Schild-Datei Klassen oder Klassenlehrkräfte sind, die in Ihren Klassen- bzw. Lehrkräftedateien noch nicht vorkommen. Dies weist auf die Notwendigkeit der Aktualisierung hin.



## Alternative Verwendung über Kommandozeile
<details>
<summary><b>Einblenden/Ausblenden</b></summary>
  
- Navigieren Sie in das Verzeichnis der `.exe`, klicken Sie auf die Adresszeile im Explorer, geben Sie `cmd` ein und drücken Sie Enter.
   
- Variante A: Geben Sie `Schild-WebUntis-Tool.exe --no-web --process` ein und drücken Sie Enter. Es wird nur die Hauptfunktion ausgeführt. Warnungen werden nur auf der Konsolde dargestellt.

-  Variante B: Geben Sie `Schild-WebUntis-Tool.exe --no-web --process --generate-emails --send-emails` ein und drücken Sie Enter. Die Warnungen werden per Mail an die Klassenlehrkräfte versendet (korrekte Konfiguration vorrausgesetzt). 
   
In der Konsole sehen Sie den Prozess durchlaufen.

<b>Verfügbare Argumente für die Kommandozeile:</b>
- `--no-web` deaktiviert dabei die Weboberfläche.
- `--process` verarbeitet die Dateien mit den Standardeinstellungen der Weboberfläche (alle Warnungen werden generiert).
- `--generate-emails` generiert die E-Mails auf Grundlage der `email_settings.ini`.
- `--send-emails` versendet die generierten E-Mails auf Grundlage der `email_settings.ini`.
- `--skip-admin-warnings` ermöglicht es, das Generieren von Admin-Warnungen zu deaktivieren.
- `--send-admin-warnings` sendet vorhandene Admin-Warnungen an die in der `email_settings.ini` definierte Admin-E-Mail-Adresse.
- `--no-log` verhindert die Erstellung der `.log`-Datei bei der Verarbeitung. (Funktioniert auch mit WebEnd)
- `--no-xlsx` verhindert die Erstellung der `.xlsx`-Datei bei der Verarbeitung. (Funktioniert auch mit WebEnd)
- `--send-log-email` Ermöglicht den Versand eines Änderungs-Logs (HMTL Tabelle + .xlsx-Datei) per Mail auf Grundlage eines Zeitintervalls für das Mindestalter der Vergleichs-Datei

</details>


## Hinweise
- **Testumgebung:** Nutzen Sie eine WebUntis-Spielwiese für Tests. Für Produktionsumgebungen sind keine Garantie oder Haftung gegeben.
- **Screenshots:** 
  <br>
  <img src="/Screenshots/Start Ohne Daten.png" alt="Start Ohne Daten" width="500" />
  <br>
  <img src="/Screenshots/Start mit Daten.png" alt="Start mit Daten" width="500" />
  <br>
  <img src="/Screenshots/Beispiel Warnungen.png" alt="Beispiel Warnungen" width="500" />
  <br>
  <img src="/Screenshots/Email Editor NEU.png" alt="EMail Vorlagen Editor" width="500" />
  <br>
  <img src="/Screenshots/Beispiel EMail.png" alt="Beispiel EMail" width="500" />
  <br>
  <img src="/Screenshots/Einstellungs-Editor.png" alt="Einstellungs-Editor" width="500" />
  <br>
  <img src="/Screenshots/Befehl-und Verknüpfungsersteller.png" alt="Befehl-und Verknüpfungsersteller" width="500" />

 
## Updates
<details>
<summary><b>Update 2.0</b></summary>

- **Neue Warnungen:** 
  - Dokumentationslücken bei Aufnahmedatum und Entlassdatum.
  - Detaillierte Warnungsnachrichten mit betroffenen Zeiträumen.
- **E-Mail-Integration:** Vollständig generierte E-Mails für Warnungen direkt über das Tool versenden.
- **Flexibilität:** Benutzerdefinierte Auswahl, welche Warnungen erstellt oder ignoriert werden sollen.
- **Strukturverbesserungen:** Automatische Ordnererstellung für Klassendaten, Lehrerdaten und Importe.

</details>

<details>
<summary><b>Update 2.1</b></summary>

- **Vorlagen-Editor:** Die Email-Vorlagen lassen sich in einer `.ini` Datei und in einem Web-Editor anpassen.
- **Bug-Fix:** Das aktuelle Datum wird bei nicht-dokumentierten Zeiträumen jetzt korrekt berücksichtigt.

</details>
<details>
<summary><b>Update 2.2</b></summary>

- **Kommandozeilen-Argumente:** Es ist nun möglich, das Tool auch von der Kommandozeile aus zu bedienen.
- **Admin-Warnungen:** Bei im Vergleich zur Importdatei fehlenden Klassen oder Klassenlehrkräften in der Klassen- oder Lehrkraftdatei werden Admin-Warnungen generiert und bei Nutzung der Kommandozeile auf Wunsch auch an die hinterlegte Admin Email-Adresse gesendet.
- **Anpassung von Verarbeitungs-Standard-Einstellungen:** Die Standard-Einstellungen für die Verarbeitung im WebEnd bzw. die Verarbeitung über die Kommandozeile lassen sich jetzt über die settings.ini anpassen.

</details>
<details>
<summary><b>Update 2.3</b></summary>
  
- **Änderungs-Log Funktion:** Nach jeder Datenumwandlung wird die aktuelle Import-Datei mit der zuvor erstellten Import-Datei vergleichen und die Unterschiede in Änderungs-Log Dateien festgehalten. 
- **Mehr Kommandozeilen-Argumente:** Es möglich die Erstellung der Änderungs-Logs per Kommandozeilen-Argumente zu unterbinden und Änderungs-Logs per E-Mail (auch auf Grundlage eines Zeitintervalls für das Mindestalter der Vergleichs-Datei) zur zu erhalten. 
</details>
<details>
<summary><b>Update 2.4</b></summary>
  
- **FrontEnd-Einstellungs-Editor:** Alle Standard-Einstellungen lassen sich jetzt über einen Editor im Browser ändern. Darunter Verzeichnisse, Warn-Einstellungen, SMTP-Einstellungen, die Admin-Email Adresse für die Logs,... . Einfach alles :).
- **Befehl-/Verknüpfungs-Ersteller:** Es wurde ein Tool hinzugefügt, mit dem Sie Verknüpfungen und Eingabeaufforderungs-Befehle erstellen können, die bei Ausführung sämtliche gewünschten Funktionen ausführen ohne im (sich nur noch optional öffnenden) WebEnd etwas klicken zu müssen.
- **Alle Verzeichnisse frei wählbar:** Auch das Verzeichnis für die WebUntis Importe ist jetzt frei wählbar.
- **Logo hinzugefügt:** Logo und Favicon für den Browser und die .exe Datei hinzugefügt.
</details>

### Update 2.5
- **Release der Version für die Produktionsumgebung:** Die Entwicklung des Tools ist größtenteils abgeschlossen. Es wurde daher nun auch eine Version für die Produktionsumgebung veröffentlicht. Die Entwicklungsversion wird nicht mehr aktualisiert.
- **Verbesserung der Konsolen-Lesbarkeit:** Die Ausgabe auf der Konsole wurden überarbeitet (erweitert und vervollständigt) und farbcodiert, sodass man Sie besser lesen kann.
