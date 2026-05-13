# Schild-WebUntis-Tool
**Dieses Tool ist eine Weiterentwicklung des [SchildNRW-WebUntis-Umwandlers](https://github.com/CmoneBK/SchildNRW-WebUntis-Umwandler/tree/master)**

Dieses Tool hilft dabei, Schülerdaten aus SchildNRW zu exportieren, für WebUntis aufzubereiten* und Warnungen oder Benachrichtigungen basierend auf spezifischen Kriterien zu generieren. Es unterstützt Sie bei dem Nachhalten der Änderungen und der Kommunikation an Klassenlehrkräfte, insbesondere bei kritischen Änderungen wie Entlassdaten, Aufnahmedaten, Klassenwechseln oder neu hinzustoßenden Schüler/innen. Darüber hinaus bietet es die Möglichkeit den Prozess teilweise zu automatisieren.
<a href="/Screenshots/Hauptbereich.png" target="_blank">
  <img src="/Screenshots/Hauptbereich.png" alt="Hauptbereich" width="600">
</a>

*Darunter auch insbesondere solche Daten, die im Schild-Export nicht kompatibel mit WebUntis sind (Status, Schulpflicht, Attestpflicht, Nachteilsausgleich, ... ).

## Funktionen

###  Datenquellen & Verarbeitung
<details><summary><b>🔄Datenumwandlung:</b> Automatische Anpassung von Schülerdaten aus SchildNRW für den WebUntis-Import.</summary>Daten wie Schulpflicht müssen boolsch (Nein->Ja,Ja->Nein) umgekehrt werden damit sie passen. Beim Status wird bei Schild eine 2, 6, 7, 8 ausgegeben, was in WebUntis auch boolschen Werten entspricht. Externe Schüler (Status 6) sind dabei optional als „aktiv" zu behandeln. Solche Umwandlungen können grade bei größeren Schulen und täglichem Import mühsam sein. Jetzt nicht mehr.</details>
<details><summary><b>🔍Vorab-Validierung der Importdateien:</b> Probleme erkennen, bevor sie zum Problem werden</summary>Auf Knopfdruck werden Schild-, Lehrer- und Klassendateien auf fehlende Pflichtspalten, falsche Trennzeichen und leere Verzeichnisse geprüft — bevor die eigentliche Verarbeitung gestartet wird.</details>
<details><summary><b>🏫Schild-API (Schild 3.x):</b> Direkter Zugriff auf den SVWS-Server statt CSV-Export</summary>Statt Schüler-, Klassen- und Lehrerdaten manuell aus Schild zu exportieren, kann das Tool sie ab <strong>Schild 3.x</strong> direkt vom SVWS-Server über die REST-API abrufen. Dazu wird ein technischer Benutzer mit minimalen Lese-Kompetenzen angelegt und im Tool unter <code>⚙️ Einstellungen → 🏫 Schild API</code> eingetragen. Ein Verbindungstest, ein konfigurierbarer Schuljahresabschnitt und eine Status-Whitelist (z.B. Aktiv, Abschluss, Abgang) gehören dazu. Auch Attestpflicht- und Nachteilsausgleich-Schüler können pro Vermerkart direkt über die API ermittelt werden — der separate Schild-Filter-Export entfällt dann. Pro Vermerk lässt sich einzeln zwischen CSV-Datei und SVWS-API wählen. Bei API-Fehlern fällt das Tool automatisch auf den CSV-Pfad zurück. Schild-2-Schulen oder Schulen ohne API-Zugang nutzen weiterhin nahtlos den CSV-Weg — die Funktion ist optional.</details>

###  Warnungen & Benachrichtigungen
<details><summary><b>⚠️Warnungen für Klassenlehrkräfte:</b> Generiert (auf Wunsch) Warnungen:</summary>
Menschen machen Fehler und Prozesse sind nicht immer perfekt. So kann es in Schild zu ungünstigen Eingaben kommen die aber noch ungünstigere Konsequenzen haben. Hier werden Warnungen erstellt:

  - für Entlassdaten, die in die Zukunft verschoben werden und zu einem nicht dokumentierten Zeitraum führen.
  - für Aufnahmedaten, die in die Vergangenheit verschoben werden und Dokumentationslücken verursachen.
  - für Klassenwechsel, die eine manuelle Nachbearbeitung in WebUntis erfordern.
  - für neue Schüler, die ggf. ein aktualisieren von Schülergruppen erforderlich  machen.
  - für aus dem Schild-Export verschwundene Schüler ("Karteileichen").
    </details>
<details><summary><b>📩E-Mail-Benachrichtigungen:</b> E-Mails für Klassenlehrkräfte</summary>Automatisches Generieren und Versenden von (anpassbaren) E-Mails an Klassenlehrkräfte mit detaillierten Informationen zu den Warnungen. Bei Klassenwechseln können wahlweise alte, neue oder beide Klassenlehrkräfte adressiert werden.</details>
<details><summary><b>ℹ️Info-Mails bei Feldänderungen:</b> Lehrkräfte aktiv über Änderungen informieren</summary>Frei wählbare Schülerfelder (z.B. Nachteilsausgleich, Attestpflicht, Telefonnummer) werden auf Änderungen überwacht. Bei Änderungen werden automatisch Info-Mails an die zuständigen Klassenlehrkräfte generiert. Vor dem Versand zeigt eine Vorschau-Tabelle alle Mails an — einzelne lassen sich per Checkbox abwählen. Die Feldauswahl wird geräteübergreifend in der `settings.ini` gespeichert.</details>
<details><summary><b>📢Admin Warnungen:</b> Wenn Ihre Daten durch Veralterung inkonsistent werden bekommen Sie Meldungen bevor was schiefgeht.</summary>Der Nutzer erhält per Konsole (optional Mail) Meldungen, wenn in den Schild-Daten (plötzlich) Klassen oder Klassenlehrkräfte vorkommen die in den bereitgestellten Klassen- und Lehrkräftedaten noch fehlen.</details>

###  Auswertung & Nachvollziehbarkeit
<details><summary><b>📊Dashboard mit Historien-Auswertung:</b> Statistiken und Trends auf einen Blick</summary>Eine eigene persistente Historien-Datenbank protokolliert alle Importe und Änderungen. Im Dashboard werden Statistiken, Klassen-Hotspots und Verlaufstrends mit Diagrammen dargestellt. Einzelne Klassen lassen sich über die Zeit nachvollziehen, und die gesamte Historie kann als Excel exportiert werden.</details>
<details><summary><b>🔃📜Änderungs-Log-Dateien:</b> Alle Dateiumwandlugnen werden protokolliert und bei Bedarf an Sie versendet.</summary>Nach jeder Datenumwandlung wird die aktuelle Import-Datei mit der zuvor erstellten Import-Datei vergleichen und die Unterschiede in Änderungs-Log Dateien festgehalten. Bei Angabe einer E-Mail Adresse ist auch ein Versand an diese möglich.</details>

###  Bedienung & Betrieb
<details><summary><b>🖥️Benutzerfreundliches Web-Interface:</b> Siehe Screenshots weiter unten</summary>Auswahl von zu generierenden Warnungen, Generieren von Berichten, Senden von E-Mails und Editieren der E-Mail Vorlagen (mit komfortablem WYSIWYG-Editor) sowie Ändern aller Einstellungen und Verzeichnisse direkt über den Browser. Mit Dark Mode.</details>
<details><summary><b>#️⃣Kommandozeilen-Modus:</b> Einer Voll-Automatisierung steht nichts im Weg.</summary>Auf Wunsch kann die gesammte Funktion zur besseren Automatisierung auch per Kommandozeile ausgeführt werden. Dabei gibt es auch nützliche Zusatzfunktionen wie den Log-Versand per E-Mail oder den Zeitraum-Vergleich für die Windows-Aufgabenplanung.</details>
<details><summary><b>🤖Automatische Konfiguration:</b> Entpackt sich selbst und ist portabel.</summary>Erstellt die benötigten Ordner und .ini-Dateien bei der ersten Ausführung, falls diese fehlen. Bestehende Konfigurationsdateien werden bei Updates automatisch um neue Optionen ergänzt (Auto-Patcher) — ohne manuelles Nachpflegen.</details>
<details><summary><b>🔐Sicherheit und internetunabhänige Verarbeitung:</b> Internetverbindung nur für Mail-Versand und visuelle Darstellung erforderlich</summary>Das Tool verarbeitet Daten unabhängig vom Internet. Eine Verbindung ist bei Nutzung des Kommandozeilenmodus ausschließlich für den Mail-Versand erforderlich. Im Browser-Frontend wird lediglich lesend auf externe visuelle Online Ressourchen zugegriffen. Es werden keinerlei Daten versendet. </details>

###  Zusatzfunktionen
<details><summary><b>➕Zusatzfunktionen:</b> Klassenstärkenauswertung, Attestpflicht, Nachteilsausgleich und Sonderpädagogen-Arbeitsdatei</summary>
<p>Das Tool bietet zusätzlich zur Hauptverarbeitung die Funktion, die Klassenstärken auf Grundlage des Import-Datenstandes zu ermitteln und in ein gewünschtes Verzeichnis auszugeben. Bei uns profitieren vor allem das Vertretungsteam und Stundenplaner davon, leicht an diese Daten zu kommen.</p>
<p>Die Attestpflichtfunktion fügt eine Attestpflicht-Spalte (Ja/Nein) dem WebUntis-Importdokument hinzu, basierend auf einer weiteren (per Schild leicht erstellbaren) Importdatei mit nur denjenigen Schülern mit Attestpflicht.</p>
<p>Die Nachteilsausgleichfunktion fügt eine Nachteilsausgleich-Spalte (Ja/Nein) dem WebUntis-Importdokument hinzu, analog zur Attestpflicht.</p>
<p><b>Neu in 3.0 — Nachteilsausgleich-Arbeitsdatei für Sonderpädagogen:</b> Eine Excel-Arbeitsdatei wird automatisch mit allen Schülern befüllt und enthält fünf Detailspalten (Zeitlich, Technisch, Räumlich, Personell, Sonstige Vereinbarungen) zur freien Bearbeitung durch Sonderpädagogen. Bei Nachteilsausgleich-Änderungen werden die Detailangaben automatisch in die Info-Mails übernommen — und sind in der Mail-Vorschau über einen ℹ️-Button direkt einsehbar. Vorhandene Einträge bleiben bei jedem neuen Import erhalten.</p></details>
<details><summary><b>🖼️Foto-Verwaltung:</b> Schüler-Fotos für WebUntis aufbereiten</summary>
<p>Schild kann Schüler-Fotos exportieren, benannt nach der Internen ID. Das Tool liest diese aus einem konfigurierbaren Foto-Verzeichnis und stellt im Bereich „🖼️ Fotos managen" (Button rechts in der Verarbeiten-Zeile) folgende Funktionen bereit:</p>
<ul>
<li><b>Übersicht:</b> Welche Fotos zu aktuellen Schülern passen, welche verwaist sind (Schüler nicht mehr im Import), welche bereits archiviert sind — mit Thumbnail-Vorschau.</li>
<li><b>ZIP-Export für WebUntis:</b> Die Fotos der Schüler im aktuellen Import (optional nach Schild-Status gefiltert; Standard = die im Import vorkommenden Stati) werden als ZIP gepackt. Der Dateiname ist über eine Vorlage mit Platzhaltern (Datum, Uhrzeit etc.) konfigurierbar. „📦 ZIP erstellen" legt das ZIP in einem konfigurierbaren Ausgabeverzeichnis ab; „⬇️ ZIP herunterladen" lädt es zusätzlich über den Browser.</li>
<li><b>Verwaiste archivieren:</b> Fotos von Schülern, die nicht mehr im Import sind, werden per Klick in einen Unterordner <code>Archiv</code> verschoben — so erscheinen sie nicht mehr in der Auswahl. Einzeln zurückholbar.</li>
</ul>
<p>Zusätzlich wird das Foto eines Schülers im Dashboard bei der Schülerhistorien-Suche angezeigt.</p></details>


## Voraussetzungen
<details>
<summary><b>1. Auswahlsfilter in SchildNRW und Export</b></summary>

> 💡 **Hinweis:** Wenn Sie die **Schild-API (Punkt 6)** nutzen, ist dieser Schritt **nicht nötig** — die Schülerdaten werden dann direkt vom SVWS-Server abgerufen.

- **Filtereinstellungen:**
  - Unten bei Laufbahninfo: `Schuljahr das aktuelle Schuljahr` auswählen
  - Oben rechts bei Status: `Aktiv`, `Abschluss` und `Abgänger` anwählen
  - Sie sollten diesen Filter speichern, damit Sie ihn später über "Auswahl - Vorhandene Filter laden" wieder verwenden können.
- **Ein Export aus SchildNRW als Text/Excel Export, jedoch unbedingt mit der manuell eingegebenen Dateiendung .csv.**
  - Als Seperator ist ";" zu wählen.
  - Erforderliche Daten (idealerweise auch in dieser Reihenfolge): Interne ID-Nummer, Nachname, Vorname, Klasse, Geburtsdatum, Geschlecht, vorrauss. Abschluss, Aufnahmedatum, Entlassdatum, Volljährig, Schulpflicht erfüllt, Status
  - Optionale Daten: Klassenlehrer, E-mail (privat), Telefon-Nr., Fax-Nr., Straße, Postleitzahl, Ortsname

- **Wo findet man den Export?**
  - **Schild 3:** `Verwaltung → Export → Als Excel-/Text-Dateien`. Um die `.csv`-Endung manuell eingeben zu können, beim Dateityp der Ausgabedatei *„Alle Dateien"* auswählen.
  - **Schild 2:** `Datenaustausch → Export in Text-/Excel-Dateien → Exportieren`. Auch hier als Dateityp *„Alle Dateien"* wählen.

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

> 💡 **Hinweis:** Wenn Sie die **Schild-API (Punkt 6)** nutzen, sind diese Exporte **nicht nötig** — Lehrer- und Klassendaten kommen dann direkt vom SVWS-Server.

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
<details>
<summary><b>4. Optional: Für die Attestpflicht-Spalte</b></summary>

> 💡 **Hinweis:** Wenn Sie die **Schild-API (Punkt 6)** nutzen, können Sie bei „Quelle" auf <em>SVWS-API</em> umstellen und die Vermerk-Bezeichnung direkt eintragen — der untenstehende manuelle Schild-Filter-Export entfällt dann komplett.

Falls die Attestpflicht-Spalte verwenden möchten, aktivieren Sie die Funktion und stellen einen Datensatz mit Schid wie folgt her:

Die Attestpflicht wird als Vermerk in Schild hinterlegt. Daher brauchen wir zunächst einen Filter, der alle Schüler aus dem aktuellen Schuljahr mit der Vermerkart "Attestpflicht" identifiziert.
1. Laden Sie dazu zunächst den Filter, den Sie für den normalen Schüler-Export für dieses Tool nutzen.
2. Nutzen Sie anschließend bei "Auswahl" den "Filter II". Dort:
 - Klicken Sie unten auf "Aktuelle Auswahl übernehmen"
 - Wählen oben bei Feldname "Vermerk-Art" und beim Fedlwert ihren Attestpflicht Wert.
 - Klicken Sie auf "In Filterbedingungen übernehmen".
 - Testen Sie den Filter per Klick auf Testen (Schließen Sie ihn nicht!)
 - Klicken Sie anschließend auf Speichern und geben Sie ihm einen für Sie eindeutigen und vom normalen Schüler Import Filter gut unterscheidbaren Namen
   
Jetzt haben Sie alle Schüler mit Attestpflicht in ihrem aktutellen Schuljahr ausgewählt und können Sie exportieren.

3. Erstellen Sie dazu eine neue Exportvorlage mit nur der Internen-ID-Nummer der Schüler (für Ihre Übersicht können Sie noch mehr hinzunehmen) und
stellen Sie die Ausgabedatei wie schon für den normalen Export auf .csv und in das Verzeichnis, in dem das Tool die Attestpflicht Daten abgreifen soll.

4. Fertig. Wenn die Datei exportiert und die Funktion aktiviert wurde erkennt das Tool die Schüler, fügt eine Attestpflicht Spalte hinzu und trägt bei allen aus der Datei ein Ja und bei allen anderen ein Nein ein.
</details>

<details>
<summary><b>5. Optional: Für die Nachteilsausgleich-Spalte</b></summary>

> 💡 **Hinweis:** Wie bei der Attestpflicht — bei aktivierter **Schild-API (Punkt 6)** kann die Quelle auf <em>SVWS-API</em> umgestellt werden, dann wird der Schild-Filter-Export überflüssig.

Falls die Nachteilsausgleich verwenden möchten muss dieser auch in Schild als Vermerk hinterlegt sein. Ansonsten ist das Vorgehen zu 100% äquivalent zur Attestpflicht-Spalte.

</details>

<details>
<summary><b>6. Optional: Schild-API (SVWS-Server, Schild 3.x) als Alternative zum CSV-Export</b></summary>

Ab **Schild 3.x** kann das Tool die Schüler-, Klassen- und Lehrerdaten direkt vom SVWS-Server über dessen REST-API abrufen — die manuellen Schild-Exporte (Punkt 1, 2, 3) entfallen dann. **Schild-2-Schulen** oder Schulen, die diese Option nicht freischalten möchten, können den CSV-Weg unverändert weiter verwenden.

**Voraussetzungen serverseitig:**

1. Ein laufender SVWS-Server, der vom Rechner erreichbar ist (z.B. `https://schild.schule.local` oder `https://localhost`).
2. Ein **technischer Benutzer** im SVWS-Server mit minimalen Lese-Kompetenzen. So legen Sie ihn an:
   - Im SVWS-Web-Client als Admin anmelden → unten links auf `⚙️ Einstellungen` → `Benutzerverwaltung` → auf das `+` klicken, um einen neuen Benutzer anzulegen
   - Empfohlener Name: `APIZugang` (oder ähnlich)
   - Passwort vergeben und sicher aufbewahren
   - Auf der Berechtigungs-Seite folgende vier Kompetenzen freigeben (jeweils nur den **„Ansehen"**-Haken):
     - ☑ **Schüler Individualdaten** → Ansehen
     - ☑ **Lehrerdaten** → Ansehen
     - ☑ **Schulbezogene Daten** → Ansehen
     - ☑ **Katalog-Einträge** → Ansehen
   - **Nicht** benötigt werden: Leistungsdaten, Berichte, Stundenplanung, Notenmodul, Import/Export, Datenbank-Management, Blockoperationen u.a.

**Konfiguration im Tool:**

1. Im Browser unter `⚙️ Einstellungen → 🏫 Schild API` öffnen
2. `Schild-API verwenden`: **Ja**
3. `Server-URL` (Basis ohne Pfad), `DB-Schema` (typischerweise `svwsdb`), `Benutzername` und `Passwort` des technischen Users eintragen
4. `TLS-Zertifikat prüfen`: Bei Self-signed Cert auf **Nein** lassen, in Produktion mit gültigem Zertifikat auf **Ja**
5. `Fallback auf CSV bei API-Fehler`: empfohlen **Ja** — bei Verbindungsabbruch arbeitet das Tool automatisch mit dem letzten CSV-Stand weiter
6. `Schuljahresabschnitt`: Default „Aktuell aktiver Abschnitt" — der Server liefert immer den richtigen
7. `Schild-Status` (Whitelist): Default `2, 6, 8, 9` (Aktiv, Extern, Abschluss, Abgang) — entspricht dem klassischen Schild-Filter „Aktive, Abgänger und Abschlüsse"
8. **Quellen für Attestpflicht / Nachteilsausgleich** *(unten im Tab)*: Pro Vermerk wählen Sie zwischen:
   - **CSV-Datei** (Default) — wie bisher, separater Schild-Filter-Export gemäß Voraussetzungen Punkt 4 / 5
   - **SVWS-API** — die betroffenen Schüler werden direkt vom Server über eine Vermerkart ermittelt. Tragen Sie dazu die exakte **Vermerkart-Bezeichnung** ein, wie sie in Schild definiert ist (z.B. `Attestpflicht`). Mit dem Button „🔄 Vermerkarten vom Server laden" können Sie die Liste aller in Schild definierten Vermerkarten als Vorschläge laden.
9. **Verbindung testen** anklicken — bei grünem ✅ Speichern

Bei aktiver Schild-API werden die Verzeichnisse für Klassendaten, Lehrerdaten und Schild-Exporte automatisch gesperrt (sie werden nicht mehr verwendet) und ein entsprechender Hinweis erscheint. Ist zusätzlich für Attestpflicht und/oder Nachteilsausgleich die Quelle auf <em>SVWS-API</em> gestellt, werden auch die jeweiligen Datei-Verzeichnisse (Voraussetzungen 4/5) gesperrt — pro Vermerk unabhängig.

**Bekannte Einschränkungen der API-Methode:**

- Das Feld **„vorauss. Abschlussdatum"** ist in der aktuellen SVWS-Server-Version (Stand 1.3.x) **nicht über die REST-API erreichbar**, obwohl es im Schild-Client unter „Aktuelle Laufbahndaten" sichtbar und persistent ist. Im API-Modus bleibt dieses Feld daher leer; die Option `use_abschlussdatum` (Entlassdatum durch Abschlussdatum ersetzen) wirkt entsprechend nicht. Für Schulen, die genau diese Funktion benötigen, ist der CSV-Weg vorzuziehen.
- Performance: Bei sehr großen Schulen (>2000 Schüler) dauert ein API-Lauf ca. 1–3 Minuten — der CSV-Lauf wäre deutlich schneller. Für reguläre Schulgrößen (bis ~500 Schüler) ist der Unterschied marginal.

</details>

<details>
<summary><b>7. Optional: Für die Nachteilsausgleich-Arbeitsdatei (Sonderpädagogen)</b></summary>

Falls Sonderpädagogen Nachteilsausgleich-Details (Zeitlich, Technisch, Räumlich, Personell, Sonstige Vereinbarungen) pflegen sollen, die in Info-Mails bei Änderungen mitversendet werden:

- **Keine zusätzlichen Schild-Exports nötig.** Das Tool generiert die Excel-Arbeitsdatei automatisch bei jedem Import auf Grundlage der Schülerdaten.
- **Verzeichnis konfigurieren:** In den Einstellungen unter `📂 Verzeichnisse` → `Arbeitsverzeichnisse` ein Verzeichnis für die `Nachteilsausgleich-Arbeitsdatei` festlegen. Idealerweise ein Netzlaufwerk, auf das auch die Sonderpädagogen Schreibzugriff haben.
- **Befüllung:** Sonderpädagogen öffnen die Datei `Nachteilsausgleich_Arbeitsdatei.xlsx` und tragen ihre Details in die orange markierten Spalten (`Zeitlich`, `Technisch`, `Räumlich`, `Personell`, `Sonstige Vereinbarungen`) ein. Pro Zelle sind Zeilenumbrüche und mehrere Einträge möglich.
- **Aktivierung:** Damit die Details in Info-Mails einfließen, muss `Nachteilsausgleich` als Feld im Info-Mails-Bereich aktiviert sein.

Das Tool liest die Datei bei jedem Lauf zurück, übernimmt vorhandene Einträge in die neu erstellte Datei und ergänzt nur die Schülerliste — nichts geht verloren.

</details>

<details>
<summary><b>8. Optional: Für die Foto-Verwaltung</b></summary>

Falls Sie Schüler-Fotos im Dashboard anzeigen und/oder als ZIP für den WebUntis-Foto-Import vorbereiten möchten:

- **Foto-Export aus Schild:**
  - **Schild 2:** `Datenaustausch → Fotos → Fotos exportieren`. Wählen Sie als Benennung die **Interne ID-Nummer** der Schüler.
  - **Schild 3:** `Verwaltung → Export → Fotos`. — auch hier ist die Benennung nach Interner ID-Nummer zu wählen.
- **Verzeichnis konfigurieren:** In den Einstellungen unter `📂 Verzeichnisse` → `Arbeitsverzeichnisse` das `🖼️ Foto-Verzeichnis` festlegen und die exportierten Fotos dorthin ablegen. (Das `📦 Foto-ZIP-Ausgabeverzeichnis` unter „Ausgabedateien-Verzeichnisse" bestimmt, wohin erzeugte ZIPs geschrieben werden.)
- **Verwendung:** Über den Button `🖼️ Fotos managen` (rechts in der Verarbeiten-Zeile) sehen Sie die Übersicht, erstellen ZIPs (optional nach Schild-Status gefiltert) und können verwaiste Fotos archivieren. Im Dashboard erscheint das Foto bei der Schülerhistorien-Suche automatisch.
- Unterstützte Bildformate: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`.

</details>

## Installation
1. Laden Sie die .exe Datei des [aktuellen Releases](https://github.com/CmoneBK/Schild-WebUntis-Tool/releases/tag/v.3.0) oder, wenn Sie nicht gut auf neue Funktionen warten können, die .exe Datei unter [Schild-WebUntis-Tool-WServer](https://github.com/CmoneBK/Schild-WebUntis-Tool/blob/master/Schild_WebUntis_Tool/dist/Schild-WebUntis-Tool-WServer.exe) [Entwicklungsversion] in ein leeres (!) Verzeichnis.</br>
   Hinter letzterem Link gibt es oben rechts neben dem 'RAW' einen Download-Button.
2. Platzieren Sie die `.csv`-Datei aus dem Schild-Export im selben Verzeichnis wie die ausführbare `Schild-WebUntis-Tool-WServer.exe`-Datei.</br>
Diese Datei sollte immer durch neue Exporte überschrieben werden, was am leichtesten gelingt, indem man die Schild Export Vorlage entsprechend speichert.
<details><summary>3. Starten Sie die `.exe`-Datei. Fehlende Konfigurationsdateien (.ini) und Ordner werden automatisch erstellt.</summary>
Dazu zählen die settings.ini und email_settings.ini, sowie Verzeichnisse für Klassendaten, das Lehrerdaten, Logs, ExcelExporte (auch Logs) und die WebUntis-Importe.</details>      
<details>
<summary><b>(Optional für den Fall, dass Sie die Warnungs- und E-Mail Funktionen nutzen wollen)</b></summary>
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


## Verwendung
**Hauptfunktion:**
Das Programm wandelt bei einem Klick auf `▶️ Verarbeiten` die aktuelle Schild-Export CSV in eine WebUntis geeignete CSV um und speichert sie im Unterordner `WebUntis Importe` mit dem aktuellem Datum und Uhrzeit im Dateinamen.
Dabei vergleicht das Programm diese Datei außerdem mit der zuletzt in dieses Verzeichnis exportierten Datei und stellt kritische Unterschiede als Warnungen dar.

<details>
<summary><b>🔍 Dateien prüfen (Vorab-Validierung):</b></summary>

Vor dem eigentlichen Verarbeiten kann mit `🔍 Dateien prüfen` ein schneller Check der Schild-, Lehrer- und Klassendateien ausgeführt werden. Geprüft werden u.a. fehlende Pflichtspalten, falsche Trennzeichen und leere Verzeichnisse — so erkennen Sie Probleme, bevor sie die Verarbeitung blockieren.
</details>

<details>
<summary><b>⚠️ Warnungs-Mails:</b></summary>

- Mit einem Klick auf `✍ Emails Generieren` werden E-Mails an die Klassenlehrkräfte der von den Warnungen betroffenen Schülern/Klassen generiert.
- Mit einem Klick auf `📨 Emails Senden` werden diese E-Mails versendet.

</details>

<details>
<summary><b>ℹ️ Info-Mails (Feldänderungen):</b></summary>

Über das Menü `ℹ️ Info-Mails` lassen sich Lehrkräfte über Änderungen an WebUntis-relevanten Schülerfeldern (z.B. Nachteilsausgleich, Attestpflicht, Telefonnummer) informieren:

1. Felder auswählen, die überwacht werden sollen (Auswahl wird in der `settings.ini` gespeichert).
2. `✍ Generieren` klickt — eine Vorschau-Tabelle zeigt alle generierten Mails.
3. Einzelne Mails per Checkbox abwählen, falls einzelne nicht versendet werden sollen.
4. Bei Nachteilsausgleich-Änderungen erscheint ein ℹ️-Button — Klick zeigt die zugehörigen Details aus der Sonderpädagogen-Arbeitsdatei.
5. Mit `📨 Senden` gehen die markierten Mails raus.

</details>

<details>
<summary><b>📊 Dashboard & Historie:</b></summary>

Über das Menü `📊 Dashboard` werden Statistiken, Hotspots und Verlaufstrends aus den vergangenen Importen angezeigt. Klassen lassen sich einzeln anklicken, um den Verlauf über die Zeit zu sehen. Bei der Schülerhistorien-Suche wird (falls vorhanden) das Foto des Schülers angezeigt. Über `📜 Historie` können vergangene Logs und Excel-Logs direkt im Browser eingesehen oder als Excel exportiert werden.

</details>

<details>
<summary><b>🖼️ Fotos managen:</b></summary>

Über den Button `🖼️ Fotos managen` (rechts in der Verarbeiten-Zeile) öffnet sich der Foto-Bereich:
- **Übersicht** aller Fotos im Foto-Verzeichnis mit Thumbnail, Schüler-Zuordnung und Status (im Import / verwaist / archiviert).
- **`📦 ZIP erstellen`** packt die Fotos der Schüler im aktuellen Import (optional nach Schild-Status gefiltert) und legt das ZIP im Foto-ZIP-Ausgabeverzeichnis ab. **`⬇️ ZIP herunterladen`** lädt das zuletzt erstellte ZIP über den Browser.
- **`🗄️ Verwaiste jetzt archivieren`** verschiebt Fotos von Schülern, die nicht mehr im Import sind, in den Unterordner `Archiv` — einzeln zurückholbar.

</details>

**Optionen:**
<details><summary>1. Durch die Auswahloptionen im oberen Bereich... </summary> haben Sie die Möglichkeit für den aktuellen Durchlauf die Erstellung bestimmter Warnungsarten zu verhindern, sowie weitere nützliche Dateien zu erstellen, die auf WebUntis-kritische Fehler in den Stammdaten hindeuten und auch diese notdürftig abzufangen.</details>

2. Über `⚙️ Einstellungen` können Sie alle Einstellungen dauerhaft beeinflussen — neuerdings strukturiert in **Quelldaten-**, **Arbeits-** und **Ausgabedateien-Verzeichnisse**.

3. Über `✉️ Email-Vorlagen Editor` können Sie alle E-Mail Vorlagen dauerhaft ändern (mit komfortablem WYSIWYG-Editor und Platzhalter-Dokumentation).
<details><summary>4. Mit dem `#️⃣🔗 Befehl- und Verknüpfungs-Erstelltool` können Sie... </summary> z.B. Verknüpfungen generieren die beim Doppelklick gewählte Prozesse direkt hintereinander ausführen (auch ohne dass sich überhaupt die Webseite öffnet). Gleiches gilt für Kommandozeilen-Befehle.</details>
<details><summary>5. Auf der außerdem geöffneten Konsole können Sie den Verarbeitungsprozess beobachten. </summary> Dort werden auch spezielle Admin-Warnungen angezeigt, falls in der importierten Schild-Datei Klassen oder Klassenlehrkräfte sind, die in Ihren Klassen- bzw. Lehrkräftedateien noch nicht vorkommen. Dies weist auf die Notwendigkeit der Aktualisierung hin.</details>



## Alternative Verwendung über Kommandozeile
<details>
<summary><b>Einblenden/Ausblenden</b></summary>

      
Wichtig: Die hier dargestellten Befehle lassen sich auch mit dem `#️⃣🔗 Befehl- und Verknüpfungs-Erstelltool` generieren. Dieses bietet auch Hinweise und Anleitungen.  
      
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
- `--no-directory-change` Verhindert, dass Verzeichnisse über das WebEnd geändert werden können. Dazu wird der Tab in den Einstellungen entfernt und im BackEnd Funktionen blockiert.
- `--enable-upload` Ermöglicht einen Upload von Dateien in die Verzeichnisse.⚠️ Aus Sicherheitsgründen sollte --enable-upload niemals ohne --no-directory-change verwendet werden!⚠️
- `--host` IP-Adresse, auf der der Server laufen soll (Standard: 0.0.0.0)
- `--port` Port, auf dem der Server laufen soll (Standard: 5000)
</details>

## Hinweise
- **Testumgebung:** Nutzen Sie eine WebUntis-Spielwiese für Tests. Für Produktionsumgebungen sind keine Garantie oder Haftung gegeben.


<body>
  <h2>Screenshot-Galerie</h2>
  <table border="1" cellspacing="10" cellpadding="5" align="center">
    <tr>
      <td>
        <a href="/Screenshots/Hauptbereich.png" target="_blank">
          <img src="/Screenshots/Hauptbereich.png" alt="Hauptbereich" width="300">
        </a>
        <p>Hauptbereich</p>
      </td>
      <td>
        <a href="/Screenshots/Navigation und Module.png" target="_blank">
          <img src="/Screenshots/Navigation und Module.png" alt="Navigation und Module" width="300">
        </a>
        <p>Navigation und Module</p>
      </td>
    </tr>
    <tr>
      <td>
        <a href="/Screenshots/Warnungen.png" target="_blank">
          <img src="/Screenshots/Warnungen.png" alt="Warnungen" width="300">
        </a>
        <p>Warnungen</p>
      </td>
      <td>
        <a href="/Screenshots/Admin Check und Warnungen.png" target="_blank">
          <img src="/Screenshots/Admin Check und Warnungen.png" alt="Admin Check und Warnungen" width="300">
        </a>
        <p>Admin-Check &amp; Warnungen</p>
      </td>
    </tr>
    <tr>
      <td>
        <a href="/Screenshots/Generierte Mail.png" target="_blank">
          <img src="/Screenshots/Generierte Mail.png" alt="Generierte Mail" width="300">
        </a>
        <p>Generierte Mail</p>
      </td>
      <td>
        <a href="/Screenshots/Info Mail Optionen.png" target="_blank">
          <img src="/Screenshots/Info Mail Optionen.png" alt="Info-Mail-Optionen" width="300">
        </a>
        <p>Info-Mail-Optionen</p>
      </td>
    </tr>
    <tr>
      <td>
        <a href="/Screenshots/Email Vorlagen Editor.png" target="_blank">
          <img src="/Screenshots/Email Vorlagen Editor.png" alt="E-Mail-Vorlagen-Editor" width="300">
        </a>
        <p>E-Mail-Vorlagen-Editor</p>
      </td>
      <td>
        <a href="/Screenshots/Dashboard.PNG" target="_blank">
          <img src="/Screenshots/Dashboard.PNG" alt="Dashboard" width="300">
        </a>
        <p>Dashboard</p>
      </td>
    </tr>
    <tr>
      <td>
        <a href="/Screenshots/Trends.PNG" target="_blank">
          <img src="/Screenshots/Trends.PNG" alt="Trends" width="300">
        </a>
        <p>Trends</p>
      </td>
      <td>
        <a href="/Screenshots/Historie.png" target="_blank">
          <img src="/Screenshots/Historie.png" alt="Historie" width="300">
        </a>
        <p>Historie</p>
      </td>
    </tr>
    <tr>
      <td>
        <a href="/Screenshots/Einstellungen.png" target="_blank">
          <img src="/Screenshots/Einstellungen.png" alt="Einstellungen" width="300">
        </a>
        <p>Einstellungen</p>
      </td>
      <td>
        <a href="/Screenshots/Schild 3.0 API.png" target="_blank">
          <img src="/Screenshots/Schild 3.0 API.png" alt="Schild 3.0 API" width="300">
        </a>
        <p>Schild 3.0 API <em>(in Entwicklung)</em></p>
      </td>
    </tr>
    <tr>
      <td>
        <a href="/Screenshots/Foto Manager.png" target="_blank">
          <img src="/Screenshots/Foto Manager.png" alt="Foto-Manager" width="300">
        </a>
        <p>Foto-Manager <em>(in Entwicklung)</em></p>
      </td>
      <td>
        <a href="/Screenshots/Befehl-und Verknüpfungsersteller.png" target="_blank">
          <img src="/Screenshots/Befehl-und Verknüpfungsersteller.png" alt="Befehl- und Verknüpfungsersteller" width="300">
        </a>
        <p>Befehl- und Verknüpfungsersteller</p>
      </td>
    </tr>
  </table>
</body>






 
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
<details>
<summary><b>Update 2.5</b></summary>

- **Release der Version für die Produktionsumgebung:** Die Entwicklung des Tools ist größtenteils abgeschlossen. Es wurde daher nun auch eine Version für die Produktionsumgebung veröffentlicht. Die Entwicklungsversion wird nicht mehr aktualisiert.
- **Verbesserung der Konsolen-Lesbarkeit:** Die Ausgabe auf der Konsole wurden überarbeitet (erweitert und vervollständigt) und farbcodiert, sodass man Sie besser lesen kann.
</details>
<details>
<summary><b>Update 2.6</b></summary>

- **Neue Kommandozeilen-Befehle und Funktionen:** Über die Kommandozeile lässt sich jetzt für die Nutzung als Server die Verzeichnisänderung im WebEnd deaktivieren sowie auch ein Dateiupload-Bereich aktivieren.
- **Server Modus:** Ermöglichung der Änderung von IP und Port über die Kommandozeile.
- **Bug Fixes:** Die Verzeichnisauswahl gab bei Auswahl im WebEnd nur Verzeichnisse im Programmverzeichnis zurück. 
</details>

<details>
<summary><b>Update 2.7</b></summary>

- **Warnungen für neue Schüler:** Es wurde eine Warnoption für neue Schüler hinzugefügt. In WebUntis kann dies mit der Notwendigkeit zur Aktualisierung von Schülergruppen einhergehen, sodass nun eine automatische Info erfolgen kann.
</details>
<details>
<summary><b>Update 2.8</b></summary>
- **Attestpflicht-Spalte:** Es wurde eine Funktion zur optionalen Integration der Attestpflicht hinzugefügt. Sie basiert auf dem Vermerk der Attestpflicht in Schild.
- **Nachteilsausgleich-Spalte:** Es wurde eine Funktion zur optionalen Integration der Nachteilsausgleichen hinzugefügt. Sie basiert auf dem Vermerk der Nachteilsausgleichs in Schild.
- **Klassengrößen Auswertung:** Es wurde die Option zur Generirung eines zusätzlichen Auswertungsdokuments zu den Klassengrößen/stärken hinzugefügt. Diese Datei kann so mit jedem Import generiert und Interessierten (Vertretungsteam, Stundenplaner) zur Verfügung gestellt werden.
</details>

<details>
<summary><b>Update 2.9.5</b></summary>

- **Neu - Optionale Warnungen für aus dem Schild-Export verschwundene Schüler:** Das dürfte bei dem Filter: "Aktuelles Schuljahr - Aktive, Abgänger und Abschlüsse" im Grund nie auftreten (außer vielleicht ganz zum Schluss beim Hochschulen)
- **Verbessert - Klassenwechsel Email-Versand an alle Klassenlehrer (statt nur die der alten Klasse):** Email Versand der Warnemails über Klassenwechsel wahlweise an die Klassenlehrkräfte der alten Klasse, der neuen Klasse, oder Beide.
- **Neu - Importdatei Erstellung unterbinden:** Option zum Verhindern der Erstellung der WebUntis-Importdatei wenn zum Beispiel Admin Warnungen existieren. Das ist sehr wichtig für vollautomatisierte Nutzung dieses Tools
- **Neu - Historie:** Man kann jetzt die Logs und Excel Logs vergangener Importe direkt im Webend einsehen.
- **Verbessert - Warnungen als Menüpunkt:** Warnungen werden im Webend jetzt in einem Menüpunkt dargestellt der sich automatisch öffnet wenn welche erscheinen.

Außerdem wurden einige seltenere Bugs gefixt und die Robustheit des Programms erhöht.
</details>

### Update 3.0
- **Neu - Dashboard mit Historien-Auswertung:** Eigene persistente Datenbank zur Auswertung vergangener Importe. Statistiken, Trends und Klassen-Hotspots werden direkt im Webend mit Diagrammen dargestellt. Klassen lassen sich einzeln über die Zeit nachvollziehen, und der gesamte Verlauf kann als Excel exportiert werden.
- **Neu - Info-Mails bei Feldänderungen:** Lehrkräfte können automatisch über Änderungen an WebUntis-relevanten Schülerfeldern (z.B. Nachteilsausgleich, Attestpflicht, Telefonnummer) informiert werden. Die zu überwachenden Felder sind frei wählbar und werden geräteübergreifend in der `settings.ini` gespeichert. Vor dem Versand erscheint eine Vorschau-Tabelle, in der einzelne Mails per Checkbox abgewählt werden können.
- **Neu - Nachteilsausgleich-Arbeitsdatei für Sonderpädagogen:** Eine Excel-Datei wird automatisch mit allen Schülern befüllt und enthält fünf Detailspalten (Zeitlich, Technisch, Räumlich, Personell, Sonstige Vereinbarungen) zur freien Bearbeitung durch Sonderpädagogen. Die Inhalte werden in den Info-Mails bei Nachteilsausgleich-Änderungen mitversendet und sind in der Mail-Vorschau über einen Info-Button direkt einsehbar. Vorhandene Einträge bleiben bei jedem neuen Import erhalten.
- **Neu - Vorab-Validierung der Importdateien:** Mit einem Klick werden Schild-, Lehrer- und Klassendateien auf fehlende Pflichtspalten, falsche Trennzeichen und leere Verzeichnisse geprüft, bevor die eigentliche Verarbeitung startet.
- **Neu - Zeitraum-Vergleich für automatisierte Periodik:** Über den Kommandozeilen-Schalter `--send_log_email` lässt sich der aktuelle Import gegen den letzten Stand vor einer einstellbaren Anzahl von Stunden (`timeframe_hours`, Default 24) vergleichen. Eine Sammel-Mail mit HTML-Tabelle und Excel-Anhang geht an die Admin-Adresse — mit eingebautem Spam-Schutz, sodass pro Zeitfenster nur eine Mail versendet wird. Ideal für die Windows-Aufgabenplanung.
- **Neu - Schild-Status 6 (Extern) konfigurierbar:** Externe Schüler (Schild-Status 6) können wahlweise als „aktiv" behandelt werden, sodass sie in Klassengrößen einfließen und nicht als Karteileichen gemeldet werden.
- **Neu - Drei Verzeichniskategorien:** Die Einstellungen unterscheiden jetzt zwischen Quelldaten-, Arbeits- und Ausgabedateien-Verzeichnissen mit jeweils erklärenden Beschreibungen.
- **Verbessert - WYSIWYG-Email-Editor:** Mail-Vorlagen werden in einem komfortablen Quill-Editor mit Formatierungsmöglichkeiten bearbeitet. Alle Platzhalter sind im neuen Schlüssel-Info-Tab dokumentiert.
- **Verbessert - Auto-Patcher für Konfigurationsdateien:** Bestehende `settings.ini` und `email_settings.ini` werden bei Updates automatisch um neue Optionen ergänzt — ohne manuelles Nachpflegen.
- **Verbessert - Modulare Architektur:** Das Webend wurde in einzelne JS-Module aufgeteilt (Dashboard, Settings, Panels, Email-Editor, Upload), was zukünftige Erweiterungen deutlich erleichtert.
- **Bug Fix - Klassenlehrkräfte in Mails:** In bestimmten Konstellationen waren Klassenlehrkräfte fälschlich als „N/A" markiert — durch eine fehlerhafte Schlüsselnormalisierung. Dies wurde behoben.
- **Bug Fix - Excel-ID-Behandlung:** Numerische Schüler-IDs wurden nach dem Speichern in Excel teilweise als Float interpretiert (z.B. `12345.0`), was zu Fehlzuordnungen führen konnte. IDs werden jetzt sauber normalisiert.

Außerdem wurden zahlreiche kleinere Verbesserungen, Bug Fixes und Robustheitsmaßnahmen umgesetzt.

### Update 3.1 (in Entwicklung)
- **Neu - Schild-API (SVWS-Server):** Ab Schild 3.x kann das Tool Schüler-, Klassen- und Lehrerdaten direkt vom SVWS-Server über dessen REST-API abrufen — der manuelle CSV-Export aus Schild entfällt dann. Konfigurierbar sind: Server-URL, DB-Schema, technischer Benutzer, TLS-Verifikation, automatischer Fallback auf CSV bei API-Fehlern, Schuljahresabschnitt-Auswahl und Status-Whitelist. Auch Attestpflicht- und Nachteilsausgleich-Listen können pro Vermerk wahlweise via API (Vermerkart-Bezeichnung) oder weiter via CSV bezogen werden. Bei aktivem API-Modus werden die nicht mehr benötigten Verzeichnisse im Webend automatisch gesperrt. Schild-2-Schulen nutzen weiterhin nahtlos den CSV-Weg.
- **Neu - Foto-Verwaltung:** Schüler-Fotos (aus Schild exportiert, benannt nach Interner ID) werden im Dashboard bei der Schülerhistorien-Suche angezeigt. Über den Bereich „🖼️ Fotos managen" lassen sich Fotos als ZIP für den WebUntis-Foto-Import packen (optional nach Schild-Status gefiltert, mit konfigurierbarer Dateinamen-Vorlage; ZIP wird in ein Ausgabeverzeichnis geschrieben und/oder heruntergeladen) und verwaiste Fotos (Schüler nicht mehr im Import) in einen Archiv-Unterordner verschieben.
