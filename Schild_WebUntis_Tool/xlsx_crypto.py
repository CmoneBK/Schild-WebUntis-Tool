"""Lesen/Schreiben verschluesselter (passwortgeschuetzter) xlsx-Dateien.

Wird fuer die Sonderpaedagogen-Arbeitsdatei (Nachteilsausgleich) genutzt: die
Datei liegt typischerweise auf einem Netzlaufwerk, auf das mehrere Personen
Zugriff haben. Excel-Passwortschutz haelt zusaetzliche Augen draussen, ohne
dass es eine zentrale Schluesselverwaltung braucht.

Strategie:
* Lesen: zuerst try ohne Passwort (openpyxl). Bei BadZipFile/InvalidFile pruefen,
  ob die Datei laut msoffcrypto verschluesselt ist; falls ja, mit Passwort
  entschluesseln (BytesIO) und dann openpyxl darueber.
* Schreiben: workbook.save() in BytesIO; falls Passwort gesetzt, ueber
  msoffcrypto verschluesseln und atomar auf die Zielpfad-Datei wegspeichern.

Beide Funktionen erhalten read_only/write_only-Optionen nicht — die
Arbeitsdatei ist klein genug, dass der Bypass-Aufwand nicht lohnt.
"""
from __future__ import annotations

import io
import os
import tempfile

from openpyxl import Workbook, load_workbook


class EncryptedFileError(Exception):
    """Datei ist verschluesselt, aber kein/falsches Passwort konfiguriert."""


def excel_lock_marker_path(path: str) -> str:
    """Liefert den Pfad, den Excel als Lock-Marker anlegt, solange die Datei
    geoeffnet ist (z.B. 'C:/share/~$Datei.xlsx' fuer 'C:/share/Datei.xlsx')."""
    d, name = os.path.split(path)
    return os.path.join(d, '~$' + name)


def is_excel_open(path: str) -> bool:
    """True, wenn Excel die Datei aktuell geoeffnet zu halten scheint
    (Existenz der ~$-Lock-Datei). Funktioniert auch fuer verschluesselte xlsx."""
    return os.path.exists(excel_lock_marker_path(path))


def _is_encrypted_ooxml(path: str) -> bool:
    try:
        import msoffcrypto  # type: ignore
    except ImportError:
        return False
    try:
        with open(path, 'rb') as fh:
            office = msoffcrypto.OfficeFile(fh)
            return bool(office.is_encrypted())
    except Exception:
        return False


def load_workbook_maybe_encrypted(path: str, password: str = '', **load_kwargs):
    """Wie openpyxl.load_workbook, aber transparent fuer passwortgeschuetzte xlsx.

    `password` darf leer sein. Bei verschluesselter Datei wird ohne Passwort
    eine EncryptedFileError ausgeloest; bei falschem Passwort ebenfalls.
    """
    try:
        return load_workbook(path, **load_kwargs)
    except Exception as first_err:
        if not _is_encrypted_ooxml(path):
            raise
        if not password:
            raise EncryptedFileError(
                f"Datei ist passwortgeschuetzt, aber kein Passwort hinterlegt: {path}"
            ) from first_err
        try:
            import msoffcrypto  # type: ignore
        except ImportError as ie:
            raise EncryptedFileError(
                "msoffcrypto-tool ist nicht installiert — passwortgeschuetzte "
                "Arbeitsdateien koennen nicht gelesen werden."
            ) from ie
        try:
            plain = io.BytesIO()
            with open(path, 'rb') as fh:
                office = msoffcrypto.OfficeFile(fh)
                office.load_key(password=password)
                office.decrypt(plain)
            plain.seek(0)
            return load_workbook(plain, **load_kwargs)
        except EncryptedFileError:
            raise
        except Exception as e:
            raise EncryptedFileError(
                f"Passwortgeschuetzte Datei konnte nicht entschluesselt werden "
                f"(falsches Passwort?): {path} — {e}"
            ) from e


def save_workbook_maybe_encrypted(wb: Workbook, path: str, password: str = '') -> None:
    """Wie wb.save(path), aber verschluesselt das Ergebnis bei gesetztem Passwort.

    Es wird immer ueber eine temporaere Datei geschrieben, damit die alte Datei
    nicht halb-ueberschrieben wird, wenn das Verschluesseln scheitert.
    """
    if not password:
        wb.save(path)
        return

    try:
        from msoffcrypto.format.ooxml import OOXMLFile  # type: ignore
    except ImportError as ie:
        raise EncryptedFileError(
            "msoffcrypto-tool ist nicht installiert — passwortgeschuetzte "
            "Arbeitsdateien koennen nicht geschrieben werden."
        ) from ie

    plain = io.BytesIO()
    wb.save(plain)
    plain.seek(0)

    target_dir = os.path.dirname(os.path.abspath(path)) or '.'
    tmp_fd, tmp_path = tempfile.mkstemp(suffix='.xlsx', dir=target_dir)
    os.close(tmp_fd)
    try:
        with open(tmp_path, 'wb') as out:
            office = OOXMLFile(plain)
            office.encrypt(password, out)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise
