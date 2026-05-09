"""
SVWS-Server REST-API Client (Schild 3.x).
Liest Schüler-, Klassen- und Lehrerdaten aus dem SVWS-Server und mappt sie
auf das interne Dict-Format, das auch der CSV-Pfad erzeugt — sodass der Rest
der Verarbeitung identisch bleibt.
"""
import requests
import urllib3


# Schild-Geschlechtscodes (analog zur CSV)
_GESCHLECHT_MAP = {3: 'm', 4: 'w', 5: 'd', 6: 'x'}

# Schild-Status-Katalog (Stand SVWS-Server 1.3.x)
SCHILD_STATUS_LABELS = {
    0: "Aufnahme",
    1: "Warteliste",
    2: "Aktiv",
    3: "Beurlaubt",
    6: "Extern",
    8: "Abschluss",
    9: "Abgang (ohne Abschluss)",
    10: "Ehemalige",
}

# Default-Whitelist: entspricht Schild-Filter
# "Aktuelles Schuljahr - Aktive, Abgänger und Abschlüsse" + Externe.
DEFAULT_ALLOWED_STATUSES = {2, 6, 8, 9}


def _to_csv_date(iso_date):
    """ISO YYYY-MM-DD → DD.MM.YYYY (wie es die Schild-CSV liefert)."""
    if not iso_date:
        return ''
    try:
        y, m, d = iso_date.split('-')
        return f"{d}.{m}.{y}"
    except Exception:
        return iso_date


def _bool_to_ja_nein(value):
    if value is True:
        return 'Ja'
    if value is False:
        return 'Nein'
    return ''


