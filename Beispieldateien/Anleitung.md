# Beispieldateien

Vollständig **fiktive** Quelldateien für alle Workflows des Schild-WebUntis-Tools.
Geeignet zum Ausprobieren ohne echte Schülerdaten — die Formate sind **bit-identisch**
zu den echten Schild-/WebUntis-Exporten (Encoding, BOM, Zeilenenden, Header-Quoting,
Daten-Quote-Pattern), die Inhalte rein erfunden.

## Was ist drin

**60 fiktive Berufskolleg-Azubis** (Interne IDs 1001–1060), verteilt auf
**4 Klassen** (`BK01A` 16, `BK01B` 14, `BK02A` 15, `BK02B` 15), betreut von
**8 Lehrkräften**, mit **~100 verschiedenen Erziehern** (≈ 1,8 pro Schüler) und
**12 Ausbildungsbetrieben**.

Die Daten sind **über alle 8 Dateien hinweg konsistent**:
- jeder Schüler taucht in `SchildExport/SchildExport.csv` auf,
- seine Klasse / Klassenlehrkräfte sind in `Klassendaten/Klassen.csv` definiert,
- alle referenzierten Lehrkräfte sind in `Lehrerdaten/Lehrer.csv` hinterlegt,
- für jeden Schüler ist mindestens ein Erzieher in `ErzieherExport/` + dazu
  passende Telefonzeile(n) in `AnsprechpartnerExport/` vorhanden,
- ~95 % der Schüler haben einen Ausbildungsbetrieb in `AusbilderInput/`.

Realistische Demonstrationsfälle, die in den Workflows sofort sichtbar werden:

- **Unterschiedliche Status-Werte**: 90 % aktiv (`Status=2`), einige Abschlüsse
  (`Status=8`) mit gesetztem Entlassdatum, vereinzelt Abgänger (`Status=9`)
- **Volljährig / Schulpflicht**: Mischung aus volljährigen und minderjährigen
  Azubis (abhängig vom zufällig vergebenen Geburtsjahr)
- **Erzieher-Konstellationen**: 75 % der Azubis haben zwei Erzieher
  (Mutter + Vater, gleicher Nachname), 25 % nur einen
- **Geschwister-/Mehrfachbetreuung**: **9 Erzieher betreuen je zwei Schüler**
  (z. B. zwei Kinder mit gleichem Nachnamen aus unterschiedlichen Klassen) —
  perfekt zur Demo der „Nach Erzieher"-Gruppierungs-Funktion
- **Firmen-Verteilung** für den Ausbilder-Workflow: 12 Betriebe mit 1 bis 8
  Auszubildenden pro Betreuer, ~3 Azubis ohne Vertrag (Berufsfachschule)
- **Attestpflicht** für 6 Schüler (~10 %), **Nachteilsausgleich** für 4 Schüler

Alle E-Mails enden auf `@example.com` bzw. `@firma.example` (RFC-reservierte
Beispiel-Domains, garantiert keine real existierenden Adressen). Adresse
einheitlich „Musterstadt 12345".

## Verwendung

In den jeweiligen Standard-Verzeichnissen ablegen (oder in den Workflow-
Einstellungen die hier liegenden Pfade angeben):

| Datei                                                         | Workflow                  | Standardverzeichnis           |
| ------------------------------------------------------------- | ------------------------- | ----------------------------- |
| `SchildExport/SchildExport.csv`                               | Schüler                   | Repo-Root (`.`)               |
| `Klassendaten/Klassen.csv`                                    | Schüler                   | `Klassendaten/`               |
| `Lehrerdaten/Lehrer.csv`                                      | Schüler                   | `Lehrerdaten/`                |
| `AttestpflichtDaten/Schüler mit Attestpflicht.csv`            | Schüler (Attestpflicht)   | `AttestpflichtDaten/`         |
| `NachteilsausgleichDaten/SchülermitNachteilsausgleich.csv`    | Schüler (Nachteilsausgl.) | `NachteilsausgleichDaten/`    |
| `ErzieherExport/ErzieherExport.csv`                           | Erzieher                  | `ErzieherExport/`             |
| `AnsprechpartnerExport/AnsprechpartnerExport.csv`             | Erzieher                  | `AnsprechpartnerExport/`      |
| `AusbilderInput/AusbilderExport.csv`                          | Ausbilder                 | `AusbilderInput/`             |

