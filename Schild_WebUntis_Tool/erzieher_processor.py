"""
Erzieher-/Ansprechpartner-Verarbeitung (Phase 2).

Portiert die Logik des Standalone-Tools "SchildNRW-WebUntis Erzieher-Konvertierer"
ohne Pandas-Abhängigkeit (kleinere EXE, weniger Bloat).

Idee:
  - Schild exportiert Erzieher (Hauptdaten) und Ansprechpartner (separate Datei
    mit Telefonnummern) getrennt.
  - Wir bauen pro „n-tem Erzieher" eines Schülers eine eigene Import-Datei
    (Erzieher_1.csv, Erzieher_2.csv, …) und packen alle in ein ZIP.

WebUntis-Realitaet (Stand: Mai 2026):
  Der WebUntis-Erzieher-Import wertet derzeit nur Schueler-ID, Vorname, Nachname,
  E-Mail und (optional) Eltern-ID aus. Anrede, Briefanrede, Titel, Anschluss-Art,
  Bemerkung, Telefon-Nummer werden mit-exportiert, damit der Import nicht
  angepasst werden muss, falls WebUntis seine Verarbeitung erweitert.

  Die Telefon-Verarbeitungsoptionen (Smart-Match, phone_from_erz_first,
  lift_limit) halten die Daten-Aufbereitung trotzdem sauber — fuer die Tool-
  interne Vorschau, den Klassen-Report und einen moeglichen WebUntis-Upgrade.

Datenquellen-Strategie (welche Spalte kommt woher?):
  Beide Schild-Quellen (Erzieher- und Ansprechpartner-Export) koennen ueberlappende
  Daten enthalten. Das Tool kombiniert sie nach folgenden Regeln:

  - Erzieher-Stammdaten (Erzieher i: Vorname/Nachname/E-Mail): PFLICHT aus dem
    Erzieher-Export. Fehlt eines dieser Felder, crasht process() mit ValueError.

  - Schueler-Stammdaten (Klasse / Vorname / Nachname): PRIMAER aus dem Anspr-
    Export (Spalten 'Schueler-...'). FALLBACK aus dem Erzieher-Export, sofern die
    Schule die Spalten dort mit aufgenommen hat (mehrere Spaltennamen-Varianten
    werden erkannt — siehe _STUDENT_*_COLS). Merge: Anspr gewinnt pro Schueler,
    Erzieher fuellt einzelne Leerstellen. Siehe _merge_student_lookups().

  - Volljaehrigkeits-Erkennung: PRIMAER ueber Geburtsdatum aus dem Erzieher-Export
    (Spalten-Varianten in _GEBURTSDATUM_COLS, akzeptiert TT.MM.JJJJ und ISO).
    ZUSAETZLICH (ODER-verknuepft) ueber die Heuristik 'Erzieher: Art (Klartext)'
    enthaelt 'volljaehrig' — diese deckt Sonderfaelle ab, in denen ein Schueler
    ausdruecklich auf Erziehungsberechtigte verzichtet hat (Self-Ansprech-
    partner-Markierung), und greift als Fallback bei fehlendem Geburtsdatum.
    Siehe _is_self_volljaehrig().

  - Telefonnummern: PRIMAER die im Erzieher-Export hinterlegte primaere Nummer
    (Spaltengruppe 'Telefon-Nummern: ...') als Pseudo-Anspr-Zeile, SEKUNDAER die
    Zeilen aus dem Anspr-Export. Duplikate (gleiche Nummer normalisiert) aus dem
    Anspr-Export werden gefiltert. Siehe _merge_phone_sources(). Optional ueber
    Setting phone_from_erz_first deaktivierbar.

  Empfehlung an die Schule: All-in-One-Erzieher-Vorlage (Klasse + Geburtsdatum
  zusaetzlich zu Erzieher-Daten). Damit ist der Anspr-Export rein optional und
  alle Tool-Features (UI-Anzeige, Klassen-Report, deterministischer Vollj.-Check)
  funktionieren vollstaendig. Die Status-Box im Frontend zeigt per Badge an,
  welches Setup erkannt wurde (siehe _inspect_erz_source()).

Filter-Optionen im Ueberblick (alle persistent in [Erzieher]-Section):
  Schueler-Auswahl (greift VOR der Verarbeitung):
    - class_filter         — Klassen-Whitelist analog Ausbilder: Liste oder
                             ['__NONE__'] Sentinel; leer = alle Klassen.
                             Spiegelt UI-Chip-Auswahl. Siehe _resolve_class_filter()
                             und _student_passes_class().
    - filter_volljaehrig   — Schueler ueber _is_self_volljaehrig() rauswerfen.

  Erzieher-Slot-Auswahl (greift beim Zusammenbau der Output-CSVs):
    - require_email        — Slots ohne E-Mail ueberspringen.
    - fill_dummies         — Leere Felder mit DUMMY-Werten fuellen (siehe
                             DUMMY_VALUES).

  Telefon/Slot-Mapping:
    - smart_match          — Anschluss-Art-basiertes Slot-Mapping (siehe
                             _smart_match_student()).
    - phone_from_erz_first — Erzieher-interne Telefonnummer als prioritaere
                             Pseudo-Anspr-Zeile (siehe _erz_phone_pseudo()
                             und _merge_phone_sources()).
    - lift_limit           — Ueberzaehlige Telefon-Zeilen werden zu virtuellen
                             Erzieher_3/_4/...-Slots statt zu Orphans
                             (Phase 3 in _smart_match_student()).

  Output-Erweiterung:
    - assign_eltern_ids    — Persistente schulweite Eltern-IDs via
                             eltern_id_manager (Vorname+Nachname+E-Mail als Key).

Quell-Modi (Single-File-Konsolidierung, neu in 3.2):
  Der Schild-Schueler-Export KANN — sofern die Schild-Vorlage entsprechend
  konfiguriert ist — dieselben 'Erzieher 1: ...' / 'Erzieher 2: ...' /
  'Telefon-Nummern: ...' / 'Geburtsdatum' / 'Erzieher: Art (Klartext)'-Spalten
  enthalten, die der bisherige Erzieher-Export liefert. Diese Spalten sind in
  der Schild-Standard-Vorlage NICHT enthalten und muessen einmalig zur
  Export-Vorlage hinzugefuegt werden (Datenart 'Schueler'). Ist das geschehen,
  kann derselbe Schueler-Export, der fuer die Schueler-Hauptverarbeitung im
  'Schild Exporte'-Verzeichnis (Setting 'schildexport_directory') liegt,
  zusaetzlich als Erzieher-Quelle dienen — ein separater Schild-Erzieher-
  Export ist dann ueberfluessig.

  Welche Spalten ergaenzt werden muessen, listet inspect_schueler_for_erzieher()
  pro Schueler-CSV detailliert auf (siehe Frontend-Status-Box).

  Setting [Erzieher].schueler_export_mode:
    - 'off'      (Default) — Quelle ausschliesslich aus erzieher_export_directory.
                              Schüler-Export wird ignoriert; bisheriges Verhalten.
    - 'fallback' — wenn erzieher_export_directory leer/ohne CSV ist, wird die
                   neueste CSV aus schildexport_directory verwendet (sofern
                   sie ein Schüler-Export ist — Detection via Marker-Spalten).
                   Sonst bleibt der separate Erzieher-Export Quelle.
    - 'always'   — Schüler-Export aus schildexport_directory wird IMMER
                   bevorzugt, auch wenn ein separater Erzieher-Export existiert.

  Wichtige Limitierungen im Schüler-Export-Modus:
    - Maximal 2 Erzieher pro Schüler (Erzieher 1/Erzieher 2-Spalten). Bei
      mehr als zwei Erziehern (z.B. Mutter, Vater, Grossmutter) fehlen alle
      weiteren — separater Erzieher-Export aus Schild ist dann besser.
    - Maximal 1 Telefonnummer pro Schüler (Telefon-Nummern: ...). Anspr-
      Export ist ohnehin optional und liefert mehrere Telefone pro Schüler.

  Detection: _is_schueler_export_file(path) — True wenn der Header sowohl
  'Erzieher 1: Anrede' als auch 'Allg. Adresse: Name1' enthaelt (zweite Spalte
  taucht NUR im Schüler-Export auf, nicht im separaten Erzieher-Export).
"""

import os
import io
import re
import csv
import zipfile
import configparser
from datetime import datetime, date
from utils import safe_read_config, read_config_for_update, ConfigReadError


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

DEFAULT_ZIP_NAME_TEMPLATE = 'Erzieher_Import_{datum}'

# Erzieher-spezifische Spalten im Erzieher-Export (i = Erzieher-Nummer)
ERZIEHER_FIELDS = ['Anrede', 'Briefanrede', 'Titel', 'Nachname', 'Vorname', 'E-Mail']

# Ansprechpartner-spezifische Felder, die wir pro Erzieher mit aufnehmen
ANSPRECHPARTNER_FIELD_MAP = {
    'Anschluss-Art':  'Anschluss Art',
    'Bemerkung':      'Bemerkung',
    'Telefon-Nummer': 'Telefon-Nummer',
}

# Spalten der "primaeren" Telefonnummer im Erzieher-Export (eine pro Schueler)
ERZ_PHONE_COLS = {
    'Anschluss-Art':  'Telefon-Nummern: Anschluss-Art',
    'Bemerkung':      'Telefon-Nummern: Bemerkung',
    'Telefon-Nummer': 'Telefon-Nummern: Telefon-Nummer',
}

# ---------------------------------------------------------------------------
# Smart-Match: Anschluss-Art -> Geschlecht/Rolle (zur Zuordnung an Erzieher i)
# ---------------------------------------------------------------------------
# Werte basieren auf einer Analyse von >2000 echten Schild-Ansprechpartner-
# Zeilen: Mutter/Vater + Varianten sind die haeufigsten typisierten Werte.

_ANSCHLUSS_FEMININ = {
    'mutter', 'mama', 'mami',
    'handy mutter', 'arbeit mutter',
    'oma', 'oma handy', 'großmutter', 'grossmutter',
    'schwester', 'tante', 'pflegemutter',
}
_ANSCHLUSS_MASKULIN = {
    'vater', 'papa', 'papi',
    'handy vater', 'arbeit vater',
    'opa', 'großvater', 'grossvater',
    'bruder', 'onkel', 'pflegevater',
}
# Alle anderen Werte (Eltern, Notfallnummer, Vormund, Pflegeeltern, Ehepartner(in),
# sonstiges, ...) bleiben "neutral" und werden nach Position zugeordnet.


def _gender_from_anschluss(art):
    """Liefert 'w' / 'm' / None aus dem Anschluss-Art-Feld."""
    a = (art or '').strip().lower()
    if a in _ANSCHLUSS_FEMININ:  return 'w'
    if a in _ANSCHLUSS_MASKULIN: return 'm'
    return None


def _gender_from_anrede(anrede):
    """Liefert 'w' / 'm' / None aus dem Anrede-Feld des Erziehers."""
    a = (anrede or '').strip().lower()
    if a in ('frau', 'fr.', 'fr'):  return 'w'
    if a in ('herr', 'hr.', 'hr'):  return 'm'
    return None



def get_erzieher_export_dir():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'erzieher_export_directory', fallback='ErzieherExport').strip() or 'ErzieherExport'


def get_ansprechpartner_export_dir():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'ansprechpartner_export_directory', fallback='AnsprechpartnerExport').strip() or 'AnsprechpartnerExport'


def get_output_dir():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'erzieher_output_directory', fallback='ErzieherImporte').strip() or 'ErzieherImporte'


def get_zip_name_template():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Erzieher', 'zip_name_template', fallback=DEFAULT_ZIP_NAME_TEMPLATE).strip() or DEFAULT_ZIP_NAME_TEMPLATE


def save_zip_name_template(template):
    template = (template or '').strip()
    if not template:
        return
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    config.set('Erzieher', 'zip_name_template', template)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_smart_match():
    """True = Telefonnummern werden per Anschluss-Art an Erzieher gemappt
    (Mutter -> Frau-Erzieher, Vater -> Herr-Erzieher); Output enthaelt nur
    so viele Erzieher-CSVs wie der Erzieher-Export Slots hergibt.
    False = altes Verhalten: positional, kann "Geister-Erzieher" mit leeren
    Stammdaten erzeugen, wenn mehr Anspr-Zeilen als Erzieher existieren.

    Hinweis: WebUntis wertet die Telefon-Spalte aktuell nicht aus — die
    Smart-Match-Zuordnung ist primaer fuer Tool-interne Vorschau und Daten-
    Hygiene relevant (falls WebUntis Telefon spaeter unterstuetzt)."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'smart_match', fallback=True)


def save_smart_match(value):
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    config.set('Erzieher', 'smart_match', 'True' if value else 'False')
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def get_filter_volljaehrig():
    """True = Schueler, deren Erzieher-Art (Klartext) 'volljaehrig' enthaelt,
    werden komplett aus dem Erzieher-Export herausgefiltert (kein
    sinnvoller Erzieher-Datensatz fuer self-Ansprechpartner)."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'filter_volljaehrig', fallback=False)


def save_filter_volljaehrig(value):
    _set_erz_bool('filter_volljaehrig', value)


def get_require_email():
    """True = Erzieher ohne E-Mail-Adresse werden nicht exportiert
    (sie koennen sich in WebUntis ohnehin nicht anmelden)."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'require_email', fallback=False)


def save_require_email(value):
    _set_erz_bool('require_email', value)


def get_fill_dummies():
    """True = leere Erzieher-Felder werden mit eindeutig erkennbaren Dummy-
    Werten (DUMMY / dummy@invalid.local / 000) gefuellt, damit WebUntis nicht
    auf Pflichtfeldern stolpert und Dummies nachtraeglich gefiltert werden
    koennen."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'fill_dummies', fallback=False)


def save_fill_dummies(value):
    _set_erz_bool('fill_dummies', value)


def get_assign_eltern_ids():
    """True = jedem Erzieher wird eine schulweit eindeutige Eltern-ID zugewiesen
    (persistent in eltern_ids.json), damit WebUntis denselben Erzieher ueber
    Geschwister hinweg als denselben Account erkennt."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'assign_eltern_ids', fallback=False)


def save_assign_eltern_ids(value):
    _set_erz_bool('assign_eltern_ids', value)


def get_phone_from_erz_first():
    """True = die im Erzieher-Export hinterlegte primaere Telefonnummer
    (Spaltengruppe 'Telefon-Nummern: ...') wird als ZUSAETZLICHE erste
    Anspr-Pseudozeile pro Schueler behandelt — bekommt damit Vorrang beim
    Slot-Mapping. Duplikate gegenueber dem Anspr-Export werden gefiltert."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'phone_from_erz_first', fallback=True)


def save_phone_from_erz_first(value):
    _set_erz_bool('phone_from_erz_first', value)


def get_class_filter():
    """Klassen-Whitelist analog Ausbilder. Liefert Liste der zu beruecksichtigenden
    Klassen (leer = alle). Sentinel '__NONE__' = explizit keine Klasse aktiv
    (Default ist 'leer = alle', deshalb braucht's den Marker, um 'explizit
    nichts' von 'noch nicht konfiguriert' zu unterscheiden)."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    raw = config.get('Erzieher', 'class_filter', fallback='').strip()
    if not raw:
        return []
    return [c.strip() for c in raw.split(',') if c.strip()]


def save_class_filter(classes):
    """Speichert die Klassen-Whitelist (Liste[str])."""
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    cleaned = [str(c).strip() for c in (classes or []) if str(c).strip()]
    config.set('Erzieher', 'class_filter', ','.join(cleaned))
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


def _resolve_class_filter(class_filter):
    """Normalisiert die Whitelist in (mode, set_of_classes):
       mode='all'  -> Set ist leer und ignoriert; alle Klassen durch
       mode='none' -> keine Klasse durch (Sentinel __NONE__)
       mode='set'  -> nur die Klassen aus dem Set durch
    """
    cf = list(class_filter or [])
    if not cf:
        return ('all', set())
    if '__NONE__' in cf:
        return ('none', set())
    return ('set', {c.strip() for c in cf if c.strip()})


def _student_passes_class(stamm, mode, klassen_set):
    """Spiegelt die Backend-Filter-Logik aus filter_and_write() (Ausbilder):
    mode='all'  -> True
    mode='none' -> False
    mode='set'  -> Klasse muss im Set sein (Schueler ohne Klasse faellt raus)
    """
    if mode == 'all':  return True
    if mode == 'none': return False
    klasse = (stamm or {}).get('klasse', '') or ''
    return klasse.strip() in klassen_set


def get_lift_limit():
    """True = Anzahl Erzieher pro Schueler ist nicht mehr auf die Slots im
    Schild-Erzieher-Export begrenzt. Ueberzaehlige Ansprechpartner-Telefonzeilen
    werden zu zusaetzlichen Erzieher_N.csv-Slots (Stammdaten ggf. Dummy)."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'lift_limit', fallback=False)


def save_lift_limit(value):
    _set_erz_bool('lift_limit', value)


def _set_erz_bool(key, value):
    """Helper: bool in [Erzieher] speichern (idempotent, legt Section ggf. an)."""
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    config.set('Erzieher', key, 'True' if value else 'False')
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


# ---------------------------------------------------------------------------
# Single-File-Konsolidierung: Schueler-Export aus AusbilderInput als alternative
# Quelle nutzen. Details siehe Module-Docstring (Abschnitt "Quell-Modi").
# ---------------------------------------------------------------------------

_SCHUELER_EXPORT_MODES = ('off', 'fallback', 'always')


def get_schildexport_dir():
    """Liest das Schild-Exporte-Hauptverzeichnis aus settings.ini (gleiche
    Quelle wie die Schueler-Hauptverarbeitung). Default '.': Repo-Wurzel/CWD.
    Bewusst lokal definiert (statt aus main.py zu importieren), um keine
    Cross-Modul-Zirkelabhaengigkeit beim Modul-Laden zu erzeugen."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Directories', 'schildexport_directory',
                      fallback='.').strip() or '.'


def get_schueler_export_mode():
    """Liefert den aktiven Quell-Modus fuer den Erzieher-Workflow:
    'off'      (Default) — ausschliesslich erzieher_export_directory nutzen.
    'fallback' — Schueler-Export aus AusbilderInput nur, wenn separater
                 Erzieher-Export fehlt.
    'always'   — Schueler-Export aus AusbilderInput hat IMMER Vorrang."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    mode = config.get('Erzieher', 'schueler_export_mode',
                      fallback='off').strip().lower()
    return mode if mode in _SCHUELER_EXPORT_MODES else 'off'


def save_schueler_export_mode(mode):
    """Speichert den Quell-Modus. Wirft ValueError bei unbekanntem Wert."""
    mode = (mode or '').strip().lower()
    if mode not in _SCHUELER_EXPORT_MODES:
        raise ValueError(
            f"schueler_export_mode muss eines von {_SCHUELER_EXPORT_MODES} sein.")
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    config.set('Erzieher', 'schueler_export_mode', mode)
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


