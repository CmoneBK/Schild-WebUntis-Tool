"""
Persistente Vergabe von eindeutigen Eltern-IDs.

Schild liefert pro Erzieher keine schul-/personeneindeutige ID — bei Geschwister-
Konstellationen hat dasselbe Elternteil bei jedem Kind einen separaten Datensatz.
WebUntis kann (optional) eine schulweit eindeutige Eltern-ID als Matching-Key
auswerten, damit derselbe Erzieher-Account ueber mehrere Kinder hinweg verbunden
ist (statt fuer jedes Kind einen neuen Account anzulegen).

Dieses Modul vergibt solche IDs anhand eines Identitaets-Schluessels und merkt
sich die Zuordnung in einer JSON-Datei (Default: `eltern_ids.json` im cwd), damit
ueber mehrere Verarbeitungslaeufe hinweg derselbe Erzieher dieselbe ID behaelt.

Identitaets-Schluessel (Default):  vorname_lower | nachname_lower | email_lower
Bei leerer E-Mail Fallback auf:    vorname_lower | nachname_lower |   (leer)

Dummy-Erzieher (Nachname oder E-Mail enthaelt 'DUMMY' bzw. '@invalid.local')
werden NICHT erfasst — sie sind Platzhalter fuer fehlende Daten.

ID-Format: 'E00001', 'E00002', ... (zero-padded 5-stellig, ueber 99999 hinaus
laufend laenger).
"""

import json
import os
import re
import threading
from datetime import datetime


DEFAULT_DB_PATH = 'eltern_ids.json'
ID_PREFIX       = 'E'
ID_PAD          = 5

_DUMMY_EMAIL_RE   = re.compile(r'@invalid\.local$', re.IGNORECASE)
_DUMMY_VALUE     = 'DUMMY'

_lock = threading.Lock()


def _key(vorname, nachname, email):
    """Identitaets-Schluessel — case-insensitive, getrimmt."""
    v = (vorname  or '').strip().lower()
    n = (nachname or '').strip().lower()
    e = (email    or '').strip().lower()
    return f"{v}|{n}|{e}"


def is_dummy(vorname, nachname, email):
    """True wenn das Erzieher-Tupel als Dummy zaehlt (kein ID-Tracking)."""
    if (nachname or '').strip().upper() == _DUMMY_VALUE: return True
    if (vorname  or '').strip().upper() == _DUMMY_VALUE: return True
    if _DUMMY_EMAIL_RE.search(email or ''):              return True
    return False


def _format_id(n):
    return f"{ID_PREFIX}{n:0{ID_PAD}d}"


def _empty_db():
    now = datetime.now().isoformat(timespec='seconds')
    return {
        'next_id':  1,
        'mappings': {},
        'metadata': {'created': now, 'modified': now},
    }


def load_db(path=DEFAULT_DB_PATH):
    """Laedt die ID-Datenbank (oder liefert leeres Skelett, wenn nicht vorhanden
    bzw. defekt)."""
    if not os.path.isfile(path):
        return _empty_db()
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Minimale Validierung
        if not isinstance(data, dict) or 'mappings' not in data:
            return _empty_db()
        data.setdefault('next_id',  max((v for v in data['mappings'].values()), default=0) + 1)
        data.setdefault('metadata', {})
        return data
    except (json.JSONDecodeError, OSError):
        return _empty_db()


def save_db(db, path=DEFAULT_DB_PATH):
    """Schreibt die DB atomar (tmp + rename)."""
    db.setdefault('metadata', {})['modified'] = datetime.now().isoformat(timespec='seconds')
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2, sort_keys=True)
    os.replace(tmp, path)


def get_or_assign(vorname, nachname, email, db=None, path=DEFAULT_DB_PATH):
    """Liefert die Eltern-ID fuer (vorname, nachname, email). Erzeugt sie bei
    Bedarf neu und speichert die Aenderung sofort. Dummies bekommen keine ID
    (Rueckgabe: None).

    Wenn 'db' uebergeben wird, wird auf dem Objekt gearbeitet und NICHT
    automatisch gespeichert (Batch-Modus — Aufrufer muss save_db() machen).
    """
    if is_dummy(vorname, nachname, email):
        return None
    if not ((vorname or '').strip() or (nachname or '').strip()):
        return None  # Komplett leerer Erzieher

    standalone = db is None
    with _lock:
        if standalone:
            db = load_db(path)
        k = _key(vorname, nachname, email)
        n = db['mappings'].get(k)
        if n is None:
            n = db['next_id']
            db['mappings'][k] = n
            db['next_id'] = n + 1
            if standalone:
                save_db(db, path)
        return _format_id(n)


def stats(path=DEFAULT_DB_PATH):
    """Statistik-Snapshot der DB fuer die UI."""
    db = load_db(path)
    n = len(db['mappings'])
    next_n = db.get('next_id', 1)
    meta = db.get('metadata', {})
    return {
        'path':            path,
        'exists':          os.path.isfile(path),
        'total_ids':       n,
        'next_id':         _format_id(next_n),
        'created':         meta.get('created'),
        'modified':        meta.get('modified'),
    }


def reset(path=DEFAULT_DB_PATH):
    """Loescht die DB komplett. Liefert True wenn Datei entfernt wurde."""
    if not os.path.isfile(path):
        return False
    os.remove(path)
    return True