Quick-Start unter Windows (PowerShell, aus dem Repo-Root):

```powershell
Copy-Item Beispieldateien/SchildExport/SchildExport.csv .
Copy-Item -Recurse -Force `
  Beispieldateien/Klassendaten, `
  Beispieldateien/Lehrerdaten, `
  Beispieldateien/AttestpflichtDaten, `
  Beispieldateien/NachteilsausgleichDaten, `
  Beispieldateien/ErzieherExport, `
  Beispieldateien/AnsprechpartnerExport, `
  Beispieldateien/AusbilderInput `
  .
```

Dann das Tool starten — die Workflows finden ihre Quellen automatisch in den
Standard-Verzeichnissen.

## Erweitern / Regenerieren

Das Generator-Script [`_generate.py`](_generate.py) erzeugt alle 8 CSVs aus
**Pools von Vor-/Nachnamen, Klassen und Betrieben** und einem **deterministischen
Zufallsgenerator** (`random.seed(2026)`) — bei jedem Lauf entsteht dieselbe
Population. Wer Beispieldaten erweitern oder anpassen will, editiert oben im
Script:

| Variable                          | Bedeutung                                                |
| --------------------------------- | -------------------------------------------------------- |
| `KLASSEN`                         | Klassen-Definition inkl. Klassenlehrkräfte               |
| `KLASSENGROESSE`                  | Wieviele Schüler pro Klasse                              |
| `LEHRER`                          | Pool der Lehrkräfte (WebUntis-Format)                    |
| `BETRIEBE`                        | Pool der Ausbildungsbetriebe mit Betreuer-Daten          |
| `BETRIEB_GEWICHT`                 | Gewichtung — steuert wie viele Azubis pro Betrieb        |
| `SCHUELER_OHNE_BETRIEB_PROZENT`   | Anteil Azubis ohne Vertrag                               |
| `ERZIEHER_VERTEILUNG`             | Wahrscheinlichkeit für 1 oder 2 Erzieher pro Schüler     |
| `VORNAMEN_W`, `VORNAMEN_M`        | Namens-Pools                                             |
| `NACHNAMEN`, `STRASSEN`           | Familien-/Straßennamen-Pools                             |

Danach:

```powershell
cd Beispieldateien
python _generate.py
```

Alle 8 CSVs werden neu geschrieben und bleiben konsistent zueinander (gleiche
IDs, Klassen und Lehrkräfte über alle Dateien hinweg).

**Niemals die CSVs direkt editieren** — sonst läuft die Cross-File-Konsistenz
auseinander.

## Format-Garantie

Die Beispieldateien wurden bewusst auf **bit-identische Formatübereinstimmung**
mit den echten Schild-/WebUntis-Exporten getrimmt:

- **Encoding**: UTF-8 mit BOM (Schild-Dateien) bzw. UTF-8 ohne BOM (`Lehrer.csv`
  im WebUntis-Format)
- **Zeilenenden**: CRLF (Schild) / LF (WebUntis-Lehrer-Export)
- **Trennzeichen**: `;` (Schild) / `\t` (WebUntis-Lehrer)
- **Quoting**: Die drei Schild-Exporte mit Quotes (Erzieher, Ansprechpartner,
  Ausbilder) reproduzieren auch das **partielle Quote-Pattern** — Header
  komplett gequotet, Datenzeilen quoten nur gefüllte String-Werte (IDs, Datums,
  Schild-Codes wie `E`/`J` und Leerwerte bleiben ungequotet)

## Authentizitäts-Garantie

Sämtliche Namen, Adressen, E-Mails, Telefonnummern und Firmen sind frei
erfunden. Ähnlichkeiten mit real existierenden Personen oder Unternehmen sind
rein zufällig. Beim Aufbau der Beispieldateien wurde **kein einziger Wert** aus
realen Quelldateien übernommen — nur die Spalten-Header der Schild-Exporte
wurden gelesen, um das jeweilige Format exakt nachzubauen.
