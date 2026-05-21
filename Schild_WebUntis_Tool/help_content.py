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
        "title": "🔄 Hauptbereich — Verarbeitung, Mails, Fotos",
        "html": """
<p>Der Hauptbereich oben enthält die wichtigsten Aktionen für den täglichen Ablauf.
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

<p><strong>Hinweis:</strong> Die <em>Hauptbereich-Funktionen</em> (Verarbeiten, Dateien
prüfen, E-Mails, Fotos managen) sind oben über dem Navigationsbereich zu finden —
mit eigener Hilfe (ℹ️-Button neben den Action-Buttons).</p>
""",
    },
}


def get_help(key):
    """Liefert einen einzelnen Hilfe-Eintrag (Dict mit title, html) oder None."""
    return HELP_CONTENT.get(key)


def get_all_help():
    """Liefert alle Hilfe-Einträge als Dict {key: {title, html}}."""
    return HELP_CONTENT