# Basis-Marker fuer "ist eine per-Schueler-CSV" (nicht z.B. der separate
# Erzieher-Export, der pro Zeile EINEN Erzieher beschreibt, oder ein
# Klassen-/Lehrer-Export). 'Interne ID-Nummer' ist Schild's eindeutiger
# Per-Schueler-Key — die mit Stamm-Daten kombinierte Variante hat hohe
# Trennschaerfe ggue. anderen CSV-Typen.
_SCHUELER_BASIC_REQUIRED = ('Interne ID-Nummer',)
_SCHUELER_BASIC_STAMM    = ('Vorname', 'Nachname', 'Klasse')  # mind. EINE


# Spalten, die der Erzieher-Workflow im Single-File-Modus konkret braucht:
# - Hart-Pflicht:        Interne ID-Nummer (Schueler-Matching)
# - Mindestens EINE aus: Erzieher 1: Vorname/Nachname/E-Mail (sonst leerer Output)
# Beim Anlegen der Schild-Export-Vorlage zusaetzlich empfohlen — fuer volles
# Feature-Set (Smart-Match, Volljaehrig-Check, Schueler-Stammdaten in der UI):
_ERZIEHER_REQUIRED_HARD = ('Interne ID-Nummer',)
_ERZIEHER_REQUIRED_ANY  = ('Erzieher 1: Vorname', 'Erzieher 1: Nachname',
                           'Erzieher 1: E-Mail')
_ERZIEHER_RECOMMENDED   = (
    'Erzieher 1: Anrede', 'Erzieher 1: Briefanrede', 'Erzieher 1: Titel',
    'Erzieher 2: Vorname', 'Erzieher 2: Nachname', 'Erzieher 2: E-Mail',
    'Erzieher 2: Anrede',
    'Telefon-Nummern: Telefon-Nummer', 'Telefon-Nummern: Anschluss-Art',
    'Telefon-Nummern: Bemerkung',
    'Geburtsdatum', 'Erzieher: Art (Klartext)',
    'Klasse', 'Vorname', 'Nachname',
)


def _is_schueler_export_file(path):
    """True wenn die CSV grundsaetzlich als 'per-Schueler-Export' erkennbar ist
    (hat Interne ID-Nummer + mind. eine Stamm-Spalte). Sagt NICHTS darueber
    aus, ob die fuer den Erzieher-Workflow noetigen 'Erzieher N: ...'-Spalten
    drin sind — dafuer: inspect_schueler_for_erzieher().
    Anders gesagt: erkennt 'ist dies eine Schueler-CSV?', nicht 'ist sie schon
    fuer den Single-File-Modus gepflegt?'."""
    if not path or not os.path.isfile(path):
        return False
    headers = set(_read_csv_header(path))
    if not all(c in headers for c in _SCHUELER_BASIC_REQUIRED):
        return False
    return any(c in headers for c in _SCHUELER_BASIC_STAMM)


def inspect_schueler_for_erzieher(path):
    """Detail-Inspektion der CSV im schildexport_directory fuer den Erzieher-
    Single-File-Modus. Liefert dem Frontend genug Info, um eine konkrete
    Handlungsaufforderung anzuzeigen (welche Spalten muss man in der Schild-
    Export-Vorlage zusaetzlich aktivieren?).

    Returns dict mit:
      file_exists                 — ist ueberhaupt eine CSV im Verzeichnis?
      is_schueler_export          — Basis-Marker (ID + Stamm) erfuellt?
      usable_for_single_file_mode — alle Pflichtspalten erfuellt UND mind. eine
                                    Erzieher-N-Slot-Spalte vorhanden?
      missing_required_hard       — Liste der fehlenden Hart-Pflichtspalten
      missing_required_any        — fehlende OR-Pflicht (mind. eine muss da sein)
      present_recommended         — vorhandene empfohlene Spalten
      missing_recommended         — fehlende empfohlene Spalten
      erzieher_slots_in_header    — Max-N aus 'Erzieher N: ...' Headern (0 = keine)
    """
    info = {
        'file_exists':                 False,
        'is_schueler_export':          False,
        'usable_for_single_file_mode': False,
        'missing_required_hard':       [],
        'missing_required_any':        list(_ERZIEHER_REQUIRED_ANY),
        'present_recommended':         [],
        'missing_recommended':         list(_ERZIEHER_RECOMMENDED),
        'erzieher_slots_in_header':    0,
    }
    if not path or not os.path.isfile(path):
        return info
    info['file_exists'] = True
    headers = set(_read_csv_header(path))
    info['is_schueler_export'] = _is_schueler_export_file(path)
    info['missing_required_hard'] = [c for c in _ERZIEHER_REQUIRED_HARD if c not in headers]
    # OR-Pflicht: mind. eine aus _ERZIEHER_REQUIRED_ANY muss vorhanden sein.
    # Wenn KEINE drin ist, listen wir alle als "any-fehlend" — sonst leere Liste
    # (Anforderung erfuellt).
    any_present = any(c in headers for c in _ERZIEHER_REQUIRED_ANY)
    info['missing_required_any'] = [] if any_present else list(_ERZIEHER_REQUIRED_ANY)
    info['present_recommended']  = [c for c in _ERZIEHER_RECOMMENDED if c in headers]
    info['missing_recommended']  = [c for c in _ERZIEHER_RECOMMENDED if c not in headers]
    # Max-Slot fuer den Slot-Loop in process()/preview()
    max_slot = 0
    for h in headers:
        m = re.match(r'Erzieher\s+(\d+):', h)
        if m:
            max_slot = max(max_slot, int(m.group(1)))
    info['erzieher_slots_in_header'] = max_slot
    info['usable_for_single_file_mode'] = (
        not info['missing_required_hard']
        and any_present
        and max_slot > 0
    )
    return info


def _resolve_erzieher_path():
    """Liefert den effektiv genutzten Erzieher-Pfad und die Quell-Info fuer die
    UI — abhaengig vom schueler_export_mode-Setting und der Verfuegbarkeit der
    Verzeichnisse.

    Returns:
        (path_or_None, source_info_dict)
        source_info_dict enthaelt:
          mode               — aktueller Mode ('off'/'fallback'/'always')
          source             — 'erzieher_export' | 'schueler_export' | None
          erzieher_csv_path  — neuester Erzieher-Export (oder None)
          schueler_csv_path  — neuester Schueler-Export aus AusbilderInput (oder None)
          schueler_available — True wenn AusbilderInput-CSV ein erkannter Schueler-Export ist
          fell_back          — True wenn mode='fallback' und tatsaechlich auf Schueler-Export ausgewichen wurde
    """
    mode = get_schueler_export_mode()
    erz_path = _latest_csv(get_erzieher_export_dir())
    sch_path = _latest_csv(get_schildexport_dir())
    sch_inspect = inspect_schueler_for_erzieher(sch_path)
    # 'verwendbar' (im engeren Sinne) = alle Pflichtspalten vorhanden;
    # nur DANN wird im fallback/always wirklich auf die Schueler-CSV gewechselt.
    sch_usable = sch_inspect['usable_for_single_file_mode']
    info = {
        'mode':                  mode,
        'source':                None,
        'erzieher_csv_path':     erz_path,
        # path nur durchreichen, wenn brauchbar — sonst kann das Frontend daran
        # einen 'aktiv genutzt'-Badge falsch dranhaengen.
        'schueler_csv_path':     sch_path if sch_usable else None,
        'schueler_csv_present':  bool(sch_path),
        'schueler_available':    sch_usable,
        'schueler_inspect':      sch_inspect,
        'fell_back':             False,
    }
    if mode == 'always' and sch_usable:
        info['source'] = 'schueler_export'
        return sch_path, info
    if mode == 'fallback' and not erz_path and sch_usable:
        info['source']    = 'schueler_export'
        info['fell_back'] = True
        return sch_path, info
    if erz_path:
        info['source'] = 'erzieher_export'
        return erz_path, info
    # Letzter Ausweg: in 'off'/'fallback' ohne Erzieher-Export bleibt None
    return None, info


# Spaltennamen-Varianten fuer Geburtsdatum im Erzieher-Export
_GEBURTSDATUM_COLS = ('Geburtsdatum', 'Schüler-Geburtsdatum', 'Schüler: Geburtsdatum')


def _calc_age_from_str(geb_str, today=None):
    """Liefert Alter (int) zum Stichtag (Default: heute), oder None wenn das
    Geburtsdatum nicht parsbar ist. Akzeptiert TT.MM.JJJJ (Schild-Standard)
    sowie ISO YYYY-MM-DD als Fallback."""
    if not geb_str:
        return None
    today = today or date.today()
    for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
        try:
            geb = datetime.strptime(geb_str.strip(), fmt).date()
            return today.year - geb.year - ((today.month, today.day) < (geb.month, geb.day))
        except (ValueError, TypeError):
            continue
    return None


def _is_self_volljaehrig(erz_row):
    """True wenn der Schueler als volljaehrig gilt. Nutzt zwei Quellen:
    1. PRIMAER: Geburtsdatum aus dem Erzieher-Export (deterministisch — wenn
       die Schild-Vorlage 'Geburtsdatum' mit-exportiert; ≥ 18 = volljaehrig).
    2. ZUSAETZLICH/Fallback: Schild-Heuristik via 'Erzieher: Art (Klartext)'
       enthaelt 'volljaehrig' — deckt Sonderfaelle ab, in denen ein Schueler
       ausdruecklich auf Erziehungsberechtigte verzichtet hat (Self-
       Ansprechpartner-Markierung), und greift, wenn kein Geburtsdatum
       verfuegbar ist.
    """
    # 1) Geburtsdatum-basiert
    age = None
    for col in _GEBURTSDATUM_COLS:
        geb_str = (erz_row.get(col, '') or '').strip()
        if geb_str:
            age = _calc_age_from_str(geb_str)
            break
    if age is not None and age >= 18:
        return True
    # 2) Schild-Heuristik (Fallback + Sonderfall-Override)
    art = (erz_row.get('Erzieher: Art (Klartext)', '') or '').lower()
    return 'volljährig' in art or 'volljaehrig' in art


# ---------------------------------------------------------------------------
# Dummy-Fuellwerte (eindeutig erkennbar — leicht in WebUntis filterbar)
# ---------------------------------------------------------------------------
DUMMY_VALUES = {
    'Anrede':         '',
    'Briefanrede':    'DUMMY',
    'Titel':          '',
    'Nachname':       'DUMMY',
    'Vorname':        'DUMMY',
    'E-Mail':         'dummy@invalid.local',
    'Anschluss Art':  'DUMMY',
    'Bemerkung':      'DUMMY (automatisch ergaenzt)',
    'Telefon-Nummer': '000',
}


def _normalize_phone(num):
    """Normalisiert eine Telefonnummer fuer Duplikat-Erkennung — alle Nicht-
    Ziffern entfernen, fuehrende Nullen / +49 vereinheitlichen ist OPTIONAL und
    macht zu viele falsch-positive Treffer; daher nur Leerzeichen/Trenner weg."""
    return re.sub(r'[^0-9+]', '', (num or '').strip())


def _erz_phone_pseudo(erz_row):
    """Liefert eine Pseudo-Anspr-Zeile aus den 'Telefon-Nummern: ...'-Spalten
    des Erzieher-Exports — oder None, wenn keine Telefonnummer gepflegt ist."""
    nr = (erz_row.get(ERZ_PHONE_COLS['Telefon-Nummer'], '') or '').strip()
    if not nr:
        return None
    return {
        'Anschluss-Art':  (erz_row.get(ERZ_PHONE_COLS['Anschluss-Art'],  '') or '').strip(),
        'Bemerkung':      (erz_row.get(ERZ_PHONE_COLS['Bemerkung'],      '') or '').strip(),
        'Telefon-Nummer': nr,
        '_from_erz':      True,   # Marker fuer Stats / UI
    }


def _merge_phone_sources(erz_phone, anspr_list):
    """Fuegt die Erzieher-Export-Pseudozeile als ERSTES Element in die Liste
    ein und entfernt Duplikate (gleiche normalisierte Nummer) — die aus dem
    Erzieher-Export hat Vorrang, Duplikate aus dem Anspr-Export werden
    geloescht."""
    if not erz_phone:
        return list(anspr_list)
    key = _normalize_phone(erz_phone['Telefon-Nummer'])
    deduped = [a for a in anspr_list
               if _normalize_phone(a.get('Telefon-Nummer', '')) != key]
    return [erz_phone] + deduped


def _apply_dummies(row_out, i):
    """Fuellt leere Werte in einer Output-Zeile mit Dummy-Werten. Mutates+returns."""
    for col in list(row_out.keys()):
        if col == 'Interne_ID_Nummer':
            continue
        if row_out[col]:
            continue
        prefix = f'Erzieher {i}: '
        if not col.startswith(prefix):
            continue
        short = col[len(prefix):]
        if short in DUMMY_VALUES:
            row_out[col] = DUMMY_VALUES[short]
    return row_out


def _smart_match_student(erz_row, anspr_list, max_slots, lift_limit=False):
    """Ordnet Anspr-Zeilen den i-ten Erzieher-Slots zu — primaer per
    Anschluss-Art-Gender, Fallback per Position fuer neutrale / unklare Faelle.

    Wenn lift_limit=True werden uebrig gebliebene Anspr-Zeilen auf virtuelle
    Slots oberhalb von max_slots verteilt (statt zu Orphans zu werden).

    Returns:
        assigned: {erz_idx (1..N): anspr_dict}
        stats:    {'gender': N, 'positional': N, 'virtual': N, 'orphan_anspr': N, 'orphan_erz': N}
    """
    # Echte Erzieher-Slots (gefuellt) ermitteln
    erz_slots = []  # [(idx, gender_or_None)]
    for i in range(1, max_slots + 1):
        vor  = (erz_row.get(f'Erzieher {i}: Vorname',  '') or '').strip()
        nach = (erz_row.get(f'Erzieher {i}: Nachname', '') or '').strip()
        if not (vor or nach):
            continue
        erz_slots.append((i, _gender_from_anrede(erz_row.get(f'Erzieher {i}: Anrede', ''))))

    assigned = {}
    used = set()
    stats = {'gender': 0, 'positional': 0, 'virtual': 0, 'orphan_anspr': 0, 'orphan_erz': 0}

    # Phase 1: Anspr mit klarem Gender auf passenden Erzieher legen
    for j, anspr in enumerate(anspr_list):
        ag = _gender_from_anschluss(anspr.get('Anschluss-Art', ''))
        if ag is None:
            continue
        for idx, eg in erz_slots:
            if idx in assigned or eg != ag:
                continue
            assigned[idx] = anspr
            used.add(j)
            stats['gender'] += 1
            break

    # Phase 2: alle uebrigen Anspr-Zeilen positional auf freie Slots
    for j, anspr in enumerate(anspr_list):
        if j in used:
            continue
        for idx, _eg in erz_slots:
            if idx in assigned:
                continue
            assigned[idx] = anspr
            used.add(j)
            stats['positional'] += 1
            break

    # Phase 3 (optional): Rest auf virtuelle Slots oberhalb des Schild-Headers
    if lift_limit:
        used_idx = max((idx for idx, _ in erz_slots), default=0)
        next_slot = max(max_slots, used_idx) + 1
        for j, anspr in enumerate(anspr_list):
            if j in used:
                continue
            assigned[next_slot] = anspr
            used.add(j)
            stats['virtual'] += 1
            next_slot += 1

    stats['orphan_anspr'] = len(anspr_list) - len(used)
    stats['orphan_erz']   = sum(1 for idx, _ in erz_slots if idx not in assigned)
    return assigned, stats


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_zip_name(template):
    """Ersetzt Platzhalter im ZIP-Namen-Template."""
    now = datetime.now()
    repl = {
        'datum':    now.strftime('%Y-%m-%d'),
        'date':     now.strftime('%Y-%m-%d'),
        'datetime': now.strftime('%Y-%m-%d_%H-%M-%S'),
        'zeit':     now.strftime('%H-%M-%S'),
        'jahr':     now.strftime('%Y'),
        'monat':    now.strftime('%m'),
        'tag':      now.strftime('%d'),
    }
    name = template
    for k, v in repl.items():
        name = name.replace('{' + k + '}', v)
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    if not name.lower().endswith('.zip'):
        name += '.zip'
    return name


def _latest_csv(directory):
    """Liefert den Pfad zur neuesten .csv-Datei im Verzeichnis (oder None)."""
    if not directory or not os.path.isdir(directory):
        return None
    files = [f for f in os.listdir(directory) if f.lower().endswith('.csv')]
    if not files:
        return None
    files.sort(key=lambda f: os.path.getctime(os.path.join(directory, f)), reverse=True)
    return os.path.join(directory, files[0])


def _read_csv_rows(path):
    """Liest eine CSV mit ';'-Separator als Liste von Dicts (gestrippte Spaltennamen)."""
    rows = []
    with open(path, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f, delimiter=';')
        if reader.fieldnames:
            reader.fieldnames = [(c or '').strip() for c in reader.fieldnames]
        for row in reader:
            rows.append({(k or '').strip(): (v or '') for k, v in row.items()})
    return rows


def _read_csv_header(path):
    """Liest nur den Header der CSV (gestrippt) — billig auch bei sehr grossen
    Dateien. Liefert [] bei Fehler/leerer Datei."""
    if not path or not os.path.isfile(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f, delimiter=';')
            return [(c or '').strip() for c in (reader.fieldnames or [])]
    except Exception:
        return []


def _inspect_erz_source(path):
    """Schaut sich den Erzieher-Export-Header an und liefert Flags, welche
    optionalen Spalten die genutzte Schild-Vorlage enthaelt — fuer die UI,
    damit der Nutzer sieht, dass z.B. Stammdaten- oder Geburtsdatum-Spalten
    vorhanden sind und der Anspr-Export entsprechend (un-)noetig ist."""
    headers = set(_read_csv_header(path))
    if not headers:
        return {
            'has_student_stamm':  False,
            'has_geburtsdatum':   False,
            'klasse_col':         None,
            'vorname_col':        None,
            'nachname_col':       None,
            'geburtsdatum_col':   None,
        }
    klasse_col   = next((c for c in _STUDENT_KLASSE_COLS   if c in headers), None)
    vorname_col  = next((c for c in _STUDENT_VORNAME_COLS  if c in headers), None)
    nachname_col = next((c for c in _STUDENT_NACHNAME_COLS if c in headers), None)
    geb_col      = next((c for c in _GEBURTSDATUM_COLS     if c in headers), None)
    return {
        'has_student_stamm':  bool(klasse_col and vorname_col and nachname_col),
        'has_geburtsdatum':   bool(geb_col),
        'klasse_col':         klasse_col,
        'vorname_col':        vorname_col,
        'nachname_col':       nachname_col,
        'geburtsdatum_col':   geb_col,
    }


