# Schild-WebUntis-Tool
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

###  Zusätzliche Workflows _(neu in 3.2)_
<details><summary><b>👨‍👩‍👧 Erzieher / Ansprechpartner — Konvertierung für WebUntis:</b> Schild → WebUntis, mit Smart-Match, Volljährig-Filter, Dummy-Fill, eindeutigen Eltern-IDs und Klassen-Report fehlender Daten.</summary>
<p>SchildNRW speichert Erzieher (Stammdaten) und Ansprechpartner (Telefonnummern) in zwei getrennten Exports. Dieser Workflow konvertiert beide in WebUntis-Import-CSVs (eine pro Erzieher-Nummer, gepackt als ZIP), mit zahlreichen Optionen:</p>
<ul>
<li><b>Klassen-Whitelist:</b> farbige Chips über den Action-Buttons (analog Ausbilder-Workflow) — wirkt einheitlich auf Vorschau, Klassen-Report und Export.</li>
<li><b>Smart-Match:</b> Telefonnummern werden per Anschluss-Art (Mutter/Vater/…) dem passenden Erzieher-Slot zugewiesen.</li>
<li><b>Volljährig-Filter / E-Mail-Pflicht / Dummy-Fill:</b> für saubere Output-Daten. Volljährigkeit primär per <code>Geburtsdatum</code> (deterministisch), Fallback per Schild-Heuristik.</li>
<li><b>Limit von 2 Erziehern aufheben:</b> zusätzliche Telefonnummern landen in <code>Erzieher_3.csv</code>, <code>_4.csv</code>, …</li>
<li><b>Eindeutige Eltern-IDs:</b> persistente IDs (<code>E00001</code>, <code>E00002</code>, …) anhand Vorname+Nachname+E-Mail — Geschwister-Eltern bekommen dieselbe ID, damit WebUntis denselben Erzieher-Account über mehrere Kinder hinweg erkennt.</li>
<li><b>Klassen-Report fehlender Erzieher:</b> Klassenweise Liste minderjähriger Schüler mit fehlenden Stammdaten, Kriterien konfigurierbar, selektiv exportierbar.</li>
<li><b>Vorschau + Quelldateien-Viewer:</b> Schüler ↔ Erzieher-Zuordnung im Browser, mit Highlighting der tatsächlich genutzten Spalten.</li>
<li><b>Ansprechpartner-CSV optional:</b> der Workflow läuft auch nur mit dem Erzieher-Export durch.</li>
<li><b>📧 KL-Mail-Versand</b> <em>(neu in 3.3)</em><b>:</b> Pro Klasse eine E-Mail an die Klassenlehrkraft mit Tabelle der aktuell in Schild hinterlegten <strong>Erzieher-/Ansprechpartner-Rohdaten</strong> (3 Spalten: Schüler / komplette Erzieher-Slot-Daten / komplette Ansprechpartner-Zeilen, jeweils als „Spaltenname: Wert"-Liste) + <strong>Excel-Anhang</strong> mit vier Sheets: <em>Erzieher</em> (1 Zeile pro Schüler, getrennte Spaltenblöcke pro Erzieher-Slot, farblich abgehoben), <em>Telefonnummern</em>, <em>Mailverteiler (alle)</em> und <em>Mailverteiler (nur Minderjährige)</em> — beide Verteiler-Sheets mit BCC-tauglicher Semikolon-Direktliste zum Copy/Paste. <strong>Volljährigkeit</strong> primär aus dem <em>Haupt-Schüler-Datensatz</em> (CSV/SVWS-API), Fallback aus dem Erzieher-Export; Excel-Spalte „Volljährig (heute)" wird per Formel (<code>DATEDIF</code>/<code>TODAY</code>) dynamisch berechnet, bei Konflikten zwischen Geburtsdatum und Schild-Markierung erscheint ein gelber Warnmarker. KL-/Stv-KL-Adresse aus den bestehenden Lehrer-/Klassen-CSVs (bzw. SVWS-API). Filter (Klassen-Whitelist, „nur Minderjährige") umschaltbar. Vorlage <code>erzieher_kl_uebersicht</code> ist im neuen <strong>KL-Mail-Vorlagen-Editor</strong> (Button im Erzieher-Modul-Bereich) WYSIWYG-bearbeitbar.</li>
<li><b>📂 Single-File-Modus:</b> Wenn die Schild-Export-Vorlage für die Schüler-Hauptverarbeitung um die Spalten <code>Erzieher 1/2:</code> + <code>Telefon-Nummern:</code> + <code>Geburtsdatum</code> + <code>Erzieher: Art (Klartext)</code> erweitert wird (in der Standard-Vorlage nicht enthalten — die Status-Box listet konkret, was fehlt), kann derselbe Schüler-Export aus dem <strong>🟦📥 Schild-Exporte-Verzeichnis</strong> (Setting <code>schildexport_directory</code>) <em>auch</em> als Erzieher-Quelle dienen — ein separater Schild-Erzieher-Export ist dann überflüssig. Mode-Auswahl <em>off / fallback / always</em> in den Erzieher-Einstellungen. Limit: max. 2 Erzieher + 1 Telefon pro Schüler (für mehr weiterhin separater Schild-Erzieher-Export).</li>
</ul>
<p><i>Hinweis: WebUntis verarbeitet derzeit nur Vorname/Nachname/E-Mail (+ optional Eltern-ID); die übrigen Felder werden mit-exportiert, falls die WebUntis-Auswertung künftig erweitert wird.</i></p></details>
<details><summary><b>🏭 Ausbilder / Betreuer — DSGVO-konformer Berufskolleg-Import:</b> Filtert Auszubildende nach VO DVI für den WebUntis-Import.</summary>
<p>Speziell für Berufskollegs in NRW: Der Schild-Ausbilder-Export wird gemäß <b>VO DVI / DSGVO</b> gefiltert, sodass nur Azubis aus freigegebenen Klassen exportiert werden — und nur jene, die der Datenverarbeitung zugestimmt haben.</p>
<ul>
<li><b>Klassen-Whitelist</b> (farbige Chips in der Schüler-Tabelle, leer = alle).</li>
<li><b>Schüler-Blacklist</b> (Häkchen pro Zeile, persistiert in <code>settings.ini</code>).</li>
<li><b>Firmen-Filter:</b> Whitelist oder Blacklist, je nach Modus. <em>(neu in 3.3)</em> Zwei Helfer-Buttons: <strong>🔄 Liste invertieren &amp; Modus wechseln</strong> (z.B. Blacklist mit 28 Firmen → Whitelist mit den restlichen 2; nicht-aktive Liste bleibt unangetastet, Round-Trip identisch) und <strong>🗑️ Aktive Liste leeren</strong> (Confirm-Dialog mit konkretem Count; Modus + andere Liste unverändert).</li>
<li>Automatischer Zeitstempel bei Datei-Konflikten — kein Überschreiben.</li>
<li><b>📧 KL-Mail-Versand</b> <em>(neu in 3.3)</em><b>:</b> Pro Klasse eine E-Mail an die Klassenlehrkraft mit HTML-Tabelle der aktuell hinterlegten Ausbilder-/Betreuer-Daten (+ Excel-Anhang). Zweck: Info + Kontrolle durch die KL, ggf. Veranlassung der Korrektur über das Sekretariat in Schild. Klassenlehrkraft-E-Mail wird über die bestehenden Lehrer-/Klassen-CSVs (bzw. SVWS-API) ermittelt — identisch zu den Warnungs-Mails. Vorschau pro Klasse vor dem Versand; Filter (Klassen-Whitelist / Schüler-Blacklist / Firmen-Filter) pro Eigenschaft umschaltbar, Stv-Klassenlehrkraft optional als CC. Vorlage <code>ausbilder_kl_uebersicht</code> ist im neuen <strong>KL-Mail-Vorlagen-Editor</strong> (Button im Ausbilder-Modul-Bereich) WYSIWYG-bearbeitbar — gleiche Quill-Editor-Infrastruktur wie der Schüler-Workflow-E-Mail-Editor, aber auf diese eine Vorlage eingeschränkt.</li>
<li><b>👥 Zusatz-Ausbilder pro Schüler</b> <em>(neu in 3.3)</em><b>:</b> Schild exportiert pro Auszubildendem nur <em>einen</em> Betreuer, auch wenn dort mehrere gepflegt sind. Eine dateibasierte JSON-DB (<code>ausbilder_extra.json</code> neben <code>settings.ini</code>) sammelt deshalb alle jemals gesehenen Schild-Ausbilder pro Schüler-ID und kann manuell um weitere Co-Ausbilder ergänzt werden. <strong>Auto-Sync</strong> bei jedem Schild-Import (Match per E-Mail → Nachname+Vorname; manuelle Einträge bleiben unangetastet). Im Workflow <strong>👥 Zusatz-Ausbilder verwalten</strong> öffnet eine Schüler-Tabelle + Modal zum Anlegen/Bearbeiten/Löschen. Beim Verarbeiten landet pro Co-Ausbilder eine zusätzliche WebUntis-Import-Zeile mit identischem Schüler-Teil und überschriebenem Betreuer-Block — KL-Mail und Klassen-Tabelle bleiben Schild-rein.</li>
<li><b>📂 Single-File-Modus:</b> Symmetrisch zum Erzieher-Workflow: wenn die Schild-Vorlage für die Schüler-Hauptverarbeitung zusätzlich um die <code>Allg. Adresse: Name1</code>- und <code>Allg. Adresse: Betreuer …</code>-Spalten ergänzt wird (Standard-Vorlage hat sie nicht — die Status-Box listet konkret, was fehlt), kann derselbe Schüler-Export aus dem <strong>🟦📥 Schild-Exporte-Verzeichnis</strong> auch als Ausbilder-Quelle dienen. Mode <em>off / fallback / always</em> in den Ausbilder-Einstellungen. Damit kann eine einzige (entsprechend angereicherte) Schild-Vorlage alle drei Workflows (Schüler / Erzieher / Ausbilder) speisen — kein paralleles Pflegen mehrerer Vorlagen mehr.</li>
</ul></details>
<details><summary><b>🧪 Beispieldateien:</b> 60 fiktive Berufskolleg-Azubis zum Ausprobieren — komplett konsistent, ohne reale Schülerdaten.</summary>
<p>Im Verzeichnis <a href="Beispieldateien/"><code>Beispieldateien/</code></a> liegen 60 fiktive Azubis in 4 Klassen, 8 Lehrkräfte, ~100 Erzieher, 12 Betriebe als CSV-Sammlung — bit-identisch zum Schild-/WebUntis-Format (Encoding, BOM, Quote-Pattern). Alle drei Workflows lassen sich direkt damit testen. Daten sind über alle 8 CSVs hinweg konsistent (gleiche IDs, Klassen, Lehrkräfte). Deterministisch generiert via <code>random.seed(2026)</code>, jederzeit per Generator-Skript regenerierbar. Setup-Anleitung: <a href="Beispieldateien/Anleitung.md"><code>Beispieldateien/Anleitung.md</code></a>.</p></details>

###  Zusatzfunktionen
<details><summary><b>➕Zusatzfunktionen:</b> Klassenstärkenauswertung, Attestpflicht, Nachteilsausgleich und Sonderpädagogen-Arbeitsdatei</summary>
<p>Das Tool bietet zusätzlich zur Hauptverarbeitung die Funktion, die Klassenstärken auf Grundlage des Import-Datenstandes zu ermitteln und in ein gewünschtes Verzeichnis auszugeben. Bei uns profitieren vor allem das Vertretungsteam und Stundenplaner davon, leicht an diese Daten zu kommen.</p>
<p>Die Attestpflichtfunktion fügt eine Attestpflicht-Spalte (Ja/Nein) dem WebUntis-Importdokument hinzu, basierend auf einer weiteren (per Schild leicht erstellbaren) Importdatei mit nur denjenigen Schülern mit Attestpflicht.</p>
<p>Die Nachteilsausgleichfunktion fügt eine Nachteilsausgleich-Spalte (Ja/Nein) dem WebUntis-Importdokument hinzu, analog zur Attestpflicht.</p>
<p><b>Neu in 3.0 — Nachteilsausgleich-Arbeitsdatei für Sonderpädagogen:</b> Eine Excel-Arbeitsdatei wird automatisch mit allen Schülern befüllt und enthält fünf Detailspalten (Zeitlich, Technisch, Räumlich, Personell, Sonstige Vereinbarungen) zur freien Bearbeitung durch Sonderpädagogen. Bei Nachteilsausgleich-Änderungen werden die Detailangaben automatisch in die Info-Mails übernommen — und sind in der Mail-Vorschau über einen ℹ️-Button direkt einsehbar. Vorhandene Einträge bleiben bei jedem neuen Import erhalten.</p>
<p><b>Neu in 3.3 — 🔐 Verschlüsselte Arbeitsdatei:</b> Die Arbeitsdatei darf in Excel mit einem Passwort gesichert sein. Das Tool liest sie transparent ein und speichert sie nach jedem Lauf wieder verschlüsselt zurück. Passwort wird per Windows-DPAPI in der <code>settings.ini</code> abgelegt (benutzergebunden, nie im Klartext im Webinterface sichtbar).</p></details>
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
  - **📂 Single-File-Modus (3.2, optional):** Wenn dieselbe Datei *zusätzlich* den **Erzieher**- und/oder **Ausbilder-Workflow** speisen soll, müssen die folgenden Spalten in der Schild-Export-Vorlage *ebenfalls* aktiviert werden (Datenart bleibt **Schüler**):
    - **Für Erzieher-Workflow:** `Erzieher 1: Vorname/Nachname/E-Mail` (mind. eines davon Pflicht) + empfohlen: `Erzieher 1: Anrede/Briefanrede/Titel`, `Erzieher 2: …`, `Telefon-Nummern: Anschluss-Art/Bemerkung/Telefon-Nummer`, `Geburtsdatum`, `Erzieher: Art (Klartext)`.
    - **Für Ausbilder-Workflow:** `Allg. Adresse: Name1` (Pflicht) + empfohlen: `Allg. Adresse: Betreuer Anrede/Titel/Vorname/Name/E-Mail/Telefon/Abteilung`, `Allg. Adresse: Fax-Nr.`.
    - Die Status-Box des jeweiligen Workflows zeigt nach Aktivieren des Modus *konkret* an, welche Spalten noch fehlen. Standard-Modus ist `off` (= bisheriges Verhalten, getrennte Exports), umstellbar pro Workflow auf `fallback` / `always` unter *Einstellungen → Quelle*.

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
- **Befüllung:** Sonderpädagogen öffnen die Datei `Nachteilsausgleich_Arbeitsdatei.xlsx` (oder den abweichenden Dateinamen, falls per 📋-Pfad-Auswahl angepasst) und tragen ihre Details in die orange markierten Spalten (`Zeitlich`, `Technisch`, `Räumlich`, `Personell`, `Sonstige Vereinbarungen`) ein. Pro Zelle sind Zeilenumbrüche und mehrere Einträge möglich.
- **Optional verschlüsselt (3.3):** Die Arbeitsdatei darf in Excel mit einem **Passwort** gesichert sein (`Datei → Informationen → Arbeitsmappe schützen → Mit Kennwort verschlüsseln`). Das Passwort wird einmalig unter `📂 Verzeichnisse → Arbeitsverzeichnisse → 🔐 Passwort der Arbeitsdatei` eingetragen, lokal per **Windows-DPAPI** (benutzergebunden) in der `settings.ini` verschlüsselt abgelegt und im Webinterface nie im Klartext angezeigt. Das Tool liest die Datei dann transparent und speichert sie nach jeder Aktualisierung wieder verschlüsselt zurück.
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

<details>
<summary><b>9. Optional: Für den Erzieher- / Ansprechpartner-Workflow <em>(neu in 3.2)</em></b></summary>

Falls Sie den 👨‍👩‍👧-Workflow nutzen möchten, um Erzieher-Daten von SchildNRW nach WebUntis zu konvertieren:

- **Erzieher-Export aus Schild (Pflicht):**
  - Datenart `Schüler`, Export als `.csv` mit Semikolon-Separator. Für die Erzieher-Felder mit i&nbsp;=&nbsp;1, 2, … so viele Slots wie Schild liefert (Standard: 2). **Kein Filter** nötig — der Export-Filter aus dem Schüler-Workflow (Status 2/8/9, aktuelles Schuljahr) kann übernommen werden.

  **Empfohlene All-in-One-Vorlage** *(deckt alle Optionen ab, Schild-Screenshot-konform):*

  | Spalte in Schild | Zweck |
  |---|---|
  | `Interne ID-Nummer` | **Pflicht** — Schüler-ID / Matching |
  | `Klasse` | Schüler-Stammdaten für Vorschau und Klassen-Report (entfällt Ansprechpartner-Export nicht zwingend nötig) |
  | `Nachname` | dito |
  | `Vorname` | dito |
  | `Geburtsdatum` | **deterministischer Volljährig-Check** (≥ 18 → volljährig). Ohne diese Spalte fällt das Tool auf die Schild-Heuristik via `Erzieher: Art (Klartext)` zurück |
  | `Erzieher i: Anrede` | für Smart-Match (Telefon ↔ Erzieher-Slot per Anrede-Geschlecht) |
  | `Erzieher i: Briefanrede` | Mit-Export (WebUntis nutzt aktuell nicht) |
  | `Erzieher i: Titel` | Mit-Export |
  | `Erzieher i: Nachname` | **Pflicht** — WebUntis-Stammdaten |
  | `Erzieher i: Vorname` | **Pflicht** |
  | `Erzieher i: E-Mail` | **Pflicht** (leer → Slot wird ggf. per E-Mail-Filter ausgesondert) |
  | `Erzieher: Art (Klartext)` | Volljährig-Heuristik („Schüler/in ist volljährig") + Klassen-Report-Filter |
  | `Telefon-Nummern: Anschluss-Art` | Smart-Match (Mutter / Vater / Notfallnummer / …) |
  | `Telefon-Nummern: Bemerkung` | optional, wird durchgereicht |
  | `Telefon-Nummern: Telefon-Nummer` | primäre Telefonnummer pro Schüler |

  - Datei im konfigurierten **Erzieher-Export-Verzeichnis** ablegen.
- **Ansprechpartner-Export aus Schild (Optional, aber empfohlen):**
  - Liefert weitere Telefonnummern pro Schüler sowie — bei der Schild-Standard-Vorlage — die Schüler-Stammdaten (Klasse / Vorname / Nachname), die der Erzieher-Standard-Export nicht enthält.
  - **Spalten:** `Schüler_ID`, `Telefon-Nummer`, `Anschluss-Art`, `Bemerkung`, `Schüler-Klasse`, `Schüler-Vorname`, `Schüler-Nachname`
  - Als `.csv` mit Semikolon-Separator speichern.
  - Datei im konfigurierten **Ansprechpartner-Export-Verzeichnis** ablegen.
- **Verzeichnisse konfigurieren:** Unter `👨‍👩‍👧 Erzieher / Ansprechpartner → ⚙️ Einstellungen` werden die Quelldaten- und Ausgabeverzeichnisse festgelegt.
- **Klassen-Whitelist:** Oben im Workflow-Bereich kann die Auswahl klassenweise per farbigen Chips beschränkt werden (analog Ausbilder-Workflow). Wirkt einheitlich auf Vorschau, Klassen-Report und Export. Standard: alle Klassen aktiv. Voraussetzung: Klasse muss aus Anspr-Export oder einer erweiterten Erzieher-Vorlage (Spalte `Klasse`) abrufbar sein.

> 💡 **Hinweis zur WebUntis-Realität:** WebUntis verarbeitet beim Erzieher-Import derzeit nur Vorname / Nachname / E-Mail / Schüler-ID (sowie optional die Eltern-ID). Anrede, Titel, Telefon, Anschluss-Art und Bemerkung werden trotzdem mit-exportiert, falls WebUntis seine Auswertung erweitert. Die Telefon-Verarbeitungs-Optionen sind dafür da, dass die Daten auch für eine spätere WebUntis-Nutzung sauber aufbereitet sind.

<details><summary><strong>📊 Was nutzt das Tool aus welcher Quelle?</strong> (Effekt-Matrix für die 4 typischen Konstellationen)</summary>

| Feld | Primärquelle | Fallback | Bei Konflikt |
|---|---|---|---|
| Erzieher-Vorname / -Nachname / -E-Mail | Erzieher-Export `Erzieher i: …` | — (Pflicht) | — |
| Schüler-Klasse / -Vor- / -Nachname | Anspr-Export `Schüler-…` | Erzieher-Export `Klasse` / `Vorname` / `Nachname` | Anspr gewinnt, Erzieher füllt Lücken |
| Volljährig | Erzieher-Export `Geburtsdatum` (≥ 18) | Heuristik via `Erzieher: Art (Klartext)` enthält „volljährig" | Beides ODER-verknüpft (Heuristik kann zusätzlich „volljährig" setzen) |
| Telefonnummern | Erzieher-Export `Telefon-Nummern: …` (primär, 1 pro Schüler) | Anspr-Export-Zeilen (mehrere pro Schüler) | Erzieher-Tel zuerst, Duplikate aus Anspr werden gefiltert |
| Smart-Match Anschluss-Art → Slot | `Erzieher i: Anrede` + Anschluss-Art aus Tel-Zeile | — | Fehlt eines → positionales Matching |

| Setup | Schüler-Stammdaten | Volljährig-Check | Telefonnummern |
|---|---|---|---|
| **A. Optimal** (Erz mit Klasse + Geb.-Datum + Anspr) | aus Anspr (+ Erz als Lückenfüller) | deterministisch ✓ | beide Quellen, dedupliziert |
| **B. Erz all-in-one** (Erz mit Klasse + Geb.-Datum, kein Anspr) | aus Erz | deterministisch ✓ | nur Erz-Tel (1 pro Schüler) |
| **C. Schild-Standard** (Erz minimal + Anspr) | aus Anspr; restliche leer | nur Heuristik (ungenau) | nur Anspr |
| **D. Worst case** (Erz minimal, kein Anspr) | leer | nur Heuristik | keine |

**Empfehlung:** Setup A oder B — siehe All-in-One-Vorlage oben. Anspr-Export dann nur, wenn mehrere Telefonnummern pro Schüler exportiert werden sollen.

</details>

**Beispiele** zum Ausprobieren: `Beispieldateien/ErzieherExport/ErzieherExport.csv` + `Beispieldateien/AnsprechpartnerExport/AnsprechpartnerExport.csv` (Anleitung zum Setup: [`Beispieldateien/Anleitung.md`](Beispieldateien/Anleitung.md)).

</details>

<details>
<summary><b>10. Optional: Für den Ausbilder- / Betreuer-Workflow <em>(neu in 3.2, Berufskolleg)</em></b></summary>

> ⚠️ **Hinweis zum rechtlichen Kontext:** Dieser Workflow ist speziell für **Berufskollegs in NRW** gedacht und filtert den Schild-Export gemäß **VO DVI / DSGVO**. Eine ausführliche Erläuterung der rechtlichen Grundlagen (BASS-Verweise auf §§ DSGVO Art. 6, VO DVI Anlage 1) findet sich im ℹ️-Hilfe-Modal des Ausbilder-Workflows.

Falls Sie den 🏭-Workflow nutzen möchten, um Auszubildende inkl. Ausbildungsbetrieb / Betreuer DSGVO-konform für den WebUntis-Import zu filtern:

- **Schild-Export der Auszubildenden mit Ausbilder-Spalten:**
  - **Empfohlener Filter** in Schild (nur duale Azubis mit Betrieb oder Kammer):

    ```sql
    Schueler.Geloescht='-' AND Schueler.Status IN (2,8,9) AND Schueler.AktSchuljahr = 2025
    AND ((Schueler_AllgAdr.Adresse_ID = K_AllgAdresse.ID
          AND Schueler.ID = Schueler_AllgAdr.Schueler_ID
          AND K_AllgAdresse.AllgAdrAdressArt = 'Betrieb')
      OR (Schueler_AllgAdr.Adresse_ID = K_AllgAdresse.ID
          AND Schueler.ID = Schueler_AllgAdr.Schueler_ID
          AND K_AllgAdresse.AllgAdrAdressArt = 'Kammer'))
    ```

    Damit werden ausschließlich Schüler aus dem aktuellen Schuljahr exportiert,
    die einer Schild-Adresse mit Typ `Betrieb` oder `Kammer` zugeordnet sind —
    also alle dualen Azubis. Den vollständigen Schüler-Filter zu belassen geht
    auch, dann muss die Klassen-Whitelist im Tool die nicht-dualen Bildungsgänge
    nachträglich ausfiltern. Den Filter über *„Auswahl → Filter II → Aktuelle
    Auswahl übernehmen"* und anschließend speichern.
  - **Spalten** in der Export-Vorlage:
    - **Schüler-Identifikation:** `Interne ID-Nummer`, `Nachname`, `Vorname`, `Klasse`
    - **Ausbilder / Betreuer:** `Allg. Adresse: Betreuer Vorname`, `Allg. Adresse: Betreuer Name`, `Allg. Adresse: Betreuer E-Mail`, `Allg. Adresse: Betreuer Anrede`, `Allg. Adresse: Betreuer Titel`, `Allg. Adresse: Betreuer Telefon`, `Allg. Adresse: Betreuer Abteilung`, `Allg. Adresse: Fax-Nr.`
    - **Betrieb (Übersicht):** `Allg. Adresse: Name1` (Betriebsname)
  - Als `.csv` mit Semikolon-Separator speichern.
  - Datei im konfigurierten **Ausbilder-Eingabeverzeichnis** ablegen.
- **WebUntis-Import-Vorlage:** In WebUntis eine Import-Vorlage für **Ausbildungsbeauftragte** anlegen — die genaue Spalten-Zuordnung (Schild → WebUntis) wird im ℹ️-Hilfe-Modal aufgelistet.
- **Klassen-Whitelist + Schüler-Blacklist + Firmen-Filter** werden anschließend im Tool über die integrierte Schüler-Tabelle bzw. das Einstellungs-Panel gepflegt — alles wird automatisch persistent in der `settings.ini` gespeichert.

> 💡 **DV-Einwilligung in Schild:** Falls die Checkbox `DV-Einwilligung vorh.` in Ihrer Schule konsistent und ausschließlich für die DSGVO-Einwilligung der Ausbilder-Datenübermittlung verwendet wurde, können Sie auch direkt in Schild filtern und brauchen das Tool für diesen Schritt nicht. Wurde sie aber jemals für etwas anderes mit-benutzt, ist dieses Tool der praktikable Workaround.

**Beispiel** zum Ausprobieren: `Beispieldateien/AusbilderInput/AusbilderExport.csv` (Anleitung zum Setup: [`Beispieldateien/Anleitung.md`](Beispieldateien/Anleitung.md)).

</details>

## Installation
1. Laden Sie die `.exe`-Datei in ein **leeres (!) Verzeichnis**. Es stehen zwei Versionen zur Auswahl:

   - **Stable: [v.3.2](https://github.com/CmoneBK/Schild-WebUntis-Tool/releases/tag/v.3.2)** — enthält neben dem klassischen Schüler-CSV-Workflow auch die neuen Workflows für **Erzieher / Ansprechpartner** und **Ausbilder / Betreuer** sowie den Bugfix für den **Schild-3-API-Modus** (in 3.1 war dort der Schüler-Workflow durch CSV-Pre-Checks blockiert, siehe [#1](https://github.com/CmoneBK/Schild-WebUntis-Tool/issues/1)). Frühere Releases (v.3.1 und älter) sind über den [Releases-Tab](https://github.com/CmoneBK/Schild-WebUntis-Tool/releases) erreichbar.

   <details><summary>Alternativ: bleeding-edge Entwicklungs-Build aus dem <code>master</code>-Branch</summary>

   Wer auch zwischen den Releases die jeweils neueste Entwicklung mitnehmen möchte, kann die `.exe` direkt aus dem Repo ziehen: [Schild-WebUntis-Tool-WServer.exe](https://github.com/CmoneBK/Schild-WebUntis-Tool/blob/master/Schild_WebUntis_Tool/dist/Schild-WebUntis-Tool-WServer.exe). Oben rechts neben „Raw" findet sich ein Download-Button. Dieser Build ist nicht zwingend stabil und kann zwischen offiziellen Releases unfertige Funktionen enthalten.
   </details>
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
        <p>Schild 3.0 API</p>
      </td>
    </tr>
    <tr>
      <td>
        <a href="/Screenshots/Foto Manager.png" target="_blank">
          <img src="/Screenshots/Foto Manager.png" alt="Foto-Manager" width="300">
        </a>
        <p>Foto-Manager</p>
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

<details>
<summary><b>Update 3.0</b></summary>

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
</details>

### Update 3.1
- **Neu - Schild-API (SVWS-Server):** Ab Schild 3.x kann das Tool Schüler-, Klassen- und Lehrerdaten direkt vom SVWS-Server über dessen REST-API abrufen — der manuelle CSV-Export aus Schild entfällt dann. Konfigurierbar sind: Server-URL, DB-Schema, technischer Benutzer, TLS-Verifikation, automatischer Fallback auf CSV bei API-Fehlern, Schuljahresabschnitt-Auswahl und Status-Whitelist. Auch Attestpflicht- und Nachteilsausgleich-Listen können pro Vermerk wahlweise via API (Vermerkart-Bezeichnung) oder weiter via CSV bezogen werden. Bei aktivem API-Modus werden die nicht mehr benötigten Verzeichnisse im Webend automatisch gesperrt. Schild-2-Schulen nutzen weiterhin nahtlos den CSV-Weg.
- **Neu - Foto-Verwaltung:** Schüler-Fotos (aus Schild exportiert, benannt nach Interner ID) werden im Dashboard bei der Schülerhistorien-Suche angezeigt. Über den Bereich „🖼️ Fotos managen" lassen sich Fotos als ZIP für den WebUntis-Foto-Import packen (optional nach Schild-Status gefiltert, mit konfigurierbarer Dateinamen-Vorlage; ZIP wird in ein Ausgabeverzeichnis geschrieben und/oder heruntergeladen) und verwaiste Fotos (Schüler nicht mehr im Import) in einen Archiv-Unterordner verschieben.
- **Neu - Inline-Hilfe direkt im Webend:** An vielen relevanten Stellen (Hauptbereich, Warnungs-Bereich, Schild-API, Foto-Manager, Verzeichnisse, Einstellungs-Tabs, …) sind nun kleine **ℹ️-Buttons** platziert, die die wichtigsten Inhalte der README direkt im Browser anzeigen — offline und ohne externen Link. Alle Hilfe-Themen lassen sich zusätzlich in einem **Glossar-Modus** mit Volltextsuche und thematischer Gruppierung (Bedienung, Eingabe-Dateien, Schild-API, WebUntis, Foto-Verwaltung) durchstöbern. Die Warnungs-Hilfe enthält eine anschauliche **interaktive Timeline** für jede Warnungsart (Entlass-/Aufnahmedatum-Verschiebungen, Klassenwechsel, neue Schüler, Karteileichen).

### Update 3.2
- **Neu - Top-Level Workflow-Switcher:** Das Webend ist jetzt in drei eigenständige Arbeitsbereiche gegliedert, die über Tab-Pills oben im Hauptbereich umgeschaltet werden: 👨‍🎓 **Schüler-Verarbeitung** (der bisherige Hauptbereich), 👨‍👩‍👧 **Erzieher / Ansprechpartner** und 🏭 **Ausbilder / Betreuer**. Jeder Workflow hat seinen eigenen, unabhängigen Einstellungs-Dialog (Quelldaten- und Ausgabeverzeichnisse), so dass das Schüler-Einstellungsmenü nicht mit fachfremden Verzeichnissen überladen wird. Der zuletzt verwendete Workflow wird im Browser persistiert; geöffnete Panels schließen sich beim Wechsel automatisch.
- **Neu - Erzieher- / Ansprechpartner-Konvertierung (integriert):** Das frühere Standalone-Tool *SchildNRW-WebUntis-Erzieher-Konvertierer* ist nun direkt im Haupttool eingebaut. SchildNRW speichert Erzieher (Hauptdaten) und zusätzliche Ansprechpartner (mit Telefonnummern) getrennt; der Workflow kombiniert beide Schild-Exporte, nummeriert die Ansprechpartner pro Schüler durch und erzeugt pro „n-tem" Erzieher eine eigene WebUntis-Import-CSV (`Erzieher_1.csv`, `Erzieher_2.csv`, …) — gepackt als ZIP zum Direkt-Download. Der ZIP-Dateiname ist über eine Platzhalter-Vorlage konfigurierbar.
  - **Hinweis zur WebUntis-Realität:** WebUntis verarbeitet derzeit (Stand Mai 2026) nur Vorname / Nachname / E-Mail / Schüler-ID (sowie optional die Eltern-ID). Anrede, Titel, Anschluss-Art, Bemerkung und Telefonnummer werden trotzdem mit-exportiert, damit der Import nicht angepasst werden muss, falls WebUntis seine Auswertung erweitert. Die Telefon-Verarbeitungsoptionen sind dabei kosmetisch — sie halten Vorschau und Output sauber für eine spätere WebUntis-Nutzung.
  - **🏫 Klassen-Whitelist:** Farbige Klassen-Chips über den Action-Buttons (analog zum Ausbilder-Workflow) — wirkt einheitlich auf Vorschau, Klassen-Report und Export. Default: alle Klassen aktiv. Voraussetzung: Klassen müssen aus Anspr-Export oder einer erweiterten Erzieher-Vorlage (Spalte `Klasse`) abrufbar sein.
  - **🧠 Smart-Match (Telefon ↔ Erzieher-Slot):** Telefonnummern werden anhand der Anschluss-Art (Mutter, Vater, Notfallnummer, …) dem passenden Erzieher-Slot zugewiesen.
  - **🔞 Volljährig-Filter:** Volljährige Schüler werden optional komplett aus dem Export entfernt. Volljährigkeit wird primär per `Geburtsdatum` aus dem Erzieher-Export (deterministisch, ≥ 18 Jahre) und als Fallback per Schild-Heuristik (`Erzieher: Art (Klartext)` enthält „volljährig") erkannt — eine der beiden Quellen genügt.
  - **📧 E-Mail-Pflicht:** Erzieher ohne E-Mail können optional aussortiert werden — sie könnten sich in WebUntis ohnehin nicht anmelden.
  - **🧪 Dummy-Felder:** Leere Felder werden optional mit eindeutig erkennbaren Platzhaltern (`DUMMY` / `dummy@invalid.local` / `000`) gefüllt, in WebUntis nachträglich filterbar.
  - **♾️ Limit von 2 Erziehern aufheben:** Überzählige Telefonzeilen aus dem Ansprechpartner-Export werden als virtuelle Slots `Erzieher_3.csv`, `Erzieher_4.csv` … exportiert, statt zu Orphans zu werden.
  - **📞 Telefon aus Erzieher-Export primär:** Die im Erzieher-Export direkt hinterlegte Telefonnummer hat Vorrang vor dem separaten Anspr-Export, Duplikate werden gefiltert.
  - **🆔 Eindeutige Eltern-IDs:** Schild liefert pro Erzieher keine schulweite ID — bei Geschwistern wird derselbe Erzieher mehrfach angelegt. Diese Option vergibt persistente IDs (`E00001`, `E00002`, …) anhand Vorname + Nachname + E-Mail; gespeichert in `eltern_ids.json`. Damit kann WebUntis (sobald die Auswertung kommt) denselben Erzieher über mehrere Kinder hinweg als ein Account erkennen.
  - **⚠️ Klassenweiser Report fehlender Erzieher:** Liste minderjähriger Schüler mit fehlenden Erzieher-Daten — konfigurierbare Kriterien (kein Erzieher / Nachname / Vorname / E-Mail fehlt) mit ODER-/UND-Verknüpfung. Selektiver ZIP-Export pro Klasse mit Begründungs-Spalte.
  - **👁️ Vorschau & 📄 Quelldateien-Viewer:** Tool-interne Inspektion der Schüler ↔ Erzieher-Zuordnung sowie Raw-Tabular-Anzeige der beiden Quell-CSVs mit Highlighting der tatsächlich genutzten Spalten.
  - **Ansprechpartner-CSV ist optional:** Der Workflow läuft auch mit nur dem Erzieher-Export durch. Schüler-Stammdaten (Klasse / Vorname / Nachname) werden mit Spaltennamen-Variantenerkennung aus dem Erzieher-Export gezogen, falls die Schule sie dort aufgenommen hat.
  - **📂 Single-File-Modus (Konsolidierung):** Der Schild-<em>Schüler-Export</em> **kann** — wenn die Schild-Export-Vorlage entsprechend erweitert wird — dieselben `Erzieher 1/2:` / `Telefon-Nummern:` / `Geburtsdatum` / `Erzieher: Art (Klartext)`-Spalten enthalten, die der Erzieher-Workflow erwartet. **Wichtig:** Die Standard-Vorlage aus README-Punkt 1 enthält diese Spalten **nicht** — sie müssen einmalig zur Schild-Export-Vorlage hinzugefügt werden (Datenart *Schüler*). Ist das geschehen, kann dieselbe Datei, die für die Schüler-Hauptverarbeitung im **🟦📥 Schild-Exporte-Verzeichnis** (Setting `schildexport_directory`) liegt, auch als Erzieher-Quelle dienen — ein *separater* Schild-Erzieher-Export ist dann überflüssig. Neue Mode-Auswahl in den Erzieher-Einstellungen → *Quelle für den Erzieher-Workflow*: `off` (Default, bisheriges Verhalten), `fallback` (Schüler-Export nur wenn separater Erzieher-Export fehlt), `always` (Schüler-Export hat immer Vorrang). Die Status-Box ist zweistufig: erkennt erst „ist die CSV überhaupt ein Schüler-Export?" (Marker: `Interne ID-Nummer` + mind. eine Stamm-Spalte) und dann „sind alle Single-File-Pflichtspalten vorhanden?" — bei Lücken listet sie *konkret*, welche Spalten in der Schild-Vorlage noch ergänzt werden müssen. Limit im Single-File-Modus: max. 2 Erzieher pro Schüler (gegen beliebig viele beim separaten Schild-Erzieher-Export) und max. 1 Telefonnummer pro Schüler (gegen mehrere im Anspr-Export). Auch im Ausbilder-Workflow sichtbar: grünes Badge „✓ Betreuer-Daten erkannt" — denn ein um die Allg.-Adresse-Spalten erweiterter Schüler-Export liefert sogar *mehr* Ausbilder-Felder (Anrede / Name / E-Mail / Telefon / Abteilung / Fax) als der separate Schild-Export „Allgemeine Adressen".
- **Neu - Ausbilder- / Betreuer-Import für Berufskollegs (integriert):** Das frühere Standalone-Tool *AusbilderImporterFlask* ist nun ebenfalls im Haupttool eingebaut. Speziell für Berufskollegs in NRW: Der Schild-Export der Auszubildenden inkl. Ausbildungsbetrieb / Betreuer wird **DSGVO/VO-DVI-konform** für den WebUntis-Import gefiltert. In der integrierten Schüler-Tabelle werden über farbige Chips die **Klassen-Whitelist** (welche Bildungsgänge sollen überhaupt übernommen werden — leer = alle) und über Häkchen pro Zeile die **Schüler-Blacklist** (wer hat der Datenverarbeitung *nicht* zugestimmt) gepflegt — beides wird automatisch persistent in der `settings.ini` gespeichert. Zusätzlich filterbar nach **Firma** (Whitelist oder Blacklist, je nach Modus). Die gefilterte WebUntis-Import-CSV wird mit konfigurierbarem Dateinamen erzeugt; bei Namens-Konflikten hängt das Tool automatisch einen Zeitstempel an, statt vorhandene Dateien zu überschreiben.
  - **📂 Single-File-Modus (Konsolidierung):** Symmetrisch zum Erzieher-Workflow (siehe oben): wenn die Schild-Vorlage um die Spalten `Allg. Adresse: Name1` (Pflicht für Firmen-Filter) und `Allg. Adresse: Betreuer …` (empfohlen für UI/Detail-Ansicht) erweitert wird — **die Standard-Vorlage aus README-Punkt 1 enthält sie nicht** — kann der Schild-Schüler-Export aus dem **🟦📥 Schild-Exporte-Verzeichnis** (Setting `schildexport_directory`) auch als Ausbilder-Quelle dienen und liefert sogar *mehr* Betreuer-Felder (Anrede / Titel / Vorname / Name / E-Mail / Telefon / Abteilung) als der separate Schild-Export „Allgemeine Adressen" (dort nur Freitext-Feld). Mode-Auswahl in den Ausbilder-Einstellungen → *Quelle für den Ausbilder-Workflow*: `off` (Default, bisheriges Verhalten — `ausbilder_input_directory`), `fallback` (Schüler-Export nur wenn AusbilderInput leer), `always` (Schüler-Export hat immer Vorrang). Status-Box-Logik identisch zum Erzieher-Workflow: zeigt bei Lücken *konkret*, welche Spalten in der Schild-Vorlage noch fehlen. Damit kann **eine einzige (entsprechend angereicherte) Schild-Export-Datei alle drei Workflows speisen** (Schüler / Erzieher / Ausbilder) — kein paralleles Pflegen mehrerer Schild-Vorlagen mehr.
- **Neu - Beispieldateien für alle Workflows:** Im neuen `Beispieldateien/`-Verzeichnis liegen 60 fiktive Berufskolleg-Azubis in 4 Klassen, 8 Lehrkräfte, ~100 Erzieher und 12 Ausbildungsbetriebe als komplett konsistente CSV-Sammlung. Das Format ist bit-identisch zu echten Schild-/WebUntis-Exporten (Encoding, BOM, Zeilenenden, Quote-Pattern); die Daten sind deterministisch generiert via `random.seed(2026)`. Ideal zum Ausprobieren des Tools ohne reale Schülerdaten — alle drei Workflows lassen sich direkt damit testen.
- **Verbessert - Pandas-frei portiert:** Beide integrierten Workflows wurden bewusst ohne Pandas-Abhängigkeit umgesetzt (nur Python-Bordmittel: `csv`, `configparser`), so dass die EXE-Größe nicht aufgebläht wird. Encoding wird automatisch erkannt (UTF-8-BOM → UTF-8 → cp1252-Fallback).
- **Verbessert - Inline-Hilfe erweitert:** Beide neuen Workflows haben eigene ℹ️-Buttons mit ausführlicher Hilfe (Vorbereitungs-Schritte, Verarbeitungs-Ablauf, DSGVO-Hintergrund beim Ausbilder-Workflow, exakte Spalten-Tabellen nach Verwendungszweck gruppiert) und sind im Glossar-Modus unter „🛠️ Bedienung & Workflows" auffindbar.
- **Bug Fix - Schild-API-Modus blockierte Schüler-Workflow:** Im aktiven SVWS-API-Modus erschien beim Öffnen der Schüler-Seite hartnäckig der rote Fehler-Banner „Die Haupt-CSV-Datei fehlt im Hauptverzeichnis…", und das ▶️ Verarbeiten-POST schlug am gleichen Pre-Check fehl — die API-Verarbeitung lief gar nicht erst an (Siehe [#1](https://github.com/CmoneBK/Schild-WebUntis-Tool/issues/1)). Insgesamt vier Stellen waren betroffen: `index()` (Schüler-Seite), `validate_imports()` (Datei-prüfen-Button), `admin_warnings()` (Klassen-CSV-Reread) sowie die Option „zweite Importdatei" in `save_files()`. Alle Pre-Checks sind jetzt `use_api`-bewusst; die „zweite Importdatei" wurde so refaktoriert, dass sie keinen Quell-CSV-Reread mehr braucht (Filter direkt auf den bereits eingelesenen Schülerdaten). CSV-Modus verhält sich unverändert.

### Update 3.3 _(In Entwicklung)_
- **Neu - Passwortgeschützte Sonderpädagogen-Arbeitsdatei:** Die `Nachteilsausgleich_Arbeitsdatei.xlsx` darf jetzt in Excel mit einem **Passwort** gesichert sein (`Datei → Informationen → Arbeitsmappe schützen → Mit Kennwort verschlüsseln`) — sinnvoll auf Netzlaufwerken mit weiterem Mitleser-Personal. Das Tool liest verschlüsselte Dateien transparent ein (per `msoffcrypto-tool`) und speichert sie nach jedem Aktualisierungslauf wieder mit demselben Passwort zurück, sodass die Datei nie ungeschützt auf dem Share liegt.
  - **Passwort-Eingabe** unter `⚙️ Einstellungen → Verzeichnisse → Arbeitsverzeichnisse → 🔐 Passwort der Arbeitsdatei` (neues Feld direkt unter dem Verzeichnis-Pfad). 👁-Button für Sichtbarkeits-Toggle, 🗑️-Button zum Entfernen eines hinterlegten Passworts.
  - **Verschlüsselte Ablage** in der `settings.ini` per **Windows-DPAPI** (`win32crypt.CryptProtectData`, gebunden an aktuellen Windows-Benutzer + Rechner — Klartext-Passwort verlässt nie diesen Kontext). Praefix in der ini: `dpapi:<base64>`. Auf nicht-Windows-Systemen fällt das Tool ehrlich auf Klartext zurück (Praefix `plain:` + UI-Warnhinweis), damit kein falsches Sicherheitsgefühl entsteht. Im Webinterface wird das Passwort **niemals** im Klartext angezeigt — nur der Status „hinterlegt".
  - **Robust bei falschem Passwort:** Statt die vorhandenen Sonderpädagogen-Details zu überschreiben, **überspringt** das Tool die Aktualisierung mit klarem Fehlertext im Konsolen-Log; Info-Mails gehen dann ohne Sonderpädagogen-Details raus.
- **Neu - Concurrency-Schutz + manueller Refresh-Button für die Sonderpädagogen-Arbeitsdatei:** Wenn die Arbeitsdatei mit einem anderen Tool (z.B. **SoPaed-Tool**) oder direkt in Excel geteilt wird, sind echte gleichzeitige Schreibvorgänge möglich — ohne Schutz hätte das ein klassisches **Lost-Update-Problem** zur Folge (der zweite Schreibende überschreibt die Änderungen des ersten). Schild-WebUntis-Tool fängt das jetzt mit zwei Best-Effort-Mechanismen ab:
  - **Excel-Lock-Marker-Erkennung:** Vor dem Schreibvorgang wird geprüft, ob Excel die Datei aktuell geöffnet hält (Existenz der `~$<Dateiname>`-Lock-Datei, die Excel beim Öffnen anlegt). Falls ja: Update überspringen mit klarer Konsolen-Meldung, statt mit kryptischem OS-Fehler abzubrechen. Helper-Funktionen `excel_lock_marker_path()` + `is_excel_open()` in `xlsx_crypto.py`.
  - **Optimistic-Concurrency-Check via mtime/size:** Beim Lesen wird ein Snapshot `(st_size, st_mtime_ns)` der Datei gemerkt. Direkt vor dem Schreiben re-checken — wenn sich entweder Größe oder Modifikationszeit geändert hat (SoPaed-Tool, paralleler Schild-WebUntis-Tool-Lauf), Update überspringen mit klarer Meldung. Schließt das TOCTOU-Fenster nicht zu 100% (Millisekunden zwischen letztem Check und `os.replace`), fängt aber in der Praxis alle realistischen Fälle.
  - **Keine Datenlücke:** Beide Schutz-Pfade sind sicher gegenüber dem nächsten Lauf — `update_nachteilsausgleich_excel` schreibt jedes Mal frisch komplett neu und die Info-Mail-Auslöse-Logik vergleicht gegen die letzte tatsächlich geschriebene WebUntis-Import-CSV (nicht gegen die übersprungene). Heißt: Übersprungene Updates trickeln beim nächsten erfolgreichen Lauf automatisch durch, keine Änderung geht permanent verloren.
  - **🔄 „Jetzt aktualisieren"-Button:** Neuer Button neben dem Pfad-Feld (Einstellungen → Verzeichnisse). Triggert die Arbeitsdatei-Aktualisierung **ad-hoc**, ohne den vollen `▶️ Verarbeiten`-Lauf — praktisch nach einem Concurrency-Skip oder wenn das SoPaed-Tool die Datei aktualisiert hat und man die WebUntis-Aktiv-Spalte sofort neu setzen möchte. Endpoint: `POST /api/nachteilsausgleich/refresh-excel`. Liest aktuelle Schülerdaten (CSV oder SVWS-API), läuft durch denselben Schutz-Pfad.
  - **📢 „Erstversand: alle Nachteilsausgleich-Mails"-Button** (im Info-Mails-Panel, eigener Warnhinweis-Block): generiert für **jeden** aktuell mit Nachteilsausgleich erfassten Schüler eine Info-Mail an die Klassenlehrkraft, **ohne** Change-Detection — auch wenn die Lehrkraft schon einmal benachrichtigt wurde. Sinnvoll für die **Erst-Einrichtung** mit bereits gepflegter SoPaed-Arbeitsdatei (einmaliger Push aller bestehenden Details an die KL). Workflow: Klick → JS-Confirm mit Spam-Warnung → Backend generiert synthetische Change-Records (`Nachteilsausgleich: '(Erstversand)' → 'Ja'`), füttert sie durch das bestehende `create_info_notifications` und füllt damit den vorhandenen Preview-Tabellen-Cache. KL-Auflösung, Templating und Sonderpädagogen-Details-Anhängen geschehen exakt wie im regulären Change-basierten Flow. Sender-Button (`📨 Senden`) bleibt der bestehende — Benutzer kann vor dem Versand in der Tabelle einzelne Mails per Checkbox abwählen. Endpoint: `POST /api/nachteilsausgleich/generate_full_mails`.
- **Neu - Volle Datei-Auswahl + Rich-Text-Erhalt für die Sonderpädagogen-Arbeitsdatei:** Damit die Arbeitsdatei mit anderen Tools (insb. **SoPaed-Tool**, das das gleiche Schema und das gleiche MS-OFFCRYPTO-Verschlüsselungsformat verwendet) **geteilt** werden kann:
  - **Pfad statt Verzeichnis+Name:** Die zwei alten Felder (Verzeichnis + Dateiname) sind durch ein einziges Pfad-Feld `📋 Nachteilsausgleich-Arbeitsdatei (Pfad)` ersetzt. Eingabe wahlweise per Tastatur oder über einen 🗂️ <em>Durchsuchen</em>-Button, der eine echte Windows-Dateiauswahl öffnet (`asksaveasfilename`, akzeptiert auch noch-nicht-existierende Dateinamen — das Tool legt die Datei beim nächsten Lauf an). Neues Setting `[Directories].nachteilsausgleich_excel_path` (voller Pfad). Bestandsinstallationen funktionieren unverändert weiter: wenn der neue Pfad leer ist, fallen das Resolver-Modul und die Settings-UI auf die alten Settings `nachteilsausgleich_excel_directory` + `nachteilsausgleich_excel_filename` zurück und zeigen den komponierten Pfad als Initialwert an.
  - **Generischer `data-file-input`-Mechanismus:** Analog zum bestehenden `data-directory-input` neuer Flask-Endpoint `/select-file` (tkinter `asksaveasfilename`, Titel/Default-Extension/Filetypes per JSON-Payload steuerbar) + Button-Handler in [base.html](Schild_WebUntis_Tool/templates/base.html). Wiederverwendbar für künftige Datei-Pfad-Settings.
  - **Zellformatierung wird erhalten:** Die Aktualisierung baut die Arbeitsdatei nicht mehr als Klartext-Tabelle neu auf, sondern liest die bestehenden Detailzellen mit `rich_text=True` und überträgt **CellRichText (Inline-Fonts, -Farben)** ebenso wie **Zell-Font, -Hintergrundfarbe und -Ausrichtung** in die neu erstellte Datei. Damit überleben Formatierungen, die Sonderpädagogen z.B. im SoPaed-Tool gesetzt haben (`copy.copy()` der Style-Objekte, da openpyxl Stile cross-workbook nicht direkt teilen kann).
- **Neu - KL-Mail-Versand im Erzieher-/Ansprechpartner-Workflow:** Symmetrisch zum Ausbilder-KL-Mail-Versand: aus dem Erzieher-Workflow heraus lassen sich pro Klasse E-Mails an die zuständigen **Klassenlehrkräfte** verschicken mit den aktuell in Schild hinterlegten **Erzieher-/Ansprechpartner-Rohdaten** (kein Smart-Match, kein Dummy-Fill, keine E-Mail-Pflicht-Aussortierung — die Daten genau so, wie sie aus Schild kommen). Zweck: Info + Kontrolle durch die KL — bei fehlenden Erzieher-Datensätzen, leeren E-Mail-Adressen oder unklarer Volljährigkeit leitet sie die Korrektur über das Sekretariat in Schild ein.
  - **Trigger:** neuer Button **📧 KL-Mails: Vorschau** im Erzieher-Workflow.
  - **HTML-Tabelle pro Klasse** in einem **3-Spalten-Layout**: links der Schüler (Name + ID + Geburtsdatum + Volljährig-Status), Mitte „Erzieher Rohdaten" (pro Slot eine farbige Box mit *allen* `Erzieher i: …`-Spalten als „Spaltenname: Wert"-Zeilen), rechts „Ansprechpartner Rohdaten" (pro Anspr-Zeile eine grüne Box mit *allen* Spalten als Zeilen). Damit sieht die KL exakt, was in Schild hinterlegt ist — inklusive leerer Felder, die mit grauem Bindestrich angezeigt werden. Inline-Styles für Outlook/Gmail/Thunderbird-Kompatibilität.
  - **Volljährigkeits-Erkennung** primär per Geburtsdatum (deterministisch), Fallback per Schild-Heuristik (`Erzieher: Art (Klartext)` enthält „volljährig"). Bei **Konflikten** (Schild sagt volljährig, Geburtsdatum widerspricht) erscheint im Mail-Body eine gelbe Warn-Box „⚠️ Konflikt: Schild markiert als *volljährig*, das Geburtsdatum sagt aber **minderjährig**. Bitte in Schild prüfen/korrigieren." Wenn kein Geburtsdatum hinterlegt ist und Schild den Vollj.-Status nicht markiert, erscheint statt eines Werts ein deutlicher Hinweis „⚠️ Geburtsdatum fehlt".
  - **Geburtsdatum-Quelle** primär aus dem **Haupt-Schüler-Datensatz** (CSV im Schild-Exporte-Verzeichnis bzw. via SVWS-API über `main.read_students()`), Fallback aus dem Erzieher-Export. Damit ist die Volljährig-Berechnung auch dann verlässlich, wenn die Erzieher-Vorlage in Schild kein Geburtsdatum mit-exportiert. Statistik im UI: zeigt pro Klasse, wieviele Schüler über die Hauptquelle bzw. den Fallback versorgt wurden.
  - **Excel-Anhang** mit **vier Sheets** pro Klasse:
    - <em>Erzieher</em>: **1 Zeile pro Schüler** (nicht mehr pro Slot) mit dynamischer Spaltenstruktur — Schüler-Stammdaten in den grauen Spalten A–G, dann pro Erzieher-Slot ein eigener farbig hinterlegter 6-Spalten-Block (`Erzieher 1: Anrede/Titel/Vorname/Nachname/Briefanrede/E-Mail` hellblau, `Erzieher 2: …` hellgrün, weitere Slots: hellorange/-rosa/-lila). Slot-Anzahl wird klassenweit ermittelt (mind. 2). Geburtsdatum-Spalte als echtes Datum-Objekt mit Number-Format `DD.MM.YYYY`. Volljährig-Spalte „Volljährig (heute)" wird per **Excel-Formel** (`=IF(ISNUMBER(E?),IF(DATEDIF(E?,TODAY(),"Y")>=18,"ja","nein"),"?")`) **dynamisch** berechnet — beim erneuten Öffnen der Datei in Wochen/Monaten zeigt sie automatisch den aktuellen Stand. Multi-Line-Header mit Hinweis-Box und Cell-Comments erklären den Unterschied zwischen der dynamisch berechneten Volljährig-Spalte und der statischen „Erzieher: Art (Klartext)"-Spalte (Stand letzter Export).
    - <em>Telefonnummern</em>: 1 Zeile pro Nummer mit Quell-Marker (Erzieher- vs. Ansprechpartner-Export).
    - <em>Mailverteiler (alle)</em>: alle aktuell hinterlegten Eltern-/Ansprechpartner-E-Mail-Adressen der Klasse, inklusive Adressen volljähriger Schüler (z.B. eigene Mail-Adresse eines volljährigen Self-Ansprechpartners). Direkt-Liste in einer großen, farbig hinterlegten Zelle, **semikolon-getrennt** und Outlook-/Gmail-tauglich — KL markiert, kopiert, fügt in BCC ein. Darunter eine Tabelle mit Zuordnung E-Mail → Erzieher → Schüler + Volljährig-Status.
    - <em>Mailverteiler (nur Minderjährige)</em>: gleiches Layout, aber Adressen volljähriger Schüler werden ausgeschlossen — sinnvoll für Eltern-Kommunikation, die die Sorgeberechtigten voraussetzt.
  - **Dedup + Filter** im Mailverteiler: gleiche Adresse für beide Eltern oder über Geschwister hinweg wird nur einmal aufgelistet (case-insensitive). Dummy-/Beispiel-Adressen (`@invalid.local`, `@example.com` etc.) werden automatisch herausgefiltert.
  - **Empfänger-Auflösung** identisch zu den anderen Mail-Funktionen (`read_classes()` aus Lehrer-/Klassen-CSVs bzw. SVWS-API). Stv-KL optional als CC.
  - **Filter-Optionen** (in den Erzieher-Einstellungen):
    - **Klassen-Whitelist respektieren** — nur ausgewählte Klassen bekommen eine KL-Mail (Default an).
    - **Nur minderjährige Schüler** — Volljährige aus der KL-Tabelle ausblenden (Default *aus*, weil Rohdaten zeigen sollen, ob die Vollj.-Markierung in Schild stimmt).
    - **Stv-KL als CC** (Default an).
    - **Betreff-Präfix** (z.B. `[TEST]` für Probeläufe).
  - **Versand-Nachweis:** Excel-Anhänge werden zusätzlich im `erzieher_output_directory/KL_Mails/<Zeitstempel>/` abgelegt.
- **Neu - KL-Mail-Vorlagen-Editor für den Erzieher-Workflow:** Dedizierter WYSIWYG-Editor (Button **✉️ KL-Mail-Vorlage** im Erzieher-Modul-Bereich), analog zum Ausbilder-Editor und mit identischer Quill-Infrastruktur — aber auf die eine Vorlage `erzieher_kl_uebersicht` eingeschränkt. Speichert via dedizierter Route `/api/erzieher/update_kl_mail_template`, die nur diese Vorlage anfasst. Verfügbare Platzhalter: `$Klasse`, `$Klassenlehrer_Anrede`, `$Klassenlehrer_Name`, `$Klassenlehrer_E-Mail`, `$Stand`, `$Schueler_Anzahl`, `$Erzieher_Tabelle_HTML` (verschachtelte HTML-Tabelle wird automatisch eingesetzt).
- **Neu - KL-Mail-Versand im Ausbilder-Workflow:** Aus dem Ausbilder-Workflow heraus lassen sich pro Klasse E-Mails an die zuständigen **Klassenlehrkräfte** verschicken, die die aktuell in Schild hinterlegten **Ausbilder-/Betreuer-Daten** als HTML-Tabelle im Mail-Body und zusätzlich als **Excel-Anhang** enthalten. Zweck: Info + Kontrolle durch die KL — bei Inkonsistenzen leitet sie die Korrektur über das Sekretariat in Schild ein, damit die Datenbasis sauber bleibt. Trigger ist der neue Button **📧 KL-Mails: Vorschau** im Workflow.
  - **Empfänger-Auflösung:** Identisch zu den anderen Mail-Funktionen (Schüler-Workflow-Warnungen, Admin-Warnings) — KL + Stv-KL pro Klasse via `read_classes()` aus den Lehrer-/Klassen-CSVs (bzw. via SVWS-API). Wer keine aufgelöste KL-E-Mail hat, wird im Versand übersprungen — die Vorschau-Liste markiert das deutlich.
  - **Vorschau-Bereich:** Pro Klasse aufklappbar: Subject, gerenderter HTML-Body (genau wie die KL ihn sehen wird), Schüler-Anzahl, Excel-Anhang-Vorab-Download. Selektive Auswahl pro Klasse via Häkchen; **📨 Versand**-Bestätigungsdialog vor dem tatsächlichen Versand.
  - **Filter-Optionen** (in den Ausbilder-Einstellungen pro Eigenschaft umschaltbar, Default an = identisch zur WebUntis-Verarbeitung):
    - **Klassen-Whitelist respektieren** — nur ausgewählte Klassen bekommen eine KL-Mail.
    - **Schüler-Blacklist respektieren** — geblacklistete Schüler tauchen *nicht* in der KL-Tabelle auf (DSGVO-konsistent zur WebUntis-Export-Logik).
    - **Firmen-Filter respektieren** — Whitelist/Blacklist-Modus greift identisch zur Verarbeitung.
    - **Stv-KL als CC** — Stellv. Klassenlehrkraft bekommt jede Mail in Kopie.
    - **Betreff-Präfix** — optionaler Zusatz vor dem eigentlichen Betreff (z.B. `[TEST]` für Probeläufe).
  - **Versand-Nachweis:** Die generierten Excel-Anhänge werden zusätzlich im Ausbilder-Ausgabeverzeichnis unter `KL_Mails/<Zeitstempel>/` als Nachweis abgelegt.
- **Neu - KL-Mail-Vorlagen-Editor im Ausbilder-Workflow:** Ein dedizierter **WYSIWYG-Editor** für die KL-Mail-Vorlage ist über den neuen Button **✉️ KL-Mail-Vorlage** im Ausbilder-Modul-Bereich erreichbar. Gleiche Quill-Editor-Infrastruktur wie der Haupt-E-Mail-Editor im Schüler-Workflow, aber explizit auf diese eine Vorlage (`ausbilder_kl_uebersicht`) eingeschränkt — kein versehentliches Mit-Editieren der Schüler-Mail-Vorlagen. Subject und Body sind unabhängig editierbar; Standard-Vorlage per Klick wiederherstellbar. Speichert via dedizierter Route (`/api/ausbilder/update_kl_mail_template`), die nur diese eine Vorlage schreibt — andere Templates bleiben unangetastet. Verfügbare Platzhalter sind im Editor-Header dokumentiert: `$Klasse`, `$Klassenlehrer_Anrede`, `$Klassenlehrer_Name`, `$Klassenlehrer_E-Mail`, `$Stand`, `$Schueler_Anzahl`, `$Schueler_Tabelle_HTML` (die fertige HTML-Tabelle wird automatisch eingesetzt).
- **Neu - Zusatz-Ausbilder-DB im Ausbilder-Workflow:** Schild exportiert pro Auszubildendem immer nur _einen_ Betreuer, auch wenn dort mehrere gepflegt sind. Eine dateibasierte JSON-DB (`ausbilder_extra.json` im Working-Dir, neben `settings.ini`) sammelt jetzt **alle jemals beobachteten Schild-Ausbilder** pro Schüler-Interner-ID und kann manuell um weitere Co-Ausbilder ergänzt werden.
  - **Auto-Sync** bei jedem Schild-Import (Aufruf der Schüler-Tabelle oder `▶️ Verarbeiten`). Match-Heuristik: primär per E-Mail (case-insensitiv), sekundär per Nachname+Vorname. Bestehende Schild-Einträge werden bei Match aufgefrischt, manuelle Einträge (source=manual) bleiben unangetastet. Schild-Zeilen mit komplett leerem Betreuer-Block erzeugen keinen Geister-Eintrag.
  - **UI:** Button **👥 Zusatz-Ausbilder verwalten** klappt eine Schüler-Tabelle auf (Klasse / Nachname / Vorname / Anzahl Schild + Manual / ID). Klick auf **✎ Bearbeiten** öffnet ein Bootstrap-Modal mit allen Ausbildern (Schild- und manuelle differenziert per Badge), pro Eintrag Bearbeiten- und Löschen-Knöpfe, darunter ein Formular für neue manuelle Einträge (8 Felder: Anrede/Titel/Vorname/Nachname/E-Mail/Telefon/Fax/Abteilung).
  - **Auswirkung auf den Export:** Beim `▶️ Verarbeiten` wird die Output-CSV wie bisher geschrieben, _aber pro Schüler-Zeile_ erscheint jeder Co-Ausbilder als zusätzliche Zeile mit identischem Schüler-Teil (Klasse, Name, ID, Firma) und überschriebenem Betreuer-Block. WebUntis interpretiert das als mehrere Ausbilder pro Azubi.
  - **KL-Mail und Klassen-Tabelle bleiben Schild-rein** — sie zeigen nur, was Schild im aktuellen Export liefert. Die Zusatz-Ausbilder beeinflussen ausschließlich die WebUntis-Import-CSV (Hauptzweck).
  - Schüler, die aus Schild verschwinden, bleiben in der DB stehen (mit `last_seen_in_schild`-Datum) und können bei Bedarf manuell entfernt werden. Die Datei ist mit jedem Texteditor lesbar.
- **Neu - Firmen-Filter-Helfer im Ausbilder-Workflow:** Zwei neue Buttons direkt im Firmen-Filter-Bereich:
  - **🔄 Liste invertieren & Modus wechseln** — wandelt die aktuell aktive Liste mathematisch in das Gegenteil um (z.B. Blacklist mit 28 Firmen → Whitelist mit den restlichen 2) und schaltet den `firma_filter_mode` um. Berechnungsbasis: alle Firmen in der aktuellen CSV. Stale-Einträge in der Quell-Liste (Firmen, die nicht mehr in der CSV vorkommen) werden ignoriert — kein Geister-Eintrag in der Ziel-Liste. Die nicht-aktive Liste vor dem Switch bleibt unangetastet, sodass erneutes Invertieren den Original-Stand wiederherstellt. Confirm-Dialog zeigt vorab konkrete Counts (alt → neu) basierend auf den lokalen State-Daten — keine Überraschungen.
  - **🗑️ Aktive Liste leeren** — leert die aktuell aktive Firmen-Liste (Whitelist *oder* Blacklist je nach Modus). Modus bleibt unverändert, die andere Liste ebenfalls. Confirm-Dialog mit Count der zu löschenden Einträge; wenn die Liste schon leer ist, kommt ein freundlicher Info-Dialog statt eines unnötigen Server-Calls.
- **Bug Fix - Einstellungen ließen sich mit `%` im Wert nicht speichern:** Enthielt ein Feld ein Prozentzeichen — typischerweise ein SVWS-API- oder SMTP-Passwort, aber auch CSS-Angaben wie `width: 100%` in einer Mail-Vorlage — brach das Speichern mit `Value error: invalid interpolation syntax in ... at position 2` ab ([Issue #2](https://github.com/CmoneBK/Schild-WebUntis-Tool/issues/2)). Ursache: Pythons `configparser` deutet `%` standardmäßig als Platzhalter-Syntax (`BasicInterpolation`). Das Tool legt seine Konfigurations-Parser jetzt durchgängig mit `interpolation=None` an (106 Stellen in 8 Modulen), sodass Werte exakt so gespeichert und gelesen werden, wie sie eingegeben wurden. Betroffen war nicht nur das Speichern: auch das *Lesen* eines solchen Werts lief in einen `InterpolationSyntaxError`, den ein angegebenes `fallback` nicht abfing. Bestehende `.ini`-Dateien müssen **nicht** angepasst werden — keine der mitgelieferten Konfigurationen nutzt Interpolation.
- **Bug Fix - Start scheiterte bei unvollständiger Konfiguration:** Fehlte in einer bestehenden `settings.ini` der Abschnitt `[ProcessingOptions]` oder `[Directories]` (bzw. `[Templates]` in der `email_settings.ini`), brach der Auto-Patcher mit `NoSectionError` ab — und zwar beim Start *und* nach jedem Speichern der Einstellungen. Diese Abschnitte werden jetzt wie alle übrigen bei Bedarf angelegt; selbst eine nahezu leere `.ini` wird vollständig aus den Standardwerten rekonstruiert.
- **Verbessert - Schutz vor Datenverlust in den `.ini`-Dateien:** Alle Speicherfunktionen arbeiten nach dem Muster „lesen → einzelne Werte setzen → komplette Datei neu schreiben". War die vorhandene Datei nicht lesbar (defekte Syntax, kaputte Kodierung), wurde sie dabei stillschweigend auf die gerade gesetzten Abschnitte gekürzt — alle übrigen Einstellungen waren verloren. Solche Schreibvorgänge brechen jetzt mit einer klaren Meldung ab und lassen die Datei unangetastet (`read_config_for_update()` in `utils.py`, an allen 22 Read-Modify-Write-Stellen aktiv).
- **Neu - Fortschrittsanzeige beim Laden der Schulbesuchsdaten (SVWS-API):** Das Entlassdatum liefert der SVWS-Server nur **einzeln pro Schüler** — einen Sammel-Abruf gibt es dafür nicht (geprüft gegen `svws-openapi`: `APISchueler` registriert ausschließlich `/{id}/schulbesuch`, und das Bulk-DTO `SchuelerStammdaten` enthält kein `entlassungDatum`). Bei grossen Schulen ist das der mit Abstand längste Schritt der Verarbeitung, und bisher lief er komplett ohne Ausgabe — der Lauf wirkte eingefroren. Jetzt nennt die Konsole zu Beginn die Gesamtzahl und meldet danach alle 250 Schüler den Stand mit Prozentangabe.
- **Neu - Parallele Abrufe der Schulbesuchsdaten (optional):** Neues Feld unter `⚙️ Einstellungen → 🏫 Schild API → „Parallele Abrufe der Schulbesuchsdaten"` (Setting `[SchildAPI].schulbesuch_workers`). **Standard `1` = sequenziell wie bisher**, Bestandsinstallationen ändern ihr Verhalten also nicht. Höhere Werte holen entsprechend viele Schüler gleichzeitig (Maximum 16); gemessen an 400 Schülern mit simulierter Latenz ergibt sich mit 8 Workern Faktor **7,5**. Jeder Worker bekommt eine eigene `requests.Session`, da diese nicht als threadsicher zugesichert ist; die Ergebnisse sammelt der Haupt-Thread ein. Verifiziert: das Ergebnis ist bei 1/2/8/16 Workern identisch zum sequenziellen Lauf. <em>Vorsicht:</em> mehr gleichzeitige Anfragen bedeuten mehr Last auf dem SVWS-Server — bei einem ohnehin ausgelasteten Server kann ein hoher Wert kontraproduktiv sein. Empfohlener Einstieg: 4.
- **Neu - Timeout der SVWS-API einstellbar:** Neues Feld `⏱️ Timeout pro Abruf (Sekunden)` (Setting `[SchildAPI].timeout`, Standard `30`). Bei langsamen Servern hilft ein höherer Wert (z.B. 60–120), `0` deaktiviert den Timeout ganz. Zuvor war er fest auf 30 Sekunden verdrahtet. Da Fehler einzelner Abrufe bewusst geschluckt werden, kostete ein zäher Server bis dahin pro Schüler bis zu 30 Sekunden, ohne dass etwas sichtbar wurde. Bei `0` warnt die Konsole beim Start, weil ein nicht antwortender Server den Lauf dann unbegrenzt blockieren kann. Die Schaltflächen „Verbindung testen", „Vermerkarten laden" und „Abschnitte laden" behalten immer 30 Sekunden, damit das Webinterface nicht hängen bleibt.
- **Bug Fix - Schild 3 exportiert die Klassenlehrkraft unter anderem Spaltennamen:** Schild 2 liefert die Spalte als `Klassenlehrer`, Schild 3 als `Klassenlehrer: Nachname`. Die Vorab-Prüfung meldete bei Schild-3-Exporten deshalb eine fehlende Pflichtspalte, und die Verarbeitung liess den Namen leer — bis man die Spaltenüberschrift von Hand umbenannte. **Beide Schreibweisen werden jetzt akzeptiert**, ein Anpassen der Export-Vorlage ist nicht mehr nötig. Inhaltlich sind sie identisch: der Wert wird gegen dieselben Lehrkraft-Namen geprüft wie `Klassenlehrkraft` aus der Klassen-CSV, und die enthält Nachnamen. Fehlt die Spalte tatsächlich, meldet die Prüfung weiterhin einen Fehler.
- **Bug Fix - Leere WebUntis-Importdatei wird nicht mehr erstellt:** Lagen keine Schülerdaten vor — etwa weil die SVWS-API fehlschlug **und** im Schild-Exporte-Verzeichnis keine CSV lag —, schrieb das Tool bisher eine **komplett leere** Importdatei und meldete sie als erfolgreich erstellt. Das ist nicht harmlos: je nach Import-Filter deaktiviert WebUntis damit sämtliche Schüler. Jetzt bricht die Erstellung mit einer deutlichen Fehlermeldung ab, und die zuletzt erzeugte Importdatei bleibt unangetastet. Der Schutz greift auch, wenn nur die Kopfzeile ohne einen einzigen Schüler vorliegt.
- **Verbessert - API-Fehlermeldungen nennen jetzt den Grund:** Bei einem HTTP-Fehler der SVWS-API wurde bisher nur der Statuscode ausgegeben (`500 Server Error for url: …`) — die Begründung, die der SVWS-Server im Antwort-Body mitschickt, ging verloren. Diese wird jetzt mit ausgegeben (auf 500 Zeichen gekürzt), sodass z.B. `HTTP 500 bei …/klassen/details/abschnitt/1 — Antwort des Servers: {"log": ["Fehler beim Zugriff auf …"]}` sichtbar wird. Besonders hilfreich, wenn ein Reverse-Proxy vor dem SVWS-Server steht und sonst unklar bleibt, wer den Fehler erzeugt hat.
- **Bug Fix - Programm startete nach einem Update nicht mehr (Konsolenfenster schloss sich sofort):** Fehlte in einer bestehenden `settings.ini` einer der Schlüssel `classes_directory` oder `teachers_directory`, brach das Tool beim Start mit einem unbehandelten `NoOptionError` ab — das Fenster war weg, bevor man die Meldung lesen konnte, und half nur noch das Löschen des kompletten Verzeichnisses. Drei Änderungen beheben das: Der **Auto-Patcher ergänzt jetzt alle** `[Directories]`-Schlüssel aus dem Standard-Template (nicht mehr nur die zuletzt hinzugekommenen; bestehende Werte bleiben unangetastet), die beiden Lesevorgänge in `run()` und `admin_warnings()` nutzen einen `fallback` wie die übrigen Stellen im Code, und **unbehandelte Ausnahmen beenden das Programm nicht mehr wortlos**: Es erscheint eine verständliche Meldung samt Lösungsvorschlag und das Fenster bleibt offen, bis man Enter drückt. Die Wartepause gilt nur für interaktive Konsolen — in der Windows-Aufgabenplanung würde sie den Task blockieren und entfällt deshalb dort.