class SVWSClient:
    def __init__(self, server_url, schema, user, password, verify_ssl=False, timeout=30):
        self.base_url = server_url.rstrip('/')
        self.schema = schema
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.session.verify = verify_ssl
        self.session.headers.update({"Accept": "application/json"})
        self.timeout = timeout
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _db(self, path):
        return f"{self.base_url}/db/{self.schema}{path}"

    # --- Low-level Helfer -------------------------------------------------

    def _get(self, path):
        r = self.session.get(self._db(path), timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def _post_json(self, path, body):
        r = self.session.post(self._db(path), json=body,
                              headers={"Content-Type": "application/json"},
                              timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # --- Verbindung -------------------------------------------------------

    def test_connection(self):
        """Liefert (erfolg: bool, nachricht: str)."""
        try:
            # /schule/stammdaten testet Erreichbarkeit, Auth UND Schema in einem Rutsch.
            # /status/alive wird bewusst NICHT verwendet, weil der SVWS-Server
            # bei diesem Endpoint mit Accept: application/json einen 500 wirft.
            r = self.session.get(self._db("/schule/stammdaten"), timeout=self.timeout)
            if r.status_code == 401:
                return False, "Authentifizierung fehlgeschlagen (Benutzername/Passwort prüfen)."
            if r.status_code == 404:
                return False, f"Schema '{self.schema}' nicht gefunden."
            if r.status_code == 403:
                return False, "Auth ok, aber Benutzer hat keine Berechtigung für diesen Endpoint."
            r.raise_for_status()
            data = r.json()
            return True, f"Verbindung OK. Schule: {data.get('bezeichnung1', '')} ({data.get('schulNr', '')})"
        except requests.exceptions.SSLError as e:
            return False, f"TLS-Fehler: {e}. Ggf. Self-signed Cert akzeptieren."
        except requests.exceptions.ConnectionError:
            return False, f"Server nicht erreichbar: {self.base_url}"
        except Exception as e:
            return False, f"Fehler: {e}"

    def get_aktiver_abschnitt(self):
        """Liefert die idSchuljahresabschnitt des aktuell aktiven Abschnitts."""
        return self._get("/schule/stammdaten").get("idSchuljahresabschnitt")

    def get_schuljahresabschnitte(self):
        """Liefert (active_id, [{id, schuljahr, abschnitt, label}, ...]) — alle Abschnitte."""
        s = self._get("/schule/stammdaten")
        active = s.get("idSchuljahresabschnitt")
        anzahl = (s.get("schuleAbschnitte") or {}).get("anzahlAbschnitte", 2)
        bez = (s.get("schuleAbschnitte") or {}).get("abschnittBez", "Halbjahr")
        bez_list = (s.get("schuleAbschnitte") or {}).get("bezAbschnitte") or []
        out = []
        for a in (s.get("abschnitte") or []):
            schuljahr = a.get("schuljahr")
            nr = a.get("abschnitt")
            label_ab = bez_list[nr - 1] if (nr and 1 <= nr <= len(bez_list)) else f"{bez} {nr}"
            label = f"Schuljahr {schuljahr}/{schuljahr + 1 if schuljahr else '?'} — {label_ab}"
            out.append({
                "id": a.get("id"),
                "schuljahr": schuljahr,
                "abschnitt": nr,
                "label": label,
                "is_active": a.get("id") == active,
            })
        # Sortieren: neueste zuerst
        out.sort(key=lambda x: (x.get("schuljahr") or 0, x.get("abschnitt") or 0), reverse=True)
        return active, out

    # --- Bulk-Loads -------------------------------------------------------

    def get_orte_lookup(self):
        """{wohnortID: {'plz': ..., 'ortsname': ...}}."""
        try:
            orte = self._get("/orte")
            return {o['id']: {'plz': o.get('plz', ''), 'ortsname': o.get('ortsname', '')}
                    for o in orte if o.get('id')}
        except Exception:
            return {}

    def get_klassen_im_abschnitt(self, abschnitt_id):
        """Liefert eine Liste aller Klassen im gegebenen Abschnitt mit klassenLeitungen[]."""
        return self._get(f"/klassen/details/abschnitt/{abschnitt_id}")

    def get_lehrer_stammdaten_bulk(self, lehrer_ids):
        """POST /lehrer/stammdaten mit Liste von IDs → Liste von Lehrer-Stammdaten."""
        if not lehrer_ids:
            return []
        return self._post_json("/lehrer/stammdaten", list(lehrer_ids))

    def get_schueler_aktuell(self):
        """Kompakte Liste aller aktuellen Schüler (id, idKlasse, status, ...)."""
        return self._get("/schueler/aktuell")

    def get_schueler_stammdaten_bulk(self, schueler_ids):
        """POST /schueler/stammdaten mit Liste von IDs → vollständige Stammdaten."""
        if not schueler_ids:
            return []
        return self._post_json("/schueler/stammdaten", list(schueler_ids))

    def get_schueler_schulbesuch(self, schueler_id):
        """Einzel-Call für Entlassdatum (kein Bulk-Endpoint vorhanden)."""
        try:
            return self._get(f"/schueler/{schueler_id}/schulbesuch")
        except Exception:
            return {}

    # --- High-level: kombinierter Schüler-/Klassen-Aufbau ----------------

    def fetch_classes_with_teachers(self, abschnitt_id=None):
        """
        Liefert classes_by_name (analog zu read_classes()).
        Format: {klassen_kuerzel_lower: {Klassenlehrkraft_1, _Email, _2, _2_Email}, ...}
        """
        if abschnitt_id is None:
            abschnitt_id = self.get_aktiver_abschnitt()

        klassen = self.get_klassen_im_abschnitt(abschnitt_id)

        # Alle benötigten Lehrer-IDs sammeln
        lehrer_ids = set()
        for k in klassen:
            for lid in (k.get('klassenLeitungen') or []):
                lehrer_ids.add(lid)

        # Lehrer in einem Bulk-Call holen
        lehrer_list = self.get_lehrer_stammdaten_bulk(lehrer_ids)
        lehrer_by_id = {l['id']: l for l in lehrer_list}

        classes_by_name = {}
        for k in klassen:
            kuerzel = (k.get('kuerzel') or '').strip()
            if not kuerzel:
                continue
            kl_ids = list(k.get('klassenLeitungen') or [])
            kl1 = lehrer_by_id.get(kl_ids[0]) if len(kl_ids) >= 1 else None
            kl2 = lehrer_by_id.get(kl_ids[1]) if len(kl_ids) >= 2 else None

            def _name(l):
                if not l: return 'N/A'
                return f"{l.get('vorname', '')} {l.get('nachname', '')}".strip() or 'N/A'

            def _mail(l):
                if not l: return 'N/A'
                return l.get('emailDienstlich') or l.get('emailPrivat') or 'Keine E-Mail gefunden'

            classes_by_name[kuerzel.lower()] = {
                'Klassenlehrkraft_1':       _name(kl1),
                'Klassenlehrkraft_1_Email': _mail(kl1),
                'Klassenlehrkraft_2':       _name(kl2),
                'Klassenlehrkraft_2_Email': _mail(kl2),
                'api_data': True,
            }
        return classes_by_name

    def fetch_students(self, abschnitt_id=None, fetch_entlassdatum=True, allowed_statuses=None):
        """
        Liefert (output_data_students, students_by_id) — exakt wie read_students()
        aus main.py es per CSV liefert. So kann der CSV-Pfad transparent ersetzt werden.

        Filter:
          - idSchuljahresabschnitt == aktueller Abschnitt
          - status in allowed_statuses (Default DEFAULT_ALLOWED_STATUSES)
        """
        if abschnitt_id is None:
            abschnitt_id = self.get_aktiver_abschnitt()
        if allowed_statuses is None:
            allowed_statuses = self._read_allowed_statuses_from_settings()

        # 1) Klassen-Lookup für Klassennamen aus idKlasse
        klassen = self.get_klassen_im_abschnitt(abschnitt_id)
        klasse_kuerzel_by_id = {k['id']: k.get('kuerzel', '') for k in klassen}

        # 2) Aktuelle Schüler (kompakt) — nur die im aktiven Abschnitt
        #    UND mit erlaubtem Status
        aktuell = self.get_schueler_aktuell()
        aktuell_im_abschnitt = [
            s for s in aktuell
            if s.get('idSchuljahresabschnitt') == abschnitt_id
            and s.get('status') in allowed_statuses
        ]
        schueler_ids = [s['id'] for s in aktuell_im_abschnitt]
        idKlasse_by_id = {s['id']: s.get('idKlasse') for s in aktuell_im_abschnitt}
        status_by_id = {s['id']: s.get('status') for s in aktuell_im_abschnitt}

        # 3) Stammdaten Bulk
        stammdaten = self.get_schueler_stammdaten_bulk(schueler_ids)

        # 4) Orte-Lookup
        orte = self.get_orte_lookup()

        # 5) Schulbesuch pro Schüler für Entlassdatum (kein Bulk vorhanden)
        entlassdatum_by_id = {}
        if fetch_entlassdatum:
            for sid in schueler_ids:
                sb = self.get_schueler_schulbesuch(sid)
                ed = sb.get('entlassungDatum')
                if ed:
                    entlassdatum_by_id[sid] = _to_csv_date(ed)

        # 6) Mapping aufbauen — exakt das Format das CSV-Pfad in read_students liefert
        output_columns = [
            'Interne ID-Nummer', 'Nachname', 'Vorname', 'Geburtsdatum', 'Klasse',
            'Geschlecht', 'Entlassdatum', 'Aufnahmedatum', 'vorauss. Abschlussdatum',
            'Schulpflicht', 'Volljährig', 'E-Mail (privat)', 'Telefon-Nr.',
            'Fax-Nr.', 'Straße', 'Postleitzahl', 'Ortsname', 'Aktiv',
        ]
        # ACTIVE_SCHILD_STATUS dynamisch lesen (analog main.get_active_schild_status())
        active_statuses = self._read_active_status_from_settings()

        output_data_students = [output_columns]
        students_by_id = {}

        for sd in stammdaten:
            sid = sd['id']
            wohnort = orte.get(sd.get('wohnortID')) or {}
            strasse_raw = ' '.join(filter(None, [
                sd.get('strassenname') or '',
                sd.get('hausnummer') or '',
                sd.get('hausnummerZusatz') or '',
            ])).strip()
            geschlecht_int = sd.get('geschlecht')
            geschlecht = _GESCHLECHT_MAP.get(geschlecht_int, '')
            status_str = str(status_by_id.get(sid, sd.get('status', '')))
            id_klasse = idKlasse_by_id.get(sid)
            klasse_name = klasse_kuerzel_by_id.get(id_klasse, '')

            # Schulpflicht-Logik (CSV-Pfad invertiert "Ja"/"Nein"):
            #   Schild-Feld istSchulpflichtErfuellt:
            #     True  → "Schulpflicht erfüllt" → "Schulpflicht: Nein"
            #     False → "Schulpflicht erfüllt: Nein" → "Schulpflicht: Ja"
            spe = sd.get('istSchulpflichtErfuellt')
            if spe is True:
                schulpflicht = 'Nein'
            elif spe is False:
                schulpflicht = 'Ja'
            else:
                schulpflicht = ''

            row = {
                'Interne ID-Nummer':         str(sid),
                'Nachname':                  sd.get('nachname', '') or '',
                'Vorname':                   sd.get('vorname', '') or '',
                'Geburtsdatum':              _to_csv_date(sd.get('geburtsdatum')),
                'Klasse':                    klasse_name,
                'Klassenlehrer':             '',  # über classes_by_name Lookup im Mailing
                'Geschlecht':                geschlecht,
                'Entlassdatum':              entlassdatum_by_id.get(sid, ''),
                'Aufnahmedatum':             _to_csv_date(sd.get('aufnahmedatum')),
                'vorauss. Abschlussdatum':   '',  # nicht direkt im API verfügbar
                'Schulpflicht':              schulpflicht,
                'Schulpflicht erfüllt':      _bool_to_ja_nein(spe),
                'Volljährig':                _bool_to_ja_nein(sd.get('istVolljaehrig')),
                'E-Mail (privat)':           sd.get('emailPrivat') or '',
                'Telefon-Nr.':               sd.get('telefon') or '',
                'Fax-Nr.':                   '',  # in API nicht vorhanden
                'Straße':                    strasse_raw,
                'Postleitzahl':              wohnort.get('plz', ''),
                'Ortsname':                  wohnort.get('ortsname', ''),
                'Status':                    status_str,
                'Aktiv':                     'Ja' if status_str in active_statuses else 'Nein',
            }
            students_by_id[row['Interne ID-Nummer']] = row
            output_data_students.append([row.get(c, '') for c in output_columns])

        return output_data_students, students_by_id

    @staticmethod
    def _read_active_status_from_settings():
        """Liest ACTIVE_SCHILD_STATUS aus settings.ini (Vermeidet Zirkular-Import von main.py)."""
        import configparser
        config = configparser.ConfigParser()
        try:
            config.read('settings.ini', encoding='utf-8-sig')
            treat_6 = config.getboolean('ProcessingOptions', 'treat_status_6_as_active', fallback=True)
        except Exception:
            treat_6 = True
        return {'2', '6'} if treat_6 else {'2'}

    @staticmethod
    def _read_allowed_statuses_from_settings():
        """Liest [SchildAPI].allowed_statuses (Komma-Liste) aus settings.ini.
        Default: DEFAULT_ALLOWED_STATUSES."""
        import configparser
        config = configparser.ConfigParser()
        try:
            config.read('settings.ini', encoding='utf-8-sig')
            raw = config.get('SchildAPI', 'allowed_statuses', fallback='')
            if not raw.strip():
                return set(DEFAULT_ALLOWED_STATUSES)
            return {int(s.strip()) for s in raw.split(',') if s.strip().isdigit()}
        except Exception:
            return set(DEFAULT_ALLOWED_STATUSES)