# ---------------------------------------------------------------------------
# Verarbeitung
# ---------------------------------------------------------------------------

def status_info():
    """Liefert Info über aktuelle Eingabedateien + letztes ZIP für die UI."""
    erz_dir   = get_erzieher_export_dir()
    ansp_dir  = get_ansprechpartner_export_dir()
    out_dir   = get_output_dir()
    # Resolver entscheidet anhand schueler_export_mode, welche Quelle wirksam ist;
    # ohne den waere der UI-Status nur halbe Wahrheit (Buttons wuerden trotz
    # vorhandenem Schueler-Export im 'always'-Mode auf 'keine Quelle' stehen).
    erz_file, source_info = _resolve_erzieher_path()
    ansp_file = _latest_csv(ansp_dir)
    erz_inspect = _inspect_erz_source(erz_file)
    # Verfuegbare Klassen + aktiver Whitelist-Filter — fuer die Chip-UI.
    # Klassen kommen primaer aus dem Anspr-Export (Schueler-Klasse), Fallback
    # aus dem Erzieher-Export (falls Klasse-Spalte vorhanden).
    classes_available = []
    if erz_file:
        try:
            lookup = _merge_student_lookups(
                _student_lookup_from_anspr(ansp_file),
                _student_lookup_from_erz(_read_csv_rows(erz_file)),
            )
            classes_available = sorted({s['klasse'] for s in lookup.values()
                                        if s.get('klasse')})
        except Exception:
            classes_available = []
    # Schueler-Export-Quelle (Konsolidierung): zeige separat, was im
    # 'Schild Exporte'-Hauptverzeichnis (schildexport_directory) liegt —
    # damit das Frontend auch bei mode='off' anbieten kann, auf
    # 'fallback'/'always' umzuschalten, falls dort ein nutzbarer Schueler-Export
    # liegt. UI rendert daraus das Hinweis-Banner + Quellwahl-Radios.
    schexp_dir     = get_schildexport_dir()
    schexp_csv     = source_info.get('schueler_csv_path')
    return {
        'erzieher_export_directory':        erz_dir,
        'ansprechpartner_export_directory': ansp_dir,
        'output_directory':                 out_dir,
        # Welche optionalen Spalten enthaelt die genutzte Erzieher-Vorlage?
        'erz_source_inspect':               erz_inspect,
        # Klassen-Whitelist (analog Ausbilder)
        'classes_available':                classes_available,
        'class_filter':                     get_class_filter(),
        'zip_name_template':                get_zip_name_template(),
        'smart_match':                      get_smart_match(),
        'filter_volljaehrig':               get_filter_volljaehrig(),
        'require_email':                    get_require_email(),
        'fill_dummies':                     get_fill_dummies(),
        'lift_limit':                       get_lift_limit(),
        'phone_from_erz_first':             get_phone_from_erz_first(),
        'assign_eltern_ids':                get_assign_eltern_ids(),
        'latest_erzieher_export':           os.path.basename(erz_file) if erz_file else None,
        'latest_ansprechpartner_export':    os.path.basename(ansp_file) if ansp_file else None,
        'erzieher_export_path':             erz_file,
        'ansprechpartner_export_path':      ansp_file,
        # Anspr-Export ist optional — Process- und Preview-Buttons brauchen ihn nicht
        'anspr_available':                  bool(ansp_file),
        'anspr_optional':                   True,
        # Single-File-Konsolidierung (3.2): aktiver Mode + erkannte Schueler-Export-Quelle
        'schueler_export_mode':             get_schueler_export_mode(),
        'schueler_export_source':           source_info,
        'schildexport_directory':           schexp_dir,
        'latest_schueler_export':           os.path.basename(schexp_csv) if schexp_csv else None,
    }


def process(erzieher_path=None, ansprechpartner_path=None, smart_match=None,
            filter_volljaehrig=None, require_email=None, fill_dummies=None,
            lift_limit=None, phone_from_erz_first=None, assign_eltern_ids=None,
            class_filter=None):
    """
    Verarbeitet die zwei CSVs und liefert (result_files, stats).

    Optionen (default = jeweiliges Setting in settings.ini):
      smart_match          — Telefon ↔ Erzieher-Slot per Anschluss-Art (Mutter/Vater/...)
      filter_volljaehrig   — Schueler mit Self-Ansprechpartner ("volljaehrig") rauswerfen
      require_email        — Erzieher ohne E-Mail nicht exportieren
      fill_dummies         — Leere Erzieher-Felder mit eindeutigen Dummies fuellen
      lift_limit           — Limit von 2 Erziehern pro Schueler aufheben (zusaetzliche
                             Telefon-Zeilen landen in Erzieher_3.csv, _4.csv, ...)
      phone_from_erz_first — Telefonnummer aus dem Erzieher-Export (Spalten
                             'Telefon-Nummern: ...') wird als zusaetzliche, prioritaere
                             Pseudo-Anspr-Zeile pro Schueler behandelt; Duplikate
                             gegenueber dem Anspr-Export werden gefiltert.
    """
    if smart_match is None:        smart_match = get_smart_match()
    if filter_volljaehrig is None: filter_volljaehrig = get_filter_volljaehrig()
    if require_email is None:      require_email = get_require_email()
    if fill_dummies is None:       fill_dummies = get_fill_dummies()
    if lift_limit is None:         lift_limit = get_lift_limit()
    if phone_from_erz_first is None: phone_from_erz_first = get_phone_from_erz_first()
    if assign_eltern_ids is None:    assign_eltern_ids = get_assign_eltern_ids()
    if class_filter is None:         class_filter = get_class_filter()

    # Resolver respektiert schueler_export_mode — kann auf den Schueler-Export
    # aus AusbilderInput ausweichen, wenn so konfiguriert / wenn der separate
    # Erzieher-Export fehlt.
    if erzieher_path is None:
        erzieher_path, _src = _resolve_erzieher_path()
    ansprechpartner_path = ansprechpartner_path or _latest_csv(get_ansprechpartner_export_dir())

    if not erzieher_path or not os.path.isfile(erzieher_path):
        raise FileNotFoundError("Keine Erzieher-Export-CSV gefunden. Bitte Verzeichnis prüfen.")

    erz_rows = _read_csv_rows(erzieher_path)
    if not erz_rows:
        raise ValueError("Erzieher-Export ist leer.")
    if 'Interne ID-Nummer' not in erz_rows[0]:
        raise ValueError("Spalte 'Interne ID-Nummer' fehlt im Erzieher-Export.")

    # Ansprechpartner-Export ist OPTIONAL — wenn er fehlt, laufen alle Telefon-
    # Verarbeitungsschritte ueber die im Erzieher-Export hinterlegte primaere
    # Telefonnummer (Spaltengruppe 'Telefon-Nummern: ...') bzw. entfallen.
    anspr_available = bool(ansprechpartner_path and os.path.isfile(ansprechpartner_path))
    ansp_rows = []
    if anspr_available:
        ansp_rows = _read_csv_rows(ansprechpartner_path)
        if ansp_rows and 'Schüler_ID' not in ansp_rows[0]:
            raise ValueError("Spalte 'Schüler_ID' fehlt im Ansprechpartner-Export.")

    # Klassen-Whitelist anwenden — VOR allen anderen Filterstufen, damit die
    # nachfolgenden Stats (volljaehrig_filtered, dummy_fills, …) sich nur auf
    # den vom Nutzer ausgewaehlten Klassen-Pool beziehen.
    class_mode, classes_set = _resolve_class_filter(class_filter)
    class_filtered = 0
    if class_mode != 'all':
        student_lookup = _merge_student_lookups(
            _student_lookup_from_anspr(ansprechpartner_path),
            _student_lookup_from_erz(erz_rows),
        )
        before = len(erz_rows)
        erz_rows = [r for r in erz_rows
                    if _student_passes_class(
                        student_lookup.get((r.get('Interne ID-Nummer', '') or '').strip(), {}),
                        class_mode, classes_set)]
        class_filtered = before - len(erz_rows)

    # Volljaehrige Schueler filtern + Stats
    volljaehrig_filtered = 0
    if filter_volljaehrig:
        before = len(erz_rows)
        erz_rows = [r for r in erz_rows if not _is_self_volljaehrig(r)]
        volljaehrig_filtered = before - len(erz_rows)

    # Anspr-Zeilen pro Schueler-ID sammeln (Reihenfolge der CSV bewahrt)
    ansp_by_sid = {}
    for r in ansp_rows:
        ansp_by_sid.setdefault(r.get('Schüler_ID', ''), []).append(r)

    # Maximale Erzieher-Slot-Nummer aus dem Erzieher-CSV-Header ableiten
    max_slots_in_csv = 0
    for col in (erz_rows[0].keys() if erz_rows else []):
        m = re.match(r'Erzieher\s+(\d+):', col)
        if m:
            max_slots_in_csv = max(max_slots_in_csv, int(m.group(1)))

    # Pro Schueler die Anspr-Zuordnung berechnen
    match_stats_total = {'gender': 0, 'positional': 0, 'virtual': 0,
                         'orphan_anspr': 0, 'orphan_erz': 0}
    assignment_by_sid = {}  # sid -> {erz_idx: anspr_dict}
    phone_from_erz_used      = 0  # wie oft pseudo-Zeile uebernommen wurde
    phone_from_erz_duplicates = 0  # wie oft Duplikate im Anspr-Export gefiltert wurden
    for erz_row in erz_rows:
        sid = erz_row.get('Interne ID-Nummer', '').strip()
        if not sid:
            continue
        anspr_list = ansp_by_sid.get(sid, [])
        if phone_from_erz_first:
            erz_phone = _erz_phone_pseudo(erz_row)
            if erz_phone:
                before = len(anspr_list)
                anspr_list = _merge_phone_sources(erz_phone, anspr_list)
                phone_from_erz_used += 1
                # +1 fuer die neue Pseudo-Zeile; Differenz = entfernte Duplikate
                phone_from_erz_duplicates += (before + 1) - len(anspr_list)
        if smart_match:
            assigned, st = _smart_match_student(erz_row, anspr_list, max_slots_in_csv,
                                                lift_limit=lift_limit)
            for k in match_stats_total:
                match_stats_total[k] += st[k]
        else:
            # Positional: i-te Anspr-Zeile -> Erzieher i (lift_limit ist hier ohnehin
            # implizit aktiv, da nicht durch max_slots_in_csv begrenzt)
            assigned = {i + 1: anspr_list[i] for i in range(len(anspr_list))}
        assignment_by_sid[sid] = assigned

    # max_erzieher (= Anzahl Output-CSVs) aus den tatsaechlich getroffenen
    # Zuweisungen + gefuellten Stammdaten-Slots ableiten
    max_erzieher = 0
    for er in erz_rows:
        sid = er.get('Interne ID-Nummer', '').strip()
        # Gefuellte Stammdaten-Slots
        upper_for_stamm = max_slots_in_csv
        for i in range(1, upper_for_stamm + 1):
            if (er.get(f'Erzieher {i}: Vorname', '') or er.get(f'Erzieher {i}: Nachname', '')).strip():
                max_erzieher = max(max_erzieher, i)
        # Zugeordnete Slots (inkl. virtueller bei lift_limit)
        for idx in assignment_by_sid.get(sid, {}).keys():
            max_erzieher = max(max_erzieher, idx)

    # Eltern-ID-DB einmal laden (Batch-Modus), spaeter atomar speichern
    eltern_db        = None
    eltern_id_new    = 0
    eltern_id_reused = 0
    if assign_eltern_ids:
        import eltern_id_manager
        eltern_db = eltern_id_manager.load_db()

    # Pro Erzieher-Index eine Ergebnisdatei bauen
    result_files = {}
    skipped_no_email = 0
    dummy_fills      = 0
    for i in range(1, max_erzieher + 1):
        header = ['Interne_ID_Nummer']
        for field in ERZIEHER_FIELDS:
            header.append(f'Erzieher {i}: {field}')
        for src in ANSPRECHPARTNER_FIELD_MAP.values():
            header.append(f'Erzieher {i}: {src}')
        if assign_eltern_ids:
            header.append(f'Erzieher {i}: Eltern-ID')

        result_rows = []
        for erz_row in erz_rows:
            sid = erz_row.get('Interne ID-Nummer', '').strip()
            if not sid:
                continue
            ansp = assignment_by_sid.get(sid, {}).get(i, {})
            stamm = {fld: (erz_row.get(f'Erzieher {i}: {fld}', '') or '').strip()
                     for fld in ERZIEHER_FIELDS}
            has_stamm = any(stamm.values())
            has_ansp  = any((ansp.get(c, '') or '').strip() for c in ANSPRECHPARTNER_FIELD_MAP)
            if not (has_stamm or has_ansp):
                continue  # leerer Slot fuer diesen Schueler -> nicht exportieren
            if require_email and not stamm.get('E-Mail', ''):
                skipped_no_email += 1
                continue

            row_out = {'Interne_ID_Nummer': sid}
            for field in ERZIEHER_FIELDS:
                row_out[f'Erzieher {i}: {field}'] = stamm[field]
            for src_col, tgt_col_short in ANSPRECHPARTNER_FIELD_MAP.items():
                row_out[f'Erzieher {i}: {tgt_col_short}'] = ansp.get(src_col, '')

            # Eltern-ID auf Basis der ECHTEN Stammdaten (vor Dummy-Fill) holen
            if assign_eltern_ids:
                import eltern_id_manager
                key = eltern_id_manager._key(stamm['Vorname'], stamm['Nachname'],
                                             stamm['E-Mail'])
                existed = key in eltern_db['mappings']
                eid = eltern_id_manager.get_or_assign(
                    stamm['Vorname'], stamm['Nachname'], stamm['E-Mail'],
                    db=eltern_db)
                row_out[f'Erzieher {i}: Eltern-ID'] = eid or ''
                if eid is not None:
                    if existed: eltern_id_reused += 1
                    else:       eltern_id_new    += 1

            if fill_dummies:
                before = sum(1 for v in row_out.values() if not v)
                _apply_dummies(row_out, i)
                after  = sum(1 for v in row_out.values() if not v)
                dummy_fills += (before - after)

            result_rows.append(row_out)

        result_files[f'Erzieher_{i}'] = {'header': header, 'rows': result_rows}

    # Eltern-ID-DB persistieren (atomar)
    if assign_eltern_ids and eltern_db is not None:
        import eltern_id_manager
        eltern_id_manager.save_db(eltern_db)

    stats = {
        'erzieher_rows':        len(erz_rows),
        'ansprechpartner_rows': len(ansp_rows),
        'anspr_available':      anspr_available,
        'max_erzieher':         max_erzieher,
        'output_files':         list(result_files.keys()),
        'match_mode':           'smart' if smart_match else 'positional',
        'match_stats':          match_stats_total,
        'filter_volljaehrig':       filter_volljaehrig,
        'volljaehrig_filtered':     volljaehrig_filtered,
        'require_email':            require_email,
        'skipped_no_email':         skipped_no_email,
        'fill_dummies':             fill_dummies,
        'dummy_fills':              dummy_fills,
        'lift_limit':               lift_limit,
        'phone_from_erz_first':         phone_from_erz_first,
        'phone_from_erz_used':          phone_from_erz_used,
        'phone_from_erz_duplicates':    phone_from_erz_duplicates,
        'assign_eltern_ids':            assign_eltern_ids,
        'eltern_id_new':                eltern_id_new,
        'eltern_id_reused':             eltern_id_reused,
        'class_filter':                 list(class_filter or []),
        'class_filter_mode':            class_mode,
        'class_filtered':               class_filtered,
        'erzieher_source_path':         erzieher_path,
        'erzieher_source_is_schueler':  _is_schueler_export_file(erzieher_path),
    }
    return result_files, stats


