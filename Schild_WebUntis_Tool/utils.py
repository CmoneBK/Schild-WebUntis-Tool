import os
import configparser

def safe_read_config(config_obj, filename):
    """
    Versucht eine Konfigurationsdatei mit utf-8-sig zu laden, 
    fällt bei Fehlern auf latin-1 zurück.
    """
    if not os.path.exists(filename):
        return False
    
    # Erst mit utf-8-sig versuchen
    try:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            config_obj.read_file(f)
        return True
    except (UnicodeDecodeError, Exception):
        # Fallback auf latin-1
        try:
            config_obj.clear() # Falls teilweise geladen
            with open(filename, 'r', encoding='latin-1') as f:
                config_obj.read_file(f)
            return True
        except Exception as e:
            print(f"Fehler beim Lesen der Datei {filename}: {e}")
            return False


class ConfigReadError(RuntimeError):
    """
    Eine vorhandene Konfigurationsdatei konnte nicht gelesen werden.
    Wird ausgeloest, bevor die Datei zurueckgeschrieben wird — sonst wuerde
    der Schreibvorgang die nicht eingelesenen Abschnitte verwerfen.
    """
    pass


def read_config_for_update(config_obj, filename):
    """
    Liest eine INI-Datei ein, die anschliessend wieder komplett zurueckgeschrieben wird.

    Unterschied zu safe_read_config: Eine *vorhandene*, aber unlesbare Datei ist hier
    ein harter Fehler. Alle Speicherfunktionen arbeiten nach dem Muster
    "lesen -> einzelne Werte setzen -> komplette Datei neu schreiben". Schlaegt das
    Lesen still fehl, ist das Config-Objekt leer und der Schreibvorgang kuerzt die
    Datei auf die gerade gesetzten Abschnitte zusammen — alle uebrigen Einstellungen
    waeren verloren. Fehlt die Datei dagegen, wird sie regulaer neu angelegt.
    """
    if not os.path.exists(filename):
        return  # Datei wird neu angelegt — nichts zu verlieren.
    if not safe_read_config(config_obj, filename):
        raise ConfigReadError(
            f"'{filename}' existiert, konnte aber nicht gelesen werden. "
            f"Zum Schutz der vorhandenen Einstellungen wurde nichts gespeichert. "
            f"Bitte die Datei pruefen (Syntax/Kodierung) oder aus einer Sicherung wiederherstellen."
        )
