"""
Zentrale Quelle für die Inline-Hilfe-Texte im Webend.

Jeder Eintrag besteht aus:
  - title: Anzeige-Titel im Modal
  - html:  Vollständiger HTML-Body (offline eingebettet, kein README-Link nötig)

Aufruf:
  - get_help(key) → einzelner Eintrag (für Info-Buttons)
  - get_all_help() → alle Einträge (für den Glossar-Modus)
"""

# Inhalte sind im Stil des README ausführlich gehalten, aber stärker
# auf konkrete Handlungsschritte fokussiert.

HELP_CONTENT = {

    # =====================================================================
    # ALLGEMEIN
    # =====================================================================
    "general_workflow": {
        "title": "🔄 Schüler-Verarbeitung — Verarbeitung, Mails, Fotos",
        "html": """
<p>Der Schüler-Verarbeitungs-Bereich oben enthält die wichtigsten Aktionen für den
täglichen Ablauf — und die <em>Einstellungen für die aktuelle Ausführung</em>
(dauerhafte Einstellungen liegen im ⚙️ Einstellungs-Panel).
Hier ein Überblick, was die einzelnen Buttons tun:</p>

<h6>▶️ Verarbeiten <em>(Hauptfunktion)</em></h6>
<p>Bei einem Klick passiert Folgendes:</p>
<ol>
  <li>Das Tool sucht die <strong>neueste CSV-Datei</strong> im Schild-Export-Verzeichnis
      (oder, falls aktiv, ruft die Daten direkt vom SVWS-Server ab).</li>
  <li>Die Schülerdaten werden für WebUntis umgewandelt — u.a. werden <em>Schulpflicht</em>
      und <em>Status</em> in boolesche Werte konvertiert (Schild 2/Aktiv → WebUntis-Aktiv).</li>
  <li>Optional werden Zusatzspalten <em>Attestpflicht</em> und <em>Nachteilsausgleich</em>
      ergänzt — entweder aus separaten CSV-Dateien oder über die Schild-API.</li>
  <li>Die fertige WebUntis-Import-CSV wird mit Datum/Uhrzeit-Stempel im
      Import-Verzeichnis gespeichert.</li>
  <li>Der neue Import wird mit dem zuletzt erstellten verglichen — Änderungen werden
      als Log-Datei (Plaintext + Excel) protokolliert und in der Historie gespeichert.</li>
  <li>Bei kritischen Änderungen (Entlassdatum, Klassenwechsel, neue Schüler, …) werden
      Warnungen erzeugt, die anschließend per E-Mail verschickt werden können.</li>
</ol>

<h6>🔍 Dateien prüfen</h6>
<p>Vorab-Validierung der Eingabedateien <strong>bevor</strong> die eigentliche Verarbeitung
gestartet wird. Geprüft werden: fehlende Pflichtspalten, falsche Trennzeichen, leere
Verzeichnisse. So sehen Sie sofort, ob mit einem Schild-Export etwas nicht stimmt —
ohne dass schon ein fehlerhafter WebUntis-Import erzeugt wird.</p>

<h6>✍ Emails Generieren / 📨 Emails Senden</h6>
<p>Nach dem Verarbeiten werden ggf. <strong>Warnungs-Mails</strong> für Klassenlehrkräfte
vorbereitet (z.B. bei Klassenwechseln, Entlassdatum-Problemen, neuen Schülern).</p>
<ul>
  <li><strong>Emails Generieren</strong> erzeugt die Mails (noch nicht verschickt) und
      zeigt eine Vorschau-Liste an. Vorlagen lassen sich im
      <em>Email-Vorlagen Editor</em> anpassen.</li>
  <li><strong>Emails Senden</strong> verschickt die zuvor generierten Mails über den
      konfigurierten SMTP-Server.</li>
</ul>
<p>Dieser Zwei-Schritt-Prozess gibt Ihnen die Gelegenheit, vor dem Versand nochmal
zu prüfen, an wen welche Mail geht.</p>

<h6>🖼️ Fotos managen</h6>
<p>Öffnet den Foto-Verwaltungs-Bereich (Button rechts in der Zeile):</p>
<ul>
  <li><strong>Übersicht</strong> aller Schüler-Fotos im Foto-Verzeichnis mit
      Thumbnail-Vorschau und Schüler-Zuordnung.</li>
  <li><strong>ZIP-Export</strong> für den WebUntis-Foto-Import (optional nach
      Schild-Status gefiltert).</li>
  <li><strong>Umbenanntes Kopieren</strong> in einen Unterordner mit lesbaren Namen.</li>
  <li><strong>Verwaiste archivieren</strong>: Fotos von Schülern, die nicht mehr im
      Import sind, in einen <code>Archiv</code>-Unterordner verschieben.</li>
</ul>

<h6>Verarbeitungseinstellungen <em>(Checkboxen oben)</em></h6>
<p>Die Optionen <em>„Benutze Vorrauss. Abschlussdatum als Entlassdatum"</em>,
<em>„Attestpflicht-Spalte"</em>, <em>„Nachteilsausgleich-Spalte"</em> und die
Warnungs-Schalter wirken jeweils <strong>für den nächsten Lauf</strong>. Dauerhaft
können sie in den <em>⚙️ Einstellungen</em> gesetzt werden.</p>
""",
    },

    # =====================================================================
    # QUELLDATEN
    # =====================================================================
    "schild_export": {
        "title": "📥 Schild-Export einrichten",
        "html": """
<h6>1. Filter in Schild setzen</h6>
<ul>
  <li>Unten bei <strong>Laufbahninfo</strong>: <code>Schuljahr = aktuelles Schuljahr</code></li>
  <li>Oben rechts bei <strong>Status</strong>: <code>Aktiv</code>, <code>Abschluss</code>
      und <code>Abgänger</code> anhaken</li>
  <li>Filter <strong>speichern</strong>, damit er später über
      <em>„Auswahl → Vorhandene Filter laden"</em> wieder verfügbar ist.</li>
</ul>

<h6>2. Wo findet man den Export?</h6>
<ul>
  <li><strong>Schild 3:</strong> <code>Verwaltung → Export → Als Excel-/Text-Dateien</code></li>
  <li><strong>Schild 2:</strong> <code>Datenaustausch → Export in Text-/Excel-Dateien → Exportieren</code></li>
</ul>
<p>Um die <code>.csv</code>-Endung manuell eingeben zu können, beim Dateityp der
Ausgabedatei <strong>„Alle Dateien"</strong> auswählen.</p>

<h6>3. Erforderliche Daten</h6>
<p>Idealerweise in dieser Reihenfolge:</p>
<p><code>Interne ID-Nummer; Nachname; Vorname; Klasse; Geburtsdatum; Geschlecht;
vorrauss. Abschluss; Aufnahmedatum; Entlassdatum; Volljährig; Schulpflicht erfüllt; Status</code></p>
<p>Als Trennzeichen ist <code>;</code> zu wählen.</p>

<h6>4. Optionale Daten</h6>
<p><code>Klassenlehrer; E-Mail (privat); Telefon-Nr.; Fax-Nr.; Straße; Postleitzahl; Ortsname</code></p>

<p><strong>Wichtig:</strong> Der Export muss als <em>Textdatei</em> mit manuell ergänzter
<code>.csv</code>-Endung erfolgen. Eine Excel-Datei, die nur in <code>.csv</code> umbenannt
wird, funktioniert nicht (falsche interne Struktur). Speichern Sie die Exporteinstellung
als Vorlage ab, um sie später schneller wieder verwenden zu können.</p>

<p><em>Hinweis:</em> Wenn die <strong>Schild-API (SVWS-Server)</strong> aktiviert ist,
entfällt dieser manuelle Export — die Daten werden direkt vom Server gelesen.</p>
""",
    },

    "klassen_csv": {
        "title": "🏫 Klassendaten-Export (WebUntis)",
        "html": """
<p>Die Klassendaten werden für die <strong>Zuordnung der Klassenlehrkräfte</strong>
zu den Klassen benötigt — z.B. damit Warnungs-Mails an die richtigen Adressaten gehen.</p>

<h6>So erzeugen Sie die Datei</h6>
<ol>
  <li>In WebUntis: <code>Stammdaten → Klassen</code> öffnen.</li>
  <li>Die Tabelle in eine Excel-Datei kopieren mit folgenden Spalten in <strong>genau dieser
      Reihenfolge</strong> (nichts umbenennen):
      <ul>
        <li><code>Auswahl</code></li>
        <li>(eine leere Spalte)</li>
        <li><code>Klasse</code></li>
        <li><code>Langname</code></li>
        <li><code>Alias</code></li>
        <li><code>Jahrgangsstufe</code></li>
        <li><code>Text</code></li>
        <li><code>Klassenlehrkraft</code></li>
        <li><code>Klassenlehrkraft</code> <em>(2. Klassenlehrkraft, falls vorhanden)</em></li>
        <li><code>Abteilung</code></li>
        <li><code>Von</code></li>
        <li><code>Bis</code></li>
      </ul>
  </li>
  <li>Die Excel-Datei anschließend als <code>.csv</code> exportieren (Spalten-Trenner <code>;</code>).</li>
  <li>Die fertige CSV in das konfigurierte <strong>Klassendatenverzeichnis</strong> ablegen.</li>
</ol>

<p>Das Tool nimmt automatisch immer die <strong>neueste</strong> CSV-Datei aus diesem
Verzeichnis — ältere Versionen müssen also nicht gelöscht werden.</p>

<p><em>Hinweis:</em> Bei aktivierter <strong>Schild-API</strong> entfällt dieser Schritt —
Klassen und Klassenleitungen werden direkt vom Server gelesen.</p>
""",
    },

    "lehrer_csv": {
        "title": "🧑‍🏫 Lehrerdaten-Export (WebUntis)",
        "html": """
<p>Die Lehrerdaten werden für die <strong>Namens- und E-Mail-Ermittlung</strong> der
Klassenlehrkräfte benötigt.</p>

<h6>So erzeugen Sie die Datei</h6>
<ol>
  <li>In WebUntis: <code>Stammdaten → Lehrkräfte</code> öffnen.</li>
  <li>Nach unten scrollen und auf <code>Berichte</code> klicken.</li>
  <li>Den <strong>CSV-Bericht „Lehrkräfte"</strong> auswählen und herunterladen.</li>
  <li>Die Datei in das konfigurierte <strong>Lehrerdatenverzeichnis</strong> ablegen.</li>
</ol>

<h6>Wichtige Hinweise</h6>
<ul>
  <li>Die Datei ist <strong>Tab-getrennt</strong>, nicht Semikolon-getrennt.</li>
  <li>Das Feld für die <strong>E-Mail-Adressen</strong> muss mit den Dienst-E-Mail-Adressen
      der Kollegen gefüllt sein, damit der spätere Mail-Versand funktioniert.</li>
  <li>Das Tool verwendet automatisch immer die <strong>neueste</strong> CSV-Datei
      im Verzeichnis.</li>
</ul>

<p><em>Hinweis:</em> Bei aktivierter <strong>Schild-API</strong> entfällt dieser Schritt —
Lehrer-Stammdaten inkl. E-Mail-Adressen werden direkt vom Server gelesen.</p>
""",
    },

    "attest_export": {
        "title": "📑 Attestpflicht — Datenquelle einrichten",
        "html": """
<p>Damit das Tool eine <strong>Attestpflicht-Spalte</strong> (Ja/Nein) im WebUntis-Import
ergänzen kann, braucht es eine Liste der betroffenen Schüler. Es gibt zwei Wege:</p>

<h6>Variante A — CSV-Datei aus Schild (Standard)</h6>
<p>Die Attestpflicht wird in Schild als <strong>Vermerk</strong> hinterlegt. So filtern Sie:</p>
<ol>
  <li>Den normalen Schüler-Filter laden, den Sie sonst für den Tool-Export verwenden.</li>
  <li>Bei <em>„Auswahl"</em> den <strong>„Filter II"</strong> öffnen:
    <ul>
      <li>Unten: <em>„Aktuelle Auswahl übernehmen"</em></li>
      <li>Oben bei <em>Feldname</em>: <strong>Vermerk-Art</strong></li>
      <li>Bei <em>Feldwert</em>: Ihren Attestpflicht-Wert</li>
      <li><em>„In Filterbedingungen übernehmen"</em>, dann <em>„Testen"</em>, dann
          <em>„Speichern"</em> mit eindeutigem Namen.</li>
    </ul>
  </li>
  <li>Neue Exportvorlage erstellen mit (mindestens) der <strong>Internen ID-Nummer</strong>.</li>
  <li>Als <code>.csv</code> exportieren und in das konfigurierte
      <strong>Attestpflicht-Datei-Verzeichnis</strong> ablegen.</li>
</ol>
<p>Bei jedem Tool-Lauf wird die neueste Datei darin gelesen und alle Schüler mit
einer ID aus dieser Liste bekommen die Spalte <code>Attestpflicht = Ja</code>.</p>

<h6>Variante B — Direkt über die Schild-API (Schild 3.x)</h6>
<p>Wenn die <strong>Schild-API</strong> aktiv ist, können Sie unter
<code>⚙️ Einstellungen → 🏫 Schild API</code> bei
<em>„Attestpflicht — Quelle"</em> auf <strong>SVWS-API</strong> wechseln und die exakte
<strong>Vermerkart-Bezeichnung</strong> aus Schild eintragen (z.B.&nbsp;<code>Attestpflicht</code>).
Damit entfällt der separate CSV-Export.</p>
""",
    },

    "nachteil_export": {
        "title": "♿ Nachteilsausgleich — Datenquelle einrichten",
        "html": """
<p>Damit das Tool eine <strong>Nachteilsausgleich-Spalte</strong> (Ja/Nein) im
WebUntis-Import ergänzen kann, braucht es eine Liste der betroffenen Schüler.</p>

<h6>Variante A — CSV-Datei aus Schild (Standard)</h6>
<p>Das Vorgehen ist <strong>identisch zur Attestpflicht</strong>:</p>
<ol>
  <li>Normalen Schüler-Filter laden, dann „Filter II" mit der Vermerkart
      <em>Nachteilsausgleich</em> erstellen.</li>
  <li>Neue Exportvorlage mit der Internen ID-Nummer.</li>
  <li>Als <code>.csv</code> in das <strong>Nachteilsausgleich-Datei-Verzeichnis</strong> ablegen.</li>
</ol>

<h6>Variante B — Direkt über die Schild-API (Schild 3.x)</h6>
<p>Mit aktiver Schild-API kann unter
<code>⚙️ Einstellungen → 🏫 Schild API</code> bei
<em>„Nachteilsausgleich — Quelle"</em> auf <strong>SVWS-API</strong> umgestellt werden.
Die genaue Vermerkart-Bezeichnung muss exakt der Schild-Definition entsprechen
(z.B.&nbsp;<code>Nachteilsausgleich</code>).</p>

<h6>Bonus: Detail-Pflege durch Sonderpädagogen</h6>
<p>Wenn die <strong>Nachteilsausgleich-Arbeitsdatei</strong> aktiv ist, können
Sonderpädagogen in fünf Spalten <em>(Zeitlich, Technisch, Räumlich, Personell,
Sonstige Vereinbarungen)</em> Details pflegen — diese werden in den Info-Mails
bei Änderungen automatisch mitversendet.</p>
""",
    },

    "sopaed_workflow": {
        "title": "📋 Nachteilsausgleich-Arbeitsdatei für Sonderpädagogen",
        "html": """
<p>Eine Excel-Arbeitsdatei, die Sonderpädagogen mit den <strong>Details</strong>
des jeweiligen Nachteilsausgleichs befüllen — und die bei Änderungen automatisch
in die Info-Mails übernommen wird.</p>

<h6>Wie funktioniert es?</h6>
<ol>
  <li>Das Tool erzeugt bei jedem Lauf eine Datei <code>Nachteilsausgleich_Arbeitsdatei.xlsx</code>
      mit allen Schülern. Sie hat 10 Spalten:
      <ul>
        <li><strong>Blau (System-gepflegt):</strong> Interne ID, Nachname, Vorname,
            Klasse, „Nachteilsausgleich in WebUntis aktiv"</li>
        <li><strong>Orange (Sonderpädagogen-Spalten):</strong> Zeitlich, Technisch,
            Räumlich, Personell, Sonstige Vereinbarungen</li>
      </ul>
  </li>
  <li>Sonderpädagogen öffnen die Datei (idealerweise auf einem Netzlaufwerk) und
      tragen in die orangen Spalten ihre Details ein.
      Pro Zelle sind <strong>Zeilenumbrüche und mehrere Einträge</strong> möglich
      (z.B.&nbsp;„Mathe: 20% mehr Zeit / Klassenarbeiten: separater Raum").</li>
  <li>Beim nächsten Tool-Lauf werden die Einträge gelesen, gespeicherte Werte bleiben
      <strong>immer erhalten</strong> — auch wenn neue Schüler dazukommen oder andere wegfallen.</li>
  <li>Wenn unter <em>Info-Mails</em> das Feld <strong>Nachteilsausgleich</strong> aktiviert ist
      und sich der Wert ändert, geht eine Info-Mail an die Klassenlehrkräfte —
      <strong>mit den Detailangaben aus der Arbeitsdatei</strong>.</li>
</ol>

<h6>Konfiguration</h6>
<p>Pfad einstellbar unter <code>⚙️ Einstellungen → Verzeichnisse → Arbeitsverzeichnisse →
Nachteilsausgleich-Arbeitsdatei-Verzeichnis</code>. Empfohlen: ein Netzlaufwerk, auf
das die Sonderpädagogen Schreibzugriff haben.</p>

<p><strong>Vorteil:</strong> Schreibarbeit wird einmal an zuständige Personen delegiert
und ist anschließend dauerhaft im Tool verfügbar. Kein „Wo hatten wir nochmal
hingeschrieben…"-Problem mehr.</p>
""",
    },

    "foto_export": {
        "title": "🖼️ Foto-Export aus Schild",
        "html": """
<p>Damit das Tool Schüler-Fotos im Dashboard anzeigen und für den WebUntis-Foto-Import
vorbereiten kann, müssen die Fotos aus Schild exportiert werden.</p>

<h6>Schild 2</h6>
<ol>
  <li><code>Datenaustausch → Fotos → Fotos exportieren</code></li>
  <li>Als Benennung die <strong>Interne ID-Nummer</strong> wählen
      (NICHT Nachname/Vorname o.ä.).</li>
  <li>Ausgabeordner = das konfigurierte Foto-Verzeichnis.</li>
</ol>

<h6>Schild 3</h6>
<p>Der entsprechende Foto-Export findet sich ebenfalls im Bereich Datenaustausch/Export —
auch hier ist die Benennung nach <strong>Interner ID-Nummer</strong> zu wählen.</p>

<h6>Konfiguration im Tool</h6>
<p>Foto-Verzeichnis einstellbar unter <code>⚙️ Einstellungen → Verzeichnisse →
Arbeitsverzeichnisse → 🖼️ Foto-Verzeichnis</code>.</p>

<h6>Unterstützte Bildformate</h6>
<p><code>.jpg</code>, <code>.jpeg</code>, <code>.png</code>, <code>.gif</code>, <code>.bmp</code> —
case-insensitive (auch <code>.JPG</code> etc.).</p>

<h6>Funktionen mit den Fotos</h6>
<ul>
  <li><strong>Dashboard:</strong> Das Foto erscheint automatisch bei der Schülerhistorien-Suche.</li>
  <li><strong>ZIP-Export:</strong> Fotos der aktiven Schüler (Status-gefiltert) als ZIP für den
      WebUntis-Foto-Import packen.</li>
  <li><strong>Umbenanntes Kopieren:</strong> Fotos mit lesbaren Namen
      (z.B.&nbsp;<code>Mueller_Max_12345.jpg</code>) in einen Unterordner kopieren.</li>
  <li><strong>Archivieren:</strong> Fotos von Schülern, die nicht mehr im Import sind,
      automatisch in den Unterordner <code>Archiv</code> verschieben.</li>
</ul>
""",
    },

    # =====================================================================
    # SCHILD-API
    # =====================================================================
    "schild_api_setup": {
        "title": "🏫 Schild-API einrichten (Schild 3.x)",
        "html": """
<p>Ab <strong>Schild 3.x</strong> mit aktivem SVWS-Server können Schüler-, Klassen-
und Lehrerdaten direkt vom Server geladen werden — der manuelle CSV-Export entfällt
dann komplett.</p>

<h6>1. Technischen Benutzer im SVWS-Server anlegen</h6>
<ol>
  <li>Als Admin im SVWS-Web-Client anmelden.</li>
  <li>Unten links: <code>⚙️ Einstellungen → Benutzerverwaltung → + (neuer Benutzer)</code></li>
  <li>Empfohlener Name: <code>APIZugang</code>. Passwort vergeben und sicher aufbewahren.</li>
  <li>Auf der Berechtigungs-Seite folgende <strong>vier Kompetenzen</strong> auf <em>„Ansehen"</em>
      setzen — keine weiteren Rechte nötig:
      <ul>
        <li>☑ Schüler Individualdaten</li>
        <li>☑ Lehrerdaten</li>
        <li>☑ Schulbezogene Daten</li>
        <li>☑ Katalog-Einträge</li>
      </ul>
  </li>
</ol>

<h6>2. Im Tool eintragen</h6>
<p>Unter <code>⚙️ Einstellungen → 🏫 Schild API</code>:</p>
<ul>
  <li><strong>Verwenden:</strong> Ja</li>
  <li><strong>Server-URL:</strong> z.B. <code>https://schild.schule.local</code></li>
  <li><strong>DB-Schema:</strong> meist <code>svwsdb</code></li>
  <li><strong>Benutzer/Passwort:</strong> Daten des technischen Users</li>
  <li><strong>TLS-Zertifikat prüfen:</strong> Bei Self-Signed Cert auf <em>Nein</em>,
      in Produktion mit gültigem Zertifikat auf <em>Ja</em>.</li>
  <li><strong>Fallback auf CSV:</strong> Empfohlen <em>Ja</em> — bei API-Fehlern arbeitet
      das Tool automatisch mit dem letzten CSV-Stand weiter.</li>
  <li><strong>Schuljahresabschnitt:</strong> Default „Aktuell aktiver Abschnitt" reicht meistens.</li>
  <li><strong>Status-Whitelist:</strong> Default <code>2,6,8,9</code> entspricht
      „Aktive, Externe, Abschluss, Abgang".</li>
</ul>

<h6>3. Verbindung testen</h6>
<p>Mit <em>🔍 Verbindung testen</em> prüfen. Bei grünem ✅ Speichern.</p>

<h6>Wichtige Einschränkungen</h6>
<ul>
  <li>Das Feld <em>„vorauss. Abschlussdatum"</em> ist über die SVWS-API derzeit
      <strong>nicht</strong> erreichbar (Stand 1.3.x). Die Option <em>„Abschlussdatum als
      Entlassdatum verwenden"</em> wird im API-Modus automatisch deaktiviert.</li>
  <li>Performance: bei großen Schulen (>2000 Schüler) dauert ein API-Lauf ca. 1–3 Minuten.</li>
</ul>

<p>Bei aktivem API-Modus werden im Webend die nicht mehr benötigten Verzeichnisse
(Klassendaten, Lehrerdaten, Schild-Exporte) automatisch <strong>gesperrt</strong> —
mit Hinweis-Banner.</p>
""",
    },

    "vermerkart_naming": {
        "title": "📑 Vermerkart-Bezeichnung (Schild-API)",
        "html": """
<p>Wenn die Schild-API als Quelle für <strong>Attestpflicht</strong> oder
<strong>Nachteilsausgleich</strong> aktiv ist, holt das Tool die Liste der betroffenen
Schüler über die <em>Vermerke</em> aus Schild.</p>

<h6>So funktioniert es</h6>
<ol>
  <li>In Schild ist die jeweilige Vermerkart unter
      <code>Schule → Vermerkarten</code> mit einer bestimmten <em>Bezeichnung</em> definiert
      (z.B.&nbsp;<code>Attestpflicht</code> oder <code>Nachteilsausgleich</code>).</li>
  <li>Diese Bezeichnung müssen Sie im Tool <strong>exakt</strong> eintragen
      (Vergleich erfolgt case-insensitive, aber sonst zeichengenau).</li>
  <li>Klick auf <em>🔄 Vermerkarten vom Server laden</em> lädt die Liste aller
      definierten Vermerkarten als <strong>Vorschläge</strong> in das Eingabefeld —
      so vermeiden Sie Tippfehler.</li>
</ol>

<h6>Quelle pro Vermerk wählbar</h6>
<p>Pro Vermerk können Sie unabhängig wählen, woher die Daten kommen:</p>
<ul>
  <li><strong>CSV-Datei:</strong> Wie bisher, separater Schild-Filter-Export
      (siehe Hilfe zur Attestpflicht/Nachteilsausgleich-Datei).</li>
  <li><strong>SVWS-API:</strong> Direkt vom Server anhand der Vermerkart-Bezeichnung.</li>
</ul>

<h6>Bei aktiver API-Quelle</h6>
<p>Wird das jeweilige Datei-Verzeichnis (Attestpflicht-Datei bzw. Nachteilsausgleich-Datei)
im Webend automatisch <strong>gesperrt</strong> — die separaten Schild-Filter-Exporte
werden dann nicht mehr benötigt.</p>

<p><em>Hinweis:</em> Die SVWS-API ist nur in Schild 3.x verfügbar. Mit Schild 2 muss
weiterhin die CSV-Variante verwendet werden.</p>
""",
    },

    # =====================================================================
    # INFO-MAILS
    # =====================================================================
    "warnungen": {
        "title": "⚠️ Warnungen — wann und warum?",
        "html": """
<p>Das Tool erkennt fünf typische Situationen, die in WebUntis zu Inkonsistenzen
führen können. Klicken Sie auf eine Szene, um Details und die Wirkung auf den
„Zeitstrahl" zu sehen.</p>

<style>
.warn-timeline { position:relative; height:64px; margin:14px 0 4px; }
.warn-axis { position:absolute; left:0; right:0; top:32px; height:2px; background:#adb5bd; }
.warn-axis::before, .warn-axis::after { content:''; position:absolute; top:-4px; width:2px; height:10px; background:#adb5bd; }
.warn-axis::before { left:4%; }
.warn-axis::after  { right:4%; }
.warn-axis-label { position:absolute; top:42px; font-size:0.72rem; color:#6c757d; }
.warn-axis-label.left  { left:1%;  }
.warn-axis-label.right { right:1%; text-align:right; }
.warn-marker { position:absolute; top:18px; width:14px; height:14px; border-radius:50%;
               box-shadow:0 0 0 3px #fff, 0 0 0 4px rgba(0,0,0,0.15); transform:translateX(-50%); }
.warn-marker.now { background:#0d6efd; top:24px; width:8px; height:32px; border-radius:2px; }
.warn-marker.old { background:#dc3545; }
.warn-marker.new { background:#198754; }
.warn-arrow { position:absolute; top:25px; height:2px; background:#fd7e14; transform:translateX(0); }
.warn-arrow::after { content:'▶'; position:absolute; right:-4px; top:-8px; color:#fd7e14; font-size:10px; }
.warn-gap { position:absolute; top:14px; height:20px; background:rgba(220,53,69,0.15);
            border:1px dashed #dc3545; border-radius:3px; }
.warn-gap-label { position:absolute; top:-2px; font-size:0.7rem; color:#dc3545; font-weight:bold; white-space:nowrap; }
details.warn-case { margin-bottom:10px; border-left:4px solid #fd7e14; padding-left:10px; }
details.warn-case[open] { background:#fff8f0; }
details.warn-case > summary { cursor:pointer; font-weight:600; padding:6px 0; outline:none; }
details.warn-case > summary::-webkit-details-marker { display:none; }
details.warn-case > summary::before { content:'▶ '; color:#fd7e14; font-size:0.8rem; margin-right:4px; }
details.warn-case[open] > summary::before { content:'▼ '; }
.warn-legend { font-size:0.78rem; color:#6c757d; margin-top:4px; }
.warn-legend .dot { display:inline-block; width:10px; height:10px; border-radius:50%; vertical-align:middle; margin:0 4px 2px 8px; }
.warn-legend .dot.now { background:#0d6efd; border-radius:2px; height:14px; width:4px; }
.warn-legend .dot.old { background:#dc3545; }
.warn-legend .dot.new { background:#198754; }
body.dark-mode details.warn-case[open] { background:#3a2a14; }
body.dark-mode .warn-axis-label { color:#adb5bd; }
</style>

<p class="warn-legend">
  Legende:
  <span class="dot now"></span>Heute
  <span class="dot old"></span>Alter Wert
  <span class="dot new"></span>Neuer Wert
  <span style="color:#dc3545;border:1px dashed #dc3545;padding:0 4px;margin-left:8px;font-size:0.75rem;">Dokumentationslücke</span>
</p>

<!-- ===== 1. Entlassdatum in die Zukunft ===== -->
<details class="warn-case">
  <summary>📅 Entlassdatum in die Zukunft verschoben</summary>
  <div class="warn-timeline">
    <div class="warn-axis"></div>
    <span class="warn-axis-label left">Schuljahres-Beginn</span>
    <span class="warn-axis-label right">Schuljahres-Ende</span>
    <div class="warn-marker old" style="left:35%" title="Altes Entlassdatum"></div>
    <div class="warn-marker now" style="left:55%" title="Heute"></div>
    <div class="warn-marker new" style="left:75%" title="Neues Entlassdatum"></div>
    <div class="warn-arrow" style="left:35%;width:40%"></div>
    <div class="warn-gap" style="left:35%;width:20%">
      <span class="warn-gap-label">Lücke: alt → heute nicht dokumentiert</span>
    </div>
  </div>
  <p><strong>Was ist passiert?</strong> Das Entlassdatum eines Schülers wurde nach hinten verschoben
  (z.B. von April auf Juni). Lag das alte Entlassdatum vor heute, war der Schüler in
  WebUntis bereits „entlassen" — der Zeitraum bis heute ist dort nicht dokumentiert.</p>
  <p><strong>Folge:</strong> In WebUntis muss der Schüler manuell wieder „aufgenommen" werden,
  damit die fehlenden Tage korrekt dokumentiert werden können.</p>
</details>

<!-- ===== 2. Aufnahmedatum in die Vergangenheit ===== -->
<details class="warn-case">
  <summary>📅 Aufnahmedatum in die Vergangenheit verschoben</summary>
  <div class="warn-timeline">
    <div class="warn-axis"></div>
    <span class="warn-axis-label left">Schuljahres-Beginn</span>
    <span class="warn-axis-label right">Schuljahres-Ende</span>
    <div class="warn-marker new" style="left:25%" title="Neues Aufnahmedatum (früher)"></div>
    <div class="warn-marker old" style="left:55%" title="Altes Aufnahmedatum"></div>
    <div class="warn-marker now" style="left:75%" title="Heute"></div>
    <div class="warn-arrow" style="left:25%;width:30%;transform:rotate(180deg);transform-origin:left"></div>
    <div class="warn-gap" style="left:25%;width:30%">
      <span class="warn-gap-label">Lücke: neu → alt nicht dokumentiert</span>
    </div>
  </div>
  <p><strong>Was ist passiert?</strong> Das Aufnahmedatum eines Schülers wurde nach vorne verschoben
  (z.B. von November auf September). In WebUntis ist der Schüler erst ab dem alten
  Aufnahmedatum bekannt — für den nun früher liegenden Zeitraum gibt es keine Doku.</p>
  <p><strong>Folge:</strong> Manuelle Nachpflege in WebUntis: Schüler-Status für die früher
  liegende Zeit ergänzen.</p>
</details>

<!-- ===== 3. Klassenwechsel ===== -->
<details class="warn-case">
  <summary>🔄 Klassenwechsel mitten im Schuljahr</summary>
  <div class="warn-timeline">
    <div class="warn-axis"></div>
    <span class="warn-axis-label left">Schuljahres-Beginn</span>
    <span class="warn-axis-label right">Schuljahres-Ende</span>
    <div style="position:absolute;left:5%;width:50%;top:24px;height:16px;background:rgba(220,53,69,0.5);border-radius:3px;color:#fff;font-size:0.7rem;text-align:center;line-height:16px;">alte Klasse</div>
    <div style="position:absolute;left:55%;width:40%;top:24px;height:16px;background:rgba(25,135,84,0.6);border-radius:3px;color:#fff;font-size:0.7rem;text-align:center;line-height:16px;">neue Klasse</div>
    <div class="warn-marker now" style="left:55%;background:#000" title="Wechsel-Zeitpunkt"></div>
  </div>
  <p><strong>Was ist passiert?</strong> Ein Schüler hat die Klasse gewechselt
  (z.B. von 10A nach 10B). Schild meldet ab sofort die neue Klasse — WebUntis
  übernimmt das nicht rückwirkend.</p>
  <p><strong>Folge:</strong> Im Digitalen Klassenbuch muss der Wechsel <em>manuell</em>
  zum richtigen Datum eingetragen werden — sonst landen Einträge in der falschen
  Klasse. E-Mails gehen auf Wunsch an alte, neue oder beide Klassenlehrkräfte.</p>
</details>

<!-- ===== 4. Neue Schüler ===== -->
<details class="warn-case">
  <summary>🆕 Neuer Schüler im Import</summary>
  <div class="warn-timeline">
    <div class="warn-axis"></div>
    <span class="warn-axis-label left">Schuljahres-Beginn</span>
    <span class="warn-axis-label right">Schuljahres-Ende</span>
    <div class="warn-marker new" style="left:55%" title="Aufnahmedatum (heute)"></div>
    <div class="warn-marker now" style="left:55%;background:transparent;box-shadow:none" title="Heute"></div>
    <div style="position:absolute;left:55%;top:5px;font-size:0.7rem;color:#198754;font-weight:bold;">★ neu</div>
  </div>
  <p><strong>Was ist passiert?</strong> Ein Schüler taucht erstmals im Schild-Export auf
  (Interne ID war im vorigen Import noch nicht vorhanden).</p>
  <p><strong>Folge:</strong> In WebUntis muss der Schüler ggf. in Schülergruppen
  (z.B. Fächergruppen, AGs, Kurse) ergänzt werden — das passiert beim Standard-Import
  nicht automatisch.</p>
</details>

<!-- ===== 5. Karteileichen ===== -->
<details class="warn-case">
  <summary>👻 Karteileiche — Schüler verschwunden</summary>
  <div class="warn-timeline">
    <div class="warn-axis"></div>
    <span class="warn-axis-label left">Schuljahres-Beginn</span>
    <span class="warn-axis-label right">Schuljahres-Ende</span>
    <div class="warn-marker old" style="left:55%" title="Letzter Stand"></div>
    <div class="warn-marker now" style="left:60%" title="Heute"></div>
    <div style="position:absolute;left:60%;width:35%;top:24px;height:16px;background:repeating-linear-gradient(45deg,transparent,transparent 4px,rgba(108,117,125,0.3) 4px,rgba(108,117,125,0.3) 8px);border:1px dashed #6c757d;border-radius:3px;font-size:0.7rem;text-align:center;line-height:16px;color:#6c757d;">verschwunden ohne Entlassdatum</div>
  </div>
  <p><strong>Was ist passiert?</strong> Ein Schüler war im vorigen Import noch da,
  taucht jetzt aber nicht mehr auf — und hat <em>kein</em> Entlassdatum erhalten.
  Bei korrektem Schild-Filter („Aktuelles Schuljahr - Aktive, Abgänger und Abschlüsse")
  sollte das praktisch nie passieren.</p>
  <p><strong>Folge:</strong> Wahrscheinlich Filter-Fehler in Schild — der Schüler ist
  weder ordentlich entlassen noch noch aktiv. <em>Vor dem nächsten Import korrigieren.</em></p>
</details>

<p class="text-muted small mt-3">💡 Diese Warnungen werden bei <em>▶️ Verarbeiten</em>
automatisch ermittelt. Per <em>✍ Emails Generieren</em> entstehen daraus vorbereitete
Mails an die zuständigen Klassenlehrkräfte; <em>📨 Emails Senden</em> verschickt sie.</p>
""",
    },

    "erzieher_workflow": {
        "title": "👨‍👩‍👧 Erzieher-Workflow — Schild ↔ WebUntis",
        "html": """
<style>
details.erz-detail { margin: 10px 0; border-left: 4px solid #6f42c1; padding: 4px 0 4px 10px; background: #f8f6fc; border-radius: 0 4px 4px 0; }
details.erz-detail[open] { background: #eee6f7; }
details.erz-detail > summary { cursor: pointer; font-weight: 600; padding: 6px 0; outline: none; list-style: none; }
details.erz-detail > summary::-webkit-details-marker { display: none; }
details.erz-detail > summary::before { content: '▶ '; color: #6f42c1; font-size: 0.8rem; margin-right: 4px; }
details.erz-detail[open] > summary::before { content: '▼ '; }
details.erz-detail .erz-body { padding: 0 4px 4px 4px; }
body.dark-mode details.erz-detail { background: #2a1f3d; border-left-color: #9b7ed4; }
body.dark-mode details.erz-detail[open] { background: #36284e; }
table.col-table { width: 100%; font-size: 0.85rem; margin-bottom: 8px; }
table.col-table td { padding: 3px 6px; border-bottom: 1px solid #eee; vertical-align: top; }
table.col-table td:first-child { white-space: nowrap; }
body.dark-mode table.col-table td { border-bottom-color: #444; }
</style>

<p>SchildNRW speichert Erzieher (Hauptdaten) und zusätzliche Ansprechpartner
(mit Telefonnummern) in <strong>zwei separaten Exports</strong>. WebUntis
hingegen erwartet für jeden Erzieher/Ansprechpartner einen eigenen Datensatz
inklusive Telefonnummer.</p>

<p>Dieser Workflow überbrückt das, indem er pro „n-tem" Erzieher eines Schülers
eine eigene WebUntis-Import-CSV erzeugt (<code>Erzieher_1.csv</code>,
<code>Erzieher_2.csv</code>, …) und alles als ZIP zum Download bereitstellt.</p>

<h6>Schnellstart</h6>
<ol>
  <li>Erzieher-Export aus Schild → in <em>Erzieher-Export-Verzeichnis</em> ablegen.</li>
  <li>Ansprechpartner-Export aus Schild → in <em>Ansprechpartner-Export-Verzeichnis</em> ablegen.</li>
  <li><strong>▶️ Verarbeiten &amp; ZIP erzeugen</strong> klicken — fertig.</li>
</ol>

<p>Vorab empfiehlt sich ein Klick auf <strong>👁️ Vorschau Schüler ↔ Erzieher</strong>
oder <strong>📄 Quelldateien anzeigen</strong>, um die Datenqualität zu prüfen.</p>

<hr>
<h6>📚 Weiterführende Informationen</h6>
<p class="small text-muted mb-2">Die folgenden Abschnitte lassen sich einzeln ausklappen.</p>

<details class="erz-detail" open>
  <summary>📋 Benötigte Spalten — Erzieher-Export</summary>
  <div class="erz-body">
    <p>Schild-Export mit Semikolon-Separator (UTF-8 mit BOM, CRLF). Aus der
    Schild-Export-Vorlage <em>„Erzieher-Daten"</em> typischerweise diese Spalten:</p>
    <table class="col-table">
      <tr><td><strong>Pflicht</strong></td><td></td></tr>
      <tr><td><code>Interne ID-Nummer</code></td><td>Schüler-ID — Verknüpfung mit Ansprechpartner-Export</td></tr>
      <tr><td><code>Erzieher i: Nachname</code></td><td>i = 1, 2, … (so viele Erzieher-Slots wie Schild exportiert, i. d. R. 2)</td></tr>
      <tr><td><code>Erzieher i: Vorname</code></td><td>siehe oben</td></tr>
      <tr><td><code>Erzieher i: E-Mail</code></td><td>siehe oben (leer = wird ggf. per E-Mail-Filter ausgesondert)</td></tr>
      <tr><td><strong>Empfohlen</strong></td><td></td></tr>
      <tr><td><code>Erzieher i: Anrede</code></td><td><em>Frau / Herr</em> — wird für Smart-Match (Telefon ↔ Erzieher) benötigt</td></tr>
      <tr><td><code>Erzieher i: Briefanrede</code></td><td>WebUntis-Darstellung</td></tr>
      <tr><td><code>Erzieher i: Titel</code></td><td>z. B. Dr.</td></tr>
      <tr><td><code>Erzieher: Art (Klartext)</code></td><td>für den <strong>Volljährig-Filter</strong> — Schild markiert hier <em>„Schüler/in ist volljährig"</em></td></tr>
      <tr><td><code>Telefon-Nummern: Telefon-Nummer</code></td><td>für <strong>„Telefon aus Erzieher-Export primär"</strong> — die primäre Telefonnummer pro Schüler</td></tr>
      <tr><td><code>Telefon-Nummern: Anschluss-Art</code></td><td>Mutter / Vater / Notfallnummer / … — bestimmt mit Smart-Match den passenden Erzieher-Slot</td></tr>
      <tr><td><code>Telefon-Nummern: Bemerkung</code></td><td>optional</td></tr>
    </table>
    <p class="small text-muted mb-0">💡 Die <strong>Schüler-Stammdaten</strong>
    (Name, Klasse) liefert dieser Export <em>nicht</em> — sie werden für die
    UI-Darstellung aus dem Ansprechpartner-Export (Spalten <code>Schüler-Klasse</code>
    / <code>Schüler-Vorname</code> / <code>Schüler-Nachname</code>) hinzugejoint.</p>
  </div>
</details>

<details class="erz-detail" open>
  <summary>📋 Benötigte Spalten — Ansprechpartner-Export</summary>
  <div class="erz-body">
    <p>Schild-Export mit Semikolon-Separator (UTF-8 mit BOM). Pro Schüler
    typischerweise eine Zeile pro hinterlegter Telefonnummer (also häufig mehrere
    Zeilen pro Schüler):</p>
    <table class="col-table">
      <tr><td><strong>Pflicht</strong></td><td></td></tr>
      <tr><td><code>Schüler_ID</code></td><td>Verknüpfung mit dem Erzieher-Export (<code>Interne ID-Nummer</code>)</td></tr>
      <tr><td><code>Telefon-Nummer</code></td><td>die eigentliche Nummer</td></tr>
      <tr><td><strong>Empfohlen</strong></td><td></td></tr>
      <tr><td><code>Anschluss-Art</code></td><td>Mutter / Vater / Notfallnummer / … — Basis für Smart-Match</td></tr>
      <tr><td><code>Bemerkung</code></td><td>z. B. <em>„Handy Mutter"</em> — wird in WebUntis übernommen</td></tr>
      <tr><td><code>Schüler-Klasse</code></td><td>nur für die UI-Vorschau / Missing-Report — wird nicht in den Export geschrieben</td></tr>
      <tr><td><code>Schüler-Vorname</code></td><td>wie oben</td></tr>
      <tr><td><code>Schüler-Nachname</code></td><td>wie oben</td></tr>
    </table>
  </div>
</details>

<details class="erz-detail">
  <summary>⚙️ Verarbeitungs-Optionen im Detail</summary>
  <div class="erz-body">
    <p>Alle Optionen unter <em>⚙️ Einstellungen — Erzieher / Ansprechpartner</em>.
    Defaults sind so gewählt, dass bestehende Workflows ohne Änderung weiterlaufen.</p>

    <p><strong>🧠 Smart-Match</strong> <em>(Default: an)</em><br>
    Telefonnummern werden per <code>Anschluss-Art</code> dem passenden Erzieher-Slot
    zugeordnet — <em>Mutter</em> → Frau-Erzieher, <em>Vater</em> → Herr-Erzieher.
    Neutrale Werte (<em>Eltern / Notfallnummer / …</em>) fallen positional auf
    freie Slots zurück. <strong>Ohne</strong> Smart-Match wird rein nach Reihenfolge
    zugeordnet — bei zwei Erziehern landet dann ggf. Vaters Telefon bei der Mutter.</p>

    <p><strong>🔞 Volljährig-Filter</strong> <em>(Default: aus)</em><br>
    Schüler mit <code>Erzieher: Art (Klartext)</code> = <em>„Schüler/in ist volljährig"</em>
    werden komplett aus dem Export entfernt. Bei volljährigen Azubis ist meist kein
    echter Erzieher mehr gepflegt — sie sind ihre eigenen Ansprechpartner.</p>

    <p><strong>📧 E-Mail-Pflicht</strong> <em>(Default: aus)</em><br>
    Erzieher ohne E-Mail werden aus den Output-CSVs gestrichen — sie können sich in
    WebUntis ohnehin nicht anmelden. Nützlich, wenn man die Datenbasis sauber halten
    will und die Erzieher-Datensätze sonst keinen anderen Zweck in WebUntis erfüllen.</p>

    <p><strong>🧪 Dummy-Felder für fehlende Daten</strong> <em>(Default: aus)</em><br>
    Leere Erzieher-Felder werden mit eindeutig erkennbaren Platzhaltern gefüllt
    (Vorname/Nachname/Briefanrede = <code>DUMMY</code>, E-Mail =
    <code>dummy@invalid.local</code>, Telefon = <code>000</code>). So bleibt der
    WebUntis-Import auch bei Pflichtfeld-Lücken erfolgreich, und Dummies können in
    WebUntis nachträglich gefiltert werden.</p>

    <p><strong>♾️ Limit von 2 Erziehern aufheben</strong> <em>(Default: aus)</em><br>
    Schild liefert in der Standardvorlage 2 Erzieher-Slots. Hat ein Schüler im
    Ansprechpartner-Export mehr Telefon-Zeilen (z. B. Oma, Notfallnummer,
    Pflegeeltern), gehen die sonst beim Export verloren. Mit dieser Option entstehen
    <code>Erzieher_3.csv</code>, <code>Erzieher_4.csv</code> usw. — Stammdaten ggf.
    per Dummy-Fill.</p>

    <p><strong>📞 Telefon aus Erzieher-Export primär</strong> <em>(Default: an)</em><br>
    Die im Erzieher-Export hinterlegte primäre Telefonnummer
    (<code>Telefon-Nummern: …</code>) wird als <em>prioritäre</em> Pseudo-
    Ansprechpartner-Zeile behandelt — sie bekommt damit Vorrang beim Smart-Match-
    Slot-Mapping. Duplikate gegenüber dem Ansprechpartner-Export werden gefiltert.</p>

    <p><strong>🆔 Eindeutige Eltern-IDs vergeben</strong> <em>(Default: aus)</em><br>
    Schild hat keine schul-/personeneindeutige Eltern-ID — bei Geschwistern legt
    Schild für jedes Kind einen separaten Erzieher-Datensatz an, ohne diese als
    „dieselbe Person" zu markieren. WebUntis kann (sofern aktiv) eine schulweit
    eindeutige Eltern-ID als Matching-Key auswerten, damit derselbe Erzieher-
    Account über mehrere Kinder hinweg verbunden ist. Diese Option vergibt solche
    IDs persistent — siehe eigenen Abschnitt unten.</p>
  </div>
</details>

<details class="erz-detail">
  <summary>🆔 Eindeutige Eltern-IDs — wie funktioniert das?</summary>
  <div class="erz-body">
    <p>Aktiviert man die Option <strong>Eltern-IDs vergeben</strong>, bekommt jeder
    Erzieher eine schulweit eindeutige ID der Form <code>E00001</code>,
    <code>E00002</code>, … Die Zuordnung wird im Arbeitsverzeichnis als
    <code>eltern_ids.json</code> gespeichert und über alle Verarbeitungsläufe
    hinweg <strong>wiederverwendet</strong>.</p>

    <p><strong>Identitäts-Schlüssel:</strong> Zwei Erzieher gelten als
    „dieselbe Person", wenn alle drei Felder übereinstimmen (jeweils
    case-insensitive):</p>
    <ul>
      <li><code>Vorname</code></li>
      <li><code>Nachname</code></li>
      <li><code>E-Mail</code></li>
    </ul>
    <p>Bei leerer E-Mail wird auf <code>Vorname + Nachname</code> heruntergebrochen.
    <strong>Dummy-Erzieher</strong> (Nachname oder Vorname = <code>DUMMY</code>,
    E-Mail endet auf <code>@invalid.local</code>) bekommen <em>keine</em> ID — sie
    sind Platzhalter für fehlende Daten.</p>

    <p><strong>Output:</strong> In jedem <code>Erzieher_N.csv</code> kommt eine
    zusätzliche Spalte <code>Erzieher N: Eltern-ID</code> ans Ende. Die ID ist über
    alle Erzieher_N-Dateien hinweg konsistent — Mutter und Vater eines Geschwister-
    Paares bekommen also dieselbe ID, egal ob sie bei Kind 1 in <code>Erzieher_1.csv</code>
    und bei Kind 2 in <code>Erzieher_2.csv</code> landen.</p>

    <p><strong>Datenbank-Verwaltung:</strong> Im Settings-Panel zeigt ein Info-Block
    den aktuellen Stand (Anzahl IDs, nächste ID, letzte Änderung). Über
    <em>🗑️ ID-Datenbank zurücksetzen</em> lässt sich die Datei löschen — danach
    werden beim nächsten Verarbeiten alle IDs neu vergeben. Achtung: bestehende
    WebUntis-Verknüpfungen brechen damit auf.</p>

    <p class="text-muted small mb-0">💡 Da der WebUntis-Import-Layer die Eltern-ID-
    Spalte derzeit (Stand: Mai 2026) ohnehin als optional behandelt — er nutzt
    Vorname, Nachname und E-Mail als primären Matching-Key — kann man die Option
    sicher aktivieren, ohne Imports zu brechen. Sie wird relevant, sobald WebUntis
    Eltern-IDs offiziell unterstützt.</p>
  </div>
</details>

<details class="erz-detail">
  <summary>👁️ Vorschau, 📄 Quelldateien, ⚠️ Klassen-Report</summary>
  <div class="erz-body">
    <p><strong>👁️ Vorschau Schüler ↔ Erzieher:</strong> Zeigt das Ergebnis der
    Zuordnung pro Schüler oder pro Erzieher (Gruppen-Sicht — gleicher Erzieher
    bei mehreren Kindern). Mit Suche, Field-Mapping, Smart-Match-Statistik und
    Orphan-Liste (Telefon-Zeilen ohne Erzieher-Slot).</p>

    <p><strong>📄 Quelldateien anzeigen:</strong> Roher Blick auf die beiden CSVs —
    Tab-Umschaltung Erzieher ↔ Ansprechpartner, mit Such-Filter und farblicher
    Markierung der Spalten, die der Workflow nutzt (grün) bzw. ignoriert (grau).
    Hilfreich, um schnell zu verifizieren, dass der Schild-Export die richtigen
    Spalten enthält.</p>

    <p><strong>⚠️ Fehlende Erzieher (Klassen):</strong> Klassenweise Liste der
    <strong>nicht-volljährigen Schüler</strong>, bei denen Erzieher-Daten unvollständig
    sind. Die Kriterien sind konfigurierbar:</p>
    <ul>
      <li>Kein Erzieher hinterlegt</li>
      <li>Mind. ein Erzieher ohne Nachname / Vorname / E-Mail</li>
    </ul>
    <p>Verknüpfung wahlweise mit <em>ODER</em> (mindestens eines) oder <em>UND</em>
    (alle aktivierten). Selektion erfolgt per Klassen-Checkbox; Export erzeugt eine
    CSV pro Klasse mit Schüler-ID, Klasse, Name und Begründungs-Spalte. Praktisch,
    um Klassenlehrer:innen gezielt auf nachzupflegende Daten anzusprechen.</p>
  </div>
</details>

<details class="erz-detail">
  <summary>📥 Import in WebUntis</summary>
  <div class="erz-body">
    <p>Pro Erzieher-CSV im ZIP einen separaten Import-Lauf in WebUntis konfigurieren —
    so landet jeder Erzieher als eigenständiger Datensatz im System.</p>

    <p class="alert alert-info py-2 px-2 small mb-3">
      ⚠️ <strong>Wichtig zu wissen — was WebUntis tatsächlich verarbeitet</strong><br>
      Der WebUntis-Erzieher-Import wertet derzeit (Stand: Mai 2026) nur einen
      Bruchteil der Spalten aus. Die übrigen Spalten exportieren wir trotzdem,
      damit der Import nicht angepasst werden muss, falls WebUntis das in Zukunft
      ändert.
    </p>

    <h6>Tatsächlich von WebUntis verwendet</h6>
    <table class="col-table">
      <tr><td><code>Interne_ID_Nummer</code></td><td>→ <strong>Schüler-ID (Matching)</strong> — Pflicht</td></tr>
      <tr><td><code>Erzieher i: Vorname</code></td><td>→ <strong>Stammdaten</strong></td></tr>
      <tr><td><code>Erzieher i: Nachname</code></td><td>→ <strong>Stammdaten</strong></td></tr>
      <tr><td><code>Erzieher i: E-Mail</code></td><td>→ <strong>Stammdaten / Account-Anlage</strong></td></tr>
      <tr><td><code>Erzieher i: Eltern-ID</code></td><td>→ <em>(optional)</em> schulweit eindeutige ID — nur falls Spalte vorhanden</td></tr>
    </table>

    <h6>Mit-Exportiert, aber von WebUntis derzeit ignoriert</h6>
    <p class="text-muted small">Diese Spalten sind im Export enthalten, um vorbereitet
    zu sein, falls WebUntis die Auswertung erweitert. Sie verursachen keinen Fehler,
    werden aber aktuell nicht in WebUntis übernommen:</p>
    <table class="col-table">
      <tr><td><code>Erzieher i: Anrede</code></td><td>(ignored)</td></tr>
      <tr><td><code>Erzieher i: Briefanrede</code></td><td>(ignored)</td></tr>
      <tr><td><code>Erzieher i: Titel</code></td><td>(ignored)</td></tr>
      <tr><td><code>Erzieher i: Anschluss Art</code></td><td>(ignored)</td></tr>
      <tr><td><code>Erzieher i: Bemerkung</code></td><td>(ignored)</td></tr>
      <tr><td><code>Erzieher i: Telefon-Nummer</code></td><td>(ignored)</td></tr>
    </table>
    <p class="text-muted small mb-0">💡 Wer den Export schlanker haben möchte, kann
    die nicht genutzten Spalten manuell vor dem WebUntis-Import löschen — die vier
    relevanten Spalten reichen aus.</p>
  </div>
</details>

<p class="text-muted small mt-3">💡 Dieser Workflow wurde aus dem ursprünglichen
Standalone-Tool <em>SchildNRW-WebUntis-Erzieher-Konvertierer</em> in das Haupttool
integriert (Update 3.2).</p>
""",
    },

    "ausbilder_workflow": {
        "title": "🏭 Ausbilder-Workflow — DSGVO-konformer Import (Berufskolleg)",
        "html": """
<style>
details.ausb-detail { margin: 10px 0; border-left: 4px solid #17a2b8; padding: 4px 0 4px 10px; background: #f4fbfc; border-radius: 0 4px 4px 0; }
details.ausb-detail[open] { background: #e7f6f8; }
details.ausb-detail > summary { cursor: pointer; font-weight: 600; padding: 6px 0; outline: none; list-style: none; }
details.ausb-detail > summary::-webkit-details-marker { display: none; }
details.ausb-detail > summary::before { content: '▶ '; color: #17a2b8; font-size: 0.8rem; margin-right: 4px; }
details.ausb-detail[open] > summary::before { content: '▼ '; }
details.ausb-detail .ausb-body { padding: 0 4px 4px 4px; }
body.dark-mode details.ausb-detail { background: #16323a; border-left-color: #2aa1b8; }
body.dark-mode details.ausb-detail[open] { background: #1c4854; }
</style>

<p>Speziell für <strong>Berufskollegs in NRW</strong>: SchildNRW exportiert für
jeden Auszubildenden auch die Daten seines Ausbildungsbetriebs / Betreuers.
Diese sollen in WebUntis gepflegt werden, damit Ausbilder die Fehlstunden ihrer
Azubis sehen können.</p>

<p>Aus <strong>DSGVO/VO DVI</strong>-Gründen dürfen jedoch nur Datensätze derjenigen
Azubis übernommen werden, die der Datenverarbeitung <strong>zugestimmt</strong>
haben. Dieser Workflow filtert den Schild-Export entsprechend:</p>
<ul>
  <li><strong>Klassen-Whitelist:</strong> Nur Klassen, in denen Ausbilder-Importe
      überhaupt sinnvoll sind (z.B. duale Bildungsgänge). Leer = alle Klassen.</li>
  <li><strong>Schüler-Blacklist:</strong> Schüler ohne Einwilligung werden namentlich
      ausgeschlossen — dauerhaft, bis sie wieder aktiviert werden.</li>
</ul>

<h6>Vorbereitung im Tool</h6>
<ol>
  <li><strong>Schild-Export</strong> mit den Spalten <code>Interne ID-Nummer</code>,
      <code>Klasse</code>, <code>Vorname</code>, <code>Nachname</code> sowie allen
      benötigten Ausbilder-/Betreuer-Feldern als CSV mit Semikolon-Separator speichern.
      Datei im konfigurierten <em>Ausbilder-Eingabeverzeichnis</em> ablegen
      (Einstellungen → Quelldaten-Verzeichnis). Eine ausführliche Export-Vorlagen-
      Empfehlung ist weiter unten ausklappbar.</li>
  <li>In der Schüler-Tabelle die <strong>Klassen-Whitelist</strong> über die
      farbigen Klassen-Chips konfigurieren — wird automatisch gespeichert.</li>
  <li>In der Schüler-Tabelle das <strong>Häkchen</strong> bei jenen Schülern
      entfernen, die nicht eingewilligt haben. Die Blacklist wird sofort
      persistent gespeichert.</li>
</ol>

<h6>Verarbeitung</h6>
<p>Klick auf <strong>▶️ Verarbeiten &amp; CSV erzeugen</strong>:</p>
<ol>
  <li>Die neueste CSV im Eingabeverzeichnis wird geladen.</li>
  <li>Es werden nur die Zeilen übernommen, deren <em>Klasse</em> in der Whitelist
      steht (oder: alle, wenn die Whitelist leer ist) <strong>und</strong> deren
      <em>Interne ID-Nummer</em> nicht auf der Blacklist steht.</li>
  <li>Die gefilterte CSV wird in das <em>Ausbilder-Ausgabeverzeichnis</em>
      geschrieben — bereit für den WebUntis-Import.</li>
</ol>

<p>Anschließend lässt sich die Datei über <strong>⬇️ CSV herunterladen</strong>
auch im Browser holen.</p>

<h6>Datei-Konfliktauflösung</h6>
<p>Existiert bereits eine Datei mit demselben Namen im Ausgabeverzeichnis, hängt
das Tool automatisch einen <code>HHMMSS</code>-Zeitstempel an, statt die alte
Datei zu überschreiben.</p>

<hr>
<h6>📚 Weiterführende Informationen</h6>
<p class="small text-muted mb-2">Die folgenden Abschnitte lassen sich einzeln ausklappen.</p>

<details class="ausb-detail">
  <summary>📜 Rechtlicher Hintergrund — VO DVI &amp; DSGVO</summary>
  <div class="ausb-body">
    <p class="alert alert-warning py-2 small mb-3">
      <strong>Disclaimer:</strong> Der Autor dieses Tools ist <em>Lehrkraft, nicht Anwalt</em>.
      Die hier zusammengefasste rechtliche Einschätzung ist die <strong>vorherrschende
      Auslegung am Berufskolleg des Autors</strong>. Im Zweifel bitte selbst prüfen lassen —
      die Verantwortung für den datenschutzkonformen Einsatz liegt bei Ihnen / Ihrer Schule.
    </p>

    <p><strong>Was die VO DVI in NRW erlaubt:</strong></p>
    <p>In Nordrhein-Westfalen regelt die <em>Verordnung über die zur Verarbeitung
    zugelassenen Daten von Schülerinnen, Schülern und Eltern</em> (<strong>VO DVI</strong>),
    welche Daten Berufskollegs an Ausbildungsbetriebe übermitteln dürfen. Erlaubt ist von
    sich aus <strong>nur die Übermittlung unentschuldigter Schulversäumnisse</strong>
    (BASS-Verweis: Anlage 1, Nr. 5 zur VO DVI —
    <a href="https://bass.schul-welt.de/101.htm#:~:text=4.%20Erreichbarkeit%2C-,5.%20Angaben%20zu%20unentschuldigten%20Schulvers%C3%A4umnissen.,-(5)%20Zur%20Organisation"
       target="_blank" rel="noopener">Quelle in der BASS</a>).</p>

    <p>Die rechtliche Grundlage für diese Übermittlung ist <strong>DSGVO Art. 6 Abs. 1
    Satz 1 Buchstabe e</strong>, Abs. 3 in Verbindung mit <strong>Art. 9 Abs. 2 Buchstabe g</strong>
    (<a href="https://bass.schul-welt.de/101.htm#:~:text=Nach%20Artikel%206%20Abs.%201%20Satz%201%20Buchstabe%20e%2C%20Abs.%203%20und%20Artikel%209%20Abs.%202%20Buchstabe%20g"
        target="_blank" rel="noopener">Quelle</a>).</p>

    <p>Für <strong>alle anderen Daten</strong> — insbesondere <em>entschuldigte</em>
    Fehlzeiten — ist eine ausdrückliche <strong>Einwilligung des/der Auszubildenden</strong>
    erforderlich (<a href="https://dsgvo-gesetz.de/art-6-dsgvo/#:~:text=Die%20betroffene%20Person,betroffenen%20Person%20erfolgen%3B"
    target="_blank" rel="noopener">DSGVO Art. 6 Abs. 1 lit. a / b</a>).
    Die <a href="https://bass.schul-welt.de/101.htm#:~:text=insbesondere,6%2C%207%2C%209"
    target="_blank" rel="noopener">BASS verweist explizit</a> auf die DSGVO-Artikel 5, 6,
    7 und 9 als geltendes Recht.</p>

    <p><strong>Das konkrete WebUntis-Problem</strong> (Stand 08.07.2024):</p>
    <ul>
      <li>WebUntis <strong>unterscheidet in der Ausbilder-Sicht derzeit nicht</strong>
          zwischen entschuldigten und unentschuldigten Fehlzeiten.</li>
      <li>Ausbilder werden über die <strong>Schülerstammdaten</strong> per Abgleich der
          Betreuer-Daten automatisch zugeordnet und erhalten dadurch <strong>permanenten
          Zugriff</strong> auf die Abwesenheitsdaten <em>aller</em> ihnen so zugeordneten
          Auszubildenden — auch derjenigen, die der erweiterten Datenverarbeitung
          <strong>nicht zugestimmt</strong> haben.</li>
    </ul>

    <p><strong>Re-Identifizierungs-Risiko:</strong> Selbst wenn ausschließlich
    <em>unentschuldigte</em> Daten sichtbar wären oder wiederholt übertragen würden,
    ließe sich durch den dauerhaften bzw. wiederholten Zugriff im Nachhinein die
    <em>Entschuldigung</em> einzelner Fehlzeiten rekonstruieren — was nach VO DVI
    ebenfalls nicht zulässig wäre.</p>

    <p><strong>Lösungsweg dieses Tools:</strong> Damit Sie nicht jedes Mal manuell
    in Schild filtern müssen (sehr umständlich) oder umgekehrt komplett auf den
    Ausbilder-Import verzichten (nicht praktikabel), erlaubt dieser Workflow:</p>
    <ul>
      <li>Pauschal alle Klassen, in denen Ausbilder-Importe <em>nicht</em> sinnvoll sind,
          per <strong>Klassen-Whitelist</strong> auszuschließen (z.B. für Probephasen).</li>
      <li>Einzelne Auszubildende, die der Datenverarbeitung <em>nicht</em> zugestimmt
          haben, per <strong>Schüler-Blacklist</strong> dauerhaft aus dem Export
          herauszuhalten.</li>
    </ul>

    <p class="text-muted small mb-0">💡 <strong>Tipp:</strong> SchildNRW hat eine Checkbox
    <code>DV-Einwilligung vorh.</code> im Schüler-Datensatz. Wenn diese Checkbox in Ihrer
    Schule <em>konsistent ausschließlich</em> für die DSGVO-Einwilligung der Ausbilder-
    Datenübermittlung verwendet wurde, brauchen Sie dieses Tool eigentlich nicht — Sie
    können dann direkt in Schild über die Checkbox filtern. Wurde die Checkbox in der
    Vergangenheit jedoch jemals für etwas anderes (mit-)benutzt, ist die Datenbasis nicht
    mehr verlässlich, und dieses Tool ist der praktikable Workaround.</p>
  </div>
</details>

<details class="ausb-detail">
  <summary>📋 Vorbereitende Schritte in SchildNRW</summary>
  <div class="ausb-body">
    <p><strong>1. Betreuer-Datenpflege:</strong> Damit der spätere Ausbilder-Import in
    WebUntis sauber durchläuft (und Ausbilder nicht doppelt angelegt werden), müssen
    die Betreuer-Datensätze in Schild konsistent gepflegt sein. Bei <em>allen</em>
    Aktiven, Abgängern und Abschlüssen sollte gelten:</p>
    <ul>
      <li>Jeder Betreuer kommt in <strong>genau einer Schreibweise</strong> vor
          (Vorname, Nachname, E-Mail).</li>
      <li>Alle Namensfelder sind <strong>vorhanden und korrekt</strong> ausgefüllt.</li>
      <li>Das <strong>E-Mail-Feld</strong> ist gepflegt und enthält möglichst eine
          <em>persönliche</em> Adresse des Betreuers — keine allgemeine Firmenadresse,
          da WebUntis die E-Mail-Adresse zur Identifikation verwendet.</li>
      <li>Auch die <strong>Anrede</strong> ist gesetzt (wird in WebUntis für die
          ordentliche Darstellung benötigt).</li>
    </ul>
    <p class="small text-muted">💡 Wenn Sie die Daten neu aufbereiten, füllen Sie am
    besten <em>alle</em> Felder. Tipp: Ordnen Sie einen aufbereiteten Betreuer in Schild
    am besten gleich allen ihm/ihr betreuten Auszubildenden zu.</p>

    <p><strong>2. Schild-Filter für den Export:</strong> Erstellen Sie einen Filter,
    der zuverlässig <em>alle</em> Auszubildenden des Schuljahres erfasst — wichtig:
    inklusive <strong>Abgänger und Abschlüsse</strong>, damit deren Ausbilder-Zuweisungen
    beim nächsten Import in WebUntis auch wieder entfernt werden.</p>
    <ul>
      <li><strong>Klassisch:</strong> <code>Laufbahn-Schuljahr: Aktuelles</code>,
          <code>Status: Aktiv, Abgang, Abschluss</code>, unter <em>Weitere Daten</em>:
          <code>Beschäftigungsart: Auszubildender</code>.</li>
      <li><strong>SQL-Filter</strong> (drei vorgefertigte Varianten — prüfen entweder
          die Anwesenheit eines Betriebs-Datensatzes, die Vertragsart oder beides):
          siehe README des Original-Tools, Abschnitt <em>Vor der Installation</em>:
          <a href="https://github.com/CmoneBK/AusbilderImporterFlask#vor-der-installation"
             target="_blank" rel="noopener">AusbilderImporterFlask auf GitHub</a>.</li>
    </ul>
  </div>
</details>

<details class="ausb-detail">
  <summary>📤 Empfohlene Schild-Export-Vorlage (Spalten)</summary>
  <div class="ausb-body">
    <p>Erstellen Sie in Schild eine Export-Vorlage mit folgenden Spalten — diese sind
    entweder von dieser App, von WebUntis oder von beiden zur Identifikation der
    Auszubildenden und Betreuer nötig:</p>
    <table class="table table-sm table-bordered mb-2">
      <thead class="thead-light">
        <tr><th>Spalte in Schild</th><th>Zweck</th></tr>
      </thead>
      <tbody>
        <tr><td><code>Interne ID-Nummer</code></td><td>Identifikation Schüler (Tool + WebUntis)</td></tr>
        <tr><td><code>Nachname</code></td><td>App-Anzeige</td></tr>
        <tr><td><code>Vorname</code></td><td>App-Anzeige</td></tr>
        <tr><td><code>Klasse</code></td><td>App-Filter + Anzeige</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Anrede</code></td><td>WebUntis-Darstellung</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Vorname</code></td><td>Identifikation Betreuer</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Name</code></td><td>Identifikation Betreuer</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer E-Mail</code></td><td>WebUntis-Betreueraccount</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Titel</code></td><td>Falls als Anrede verwendet</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Telefon</code></td><td>WebUntis-Identifikation (optional)</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Abteilung</code></td><td>WebUntis-Identifikation (optional)</td></tr>
        <tr><td><code>Allg. Adresse: Fax-Nr.</code></td><td>WebUntis-Identifikation (optional)</td></tr>
        <tr><td><code>Allg. Adresse: Name1</code></td><td>Betriebsname (Übersicht)</td></tr>
      </tbody>
    </table>
    <p class="small text-muted mb-0">Die Vorlage muss als <code>.csv</code> mit Semikolon-Separator
    exportieren — in Schild ggf. den Dateityp manuell auf „Alle Dateien (*.*)" stellen und die
    Endung <code>.csv</code> selbst anhängen.</p>
  </div>
</details>

<details class="ausb-detail">
  <summary>📥 Empfohlene WebUntis-Import-Vorlage</summary>
  <div class="ausb-body">
    <p>Legen Sie in WebUntis eine Import-Vorlage für <em>Ausbildungsbeauftragte</em> an.
    Wesentliche Einstellungen:</p>
    <ul>
      <li><strong>Erste Zeile ignorieren:</strong> Ja (CSV-Header)</li>
      <li><strong>Schülerverbindung additiv importieren:</strong>
          <span class="text-danger">Nein</span> — ein „Ja" würde dazu führen, dass
          neu auf die Blacklist gesetzte Schüler ihre Ausbilder-Zuweisung
          <em>nicht</em> mehr verlieren bzw. leere Einträge vorhandene nicht
          überschreiben. <strong>Genau das wäre der Datenschutz-GAU.</strong></li>
      <li><strong>Identifikation des Ausbildungsbeauftragten:</strong> automatisch</li>
    </ul>
    <p>Feld-Zuordnung (Schild-Spalte → WebUntis-Feld):</p>
    <table class="table table-sm table-bordered mb-2">
      <thead class="thead-light">
        <tr><th>Schild-Spalte</th><th>→ WebUntis-Feld</th></tr>
      </thead>
      <tbody>
        <tr><td><code>Allg. Adresse: Betreuer Anrede</code></td><td>Titel</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Vorname</code></td><td>Vorname</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Name</code></td><td>Nachname</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer E-Mail</code></td><td>E-Mail-Adresse</td></tr>
        <tr><td><code>Allg. Adresse: Betreuer Telefon</code></td><td>Mobiltelefon (optional)</td></tr>
        <tr><td><code>Allg. Adresse: Fax-Nr.</code></td><td>Telefonnummer (optional)</td></tr>
        <tr><td><code>Interne ID-Nummer</code></td><td><strong>Schlüssel (extern, Schüler)</strong> — zentral</td></tr>
      </tbody>
    </table>
    <p class="small text-muted mb-0">Weitere optionale Betreuer-Felder helfen WebUntis
    bei der automatischen Erkennung bereits vorhandener Ausbilder — Felder, die Sie nicht
    brauchen, lassen Sie einfach leer.</p>
  </div>
</details>

<details class="ausb-detail">
  <summary>⚙️ Voraussetzungen für die Identifikation</summary>
  <div class="ausb-body">
    <ul class="mb-0">
      <li>Sie nutzen in SchildNRW die <strong>Interne ID</strong> zur Schüler-Identifikation.</li>
      <li>Sie nutzen in WebUntis den <strong>Schlüssel (extern)</strong> zur Schüler-Identifikation.</li>
    </ul>
  </div>
</details>

<p class="text-muted small mt-3">💡 Dieser Workflow wurde aus dem ursprünglichen
Standalone-Tool <em><a href="https://github.com/CmoneBK/AusbilderImporterFlask"
target="_blank" rel="noopener">AusbilderImporterFlask</a></em> in das Haupttool
integriert (Update 3.2). Die rechtlichen Erläuterungen stammen aus dessen README.</p>
""",
    },

    "info_mails": {
        "title": "ℹ️ Info-Mails bei Feldänderungen",
        "html": """
<p>Während die normalen <strong>Warnungs-Mails</strong> kritische Probleme melden
(Klassenwechsel, Entlassdatum-Probleme, …), informieren <strong>Info-Mails</strong>
Lehrkräfte proaktiv über Änderungen an beliebigen, frei wählbaren Schülerfeldern.</p>

<h6>Typische Anwendungsfälle</h6>
<ul>
  <li>Eine Schülerin bekommt einen Nachteilsausgleich — die Klassenlehrkraft soll
      sofort informiert werden, ohne dass jemand „dran denken" muss.</li>
  <li>Die Telefonnummer eines Schülers ändert sich — relevant für Notfälle.</li>
  <li>Die Attestpflicht wird gesetzt oder aufgehoben.</li>
</ul>

<h6>Workflow</h6>
<ol>
  <li>Öffnen Sie das Menü <code>ℹ️ Info-Mails</code> (Button im Navigationsbereich).</li>
  <li>Wählen Sie die Schülerfelder aus, die überwacht werden sollen. Die Auswahl
      wird <strong>geräteübergreifend in der <code>settings.ini</code></strong> gespeichert
      — d.h. wenn das Tool als Server auf mehreren Geräten bedient wird, ist die
      Auswahl überall gleich.</li>
  <li>Klick auf <em>✍ Generieren</em> → das Tool vergleicht den aktuellen Import mit dem
      letzten und zeigt eine <strong>Vorschau-Tabelle</strong> aller Mails an.</li>
  <li>In der Tabelle kann jede Mail einzeln <strong>per Checkbox abgewählt</strong>
      werden, falls sie diesmal nicht versendet werden soll (z.B. Korrektur eines
      Tippfehlers).</li>
  <li>Bei Nachteilsausgleich-Änderungen erscheint ein <strong>ℹ️-Button</strong> in der
      Vorschau-Zeile — Klick zeigt die zugehörigen <em>Details</em> aus der Sonderpädagogen-
      Arbeitsdatei.</li>
  <li>Klick auf <em>📨 Senden</em> verschickt die markierten Mails.</li>
</ol>

<h6>Mail-Vorlage</h6>
<p>Die Mail-Vorlage lässt sich im <code>✉️ Email-Vorlagen Editor</code> anpassen.
Verfügbare Platzhalter (Auszug):</p>
<ul>
  <li><code>$Vorname</code>, <code>$Nachname</code>, <code>$Klasse</code></li>
  <li><code>$Klassenlehrkraft_1</code>, <code>$Klassenlehrkraft_1_Email</code> usw.</li>
  <li><code>$aenderungen_html</code> — HTML-Tabelle aller geänderten Felder</li>
  <li><code>$nachteilsausgleich_details</code> — Details aus der Sonderpädagogen-Arbeitsdatei</li>
</ul>
""",
    },

    # =====================================================================
    # FOTO-FUNKTIONEN
    # =====================================================================
    "foto_zip": {
        "title": "📦 Foto-ZIP für WebUntis-Import",
        "html": """
<p>WebUntis akzeptiert Schüler-Fotos nur als ZIP-Paket. Das Tool baut so ein ZIP
direkt aus dem Foto-Verzeichnis — nur mit den Fotos, die zum aktuellen Import passen.</p>

<h6>Status-Auswahl</h6>
<p>Mit den Checkboxen oben legen Sie fest, welche Schüler einbezogen werden:</p>
<ul>
  <li><strong>Default-Vorschlag</strong> sind genau die Status-Werte, die im
      aktuellen Import vorkommen. Das ist meistens schon richtig.</li>
  <li>Sie können die Auswahl manuell anpassen — z.B. nur <em>Status 2 (Aktiv)</em>
      ohne Externe.</li>
  <li>Wenn alle Checkboxen aus sind, werden <strong>alle</strong> Schüler des
      Imports berücksichtigt.</li>
</ul>

<h6>Dateinamen-Vorlage</h6>
<p>Über die Vorlage steuern Sie den Namen des ZIP. Platzhalter:</p>
<ul>
  <li><code>{datum}</code> — Datum im Format <code>2026-05-21</code></li>
  <li><code>{datetime}</code> — Datum + Uhrzeit (für mehrere ZIPs am gleichen Tag)</li>
  <li><code>{zeit}</code>, <code>{jahr}</code>, <code>{monat}</code>, <code>{tag}</code></li>
</ul>
<p>Die zuletzt verwendete Vorlage wird automatisch in die <code>settings.ini</code>
gespeichert und beim nächsten Aufruf wieder vorgeschlagen.</p>

<h6>Zwei-Schritt-Prozess</h6>
<ol>
  <li><strong>📦 ZIP erstellen:</strong> Erzeugt das ZIP und legt es im
      <em>Foto-ZIP-Ausgabeverzeichnis</em> ab — auch zur manuellen Abholung am Server
      oder für automatische Weiterverarbeitung verfügbar.</li>
  <li><strong>⬇️ ZIP herunterladen:</strong> Lädt das zuletzt erstellte ZIP über
      den Browser herunter (für den direkten Upload in WebUntis).</li>
</ol>

<p>Schüler ohne passendes Foto werden übersprungen — die Statistik im Status-Banner
zeigt, wie viele Fotos gepackt und wie viele übersprungen wurden.</p>
""",
    },

    "foto_rename": {
        "title": "📂 Fotos umbenannt in Unterordner kopieren",
        "html": """
<p>Standardmäßig sind Foto-Dateien nach der <strong>Internen ID</strong> benannt
(z.B.&nbsp;<code>12345.jpg</code>) — für WebUntis ist das ideal, für menschliche
Bearbeitung nicht. Diese Funktion erzeugt eine umbenannte Kopie in einem Unterordner.</p>

<h6>Wofür?</h6>
<ul>
  <li>Klassenfotos zusammenstellen mit lesbaren Namen
      (<code>Mueller_Max_10A.jpg</code> statt <code>12345.jpg</code>).</li>
  <li>Fotos an externe Stellen schicken (z.B. Schülerausweis-Druck) wo die ID
      irrelevant ist.</li>
  <li>Fotos für eine Jahrbuch-Bearbeitung vorbereiten.</li>
</ul>

<h6>Status-Auswahl</h6>
<p>Verwendet die <strong>gleichen Status-Checkboxen</strong> wie der ZIP-Bereich oben.</p>

<h6>Dateinamen-Vorlage</h6>
<p>Frei kombinierbar aus folgenden Platzhaltern (die Datei-Endung wird automatisch
angehängt):</p>
<ul>
  <li><code>{id}</code> — Interne ID-Nummer</li>
  <li><code>{vorname}</code>, <code>{nachname}</code></li>
  <li><code>{klasse}</code></li>
  <li><code>{status}</code> — Schild-Status-Code</li>
  <li><code>{geschlecht}</code></li>
  <li><code>{geburtsdatum}</code></li>
</ul>
<p>Beispiele:</p>
<ul>
  <li><code>{nachname}_{vorname}_{id}</code> → <code>Mueller_Max_12345.jpg</code></li>
  <li><code>{klasse}_{nachname}_{vorname}</code> → <code>10A_Mueller_Max.jpg</code></li>
  <li><code>{klasse}/{nachname}_{vorname}</code> <em>(Schrägstrich wird zu Unterstrich —
      keine Verschachtelung möglich)</em></li>
</ul>

<h6>Unterordner-Name</h6>
<p>Standard: <code>Umbenannt</code>. Die Kopien landen in
<code>&lt;Foto-Verzeichnis&gt;/&lt;Unterordner&gt;/</code>.</p>

<h6>Konfliktauflösung</h6>
<p>Existiert bereits eine Datei mit dem gleichen Namen, wird ein Suffix
<code>_1</code>, <code>_2</code>, &hellip; angehängt — keine Datei wird überschrieben.</p>

<p>Sowohl Vorlage als auch Unterordner werden beim Kopieren als Standard für den
nächsten Aufruf gespeichert.</p>
""",
    },

    # =====================================================================
    # WEBUNTIS
    # =====================================================================
    "webuntis_import": {
        "title": "🟧 WebUntis-Import konfigurieren",
        "html": """
<p>Die fertige WebUntis-Import-Datei landet im konfigurierten <strong>Importe-Verzeichnis</strong>
mit aktuellem Datum/Uhrzeit im Dateinamen.</p>

<h6>Import-Einstellungen in WebUntis</h6>
<p>Damit der Import sauber funktioniert, müssen die WebUntis-Import-Einstellungen
korrekt sein:</p>
<ul>
  <li><strong>Zeichensatz:</strong> <code>UTF-8</code> (nicht ANSI oder Windows-1252)</li>
  <li><strong>Trennzeichen:</strong> Semikolon <code>;</code></li>
  <li><strong>Format:</strong> Die Spalten-Reihenfolge der vom Tool erzeugten CSV
      entspricht dem WebUntis-Standard — keine manuelle Konfiguration nötig.</li>
</ul>

<h6>Mehrfach-Import verhindert Doppel-Verarbeitung</h6>
<p>Das Tool prüft beim Verarbeiten, ob seit dem letzten Lauf relevante Änderungen
vorliegen. Über die Option <em>„Importdatei-Erstellung unterbinden"</em> in den
Verarbeitungseinstellungen lässt sich auch verhindern, dass bei Admin-Warnungen
überhaupt eine Importdatei erzeugt wird — wichtig für vollautomatisierte Nutzung.</p>

<h6>Foto-Import</h6>
<p>Fotos werden in WebUntis als <strong>ZIP-Paket</strong> hochgeladen (nicht als
einzelne Dateien). Das Foto-ZIP erstellen Sie im Bereich <code>🖼️ Fotos managen</code>.</p>
""",
    },

    # =====================================================================
    # DASHBOARD
    # =====================================================================
    "dashboard_overview": {
        "title": "📊 Dashboard & Historie",
        "html": """
<p>Das Tool führt eine eigene <strong>persistente Historien-Datenbank</strong>, in
der alle Importe und festgestellten Änderungen protokolliert werden.</p>

<h6>Was bietet das Dashboard?</h6>
<ul>
  <li><strong>Statistiken</strong> über die Schülerschaft (Anzahl, Status-Verteilung, …)</li>
  <li><strong>Klassen-Hotspots:</strong> welche Klassen haben die meisten Änderungen?</li>
  <li><strong>Verlaufstrends</strong> mit Diagrammen über die Zeit</li>
  <li><strong>Klassen-Detailansicht:</strong> Klick auf eine Klasse zeigt deren Entwicklung
      über die Zeit (Schüler-Zahl, Änderungs-Häufigkeit, …)</li>
  <li><strong>Schülerhistorien-Suche:</strong> Suche nach Name/ID zeigt die komplette
      Historie eines Schülers — alle Änderungen mit Datum, Feld und Alt-/Neu-Wert.
      Falls ein Foto verfügbar ist, wird es mit angezeigt.</li>
  <li><strong>Excel-Export:</strong> die gesamte Historie oder die eines einzelnen Schülers
      als Excel exportieren.</li>
</ul>

<h6>Historie vs. Änderungs-Log-Dateien</h6>
<ul>
  <li>Die <strong>Historie</strong> ist die strukturierte Datenbank im Tool —
      ideal für Auswertung und Analyse.</li>
  <li>Die <strong>Änderungs-Log-Dateien</strong> (Plaintext + Excel) werden bei
      jedem Lauf zusätzlich erzeugt und liegen im Log- bzw. Excel-Log-Verzeichnis —
      ideal für Archivierung und externe Auswertung.</li>
</ul>

<h6>Wie wird die Historie gefüllt?</h6>
<p>Bei jedem <em>Verarbeiten</em>-Klick wird der aktuelle Import mit dem vorherigen
verglichen und die Änderungen werden in der Historie gespeichert. Es ist keine
manuelle Aktion nötig.</p>
""",
    },

    # =====================================================================
    # NAVIGATION
    # =====================================================================
    "navigation_overview": {
        "title": "🎮 Navigation & Module",
        "html": """
<p>Im Bereich <em>„🎮 Navigation & Module"</em> finden Sie die Buttons zu allen
weiteren Modulen des Tools. Hier ein Überblick, was sich wo verbirgt:</p>

<h6>📊 Analyse & Übersicht</h6>
<ul>
  <li><strong>📊 Dashboard</strong> — Statistiken, Trends, Klassen-Auswertungen und
      Schülerhistorie. Zeigt u.a. Klassen-Hotspots, Verlaufstrends mit Diagrammen
      und eine Suchfunktion mit Foto-Anzeige des Schülers.</li>
  <li><strong>📜 Historie</strong> — Direktzugriff auf Logs und Excel-Logs vergangener
      Importe (Plaintext + Excel, in den konfigurierten Log-Verzeichnissen).</li>
  <li><strong>⚠️ Warnungen</strong> — Aktuelle Warnungen aus dem letzten Lauf
      (öffnet sich automatisch, wenn welche vorliegen).</li>
  <li><strong>ℹ️ Info-Mails</strong> — Lehrkräfte über Änderungen an frei wählbaren
      Schülerfeldern (Nachteilsausgleich, Attestpflicht, Telefonnummer, …)
      automatisiert informieren.</li>
  <li><strong>📢 Admin-Check</strong> — Prüft, ob in den Schild-Daten Klassen oder
      Klassenlehrkräfte auftauchen, die in den Klassen-/Lehrkräftedateien noch
      nicht eingepflegt sind. Hinweis auf nötige Aktualisierungen.</li>
</ul>

<h6>🛠️ Konfiguration & Bedienung</h6>
<ul>
  <li><strong>⚙️ Einstellungen</strong> — Alle dauerhaften Einstellungen: Verzeichnisse
      (Quelldaten, Arbeit, Ausgabe), Verarbeitungs-Defaults, SMTP, Schild-API,
      OAuth, Admin-Kontakt, etc.</li>
  <li><strong>✉️ Email-Vorlagen Editor</strong> — WYSIWYG-Editor für alle Mail-Vorlagen
      (Warnungs-Mails, Info-Mails). Mit Schlüssel-Info-Tab für alle verfügbaren
      Platzhalter.</li>
  <li><strong>#️⃣🔗 Befehl- und Verknüpfungs-Erstelltool</strong> — Generiert Windows-Verknüpfungen
      und CMD-Befehle, die per Doppelklick gewählte Prozesse automatisch ausführen
      (auch ohne den Browser zu öffnen).</li>
  <li><strong>⬆️ Upload</strong> <em>(nur wenn aktiviert)</em> — Server-Modus: Dateien
      direkt über den Browser in die Verzeichnisse hochladen, ohne Datei-System-Zugriff.</li>
</ul>

<p><strong>Hinweis:</strong> Die <em>Schüler-Verarbeitungs-Funktionen</em> (Verarbeiten, Dateien
prüfen, E-Mails, Fotos managen) sind oben über dem Navigationsbereich zu finden —
mit eigener Hilfe (ℹ️-Button neben den Action-Buttons).</p>
""",
    },
}


# ---------------------------------------------------------------------------
# Kategorisierung für den Glossar-Modus (Reihenfolge bestimmt Anzeige-Reihenfolge)
# ---------------------------------------------------------------------------
HELP_CATEGORIES = [
    ("🛠️ Bedienung & Workflows", [
        "general_workflow",
        "navigation_overview",
        "dashboard_overview",
        "warnungen",
        "info_mails",
        "sopaed_workflow",
        "erzieher_workflow",
        "ausbilder_workflow",
    ]),
    ("📥 Eingabe-Dateien aus Schild", [
        "schild_export",
        "klassen_csv",
        "lehrer_csv",
        "attest_export",
        "nachteil_export",
        "foto_export",
    ]),
    ("🏫 Schild-API (Schild 3.x)", [
        "schild_api_setup",
        "vermerkart_naming",
    ]),
    ("📤 WebUntis-Konfiguration", [
        "webuntis_import",
    ]),
    ("🖼️ Foto-Verwaltung", [
        "foto_zip",
        "foto_rename",
    ]),
]


def get_help(key):
    """Liefert einen einzelnen Hilfe-Eintrag (Dict mit title, html) oder None."""
    return HELP_CONTENT.get(key)


def get_all_help():
    """Liefert alle Hilfe-Einträge als Dict {key: {title, html, category}}.
    Kategorien werden zur Anzeige im Glossar-Modus mitgeliefert."""
    out = {}
    # Reverse-Mapping: Key → Kategorie
    cat_by_key = {}
    for cat_name, keys in HELP_CATEGORIES:
        for k in keys:
            cat_by_key[k] = cat_name
    for key, entry in HELP_CONTENT.items():
        out[key] = dict(entry)
        out[key]['category'] = cat_by_key.get(key, 'Sonstiges')
    return out


def get_categories():
    """Liefert die Kategorien-Definition (Liste von (name, [keys])) für die Anzeige-Reihenfolge."""
    return HELP_CATEGORIES