def preview(erzieher_path=None, ansprechpartner_path=None):
    """
    Liefert eine Vorschau der kombinierten Schueler+Erzieher-Daten ohne ZIP-
    Generierung. Geeignet, um in der UI sowohl Schueler->Erzieher als auch
    Erzieher->Schueler (gruppiert) darzustellen.

    Returns dict mit:
      - students:        Liste[{id, vorname, nachname, klasse, erzieher: [...]}]
      - erzieher_groups: Liste[{erzieher: {...}, students: [{id, vorname, nachname, klasse, nr}, ...]}]
      - stats:           {students_count, erzieher_total, max_erzieher, students_without_erzieher}
      - field_mapping:   {from_erzieher_csv: [{src,target}], from_ansprechpartner_csv: [{src,target}]}
      - sources:         {erzieher_export_file, ansprechpartner_export_file, headers_*}
    """
    # Resolver respektiert schueler_export_mode — siehe process() fuer Details.
    if erzieher_path is None:
        erzieher_path, _src = _resolve_erzieher_path()
    ansprechpartner_path = ansprechpartner_path or _latest_csv(get_ansprechpartner_export_dir())

    if not erzieher_path or not os.path.isfile(erzieher_path):
        raise FileNotFoundError("Keine Erzieher-Export-CSV gefunden. Bitte Verzeichnis pruefen.")

    erz_rows = _read_csv_rows(erzieher_path)
    if not erz_rows:
        raise ValueError("Erzieher-Export ist leer.")
    if 'Interne ID-Nummer' not in erz_rows[0]:
        raise ValueError("Spalte 'Interne ID-Nummer' fehlt im Erzieher-Export.")

    # Anspr-Export ist optional
    anspr_available = bool(ansprechpartner_path and os.path.isfile(ansprechpartner_path))
    ansp_rows = []
    if anspr_available:
        ansp_rows = _read_csv_rows(ansprechpartner_path)
        if ansp_rows and 'Schüler_ID' not in ansp_rows[0]:
            raise ValueError("Spalte 'Schüler_ID' fehlt im Ansprechpartner-Export.")

    # Header der Eingabe-Dateien (fuer die Anzeige im Field-Mapping-Block)
    erz_header  = list(erz_rows[0].keys())  if erz_rows  else []
    ansp_header = list(ansp_rows[0].keys()) if ansp_rows else []

    # Schueler-Stammdaten-Lookup — kombiniert aus beiden Quellen.
    # Anspr-Export ist die primaere Quelle (Schild-Standard); Erzieher-Export
    # ist Fallback, falls die Schule die Stammdaten-Spalten ebenfalls in die
    # Erzieher-Vorlage aufgenommen hat oder der Anspr-Export gar nicht existiert.
    # Brauchen wir frueh, weil der Klassen-Filter darauf zugreift.
    student_lookup = _merge_student_lookups(
        _student_lookup_from_anspr(ansprechpartner_path),
        _student_lookup_from_erz(erz_rows),
    )

    # Klassen-Whitelist anwenden — VOR allen anderen Filterstufen, damit die
    # nachfolgenden Stats sich nur auf den vom Nutzer ausgewaehlten Pool beziehen.
    class_filter = get_class_filter()
    class_mode, classes_set = _resolve_class_filter(class_filter)
    class_filtered = 0
    if class_mode != 'all':
        before = len(erz_rows)
        erz_rows = [r for r in erz_rows
                    if _student_passes_class(
                        student_lookup.get((r.get('Interne ID-Nummer', '') or '').strip(), {}),
                        class_mode, classes_set)]
        class_filtered = before - len(erz_rows)

    # Volljaehrige Schueler optional rausfiltern
    filter_volljaehrig = get_filter_volljaehrig()
    volljaehrig_filtered = 0
    if filter_volljaehrig:
        before = len(erz_rows)
        erz_rows = [r for r in erz_rows if not _is_self_volljaehrig(r)]
        volljaehrig_filtered = before - len(erz_rows)

    # Ansprechpartner-Zeilen pro Schueler-ID gruppieren (Reihenfolge aus CSV bewahrt).
    ansp_by_sid = {}
    for r in ansp_rows:
        ansp_by_sid.setdefault(r.get('Schüler_ID', ''), []).append(r)

    # Maximale Erzieher-Slot-Nummer aus dem Header ableiten
    max_in_header = 0
    for col in erz_header:
        m = re.match(r'Erzieher\s+(\d+):', col)
        if m:
            max_in_header = max(max_in_header, int(m.group(1)))
    if max_in_header == 0:
        max_in_header = max((len(v) for v in ansp_by_sid.values()), default=0)

    smart_match          = get_smart_match()
    require_email        = get_require_email()
    fill_dummies         = get_fill_dummies()
    lift_limit           = get_lift_limit()
    phone_from_erz_first = get_phone_from_erz_first()
    assign_eltern_ids    = get_assign_eltern_ids()
    # Eltern-IDs in der Preview NUR lesen — Vergabe erst beim Verarbeiten
    eltern_db_preview = None
    eltern_id_total      = 0
    eltern_id_known      = 0
    eltern_id_would_new  = 0
    if assign_eltern_ids:
        import eltern_id_manager
        eltern_db_preview = eltern_id_manager.load_db()

    students = []
    students_without_erzieher = 0
    skipped_no_email = 0
    dummy_fills      = 0
    match_stats = {'gender': 0, 'positional': 0, 'virtual': 0,
                   'orphan_anspr': 0, 'orphan_erz': 0}
    orphan_anspr_rows = []   # fuer detaillierte Anzeige in der Preview
    phone_from_erz_used       = 0
    phone_from_erz_duplicates = 0
    # Pro Student max-Slot ermitteln, damit virtuelle Slots (lift_limit) sichtbar werden
    assignments = {}
    for erz_row in erz_rows:
        sid = erz_row.get('Interne ID-Nummer', '').strip()
        if not sid:
            continue
        anspr_list = ansp_by_sid.get(sid, [])
        if phone_from_erz_first:
            erz_phone = _erz_phone_pseudo(erz_row)
            if erz_phone:
                before = len(anspr_list)
                anspr_list = _merge_phone_sources(erz_phone, anspr_list)
                phone_from_erz_used += 1
                phone_from_erz_duplicates += (before + 1) - len(anspr_list)
        if smart_match:
            assigned, st = _smart_match_student(erz_row, anspr_list, max_in_header,
                                                lift_limit=lift_limit)
            for k in match_stats:
                match_stats[k] += st[k]
            if not lift_limit:
                used_anspr = set(id(v) for v in assigned.values())
                for a in anspr_list:
                    if id(a) not in used_anspr:
                        stamm_o = student_lookup.get(sid, {})
                        orphan_anspr_rows.append({
                            'student_id':   sid,
                            'student_name': f"{stamm_o.get('nachname','')}, {stamm_o.get('vorname','')}".strip(', '),
                            'klasse':       stamm_o.get('klasse', ''),
                            'anschluss':    (a.get('Anschluss-Art')  or '').strip(),
                            'bemerkung':    (a.get('Bemerkung')      or '').strip(),
                            'telefon':      (a.get('Telefon-Nummer') or '').strip(),
                            'from_erz':     bool(a.get('_from_erz')),
                        })
        else:
            assigned = {i + 1: anspr_list[i] for i in range(len(anspr_list))}
        assignments[sid] = assigned

    for erz_row in erz_rows:
        sid = erz_row.get('Interne ID-Nummer', '').strip()
        if not sid:
            continue
        assigned = assignments.get(sid, {})
        # Anzeige bis max. (Header-Slots) plus alle virtuellen Slots
        max_for_student = max([max_in_header] + list(assigned.keys()), default=max_in_header)

        erzieher_list = []
        for i in range(1, max_for_student + 1):
            erz_data = {
                'nr':          i,
                'anrede':      erz_row.get(f'Erzieher {i}: Anrede',      '').strip(),
                'briefanrede': erz_row.get(f'Erzieher {i}: Briefanrede', '').strip(),
                'titel':       erz_row.get(f'Erzieher {i}: Titel',       '').strip(),
                'nachname':    erz_row.get(f'Erzieher {i}: Nachname',    '').strip(),
                'vorname':     erz_row.get(f'Erzieher {i}: Vorname',     '').strip(),
                'email':       erz_row.get(f'Erzieher {i}: E-Mail',      '').strip(),
            }
            ansp = assigned.get(i, {})
            erz_data.update({
                'anschluss':       (ansp.get('Anschluss-Art')  or '').strip(),
                'bemerkung':       (ansp.get('Bemerkung')      or '').strip(),
                'telefon':         (ansp.get('Telefon-Nummer') or '').strip(),
                'telefon_from_erz': bool(ansp.get('_from_erz')),
            })
            has_anything = any(v for k, v in erz_data.items()
                               if k not in ('nr', 'telefon_from_erz'))
            if not has_anything:
                continue
            # Flags fuer die UI
            erz_data['virtual']           = i > max_in_header
            erz_data['would_skip_email']  = bool(require_email and not erz_data['email'])
            # Eltern-ID-Preview (nur lookup, ohne neue zu erzeugen)
            if assign_eltern_ids and not erz_data['would_skip_email']:
                import eltern_id_manager
                if not eltern_id_manager.is_dummy(erz_data['vorname'],
                                                  erz_data['nachname'],
                                                  erz_data['email']) and \
                   (erz_data['vorname'] or erz_data['nachname']):
                    key = eltern_id_manager._key(erz_data['vorname'],
                                                  erz_data['nachname'],
                                                  erz_data['email'])
                    existing = eltern_db_preview['mappings'].get(key)
                    if existing is not None:
                        erz_data['eltern_id']        = eltern_id_manager._format_id(existing)
                        erz_data['eltern_id_status'] = 'known'
                        eltern_id_known += 1
                    else:
                        erz_data['eltern_id']        = '(neu)'
                        erz_data['eltern_id_status'] = 'new'
                        eltern_id_would_new += 1
                    eltern_id_total += 1
            # Dummy-Vorschau (vor allem fuer virtuelle Slots interessant)
            if fill_dummies:
                erz_data['dummies'] = {}
                for short, dummy in DUMMY_VALUES.items():
                    if short == 'E-Mail':
                        key = 'email'
                    elif short == 'Telefon-Nummer':
                        key = 'telefon'
                    elif short == 'Anschluss Art':
                        key = 'anschluss'
                    else:
                        key = short.lower()
                    if key in erz_data and not erz_data[key]:
                        erz_data['dummies'][key] = dummy
                # Zaehler aktualisieren — fuer Stats
                if erz_data.get('would_skip_email'):
                    pass  # wird ja eh nicht exportiert
                else:
                    dummy_fills += len(erz_data['dummies'])
            erzieher_list.append(erz_data)

        # Stats: wuerde dieser Slot wegen E-Mail rausfliegen?
        if require_email:
            skipped_no_email += sum(1 for e in erzieher_list if e.get('would_skip_email'))

        if not erzieher_list:
            students_without_erzieher += 1
        stamm = student_lookup.get(sid, {})
        students.append({
            'id':       sid,
            'vorname':  stamm.get('vorname')  or (erz_row.get('Vorname',  '') or '').strip(),
            'nachname': stamm.get('nachname') or (erz_row.get('Nachname', '') or '').strip(),
            'klasse':   stamm.get('klasse')   or (erz_row.get('Klasse',   '') or '').strip(),
            'erzieher': erzieher_list,
        })
    students.sort(key=lambda s: (s['klasse'], s['nachname'], s['vorname']))

    # Erzieher gruppieren ueber alle Schueler (Schluessel: nachname|vorname|email, case-insensitive)
    groups = {}
    for s in students:
        for e in s['erzieher']:
            key = (e['nachname'].lower(), e['vorname'].lower(), e['email'].lower())
            if not any(key):
                continue
            entry = groups.setdefault(key, {'erzieher': e.copy(), 'students': []})
            entry['students'].append({
                'id':       s['id'],
                'vorname':  s['vorname'],
                'nachname': s['nachname'],
                'klasse':   s['klasse'],
                'nr':       e['nr'],
            })
    erzieher_groups = sorted(
        groups.values(),
        key=lambda g: (g['erzieher']['nachname'].lower(), g['erzieher']['vorname'].lower()),
    )

    erzieher_total = sum(len(s['erzieher']) for s in students)
    max_erzieher   = max((len(s['erzieher']) for s in students), default=0)

    # Feld-Mapping: was wandert aus welcher CSV in die i-te Output-CSV?
    # 'i' ist Platzhalter; der konkrete Wert haengt vom Output-File ab.
    from_erzieher = [{'src': 'Interne ID-Nummer', 'target': 'Interne_ID_Nummer'}]
    for f in ERZIEHER_FIELDS:
        from_erzieher.append({'src': f'Erzieher i: {f}', 'target': f'Erzieher i: {f}'})
    from_ansprechpartner = [{'src': 'Schueler_ID', 'target': 'Interne_ID_Nummer (Matching)'}]
    for src, tgt in ANSPRECHPARTNER_FIELD_MAP.items():
        from_ansprechpartner.append({'src': src, 'target': f'Erzieher i: {tgt}'})

    return {
        'students':        students,
        'erzieher_groups': [
            {
                'erzieher': g['erzieher'],
                'students': sorted(g['students'], key=lambda x: (x['klasse'], x['nachname'], x['vorname'])),
            }
            for g in erzieher_groups
        ],
        'stats': {
            'students_count':            len(students),
            'students_without_erzieher': students_without_erzieher,
            'erzieher_total':            erzieher_total,
            'unique_erzieher':           len(erzieher_groups),
            'max_erzieher':              max_erzieher,
            'ansprechpartner_rows':      len(ansp_rows),
            'anspr_available':           anspr_available,
            'match_mode':                'smart' if smart_match else 'positional',
            'match_stats':               match_stats,
            'orphan_anspr_rows':         orphan_anspr_rows[:200],  # Cap fuer UI
            'orphan_anspr_count':        len(orphan_anspr_rows),
            'filter_volljaehrig':        filter_volljaehrig,
            'volljaehrig_filtered':      volljaehrig_filtered,
            'require_email':             require_email,
            'skipped_no_email':          skipped_no_email,
            'fill_dummies':              fill_dummies,
            'dummy_fills':               dummy_fills,
            'lift_limit':                lift_limit,
            'phone_from_erz_first':         phone_from_erz_first,
            'phone_from_erz_used':          phone_from_erz_used,
            'phone_from_erz_duplicates':    phone_from_erz_duplicates,
            'assign_eltern_ids':            assign_eltern_ids,
            'eltern_id_total':              eltern_id_total,
            'eltern_id_known':              eltern_id_known,
            'eltern_id_would_new':          eltern_id_would_new,
            'class_filter':                 list(class_filter or []),
            'class_filter_mode':            class_mode,
            'class_filtered':               class_filtered,
        },
        'field_mapping': {
            'from_erzieher_csv':        from_erzieher,
            'from_ansprechpartner_csv': from_ansprechpartner,
        },
        'sources': {
            'erzieher_export_file':        os.path.basename(erzieher_path),
            'ansprechpartner_export_file': os.path.basename(ansprechpartner_path) if anspr_available else None,
            'erzieher_headers':            erz_header,
            'ansprechpartner_headers':     ansp_header,
            # Konsolidierung: erkennt das Frontend, ob die genutzte Erzieher-Quelle
            # tatsaechlich ein Schueler-Export war (relevant fuer das Source-Badge).
            'erzieher_is_schueler_export': _is_schueler_export_file(erzieher_path),
        },
    }


def raw_source(max_rows=500):
    """Liefert die ersten max_rows beider Quell-CSVs als tabular dicts fuer
    die UI — damit der Nutzer schnell verifizieren kann, dass der Schild-Export
    so aussieht wie erwartet. Markiert auch welche Spalten der Workflow
    tatsaechlich liest."""
    # Resolver respektiert schueler_export_mode — so sieht der Nutzer im
    # Quelldateien-Viewer immer die Datei, die der Workflow tatsaechlich verarbeitet.
    erz_path, _src = _resolve_erzieher_path()
    anp_path = _latest_csv(get_ansprechpartner_export_dir())

    def _capped(path):
        if not path or not os.path.isfile(path):
            return None
        rows = _read_csv_rows(path)
        headers = list(rows[0].keys()) if rows else []
        sample = rows[:max_rows]
        return {
            'file':       os.path.basename(path),
            'columns':    headers,
            'rows_total': len(rows),
            'rows_shown': len(sample),
            'rows':       [[r.get(h, '') for h in headers] for r in sample],
        }

    # Welche Spalten werden vom Workflow tatsaechlich genutzt?
    # Aus dem Erzieher-Export: 'Interne ID-Nummer' + 'Erzieher i: <Field>' fuer i=1..max
    used_erz = {'Interne ID-Nummer'}
    if erz_path and os.path.isfile(erz_path):
        # Max-Slot aus dem Header lesen
        max_slot = 0
        with open(erz_path, 'r', encoding='utf-8-sig', newline='') as f:
            for col in (csv.DictReader(f, delimiter=';').fieldnames or []):
                m = re.match(r'Erzieher\s+(\d+):', (col or '').strip())
                if m:
                    max_slot = max(max_slot, int(m.group(1)))
        for i in range(1, max_slot + 1):
            for fld in ERZIEHER_FIELDS:
                used_erz.add(f'Erzieher {i}: {fld}')
    # Erzieher-Export-Telefon (Pseudo-Anspr-Zeile fuer phone_from_erz_first)
    used_erz.update(ERZ_PHONE_COLS.values())
    # Klasse / Name / Geburtsdatum / Vollj.-Flag (fuer UI-Anzeige, Missing-Report
    # und Vollj.-Filter)
    used_erz.update({'Klasse', 'Erzieher: Art (Klartext)', 'Vorname', 'Nachname'})
    used_erz.update(_GEBURTSDATUM_COLS)
    used_anp = set(ANSPRECHPARTNER_FIELD_MAP.keys()) | {'Schüler_ID'}

    return {
        'erzieher':        _capped(erz_path),
        'ansprechpartner': _capped(anp_path),
        'used_erzieher_cols':        sorted(used_erz),
        'used_ansprechpartner_cols': sorted(used_anp),
        'cap':             max_rows,
    }


# ---------------------------------------------------------------------------
# Missing-Erzieher-Report (Klassenweise Auswertung minderjaehriger Schueler
# ohne hinterlegte Erzieher-Daten)
# ---------------------------------------------------------------------------

def _is_minor(erz_row):
    """Heuristik: Schueler gilt als minderjaehrig, wenn er NICHT explizit als
    volljaehrig markiert ist. (Schild hat keine separate Volljaehrig-Spalte;
    wir nutzen denselben Proxy wie _is_self_volljaehrig.)"""
    return not _is_self_volljaehrig(erz_row)


# Kriterien fuer den Missing-Report: Key -> (Label, Test-Funktion)
# Jede Test-Funktion bekommt (erz_row, max_slots) und liefert True, wenn der
# Schueler nach DIESEM Kriterium als "fehlend" gilt.
MISSING_CRITERIA = {
    'no_erzieher': {
        'label': 'Kein Erzieher hinterlegt',
        'test':  lambda er, n: all(
            not (er.get(f'Erzieher {i}: {f}', '') or '').strip()
            for i in range(1, n + 1)
            for f in ('Vorname', 'Nachname', 'E-Mail')
        ),
    },
    'no_nachname': {
        'label': 'Mind. ein Erzieher ohne Nachname',
        'test':  lambda er, n: any(
            _slot_used(er, i) and not (er.get(f'Erzieher {i}: Nachname', '') or '').strip()
            for i in range(1, n + 1)
        ),
    },
    'no_vorname': {
        'label': 'Mind. ein Erzieher ohne Vorname',
        'test':  lambda er, n: any(
            _slot_used(er, i) and not (er.get(f'Erzieher {i}: Vorname', '') or '').strip()
            for i in range(1, n + 1)
        ),
    },
    'no_email': {
        'label': 'Mind. ein Erzieher ohne E-Mail',
        'test':  lambda er, n: any(
            _slot_used(er, i) and not (er.get(f'Erzieher {i}: E-Mail', '') or '').strip()
            for i in range(1, n + 1)
        ),
    },
}


def _slot_used(erz_row, i):
    """True wenn Erzieher-Slot i ueberhaupt benutzt wird (mind. ein Feld gefuellt)."""
    for f in ('Anrede', 'Briefanrede', 'Titel', 'Nachname', 'Vorname', 'E-Mail'):
        if (erz_row.get(f'Erzieher {i}: {f}', '') or '').strip():
            return True
    return False


# Spaltennamen-Varianten fuer Schueler-Stammdaten — Schild liefert je nach
# Export-Vorlage unterschiedliche Bezeichnungen. Wir suchen die erste nicht-leere.
_STUDENT_KLASSE_COLS   = (
    'Klasse', 'Schüler-Klasse', 'Schüler: Klasse', 'Schueler-Klasse',
    'Schueler: Klasse', 'aktuelle Klasse', 'Klasse (aktuell)',
)
_STUDENT_VORNAME_COLS  = (
    'Vorname', 'Schüler-Vorname', 'Schüler: Vorname', 'Schueler-Vorname',
    'Schueler: Vorname',
)
_STUDENT_NACHNAME_COLS = (
    'Nachname', 'Schüler-Nachname', 'Schüler: Nachname', 'Schueler-Nachname',
    'Schueler: Nachname',
)


def _first_nonempty(row, cols):
    """Liefert den ersten nicht-leeren, getrimmten Wert aus row fuer die
    gegebenen Spaltennamen-Kandidaten."""
    for c in cols:
        v = (row.get(c, '') or '').strip()
        if v:
            return v
    return ''


def _extract_student_stamm(row):
    """Versucht Schueler-Stammdaten (Klasse, Vorname, Nachname) aus EINEM Row
    zu extrahieren — toleriert verschiedene Spaltennamen-Varianten."""
    return {
        'klasse':   _first_nonempty(row, _STUDENT_KLASSE_COLS),
        'vorname':  _first_nonempty(row, _STUDENT_VORNAME_COLS),
        'nachname': _first_nonempty(row, _STUDENT_NACHNAME_COLS),
    }


