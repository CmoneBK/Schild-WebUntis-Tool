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
