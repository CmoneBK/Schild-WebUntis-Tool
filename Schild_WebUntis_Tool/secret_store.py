"""Kleiner Helfer fuer at-rest verschluesselte Geheimnisse in settings.ini.

Aktuell wird das nur fuer das Passwort der verschluesselten Sonderpaedagogen-
Arbeitsdatei (Nachteilsausgleich) genutzt. Die Idee ist bewusst minimal:

* Windows: Per DPAPI (CryptProtectData) — gebunden an den aktuellen Windows-
  Benutzer, kein zusaetzliches Master-Passwort noetig. Verhindert, dass das
  Klartext-Passwort in der settings.ini einsehbar ist, wenn die Datei z.B.
  versehentlich kopiert oder per Teamviewer eingesehen wird.
* Andere OS / fehlendes pywin32: Fallback auf Klartext mit explizitem Marker
  (`plain:`). Funktioniert weiter, ist aber im Klartext sichtbar — wird im
  Log ein Warnhinweis ausgegeben.

Format in der settings.ini:
    nachteilsausgleich_excel_password = dpapi:<base64>
    nachteilsausgleich_excel_password = plain:<klartext>
    nachteilsausgleich_excel_password =                   (leer = kein Passwort)
"""
from __future__ import annotations

import base64
import sys


_DPAPI_PREFIX = 'dpapi:'
_PLAIN_PREFIX = 'plain:'

_WIN32CRYPT = None
if sys.platform == 'win32':
    try:
        import win32crypt  # type: ignore
        _WIN32CRYPT = win32crypt
    except Exception:
        _WIN32CRYPT = None


def is_dpapi_available() -> bool:
    return _WIN32CRYPT is not None


def encrypt_secret(plain: str, description: str = 'schild-webuntis-tool') -> str:
    """Verschluesselt einen Klartext fuer die settings.ini.

    Liefert immer einen String mit Marker-Praefix (dpapi:/plain:). Leerstrings
    werden unveraendert zurueckgegeben (keine Verschluesselung von 'nichts').
    """
    if not plain:
        return ''
    if _WIN32CRYPT is None:
        # Plattform ohne DPAPI: ehrlich Klartext speichern (mit Marker).
        return _PLAIN_PREFIX + plain
    try:
        blob = _WIN32CRYPT.CryptProtectData(
            plain.encode('utf-8'), description, None, None, None, 0
        )
        return _DPAPI_PREFIX + base64.b64encode(blob).decode('ascii')
    except Exception:
        return _PLAIN_PREFIX + plain


def decrypt_secret(stored: str) -> str:
    """Liefert den Klartext aus einem in der settings.ini gespeicherten Wert.

    Akzeptiert Werte mit Marker-Praefix sowie alte Klartext-Werte ohne Marker
    (Rueckwaertskompatibilitaet — wird beim naechsten Speichern automatisch
    in dpapi:/plain: ueberfuehrt).
    """
    if not stored:
        return ''
    if stored.startswith(_PLAIN_PREFIX):
        return stored[len(_PLAIN_PREFIX):]
    if stored.startswith(_DPAPI_PREFIX):
        if _WIN32CRYPT is None:
            # DPAPI-Wert auf einem System ohne DPAPI: nicht entschluesselbar.
            return ''
        try:
            blob = base64.b64decode(stored[len(_DPAPI_PREFIX):])
            _desc, plain = _WIN32CRYPT.CryptUnprotectData(blob, None, None, None, 0)
            return plain.decode('utf-8')
        except Exception:
            return ''
    # Legacy: kein Praefix => als Klartext behandeln
    return stored


def is_secret_set(stored: str) -> bool:
    return bool(stored and decrypt_secret(stored))