def _student_lookup_from_erz(erz_rows):
    """Lookup {sid: {klasse, vorname, nachname}} aus dem Erzieher-Export.
    Wirksam nur, wenn die Schild-Export-Vorlage diese Spalten enthaelt (Standard-
    Vorlage hat sie NICHT — der Anspr-Export ist die primaere Quelle)."""
    lookup = {}
    for r in (erz_rows or []):
        sid = (r.get('Interne ID-Nummer', '') or '').strip()
        if not sid or sid in lookup:
            continue
        stamm = _extract_student_stamm(r)
        if any(stamm.values()):
            lookup[sid] = stamm
    return lookup


def _student_lookup_from_anspr(anspr_path=None):
    """Liefert {sid: {'klasse','vorname','nachname'}} aus dem Anspr-Export.

    Der Schild-Standard-Erzieher-Export enthaelt keine Schueler-Stammdaten —
    der Anspr-Export aber sehr wohl als 'Schueler-Klasse/-Nachname/-Vorname'.
    Wenn der Anspr-Export nicht erreichbar ist -> leerer Lookup (Aufrufer
    sollte dann _student_lookup_from_erz() als Fallback verwenden)."""
    anspr_path = anspr_path or _latest_csv(get_ansprechpartner_export_dir())
    if not anspr_path or not os.path.isfile(anspr_path):
        return {}
    try:
        rows = _read_csv_rows(anspr_path)
    except Exception:
        return {}
    lookup = {}
    for r in rows:
        sid = (r.get('Schüler_ID', '') or '').strip()
        if not sid or sid in lookup:
            continue
        lookup[sid] = _extract_student_stamm(r)
    return lookup


def _merge_student_lookups(*lookups):
    """Kombiniert mehrere Lookups; bei mehrfacher SID gewinnt der erste,
    fehlende Einzelfelder werden aus spaeteren ergaenzt."""
    out = {}
    for lk in lookups:
        for sid, stamm in lk.items():
            if sid not in out:
                out[sid] = dict(stamm)
            else:
                for k, v in stamm.items():
                    if not out[sid].get(k) and v:
                        out[sid][k] = v
    return out


def missing_erzieher_report(erzieher_path=None, criteria=None, match_mode='any'):
    """Liefert pro Klasse die Liste der minderjaehrigen Schueler, die nach
    mindestens einem (match_mode='any') oder allen (match_mode='all')
    aktivierten Kriterien als "fehlend" gelten.

    criteria: Liste der aktivierten Kriterien-Keys aus MISSING_CRITERIA.
              None oder leer -> ['no_erzieher'] (Default = bisheriges Verhalten).
    match_mode: 'any' (Default) oder 'all' — Verknuepfung der Kriterien.

    Returns:
        {
          'classes': [
              {'klasse': 'BK01A', 'count': 3,
               'students': [{id, vorname, nachname, reasons: [keys]}, ...]},
              ...
          ],
          'total_classes':   N,
          'total_students':  N,
          'source_file':     'ErzieherExport.csv',
          'criteria_used':   [keys],
          'available_criteria': [{'key':..., 'label':...}, ...],
          'match_mode':      'any' | 'all',
        }
    """
    if not criteria:
        criteria = ['no_erzieher']
    # Unbekannte Keys aussortieren
    criteria = [c for c in criteria if c in MISSING_CRITERIA]
    if not criteria:
        criteria = ['no_erzieher']

    if erzieher_path is None:
        erzieher_path, _src = _resolve_erzieher_path()
    available = [{'key': k, 'label': v['label']} for k, v in MISSING_CRITERIA.items()]
    if not erzieher_path or not os.path.isfile(erzieher_path):
        raise FileNotFoundError("Keine Erzieher-Export-CSV gefunden.")
    erz_rows = _read_csv_rows(erzieher_path)
    if not erz_rows:
        return {'classes': [], 'total_classes': 0, 'total_students': 0,
                'source_file': os.path.basename(erzieher_path),
                'criteria_used': criteria,
                'available_criteria': available,
                'match_mode': match_mode}

    max_slots = 0
    for col in erz_rows[0].keys():
        m = re.match(r'Erzieher\s+(\d+):', col)
        if m:
            max_slots = max(max_slots, int(m.group(1)))

    # Schueler-Stammdaten (Name/Klasse) — kombiniert aus Anspr-Export (primaer,
    # Schild-Standard-Vorlage hat die Spalten dort) und Erzieher-Export (Fallback,
    # falls die Schule sie auch in die Erzieher-Vorlage aufgenommen hat oder
    # wenn der Anspr-Export gar nicht existiert).
    student_lookup = _merge_student_lookups(
        _student_lookup_from_anspr(),
        _student_lookup_from_erz(erz_rows),
    )
    anspr_path_used = _latest_csv(get_ansprechpartner_export_dir())
    anspr_available = bool(anspr_path_used and os.path.isfile(anspr_path_used))

    # Klassen-Whitelist auch fuer den Report respektieren — sonst tauchen
    # Schueler aus abgewaehlten Klassen hier auf, obwohl der Nutzer sie aus
    # dem Workflow ausgeblendet hat.
    class_mode, classes_set = _resolve_class_filter(get_class_filter())

    by_class = {}
    total = 0
    students_unknown = 0   # Schueler komplett ohne Stammdaten in beiden Quellen
    for er in erz_rows:
        if not _is_minor(er):
            continue
        sid = (er.get('Interne ID-Nummer', '') or '').strip()
        stamm = student_lookup.get(sid, {})
        # Klassen-Whitelist
        if not _student_passes_class(stamm, class_mode, classes_set):
            continue
        # Pro Kriterium pruefen + Gruende sammeln
        hits = [k for k in criteria if MISSING_CRITERIA[k]['test'](er, max_slots)]
        if not hits:
            continue
        if match_mode == 'all' and len(hits) != len(criteria):
            continue
        klasse   = stamm.get('klasse')   or '(ohne Klasse)'
        vorname  = stamm.get('vorname',  '')
        nachname = stamm.get('nachname', '')
        if not (vorname or nachname or klasse != '(ohne Klasse)'):
            students_unknown += 1
        by_class.setdefault(klasse, []).append({
            'id':       sid,
            'vorname':  vorname,
            'nachname': nachname,
            'reasons':  hits,
        })
        total += 1

    classes = []
    for k in sorted(by_class.keys()):
        students = sorted(by_class[k], key=lambda s: (s['nachname'].lower(), s['vorname'].lower()))
        classes.append({'klasse': k, 'count': len(students), 'students': students})

    return {
        'classes':            classes,
        'total_classes':      len(classes),
        'total_students':     total,
        'students_unknown':   students_unknown,
        'anspr_available':    anspr_available,
        'class_filter_mode':  class_mode,
        'source_file':        os.path.basename(erzieher_path),
        'criteria_used':      criteria,
        'available_criteria': available,
        'match_mode':         match_mode,
    }


def write_missing_report_zip(selected_classes=None, output_dir=None,
                             criteria=None, match_mode='any'):
    """Schreibt pro ausgewaehlter Klasse eine CSV mit den minderjaehrigen
    Schuelern ohne Erzieher-Daten und packt alles in ein ZIP.

    selected_classes: Liste der Klassennamen, die ins ZIP sollen.
                      None oder leer = alle.

    Returns: (zip_pfad, zip_name, count_dict)
    """
    output_dir = output_dir or get_output_dir()
    os.makedirs(output_dir, exist_ok=True)

    report = missing_erzieher_report(criteria=criteria, match_mode=match_mode)
    sel = set(selected_classes) if selected_classes else None
    chosen = [c for c in report['classes'] if (sel is None or c['klasse'] in sel)]
    if not chosen:
        raise ValueError("Keine Klassen ausgewaehlt oder keine Datensaetze vorhanden.")

    name = f"FehlendeErzieher_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.zip"
    zip_path = os.path.join(output_dir, name)

    # Labels fuer Gruende, kommagetrennt im CSV
    label_by_key = {k: v['label'] for k, v in MISSING_CRITERIA.items()}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for c in chosen:
            csv_buf = io.StringIO()
            writer = csv.writer(csv_buf, delimiter=';')
            writer.writerow(['Interne_ID_Nummer', 'Klasse', 'Nachname',
                             'Vorname', 'Gruende'])
            for s in c['students']:
                gruende = ', '.join(label_by_key.get(r, r) for r in s.get('reasons', []))
                writer.writerow([s['id'], c['klasse'], s['nachname'],
                                 s['vorname'], gruende])
            safe_klasse = re.sub(r'[<>:"/\\|?*]', '_', c['klasse'])
            zf.writestr(f"FehlendeErzieher_{safe_klasse}.csv",
                        csv_buf.getvalue().encode('utf-8-sig'))
    with open(zip_path, 'wb') as f:
        f.write(buf.getvalue())

    return zip_path, name, {
        'classes':  len(chosen),
        'students': sum(c['count'] for c in chosen),
        'criteria_used': report['criteria_used'],
        'match_mode':    report['match_mode'],
    }


def write_zip(result_files, output_dir=None, name_template=None):
    """Schreibt die Ergebnisdateien als ZIP in das Ausgabeverzeichnis.
    Liefert (zip_pfad, zip_name)."""
    output_dir = output_dir or get_output_dir()
    os.makedirs(output_dir, exist_ok=True)
    name_template = name_template or get_zip_name_template()
    zip_name = _resolve_zip_name(name_template)
    zip_path = os.path.join(output_dir, zip_name)
    # Bei Konflikt: Zeitstempel-Suffix
    if os.path.exists(zip_path):
        base, ext = os.path.splitext(zip_name)
        zip_name = f"{base}_{datetime.now().strftime('%H%M%S')}{ext}"
        zip_path = os.path.join(output_dir, zip_name)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname, file_data in result_files.items():
            csv_buf = io.StringIO()
            writer = csv.DictWriter(csv_buf, fieldnames=file_data['header'], delimiter=';')
            writer.writeheader()
            writer.writerows(file_data['rows'])
            zf.writestr(f"{fname}.csv", csv_buf.getvalue().encode('utf-8-sig'))
    with open(zip_path, 'wb') as f:
        f.write(buf.getvalue())
    return zip_path, zip_name


# ===========================================================================
# KL-Mail-Versand fuer den Erzieher-Workflow (3.3): Aktuelle Erzieher-/
# Ansprechpartner-ROHDATEN je Klasse an die Klassenlehrkraefte, zur Info +
# Kontrolle (Korrektur ueber das Sekretariat in Schild).
# ===========================================================================
#
# Designprinzip: "Rohdaten" = ohne Smart-Match, ohne Dummy-Fill, ohne
# E-Mail-Pflicht-Aussortierung. Pro Schueler ALLE Erzieher-Slots aus dem
# Erzieher-Export plus ALLE Telefon-Eintraege (primaere aus Erz, zusaetzliche
# aus Anspr) — das ist genau das, was die KL ggf. korrigieren lassen soll.
#
# Symmetrisch zum Ausbilder-KL-Mail-Feature (siehe ausbilder_processor):
# gleiche Settings-Strukturen, gleiches Route-Set, gleicher Vorschau-
# Klappbereich, gleicher dedizierter Vorlagen-Editor im Modul-Bereich.
# Unterschiede aus der Datenstruktur:
#   - mehrere Erzieher pro Schueler (statt 1 Firma + 1 Betreuer)
#   - mehrere Telefon-Nummern pro Schueler (Erz-Pseudo + Anspr-Zeilen)
#   - Volljaehrigkeit relevant (Volljaehrige haben i.d.R. keine Erzieher)
#
# Optionen (alle in [Erzieher]-Section):
#   kl_mail_respect_class_whitelist (bool, default True)
#   kl_mail_only_minor              (bool, default False) — Volljaehrige
#                                                            ausblenden
#   kl_mail_include_stv_kl          (bool, default True)
#   kl_mail_subject_suffix          (str, default '')
# ---------------------------------------------------------------------------

DEFAULT_ERZ_KL_MAIL_SUBJECT = (
    'Erzieher-/Ansprechpartner-Daten Ihrer Klasse $Klasse — Stand $Stand'
)
DEFAULT_ERZ_KL_MAIL_BODY = (
    '<p>Sehr geehrte/r $Klassenlehrer_Anrede $Klassenlehrer_Name,</p>'
    '<p>anbei die aktuell in Schild hinterlegten Erzieher-/Ansprechpartner-'
    'Daten Ihrer Klasse <strong>$Klasse</strong> (Stand $Stand) — '
    '<em>Rohdaten</em>, also genau so, wie sie aus Schild kommen (ohne '
    'Smart-Match, Dummy-Fill o.&nbsp;ä.).</p>'
    '<p><strong>Bitte prüfen</strong> Sie die Daten auf Vollständigkeit '
    '(insbesondere fehlende E-Mail-Adressen / fehlende zweite Eltern-'
    'datensätze) und veranlassen Sie ggf. eine Korrektur über das Sekretariat '
    'in Schild. Eine Excel-Datei mit denselben Daten finden Sie zusätzlich '
    'im Anhang (zur Weiterleitung an das Sekretariat oder zur Bearbeitung).</p>'
    '$Erzieher_Tabelle_HTML'
    '<p>Mit freundlichen Grüßen<br>'
    'Ihre WebUntis-Pflege</p>'
)


def get_kl_mail_respect_class_whitelist():
    """Klassen-Whitelist (analog Ausbilder) greift auch beim KL-Mail-Versand
    des Erzieher-Workflows."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'kl_mail_respect_class_whitelist', fallback=True)


def get_kl_mail_only_minor():
    """True = nur minderjaehrige Schueler in die KL-Mail-Tabelle (Volljaehrige
    haben i.d.R. keine Erzieher im klassischen Sinn — nur sich selbst als
    Self-Ansprechpartner). Default False, weil 'Rohdaten' bedeutet, auch
    diese Eintraege zu zeigen, damit die KL z.B. eine fehlende Vollj.-
    Markierung erkennt."""
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'kl_mail_only_minor', fallback=False)


def get_kl_mail_include_stv_kl():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.getboolean('Erzieher', 'kl_mail_include_stv_kl', fallback=True)


def get_kl_mail_subject_suffix():
    config = configparser.ConfigParser(interpolation=None)
    safe_read_config(config, 'settings.ini')
    return config.get('Erzieher', 'kl_mail_subject_suffix', fallback='').strip()


def save_kl_mail_settings(settings):
    """Bulk-Speichern aller KL-Mail-Einstellungen. Akzeptierte Keys siehe
    Modul-Docstring."""
    config = configparser.ConfigParser(interpolation=None)
    read_config_for_update(config, 'settings.ini')
    if not config.has_section('Erzieher'):
        config.add_section('Erzieher')
    for k in ('kl_mail_respect_class_whitelist', 'kl_mail_only_minor',
              'kl_mail_include_stv_kl'):
        if k in settings:
            config.set('Erzieher', k, 'True' if settings[k] else 'False')
    if 'kl_mail_subject_suffix' in settings:
        config.set('Erzieher', 'kl_mail_subject_suffix',
                   str(settings['kl_mail_subject_suffix'] or '').strip())
    with open('settings.ini', 'w', encoding='utf-8-sig') as f:
        config.write(f)


# ---------------------------------------------------------------------------
# Datenaufbereitung (Rohdaten — bewusst KEIN Smart-Match / Dummy-Fill)
# ---------------------------------------------------------------------------

def _extract_all_erzieher_slots(erz_row, max_slots):
    """Liefert alle gefuellten Erzieher-Slots eines Schueler-Erz-Rows als
    Liste von Dicts. 'Gefuellt' = mind. eine Stamm-Spalte (Vorname/Nachname/
    E-Mail/Anrede) hat Inhalt. Slot-Nummer (1..N) wird beibehalten, damit
    die KL nachvollziehen kann welcher Slot wo steht."""
    out = []
    for i in range(1, max_slots + 1):
        slot = {fld: (erz_row.get(f'Erzieher {i}: {fld}', '') or '').strip()
                for fld in ERZIEHER_FIELDS}
        if any(slot.values()):
            slot['nr'] = i
            out.append(slot)
    return out


def _collect_phone_rows(sid, erz_row, ansp_by_sid):
    """Sammelt alle Telefon-Eintraege fuer einen Schueler — primaere aus dem
    Erzieher-Export (Pseudo-Anspr-Zeile) PLUS alle aus dem Anspr-Export.
    Duplikate (gleiche normalisierte Nummer) werden entfernt; Reihenfolge:
    Erz-Pseudo zuerst, dann Anspr in CSV-Reihenfolge."""
    phones = []
    erz_phone = _erz_phone_pseudo(erz_row)
    if erz_phone:
        phones.append({
            'anschluss':  erz_phone.get('Anschluss-Art', ''),
            'bemerkung':  erz_phone.get('Bemerkung', ''),
            'telefon':    erz_phone.get('Telefon-Nummer', ''),
            'from_erz':   True,
        })
    seen_keys = {_normalize_phone(p['telefon']) for p in phones if p['telefon']}
    for a in ansp_by_sid.get(sid, []):
        nr = (a.get('Telefon-Nummer', '') or '').strip()
        if not nr:
            continue
        key = _normalize_phone(nr)
        if key and key in seen_keys:
            continue
        seen_keys.add(key)
        phones.append({
            'anschluss':  (a.get('Anschluss-Art', '') or '').strip(),
            'bemerkung':  (a.get('Bemerkung', '')      or '').strip(),
            'telefon':    nr,
            'from_erz':   False,
        })
    return phones


def _load_main_schueler_birthdates():
    """Liefert {sid: 'DD.MM.YYYY'} aus der Schueler-Hauptverarbeitung.
    Quelle automatisch ueber main.read_students() — wird zur Laufzeit
    entweder die CSV aus schildexport_directory einlesen ODER (wenn aktiv)
    die SVWS-API abfragen. Damit ist der Lookup transparent fuer beide Pfade.

    Bei Fehlern (Quelle nicht erreichbar, leere CSV, API-Timeout) wird ein
    leerer Lookup zurueckgegeben — build_kl_mail_data() faellt dann pro
    Schueler auf das Geburtsdatum aus der Erzieher-Quelle zurueck (sofern
    dort eines steht). Damit bleibt das Feature in jeder Konfiguration
    funktionsfaehig.

    Hinweis zu Performance/Logging: read_students() loggt Schritte auf der
    Konsole und kann im API-Modus einige Sekunden brauchen — pro
    KL-Mail-Preview/-Send wird der Call einmal gemacht."""
    try:
        from main import read_students
        _, students_by_id = read_students(use_abschlussdatum=False)
        out = {}
        for sid, data in (students_by_id or {}).items():
            geb = (data.get('Geburtsdatum') or '').strip()
            if geb and sid:
                out[str(sid).strip()] = geb
        return out
    except Exception:
        return {}


def build_kl_mail_data(classes_by_name=None, erzieher_path=None,
                       ansprechpartner_path=None):
    """Sammelt pro Klasse die KL-Mail-Daten — Rohdaten aus Erzieher-Export
    (+ optional Anspr-Export fuer mehr Telefonnummern).

    Args:
        classes_by_name: dict {klasse.lower(): {Klassenlehrkraft_1, ...}} aus
            main.read_classes(). None = leere Lookup, Empfaenger werden nicht
            aufgeloest (UI muss das anzeigen).
        erzieher_path / ansprechpartner_path: optional, sonst Resolver +
            Default-Verzeichnis.

    Returns dict mit:
        csv_path:     genutzte Erzieher-CSV
        anspr_path:   genutzte Anspr-CSV (oder None)
        classes:      [{klasse, kl_name, kl_email, stv_kl_name, stv_kl_email,
                         students: [{id, vorname, nachname, geburtsdatum,
                                     volljaehrig, erzieher_art, erzieher: [...],
                                     telefone: [...]}, ...]}, ...]
        stats:        {students_total, students_after_filters, classes_total,
                       classes_without_kl_email}
        options_used: {respect_class, only_minor, include_stv_kl, subject_suffix}
    """
    if erzieher_path is None:
        erzieher_path, _src = _resolve_erzieher_path()
    if not erzieher_path or not os.path.isfile(erzieher_path):
        raise FileNotFoundError("Keine Erzieher-Quelle gefunden (siehe Erzieher-Workflow-Status).")
    erz_rows = _read_csv_rows(erzieher_path)
    if not erz_rows:
        return {'csv_path': erzieher_path, 'anspr_path': None, 'classes': [],
                'stats': {'students_total': 0, 'students_after_filters': 0,
                          'classes_total': 0, 'classes_without_kl_email': 0},
                'options_used': {}}

    # Optional: Anspr-Export fuer mehr Telefonnummern.
    anspr_path = ansprechpartner_path or _latest_csv(get_ansprechpartner_export_dir())
    ansp_rows = []
    if anspr_path and os.path.isfile(anspr_path):
        try:
            ansp_rows = _read_csv_rows(anspr_path)
        except Exception:
            ansp_rows = []
    ansp_by_sid = {}
    for r in ansp_rows:
        ansp_by_sid.setdefault((r.get('Schüler_ID', '') or '').strip(), []).append(r)

    # Filter-Optionen
    respect_class    = get_kl_mail_respect_class_whitelist()
    only_minor       = get_kl_mail_only_minor()
    include_stv_kl   = get_kl_mail_include_stv_kl()
    subject_suffix   = get_kl_mail_subject_suffix()

    # Klassen-Whitelist auswerten (gleiche Sentinel-Logik wie process())
    class_mode, classes_set = _resolve_class_filter(get_class_filter())

    # Schueler-Stammdaten (Klasse / Vorname / Nachname) kombinieren —
    # gleiche Quelle wie preview()/missing_report.
    student_lookup = _merge_student_lookups(
        _student_lookup_from_anspr(anspr_path),
        _student_lookup_from_erz(erz_rows),
    )

    # Geburtsdatum-Lookup PRIMAER aus der Schueler-Hauptverarbeitung
    # (schildexport_directory bzw. SVWS-API). Erzieher-Quelle bleibt als
    # Fallback — siehe Pro-Schueler-Block unten.
    main_birthdates = _load_main_schueler_birthdates()
    geb_source_stats = {'main_schueler': 0, 'erzieher_quelle': 0, 'none': 0}

    # Max-Slot-Nr fuer Erzieher-Slots aus dem Header
    max_slots = 0
    for col in (erz_rows[0].keys() if erz_rows else []):
        m = re.match(r'Erzieher\s+(\d+):', col)
        if m:
            max_slots = max(max_slots, int(m.group(1)))

    students_total = 0
    students_after_filters = 0
    by_class = {}
    for er in erz_rows:
        sid = (er.get('Interne ID-Nummer', '') or '').strip()
        if not sid:
            continue
        students_total += 1
        stamm = student_lookup.get(sid, {})
        # Klassen-Whitelist respektieren
        if respect_class and not _student_passes_class(stamm, class_mode, classes_set):
            continue
        # Geburtsdatum-Auflösung in zwei Stufen:
        #   1) PRIMAER aus dem Haupt-Schueler-Datensatz (CSV-Hauptverzeichnis
        #      oder SVWS-API) — das ist die kanonische Quelle, die immer
        #      gepflegt sein sollte.
        #   2) FALLBACK aus der Erzieher-Quelle (wie bisher) — falls die
        #      Hauptquelle nicht erreichbar ist ODER die Schueler-ID dort
        #      nicht auftaucht (Stale-Erzieher-Eintrag o.ae.).
        # Quelle wird auf jedem Student-Entry vermerkt (geb_source), damit die
        # KL in der UI/Mail Transparenz hat woher das Datum kommt.
        geb_str_main = main_birthdates.get(sid, '')
        geb_str_erz = ''
        for col in _GEBURTSDATUM_COLS:
            v = (er.get(col, '') or '').strip()
            if v:
                geb_str_erz = v
                break
        if geb_str_main:
            geb_str = geb_str_main
            geb_source = 'main_schueler'
        elif geb_str_erz:
            geb_str = geb_str_erz
            geb_source = 'erzieher_quelle'
        else:
            geb_str = ''
            geb_source = None
        geb_source_stats[geb_source or 'none'] += 1
        geb_parsed = None
        for fmt in ('%d.%m.%Y', '%Y-%m-%d'):
            try:
                geb_parsed = datetime.strptime(geb_str, fmt).date() if geb_str else None
                if geb_parsed:
                    break
            except (ValueError, TypeError):
                continue
        # Per Geburtsdatum (deterministisch, None wenn nicht parsbar):
        age = _calc_age_from_str(geb_str) if geb_str else None
        vollj_per_geb    = (age is not None and age >= 18)
        vollj_per_geb_known = (age is not None)
        # Per Schild-Heuristik (Spaltenwert 'Erzieher: Art (Klartext)'):
        erz_art       = (er.get('Erzieher: Art (Klartext)', '') or '').strip()
        vollj_per_schild = ('volljährig' in erz_art.lower()
                            or 'volljaehrig' in erz_art.lower())
        # Kombiniert (wie bisher): True wenn eine der beiden Quellen anschlaegt.
        is_vollj = vollj_per_geb or vollj_per_schild
        if only_minor and is_vollj:
            continue
        students_after_filters += 1
        klasse = stamm.get('klasse', '') or '(ohne Klasse)'
        student_entry = {
            'id':            sid,
            'vorname':       stamm.get('vorname', '')  or (er.get('Vorname', '')  or '').strip(),
            'nachname':      stamm.get('nachname', '') or (er.get('Nachname', '') or '').strip(),
            'geburtsdatum':         geb_str,
            'geburtsdatum_parsed':  geb_parsed,   # datetime.date oder None — fuer Excel
            'geburtsdatum_source':  geb_source,   # 'main_schueler' | 'erzieher_quelle' | None
            'volljaehrig':              is_vollj,
            'volljaehrig_per_geb':      vollj_per_geb,
            'volljaehrig_per_geb_known': vollj_per_geb_known,
            'volljaehrig_per_schild':   vollj_per_schild,
            # Konflikt = Schild sagt volljaehrig, Geburtsdatum (sofern bekannt)
            # sagt minderjaehrig. Anderer Fall (Schild leer + Geb-Datum sagt
            # volljaehrig) ist kein Fehler — Schild markiert das oft nicht.
            'volljaehrig_konflikt':     (vollj_per_schild and vollj_per_geb_known and not vollj_per_geb),
            'erzieher_art':  erz_art,
            'erzieher':      _extract_all_erzieher_slots(er, max_slots),
            'telefone':      _collect_phone_rows(sid, er, ansp_by_sid),
            # Roh-Zugriff fuer die KL-Mail-Tabelle 'alle Spalten als Zeilen'
            'raw_erz_row':   dict(er),
            'raw_ansp_rows': [dict(r) for r in ansp_by_sid.get(sid, [])],
        }
        by_class.setdefault(klasse, []).append(student_entry)

    # KL-Lookup
    classes_by_name = classes_by_name or {}
    classes_out = []
    classes_without_kl_email = 0
    for klasse, students in sorted(by_class.items()):
        students.sort(key=lambda s: (s['nachname'].lower(), s['vorname'].lower()))
        klasse_lower = klasse.lower()
        kl_info = classes_by_name.get(klasse_lower, {}) or {}
        kl_email     = (kl_info.get('Klassenlehrkraft_1_Email') or '').strip()
        stv_kl_email = (kl_info.get('Klassenlehrkraft_2_Email') or '').strip() if include_stv_kl else ''
        if kl_email == 'Keine E-Mail gefunden':     kl_email = ''
        if stv_kl_email == 'Keine E-Mail gefunden': stv_kl_email = ''
        if not kl_email:
            classes_without_kl_email += 1
        classes_out.append({
            'klasse':       klasse,
            'kl_name':      (kl_info.get('Klassenlehrkraft_1') or '').strip(),
            'kl_email':     kl_email,
            'stv_kl_name':  (kl_info.get('Klassenlehrkraft_2') or '').strip(),
            'stv_kl_email': stv_kl_email,
            'students':     students,
        })

    return {
        'csv_path':   erzieher_path,
        'anspr_path': anspr_path if (anspr_path and os.path.isfile(anspr_path)) else None,
        'classes':    classes_out,
        'stats': {
            'students_total':           students_total,
            'students_after_filters':   students_after_filters,
            'classes_total':            len(classes_out),
            'classes_without_kl_email': classes_without_kl_email,
            # Transparenz: Quell-Verteilung des Geburtsdatums (main vs. fallback
            # vs. komplett unbekannt). Frontend kann daraus anzeigen, wieviele
            # Schueler ueber den Haupt-Schueler-Datensatz / Fallback / gar nicht
            # versorgt wurden — laesst Pflege-Luecken im Schild-Export erkennen.
            'geb_source_main_schueler':   geb_source_stats.get('main_schueler', 0),
            'geb_source_erzieher_quelle': geb_source_stats.get('erzieher_quelle', 0),
            'geb_source_none':            geb_source_stats.get('none', 0),
        },
        'options_used': {
            'respect_class':   respect_class,
            'only_minor':      only_minor,
            'include_stv_kl':  include_stv_kl,
            'subject_suffix':  subject_suffix,
        },
    }


# ---------------------------------------------------------------------------
# HTML-Tabelle + Subject/Body-Rendering
# ---------------------------------------------------------------------------

def _kl_anrede_short_erz(kl_full_name):
    """Anrede-Heuristik aus dem Vornamen — analog ausbilder_processor."""
    if not kl_full_name:
        return ''
    first = kl_full_name.strip().split(' ', 1)[0]
    if first.endswith(('a', 'e', 'i')) and len(first) > 2:
        return 'Frau'
    return 'Herr'


def _html_escape_erz(s):
    """Minimaler HTML-Escape (duplikat zu ausbilder_processor — bewusst, um
    keine Cross-Modul-Importe einzufuehren)."""
    s = str(s or '')
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace('"', '&quot;'))


def _build_mailto_url(email, briefanrede='', nachname=''):
    """Baut einen mailto:-Link mit URL-codiertem Body, in dem die Briefanrede
    + Nachname bereits stehen. Klick im Mail-Client startet die Mail mit der
    Anrede vorbefuellt — Cursor landet auf der ersten Leerzeile nach dem
    Komma. Funktioniert in Outlook / Gmail-Web / Thunderbird / Apple Mail.

    Fallbacks bei fehlenden Daten:
        - Briefanrede + Nachname da:           'Briefanrede Nachname,\\n\\n'
        - Nur Briefanrede:                      'Briefanrede,\\n\\n'
        - Nur Nachname:                         'Sehr geehrte/r Herr/Frau Nachname,\\n\\n'
        - Beide fehlen:                         'Sehr geehrte Damen und Herren,\\n\\n'
    """
    import urllib.parse
    email = (email or '').strip()
    if not email:
        return ''
    briefanrede = (briefanrede or '').strip()
    nachname = (nachname or '').strip()
    if briefanrede and nachname:
        greeting = f"{briefanrede} {nachname},\n\n"
    elif briefanrede:
        greeting = f"{briefanrede},\n\n"
    elif nachname:
        greeting = f"Sehr geehrte/r Herr/Frau {nachname},\n\n"
    else:
        greeting = "Sehr geehrte Damen und Herren,\n\n"
    return f"mailto:{email}?body={urllib.parse.quote(greeting)}"


def _build_bulk_mailto_url(emails, generic_greeting='Sehr geehrte Damen und Herren'):
    """Sammel-mailto fuer eine Liste von Adressen — alle landen im BCC, Body
    enthaelt eine generische Anrede. Fuer den Klick auf die Direkt-Listen-Zelle
    im Mailverteiler-Sheet.

    Hinweis: einige Mail-Clients begrenzen die URL-Laenge (Outlook ~2000
    Zeichen). Bei sehr grossen Verteilern bricht das ggf. ab — die Direkt-
    Liste in der Zelle bleibt aber als Copy-Paste-Quelle in jedem Fall
    nutzbar (das ist der primaere Anwendungsfall)."""
    import urllib.parse
    emails = [e for e in (emails or []) if e and '@' in e]
    if not emails:
        return ''
    bcc_str = ','.join(emails)
    body = f"{generic_greeting},\n\n"
    return (f"mailto:?bcc={urllib.parse.quote(bcc_str)}"
            f"&body={urllib.parse.quote(body)}")


def render_erzieher_table_html(students, stand_date=None):
    """Baut die HTML-Tabelle fuer den Mail-Body — 3 Spalten:
       (1) Schueler  (2) Erzieher Rohdaten  (3) Ansprechpartner Rohdaten
    In den Roh-Spalten werden ALLE Spalten der jeweiligen CSV-Zeile als
    'Spaltenname: Wert'-Zeilen aufgelistet (Pflicht- + optional-Felder), so
    dass die KL exakt sieht, was in Schild hinterlegt ist — auch leere Felder.
    Inline-Styles fuer Outlook/Gmail/Thunderbird-Kompatibilitaet."""
    if not students:
        return '<p><em>Keine Schueler in dieser Klasse nach den aktiven Filtern.</em></p>'
    stand_date = stand_date or datetime.now().strftime('%d.%m.%Y')
    th = ('background:#f0f0f0; border:1px solid #ccc; padding:6px 8px; '
          'text-align:left; font-size:0.9em;')
    td = 'border:1px solid #ccc; padding:5px 8px; font-size:0.85em; vertical-align:top;'
    out = ['<table style="border-collapse:collapse; border:1px solid #ccc; '
           'margin:8px 0; width:100%; table-layout:fixed;">']
    out.append('<thead><tr>'
               f'<th style="{th} width:18%;">Schüler</th>'
               f'<th style="{th} width:41%;">Erzieher Rohdaten</th>'
               f'<th style="{th} width:41%;">Ansprechpartner Rohdaten</th>'
               '</tr></thead><tbody>')
    for s in students:
        schueler_cell = _format_schueler_meta_html(s, stand_date)
        erz_html      = _format_erz_rohdaten_html(s.get('raw_erz_row') or {})
        ansp_html     = _format_anspr_rohdaten_html(s.get('raw_ansp_rows') or [])
        out.append('<tr>'
                   f'<td style="{td}">{schueler_cell}</td>'
                   f'<td style="{td}">{erz_html}</td>'
                   f'<td style="{td}">{ansp_html}</td>'
                   '</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


def _format_schueler_meta_html(s, stand_date):
    """Linke Spalte: Name, ID, Geb-Datum, Volljaehrig-Status (mit Quellenangabe
    + Konflikt-Marker), Erzieher-Art (Klartext) wenn vorhanden."""
    parts = []
    parts.append(f'<strong>{_html_escape_erz(s["nachname"])}, {_html_escape_erz(s["vorname"])}</strong>')
    parts.append(f'<div style="color:#888; font-size:0.85em;">ID {_html_escape_erz(s["id"])}</div>')
    # Geburtsdatum + Quell-Hinweis: 'main_schueler' (primaer, kein Marker noetig),
    # 'erzieher_quelle' (Fallback — diskreter grauer Hinweis), None (keine Quelle).
    geb_src = s.get('geburtsdatum_source')
    if geb_src == 'erzieher_quelle':
        src_hint = ' <span style="color:#888; font-size:0.75em;" title="Aus dem Erzieher-Export gezogen — die Schüler-Hauptverarbeitung lieferte für diese ID nichts.">(Quelle: Erzieher-Export)</span>'
    elif geb_src is None and s.get('geburtsdatum'):
        # Quelle leer aber Wert da? Sollte nicht passieren, sicherheitshalber neutral.
        src_hint = ''
    else:
        src_hint = ''
    parts.append(f'<div style="margin-top:4px;"><strong>🎂</strong> {_html_escape_erz(s["geburtsdatum"] or "—")}{src_hint}</div>')
    # Volljaehrigkeit: explizit MIT Quellenangabe (Geburtsdatum vs. Schild-
    # Heuristik), damit die KL erkennt warum 'volljaehrig' steht — und vor
    # allem ob ein Konflikt vorliegt (Schild markiert, Geb-Datum widerspricht).
    if s.get('volljaehrig_konflikt'):
        parts.append('<div style="margin-top:4px; padding:3px 5px; background:#fff3cd; border:1px solid #ffc107; border-radius:3px; font-size:0.85em;">'
                     '<strong>⚠️ Konflikt:</strong> Schild markiert als <em>volljährig</em>, das Geburtsdatum sagt aber <strong>minderjährig</strong>. '
                     'Bitte in Schild prüfen/korrigieren.</div>')
    elif s.get('volljaehrig_per_geb_known'):
        # Deterministischer Fall: Geb-Datum kennen wir.
        label = 'ja' if s['volljaehrig_per_geb'] else 'nein'
        color = '#c0392b' if s['volljaehrig_per_geb'] else '#27ae60'
        parts.append(f'<div style="margin-top:4px;"><strong>Volljährig (per Geburtsdatum, Stand {_html_escape_erz(stand_date)}):</strong> '
                     f'<span style="color:{color}; font-weight:bold;">{label}</span></div>')
        if s['volljaehrig_per_schild'] and not s['volljaehrig_per_geb']:
            # Eigentlich schon im Konflikt-Block oben — dieser Pfad sollte
            # nicht erreicht werden. Defensive.
            pass
    else:
        # Geb-Datum fehlt: Fallback Schild-Heuristik mit deutlichem Marker.
        if s['volljaehrig_per_schild']:
            parts.append('<div style="margin-top:4px;"><strong>Volljährig:</strong> '
                         '<span style="color:#c0392b; font-weight:bold;">ja*</span> '
                         '<span style="color:#888; font-size:0.85em;">(nur per Schild-Markierung — kein Geburtsdatum hinterlegt!)</span></div>')
        else:
            parts.append('<div style="margin-top:4px; padding:3px 5px; background:#fff3cd; border:1px solid #ffc107; border-radius:3px; font-size:0.85em;">'
                         '<strong>⚠️ Geburtsdatum fehlt</strong> — Volljährigkeit kann nicht eindeutig bestimmt werden.</div>')
    if s.get('erzieher_art'):
        parts.append(f'<div style="margin-top:4px; color:#666; font-size:0.85em;"><em>Erzieher: Art (Klartext) = {_html_escape_erz(s["erzieher_art"])}</em></div>')
    return ''.join(parts)


# Kolumnen, die wir in der Erzieher-Rohdaten-Zelle als 'fuer den Erzieher-
# Workflow relevant' anzeigen. Filter wird auf den raw_erz_row Schluesseln
# angewendet — Schueler-Stamm-Spalten (Klasse/Vorname/Nachname/Geburtsdatum/
# Interne ID-Nummer) werden ausgeblendet, weil sie schon in der linken Spalte
# stehen oder dort impliziert sind.
_HIDDEN_ERZ_ROHDATEN_COLS = {
    'Interne ID-Nummer', 'Klasse', 'Schüler-Klasse', 'Schüler: Klasse',
    'Vorname', 'Schüler-Vorname', 'Schüler: Vorname',
    'Nachname', 'Schüler-Nachname', 'Schüler: Nachname',
    'Geburtsdatum', 'Schüler-Geburtsdatum', 'Schüler: Geburtsdatum',
    'Schüler-Jahrgang',
}


def _format_erz_rohdaten_html(erz_row):
    """Listet alle Erzieher-relevanten Spalten der erz_row auf — gruppiert
    nach Erzieher-Slot ('Erzieher 1: ...', 'Erzieher 2: ...', ...) plus
    eigener Block fuer globale 'Erzieher: ...'-Spalten."""
    if not erz_row:
        return '<em style="color:#888;">—</em>'
    # Slot-spezifische Spalten gruppieren
    slot_groups = {}  # int -> [(col_full, col_short, value), ...]
    global_cols = []  # [(col, value), ...] fuer 'Erzieher: ...' + 'Erhält Anschreiben'
    other_cols  = []  # alle anderen erlaubten Spalten
    for k, v in erz_row.items():
        if k in _HIDDEN_ERZ_ROHDATEN_COLS:
            continue
        m = re.match(r'Erzieher\s+(\d+):\s*(.+)$', k)
        if m:
            slot_idx = int(m.group(1))
            col_short = m.group(2)
            slot_groups.setdefault(slot_idx, []).append((col_short, v))
            continue
        if k.startswith('Erzieher:') or k == 'Erhält Anschreiben' \
                or k in ('Ortsname', 'Postleitzahl', 'Straße', 'Ortsteil',
                         'Postleitzahl-Land'):
            global_cols.append((k, v))
            continue
        # andere Spalten ueberspringen (waeren Schueler-spezifisch)
    out = []
    for slot_idx in sorted(slot_groups.keys()):
        cols = slot_groups[slot_idx]
        any_filled = any(v for _, v in cols)
        if not any_filled:
            continue  # leere Slots nicht anzeigen — wuerden die Zelle aufblaehen
        # Briefanrede + Nachname dieses Slots fuer die mailto-Link-Generierung
        # in _format_kv_list_html extrahieren — KL bekommt beim Klick eine
        # Mail mit korrekter Anrede vorbefuellt.
        slot_briefanrede = ''
        slot_nachname = ''
        for k, v in cols:
            if k.lower() == 'briefanrede' and v: slot_briefanrede = v.strip()
            if k.lower() == 'nachname'    and v: slot_nachname    = v.strip()
        out.append(f'<div style="margin-bottom:6px; padding:4px 6px; background:#f4f4f4; border-left:3px solid #6f42c1; border-radius:2px;">')
        out.append(f'<strong style="color:#6f42c1;">Erzieher {slot_idx}</strong>')
        out.append(_format_kv_list_html(cols, briefanrede_ctx=slot_briefanrede,
                                         nachname_ctx=slot_nachname))
        out.append('</div>')
    if global_cols and any(v for _, v in global_cols):
        out.append(f'<div style="margin-bottom:6px; padding:4px 6px; background:#eef4f8; border-left:3px solid #17a2b8; border-radius:2px;">')
        out.append('<strong style="color:#17a2b8;">Allgemein (Erzieher-Stamm)</strong>')
        out.append(_format_kv_list_html(global_cols))
        out.append('</div>')
    if not out:
        return '<em style="color:#c0392b;">⚠️ Keine Erzieher-Daten</em>'
    return '\n'.join(out)


# Spalten die in der Anspr-Rohdaten-Zelle ausgeblendet werden (Schueler-Stamm,
# der schon links steht).
_HIDDEN_ANSPR_ROHDATEN_COLS = {
    'Schüler_ID', 'Schüler-ID', 'Interne ID-Nummer',
    'Schüler-Klasse', 'Schueler-Klasse', 'Klasse',
    'Schüler-Vorname', 'Schueler-Vorname', 'Vorname',
    'Schüler-Nachname', 'Schueler-Nachname', 'Nachname',
}


def _format_anspr_rohdaten_html(anspr_rows):
    """Pro Anspr-Zeile eine Box mit ALLEN Spalten als 'Spaltenname: Wert'-
    Zeilen. Schueler-Stamm-Spalten weggelassen (links bereits sichtbar)."""
    if not anspr_rows:
        return ('<em style="color:#888;">— Keine Eintraege im Ansprechpartner-'
                'Export (oder Anspr-CSV gar nicht geladen)</em>')
    out = []
    for i, row in enumerate(anspr_rows, 1):
        cols = [(k, v) for k, v in row.items()
                if k not in _HIDDEN_ANSPR_ROHDATEN_COLS]
        out.append(f'<div style="margin-bottom:6px; padding:4px 6px; background:#f4f4f4; border-left:3px solid #28a745; border-radius:2px;">')
        out.append(f'<strong style="color:#28a745;">Anspr-Zeile #{i}</strong>')
        out.append(_format_kv_list_html(cols))
        out.append('</div>')
    return '\n'.join(out)


def _format_kv_list_html(cols, briefanrede_ctx='', nachname_ctx=''):
    """Liste von (Spaltenname, Wert)-Tupeln als kompakte HTML-Liste —
    leere Werte werden als '—' grau dargestellt, damit man sieht dass die
    Spalte da ist aber nicht gefuellt wurde.

    briefanrede_ctx + nachname_ctx: optionaler Kontext fuer mailto-Links.
    Wenn gesetzt, werden E-Mail-Felder als 'mailto:?body=Briefanrede Nachname,'
    gerendert — KL klickt und die Mail oeffnet sich mit vorausgefuellter
    Anrede (siehe _build_mailto_url)."""
    if not cols:
        return ''
    out = ['<ul style="margin:3px 0 0 0; padding-left:16px; list-style:none;">']
    for k, v in cols:
        if v:
            # E-Mail-Spalten anklickbar — bei Erzieher-Slot-Kontext mit
            # vorgefuelltem Body (Briefanrede + Nachname); sonst nur die
            # E-Mail-Adresse selbst als mailto.
            v_html = _html_escape_erz(v)
            if 'E-Mail' in k or 'e-mail' in k.lower():
                mailto_url = _build_mailto_url(v, briefanrede_ctx, nachname_ctx)
                if mailto_url:
                    v_html = (f'<a href="{_html_escape_erz(mailto_url)}" '
                              f'title="Mail öffnen mit vorausgefüllter Briefanrede">'
                              f'{v_html}</a>')
            out.append(f'<li style="margin-bottom:1px;"><span style="color:#666; font-size:0.9em;">{_html_escape_erz(k)}:</span> {v_html}</li>')
        else:
            out.append(f'<li style="margin-bottom:1px;"><span style="color:#666; font-size:0.9em;">{_html_escape_erz(k)}:</span> <span style="color:#bbb;">—</span></li>')
    out.append('</ul>')
    return '\n'.join(out)


def render_kl_mail(class_data, subject_template=None, body_template=None,
                   stand_date=None, subject_suffix=''):
    """Setzt die Platzhalter in Subject + Body ein. Symmetrisch zur
    ausbilder_processor-Variante; eigene Platzhalter
    $Erzieher_Tabelle_HTML + $Schueler_Anzahl."""
    subject_template = subject_template or DEFAULT_ERZ_KL_MAIL_SUBJECT
    body_template    = body_template    or DEFAULT_ERZ_KL_MAIL_BODY
    stand_date       = stand_date       or datetime.now().strftime('%d.%m.%Y')
    kl_full          = class_data.get('kl_name') or ''
    kl_anrede        = _kl_anrede_short_erz(kl_full)
    students = class_data.get('students', [])
    repl_pairs = [
        ('$Erzieher_Tabelle_HTML', render_erzieher_table_html(students, stand_date=stand_date)),
        ('$Klassenlehrer_Anrede',  kl_anrede),
        ('$Klassenlehrer_Name',    kl_full),
        ('$Klassenlehrer_E-Mail',  class_data.get('kl_email', '')),
        ('$Schueler_Anzahl',       str(len(students))),
        ('$Klasse',                class_data.get('klasse', '')),
        ('$Stand',                 stand_date),
    ]
    subject = subject_template
    body    = body_template
    for k, v in repl_pairs:
        subject = subject.replace(k, v)
        body    = body.replace(k, v)
    if subject_suffix:
        subject = f"{subject_suffix} {subject}".strip()
    return subject, body


# ---------------------------------------------------------------------------
# Excel-Anhang (2 Sheets: Erzieher (1 Zeile pro Slot) + Telefonnummern)
# ---------------------------------------------------------------------------

def build_kl_mail_xlsx(class_data, stand_date=None):
    """Erzeugt eine xlsx-Mappe (in-memory bytes) mit zwei Sheets:
      Sheet 1 'Erzieher':       1 Zeile pro Erzieher-Slot (Schueler-Spalten wiederholt)
      Sheet 2 'Telefonnummern': 1 Zeile pro Telefonnummer
    Beide Sheets filterbar (Autofilter), Freeze Panes ueber dem Header.
    Schueler ohne Erzieher / ohne Telefon werden trotzdem mit aufgenommen
    (Spalten leer) — sonst wuerden Luecken im Sheet verschwinden."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment
    import io

    stand_date = stand_date or datetime.now().strftime('%d.%m.%Y')
    wb = Workbook()

    # --- Sheet 1: Erzieher -------------------------------------------------
    ws1 = wb.active
    ws1.title = 'Erzieher'
    ws1['A1'] = f"Erzieher-/Ansprechpartner-Daten Klasse {class_data.get('klasse', '')}"
    ws1['A1'].font = Font(bold=True, size=13)
    ws1['A2'] = f"Stand: {stand_date}"
    ws1['A2'].font = Font(italic=True, size=10)
    kl_line = []
    if class_data.get('kl_name'):
        kl_line.append(f"KL: {class_data['kl_name']}")
    if class_data.get('stv_kl_name'):
        kl_line.append(f"Stv-KL: {class_data['stv_kl_name']}")
    if kl_line:
        ws1['A3'] = ' · '.join(kl_line)
        ws1['A3'].font = Font(italic=True, size=10)
    # Legende in Zeile 4 — erklaert den wichtigen Unterschied zwischen den zwei
    # Volljaehrigkeits-Spalten: dynamisch berechnet vs. statischer Schild-Stand.
    # Ueber 7 Spalten gemerged, damit der Text in voller Laenge lesbar ist.
    ws1['A4'] = (
        'ℹ️ "Volljährig (heute)" wird dynamisch aus dem Geburtsdatum per Excel-Formel '
        'berechnet (HEUTE/TODAY) und ist deshalb beim Öffnen immer aktuell. '
        '"Erzieher: Art" hingegen stammt statisch aus dem Schild-Export und zeigt '
        'NUR den Stand des oben angegebenen Datums — in Schild wird diese Markierung '
        'i.d.R. nachgehalten, in dieser Excel-Datei nicht.'
    )
    ws1['A4'].font = Font(italic=True, size=9, color='555555')
    ws1['A4'].alignment = Alignment(wrap_text=True, vertical='top')
    ws1.merge_cells(start_row=4, start_column=1, end_row=4, end_column=7)
    ws1.row_dimensions[4].height = 38

    header_row = 5
    # Layout: 1 Zeile pro Schueler, links die Stammdaten, dann pro Erzieher-Slot
    # ein eigener Spaltenblock (Anrede / Titel / Vorname / Nachname / Briefanrede
    # / E-Mail). Spiegelt 1:1 das Schild-Schueler-Export-Schema und macht die
    # Erzieher-1-/Erzieher-2-Zuordnung sofort sichtbar — ohne dass man pro
    # Schueler durch zwei Zeilen scrollen muss.
    # Mehrzeilige Header-Texte mit '\n' — kombiniert mit wrap_text=True + ueber
    # Row-Height-Anpassung sichtbar gemacht. Damit passt 'Volljährig (heute)'
    # auch ohne uebermaessig breite Spalte rein, und die Stand-Export-Praezisierung
    # bei 'Erzieher: Art' steht direkt im Header (Cell-Comment fuer Details unten).
    STAMM_HEADERS = [
        'Schüler-ID', 'Klasse', 'Nachname', 'Vorname',
        'Geb.-Datum',
        'Volljährig\n(heute,\nformelberechnet)',
        'Erzieher: Art\n(Klartext, Stand\nletzter Export)',
    ]
    ERZ_SLOT_SUFFIXES = ['Anrede', 'Titel', 'Vorname', 'Nachname',
                         'Briefanrede', 'E-Mail']
    # Slot-Breite klassenweit ermitteln (mind. 2 = Schild-Standard, damit das
    # Reihen-Layout ueber Klassen hinweg stabil bleibt — KL kennt das
    # Format nach der ersten Mail).
    students = class_data.get('students', [])
    max_slots = 2
    for s in students:
        for e in s.get('erzieher', []):
            n = e.get('nr')
            if isinstance(n, int) and n > max_slots:
                max_slots = n

    headers1 = list(STAMM_HEADERS)
    for i in range(1, max_slots + 1):
        for sfx in ERZ_SLOT_SUFFIXES:
            headers1.append(f'Erzieher {i}: {sfx}')

    # Header-Styling: Stamm-Block grau, Slot-Bloecke je nach Slot-Nummer
    # farblich abgehoben — Auge erkennt sofort welche Spalte zu welchem
    # Erzieher gehoert. Pastell-Farben, damit's nicht knallt.
    stamm_fill = PatternFill('solid', fgColor='DDDDDD')
    slot_fills = [
        PatternFill('solid', fgColor='D6EAF8'),  # Slot 1 — hellblau
        PatternFill('solid', fgColor='D5F5E3'),  # Slot 2 — hellgruen
        PatternFill('solid', fgColor='FDEBD0'),  # Slot 3 — hellorange
        PatternFill('solid', fgColor='FADBD8'),  # Slot 4 — hellrosa
        PatternFill('solid', fgColor='E8DAEF'),  # Slot 5 — helllila
    ]
    from openpyxl.comments import Comment
    header_font = Font(bold=True)
    for ci, h in enumerate(headers1, 1):
        c = ws1.cell(row=header_row, column=ci, value=h)
        c.font = header_font
        if ci <= len(STAMM_HEADERS):
            c.fill = stamm_fill
        else:
            slot_idx = (ci - len(STAMM_HEADERS) - 1) // len(ERZ_SLOT_SUFFIXES)
            c.fill = slot_fills[slot_idx % len(slot_fills)]
        c.alignment = Alignment(vertical='top', wrap_text=True, horizontal='left')
    # Cell-Comments fuer die zwei besonderen Spalten — Detail-Tooltip beim
    # Hover, damit der Header schmal bleiben kann und die Erklaerung trotzdem
    # an der Zelle haftet.
    ws1.cell(row=header_row, column=6).comment = Comment(
        'Diese Spalte wird beim Öffnen der Datei dynamisch aus dem '
        'Geburtsdatum berechnet (Formel: DATEDIF mit TODAY). Der Wert ist '
        'also immer aktuell — auch wenn die Datei Wochen oder Monate später '
        'geöffnet wird.',
        'KL-Mail-Tool')
    ws1.cell(row=header_row, column=7).comment = Comment(
        'Diese Markierung kommt 1:1 aus dem Schild-Export — also dem Stand, '
        'der oben unter "Stand:" steht. In Schild wird diese Angabe i.d.R. '
        'aktualisiert (z.B. wenn ein Schüler 18 wird), in dieser Excel-Datei '
        'aber NICHT — die zeigt nur den Stand vom Export-Zeitpunkt.\n\n'
        'Für eine immer aktuelle Volljährigkeit siehe Spalte links '
        '("Volljährig (heute)").',
        'KL-Mail-Tool')
    # Header-Zeile hoeher, damit die 3 Zeilen in den Multi-Line-Headern sichtbar
    # sind (Volljaehrig (heute, formelberechnet) und Erzieher: Art (Klartext,
    # Stand letzter Export) brauchen je 3 Zeilen).
    ws1.row_dimensions[header_row].height = 45

    klasse_name = class_data.get('klasse', '')
    row_idx = header_row + 1
    for s in students:
        # Stamm-Block (Spalten 1-7)
        ws1.cell(row=row_idx, column=1, value=s.get('id', ''))
        ws1.cell(row=row_idx, column=2, value=klasse_name)
        ws1.cell(row=row_idx, column=3, value=s.get('nachname', ''))
        ws1.cell(row=row_idx, column=4, value=s.get('vorname', ''))
        # Geburtsdatum: echtes date-Objekt wenn parsbar, sonst Roh-String.
        # Damit funktioniert die Volljaehrig-Formel in Spalte F mit DATEDIF
        # und Excel zeigt das Datum lokalisiert (Number-Format DD.MM.YYYY).
        geb_p = s.get('geburtsdatum_parsed')
        geb_cell = ws1.cell(row=row_idx, column=5)
        if geb_p is not None:
            geb_cell.value = geb_p
            geb_cell.number_format = 'DD.MM.YYYY'
        else:
            geb_cell.value = s.get('geburtsdatum', '')
        # Volljaehrig: dynamische Formel, damit auch bei spaeterem Oeffnen der
        # Mappe das Alter aktuell ausgewertet wird. Englische Funktionsnamen
        # (Excel lokalisiert sie beim Anzeigen).
        vollj_cell = ws1.cell(row=row_idx, column=6)
        vollj_cell.value = (
            f'=IF(ISNUMBER(E{row_idx}),'
            f'IF(DATEDIF(E{row_idx},TODAY(),"Y")>=18,"ja","nein"),"?")'
        )
        ws1.cell(row=row_idx, column=7, value=s.get('erzieher_art', ''))
        # Erzieher-Slots (Spalten 8 aufwaerts) — pro Slot ein 6er-Block. Wenn
        # ein Schueler den Slot nicht gefuellt hat, bleiben die Zellen leer.
        # E-Mail-Spalte pro Slot wird zum Hyperlink (mailto: mit body= +
        # Briefanrede + Nachname dieses Slots) — KL klickt in Excel, Mail-
        # Client oeffnet sich mit vorausgefuellter Anrede.
        erz_by_nr = {e.get('nr'): e for e in s.get('erzieher', [])
                     if isinstance(e.get('nr'), int)}
        col_idx = len(STAMM_HEADERS) + 1
        for slot_i in range(1, max_slots + 1):
            e = erz_by_nr.get(slot_i, {})
            for sfx in ERZ_SLOT_SUFFIXES:
                val = e.get(sfx, '')
                cell = ws1.cell(row=row_idx, column=col_idx, value=val)
                if sfx == 'E-Mail' and val and '@' in str(val):
                    mailto = _build_mailto_url(
                        str(val),
                        briefanrede=e.get('Briefanrede', ''),
                        nachname=e.get('Nachname', ''))
                    if mailto:
                        cell.hyperlink = mailto
                        cell.style = 'Hyperlink'
                col_idx += 1
        row_idx += 1

    # Spaltenbreiten: Stamm-Block + pro Slot die 6 Slot-Spalten.
    # Spalte F (Volljaehrig) auf 14 erhoeht (vorher 10), damit '(heute,
    # formelberechnet)' im 3-zeiligen Header sauber umbricht ohne abzuschneiden.
    from openpyxl.utils import get_column_letter
    stamm_widths = [10, 8, 18, 16, 11, 14, 24]
    slot_widths  = [8, 8, 16, 18, 22, 32]  # Anrede / Titel / Vorname / Nachname / Briefanrede / E-Mail
    widths1 = list(stamm_widths) + slot_widths * max_slots
    for ci, w in enumerate(widths1, 1):
        ws1.column_dimensions[get_column_letter(ci)].width = w
    last_col1 = get_column_letter(len(headers1))
    ws1.auto_filter.ref = f"A{header_row}:{last_col1}{max(header_row, row_idx - 1)}"
    # Freeze: Header-Zeile + 4 Stamm-Spalten (ID/Klasse/Nachname/Vorname)
    # bleiben sichtbar — beim horizontalen Scrollen durch die Slot-Bloecke
    # bleibt der Schueler erkennbar.
    ws1.freeze_panes = ws1.cell(row=header_row + 1, column=5)

    # --- Sheet 2: Telefonnummern -----------------------------------------
    ws2 = wb.create_sheet(title='Telefonnummern')
    ws2['A1'] = f"Telefonnummern Klasse {class_data.get('klasse', '')}"
    ws2['A1'].font = Font(bold=True, size=13)
    ws2['A2'] = f"Stand: {stand_date}"
    ws2['A2'].font = Font(italic=True, size=10)
    headers2 = [
        'Schüler-ID', 'Klasse', 'Nachname', 'Vorname',
        'Anschluss-Art', 'Telefon-Nummer', 'Bemerkung', 'Quelle',
    ]
    for ci, h in enumerate(headers2, 1):
        c = ws2.cell(row=header_row, column=ci, value=h)
        c.font = header_font
        c.fill = stamm_fill  # gleiche graue Headerfarbe wie Stamm-Block in Sheet 1
        c.alignment = Alignment(vertical='top')
    row_idx2 = header_row + 1
    for s in class_data.get('students', []):
        phones = s.get('telefone', [])
        if not phones:
            ws2.cell(row=row_idx2, column=1, value=s.get('id', ''))
            ws2.cell(row=row_idx2, column=2, value=klasse_name)
            ws2.cell(row=row_idx2, column=3, value=s.get('nachname', ''))
            ws2.cell(row=row_idx2, column=4, value=s.get('vorname', ''))
            row_idx2 += 1
            continue
        for p in phones:
            ws2.cell(row=row_idx2, column=1, value=s.get('id', ''))
            ws2.cell(row=row_idx2, column=2, value=klasse_name)
            ws2.cell(row=row_idx2, column=3, value=s.get('nachname', ''))
            ws2.cell(row=row_idx2, column=4, value=s.get('vorname', ''))
            ws2.cell(row=row_idx2, column=5, value=p.get('anschluss', ''))
            ws2.cell(row=row_idx2, column=6, value=p.get('telefon', ''))
            ws2.cell(row=row_idx2, column=7, value=p.get('bemerkung', ''))
            ws2.cell(row=row_idx2, column=8, value='Erzieher-Export' if p.get('from_erz') else 'Ansprechpartner-Export')
            row_idx2 += 1

    widths2 = [10, 8, 18, 16, 18, 22, 22, 22]
    for ci, w in enumerate(widths2, 1):
        ws2.column_dimensions[chr(ord('A') + ci - 1)].width = w
    last_col2 = chr(ord('A') + len(headers2) - 1)
    ws2.auto_filter.ref = f"A{header_row}:{last_col2}{max(header_row, row_idx2 - 1)}"
    ws2.freeze_panes = ws2.cell(row=header_row + 1, column=1)

    # --- Sheet 3 + 4: Mailverteiler (alle / nur Minderj.) -----------------
    # Zwei Varianten in eigenen Sheets, damit die KL nicht filtern muss —
    # einfach das richtige Sheet auswaehlen, Direkt-Liste markieren, in BCC.
    _build_mailverteiler_sheet(wb, class_data, stand_date,
                                title='Mailverteiler (alle)',
                                exclude_volljaehrige=False,
                                description=(
                                    'Diese Variante enthält ALLE in Schild '
                                    'hinterlegten Eltern-/Ansprechpartner-E-Mail-'
                                    'Adressen — inklusive Adressen, die zu '
                                    'volljährigen Schülern gehören (z.B. die '
                                    'eigene E-Mail-Adresse eines volljährigen '
                                    'Schülers als Self-Ansprechpartner).'))
    _build_mailverteiler_sheet(wb, class_data, stand_date,
                                title='Mailverteiler (nur Minderj.)',
                                exclude_volljaehrige=True,
                                description=(
                                    'Diese Variante schließt E-Mail-Adressen '
                                    'aus, die zu volljährigen Schülern gehören '
                                    '(Stand der Volljährigkeit dynamisch aus '
                                    'dem Geburtsdatum berechnet, mit Schild-'
                                    'Heuristik als Fallback). Sinnvoll z.B. '
                                    'für Eltern-Kommunikation, die die '
                                    'Sorgeberechtigten voraussetzt.'))

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _build_mailverteiler_sheet(wb, class_data, stand_date, title,
                                exclude_volljaehrige, description):
    """Baut ein Mailverteiler-Sheet in der gegebenen Workbook ein.
    Layout:
       Row 1: Titel
       Row 2: Stand + Klasse
       Row 3: KL/Stv-KL (optional)
       Row 4-5: Hinweis-Box (gemerged ueber 5 Spalten)
       Row 7: 'DIREKT-LISTE'-Header
       Row 8: ein gemergedes Zellen-Block A:E mit semikolon-getrennter Liste
              (wrap_text + grosse Row-Hoehe). KL kann markieren+kopieren.
       Row 10: Tabellenheader (E-Mail / Erzieher / Schüler / Klasse / Vollj.)
       Row 11+: Daten
       Row N+2: Statistik
    """
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    ws = wb.create_sheet(title=title[:31])  # Excel-Limit
    klasse_name = class_data.get('klasse', '')
    students = class_data.get('students', [])
    emails = _collect_parent_emails(class_data, exclude_volljaehrige=exclude_volljaehrige)

    # Hilfsstyles
    header_fill = PatternFill('solid', fgColor='DDDDDD')
    accent_fill = PatternFill('solid', fgColor='D6EAF8') if not exclude_volljaehrige \
                  else PatternFill('solid', fgColor='D5F5E3')
    hint_fill   = PatternFill('solid', fgColor='FFF9E6')
    thin_border = Border(left=Side(style='thin', color='CCCCCC'),
                         right=Side(style='thin', color='CCCCCC'),
                         top=Side(style='thin', color='CCCCCC'),
                         bottom=Side(style='thin', color='CCCCCC'))

    # Zeile 1: Titel
    ws['A1'] = f"{title} — Klasse {klasse_name}"
    ws['A1'].font = Font(bold=True, size=13)
    ws.merge_cells('A1:E1')
    # Zeile 2: Stand
    ws['A2'] = f"Stand: {stand_date}"
    ws['A2'].font = Font(italic=True, size=10)
    # Zeile 3: KL-Info
    kl_parts = []
    if class_data.get('kl_name'):
        kl_parts.append(f"KL: {class_data['kl_name']}")
    if class_data.get('stv_kl_name'):
        kl_parts.append(f"Stv-KL: {class_data['stv_kl_name']}")
    if kl_parts:
        ws['A3'] = ' · '.join(kl_parts)
        ws['A3'].font = Font(italic=True, size=10)
    # Zeile 4-5: Hinweis-Box gemerged
    ws['A4'] = f"ℹ️ {description}"
    ws['A4'].font = Font(italic=True, size=9, color='555555')
    ws['A4'].alignment = Alignment(wrap_text=True, vertical='top')
    ws['A4'].fill = hint_fill
    ws.merge_cells(start_row=4, start_column=1, end_row=5, end_column=5)
    ws.row_dimensions[4].height = 30
    ws.row_dimensions[5].height = 30

    # Zeile 7: Direkt-Listen-Header
    ws['A7'] = 'DIREKT-LISTE (Semikolon-getrennt — markieren, kopieren, in BCC einfügen):'
    ws['A7'].font = Font(bold=True, size=10)
    ws.merge_cells('A7:E7')
    # Zeile 8: semikolon-getrennte Liste als EIN gemergedes Feld — KL kann
    # einfach markieren + kopieren (Excel uebernimmt nur den Text der ersten Zelle,
    # also reicht es, A8 zu befuellen).
    if emails:
        joined = '; '.join(e['email'] for e in emails)
    else:
        joined = '— Keine gültigen E-Mail-Adressen in dieser Klasse (mit aktiver Filterung).'
    ws['A8'] = joined
    ws['A8'].font = Font(name='Consolas', size=10)
    ws['A8'].alignment = Alignment(wrap_text=True, vertical='top')
    ws['A8'].fill = accent_fill
    ws['A8'].border = thin_border
    ws.merge_cells('A8:E8')
    # Sammel-Hyperlink (mailto:?bcc=...) zusaetzlich auf A8 — KL kann mit
    # einem Klick eine neue Mail mit allen Adressen im BCC oeffnen. Bei sehr
    # langen Verteilern (>~2000 Zeichen URL) ignoriert Outlook den Link;
    # der Copy-Paste-Text bleibt davon unberuehrt.
    if emails:
        bulk_link = _build_bulk_mailto_url([e['email'] for e in emails])
        if bulk_link:
            ws['A8'].hyperlink = bulk_link
    # Row-Hoehe abhaengig von Email-Anzahl (grobe Schaetzung: 1 Zeile pro 4 Mails)
    approx_lines = max(2, (len(emails) // 4) + 1)
    ws.row_dimensions[8].height = min(20 * approx_lines, 250)

    # Zeile 10: Tabellen-Header
    table_header_row = 10
    table_headers = ['E-Mail', 'Erzieher', 'Schüler', 'Klasse',
                     'Volljährig\n(heute)']
    for ci, h in enumerate(table_headers, 1):
        c = ws.cell(row=table_header_row, column=ci, value=h)
        c.font = Font(bold=True)
        c.fill = header_fill
        c.alignment = Alignment(wrap_text=True, vertical='top')
    ws.row_dimensions[table_header_row].height = 32

    # Zeile 11+: Daten
    row_idx = table_header_row + 1
    for e in emails:
        # E-Mail-Zelle als klickbarer mailto: mit body=Briefanrede+Nachname.
        # Faellt auf "Sehr geehrte/r Herr/Frau Nachname" oder "Sehr geehrte
        # Damen und Herren" zurueck, wenn die Briefanrede in Schild leer ist.
        mail_cell = ws.cell(row=row_idx, column=1, value=e['email'])
        mailto = _build_mailto_url(
            e['email'],
            briefanrede=e.get('erz_briefanrede', ''),
            nachname=e.get('erz_nachname', ''))
        if mailto:
            mail_cell.hyperlink = mailto
            mail_cell.style = 'Hyperlink'
        erz_name_parts = [p for p in (e['erz_anrede'], e['erz_vorname'],
                                      e['erz_nachname']) if p]
        erz_name = ' '.join(erz_name_parts).strip() or '(Name unbekannt)'
        if e['slot_nr']:
            erz_name = f"{erz_name} (Slot {e['slot_nr']})"
        ws.cell(row=row_idx, column=2, value=erz_name)
        schueler_name = f"{e['schueler_nachname']}, {e['schueler_vorname']}".strip(', ')
        if e['schueler_id']:
            schueler_name = f"{schueler_name} [ID {e['schueler_id']}]"
        ws.cell(row=row_idx, column=3, value=schueler_name)
        ws.cell(row=row_idx, column=4, value=klasse_name)
        if e['schueler_volljaehrig']:
            ws.cell(row=row_idx, column=5, value='ja')
        elif not e['volljaehrig_per_geb_known']:
            ws.cell(row=row_idx, column=5, value='?')
        else:
            ws.cell(row=row_idx, column=5, value='nein')
        row_idx += 1
    last_data_row = row_idx - 1

    # Spalten-Breiten
    widths = [32, 28, 28, 10, 12]
    for ci, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(ci)].width = w

    # Autofilter nur wenn Daten vorhanden
    if emails:
        ws.auto_filter.ref = (f"A{table_header_row}:E"
                              f"{max(table_header_row, last_data_row)}")

    # Statistik-Block unten
    stat_row = max(row_idx + 1, table_header_row + 2)
    ws.cell(row=stat_row, column=1, value='Statistik:').font = Font(bold=True)
    # Mehrwert-Statistik: Schueler-Counts (gesamt + die mit/ohne Mail)
    students_with_mail = sum(
        1 for s in students
        if any((slot.get('E-Mail') or '').strip() for slot in s.get('erzieher', []))
    )
    vollj_count_in_class = sum(1 for s in students if s.get('volljaehrig'))
    excluded_by_volljaehrigkeit = vollj_count_in_class if exclude_volljaehrige else 0
    stats_lines = [
        f"Schüler in Klasse: {len(students)}",
        f"Schüler mit mind. einer Eltern-Mail: {students_with_mail}",
        f"Schüler OHNE Eltern-Mail: {len(students) - students_with_mail}",
        f"Eindeutige E-Mail-Adressen im Verteiler: {len(emails)}",
    ]
    if exclude_volljaehrige:
        stats_lines.append(
            f"Wegen Volljährigkeit ausgeschlossene Schüler: {excluded_by_volljaehrigkeit}")
    for i, line in enumerate(stats_lines):
        ws.cell(row=stat_row + 1 + i, column=1, value=line).font = Font(size=10)

    ws.freeze_panes = ws.cell(row=table_header_row + 1, column=1)


def safe_class_filename(klasse):
    """Dateinamen-sicheres Aequivalent — Duplikat zu ausbilder_processor."""
    return re.sub(r'[<>:"/\\|?*]', '_', klasse or 'Klasse')


# ---------------------------------------------------------------------------
# Eltern-Mailverteiler (3.3): zweiter Mail-Anhang neben dem Excel
# ---------------------------------------------------------------------------

# Dummy-E-Mail aus dem fill_dummies-Feature darf NIE in den Verteiler — wuerde
# bouncen + Eltern-Mailverteilern keine seriose Adressen mehr beibringen.
_INVALID_EMAIL_DOMAINS = ('invalid.local', 'invalid', 'example.com', 'example.org')


def _collect_parent_emails(class_data, exclude_volljaehrige=False):
    """Sammelt alle Erzieher-/Ansprechpartner-E-Mail-Adressen der Klasse —
    dedupliziert (case-insensitive), mit Zuordnung zu Schueler + Slot.

    Args:
        exclude_volljaehrige: wenn True, werden ALLE E-Mail-Adressen von
            Schuelern uebersprungen, deren 'volljaehrig'-Status True ist
            (Kombi-Quelle: Geburtsdatum >= 18 ODER Schild-Markierung). Damit
            kann der Aufrufer eine 'nur Minderj.'-Variante des Verteilers
            bauen. Konservativ: wenn IRGENDEINE Quelle 'volljaehrig' sagt,
            wird der Eintrag ausgeschlossen.

    Returns: Liste von Dicts in stabiler Reihenfolge (Schueler-Sortierung,
    dann Slot-Nr aufsteigend):
        {email, email_lower, schueler_id, schueler_vorname, schueler_nachname,
         erz_vorname, erz_nachname, erz_anrede, slot_nr,
         schueler_volljaehrig, volljaehrig_per_geb_known}
    Ungueltige/leere Adressen werden uebersprungen.
    """
    seen = set()
    out = []
    for s in class_data.get('students', []):
        is_vollj = bool(s.get('volljaehrig'))
        if exclude_volljaehrige and is_vollj:
            continue
        # Erzieher-Liste ist bereits nach 'nr' aufsteigend sortiert (siehe
        # _extract_all_erzieher_slots), wir behalten die Reihenfolge bei.
        for e in s.get('erzieher', []):
            email = (e.get('E-Mail') or '').strip()
            if not email or '@' not in email:
                continue
            # Dummy-/Beispiel-Adressen filtern
            domain = email.split('@', 1)[1].lower()
            if any(domain == d or domain.endswith('.' + d) for d in _INVALID_EMAIL_DOMAINS):
                continue
            key = email.lower()
            if key in seen:
                # Dedup: gleiche Adresse fuer beide Eltern (sehr selten) oder
                # ueber Geschwister hinweg (kann in Mischklassen passieren).
                continue
            seen.add(key)
            out.append({
                'email':            email,
                'email_lower':      key,
                'schueler_id':      s.get('id', ''),
                'schueler_vorname': s.get('vorname', ''),
                'schueler_nachname': s.get('nachname', ''),
                'erz_vorname':      (e.get('Vorname') or '').strip(),
                'erz_nachname':     (e.get('Nachname') or '').strip(),
                'erz_anrede':       (e.get('Anrede') or '').strip(),
                # Briefanrede zusaetzlich — fuer mailto-Body-Vorausfuellung
                # in den Mailverteiler-Sheets.
                'erz_briefanrede':  (e.get('Briefanrede') or '').strip(),
                'slot_nr':          e.get('nr', ''),
                'schueler_volljaehrig':       is_vollj,
                'volljaehrig_per_geb_known':  bool(s.get('volljaehrig_per_geb_known')),
            })
    return out


# build_parent_distribution_text() + safe_distribution_filename() wurden in
# 3.3 wieder entfernt — die Eltern-Mailverteiler werden jetzt direkt als
# weitere Sheets in die KL-Mail-Excel integriert (Sheets 3 + 4), inkl. einer
# Variante mit / ohne volljaehrige Schueler. Sheet-Builder siehe
# _build_mailverteiler_sheet() weiter unten.
