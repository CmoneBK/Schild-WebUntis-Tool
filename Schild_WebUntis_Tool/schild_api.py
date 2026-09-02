"""
SVWS-Server REST-API Client (Schild 3.x).
Liest Schüler-, Klassen- und Lehrerdaten aus dem SVWS-Server und mappt sie
auf das interne Dict-Format, das auch der CSV-Pfad erzeugt — sodass der Rest
der Verarbeitung identisch bleibt.
"""
import threading
from concurrent.futures import ThreadPoolExecutor

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

# Nach je so vielen Schülern wird beim Laden der Schulbesuchsdaten ein
# Fortschritt gemeldet (siehe fetch_students).
SCHULBESUCH_PROGRESS_STEP = 250

# Parallele Abrufe der Schulbesuchsdaten. 1 = sequenziell (Default, bisheriges
# Verhalten). Hoehere Werte holen entsprechend viele Schueler gleichzeitig —
# spuerbar schneller, erzeugt aber entsprechend Last auf dem SVWS-Server,
# deshalb bewusst opt-in ueber [SchildAPI].schulbesuch_workers.
SCHULBESUCH_WORKERS_DEFAULT = 1
SCHULBESUCH_WORKERS_MAX = 16

# Timeout pro API-Abruf in Sekunden. None = kein Timeout (Aufruf wartet
# unbegrenzt) — bewusst moeglich, weil manche SVWS-Server unter Last sehr lange
# brauchen; siehe [SchildAPI].timeout.
DEFAULT_TIMEOUT = 30


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
    def __init__(self, server_url, schema, user, password, verify_ssl=False,
                 timeout=DEFAULT_TIMEOUT):
        """timeout: Sekunden pro Abruf, oder None fuer 'unbegrenzt warten'."""
        self.base_url = server_url.rstrip('/')
        self.schema = schema
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.session.verify = verify_ssl
        self.session.headers.update({"Accept": "application/json"})
        self.timeout = timeout
        # Pro Thread eine eigene Session (siehe _thread_session).
        self._local = threading.local()
        if not verify_ssl:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def _db(self, path):
        return f"{self.base_url}/db/{self.schema}{path}"

    # --- Low-level Helfer -------------------------------------------------

    def _thread_session(self):
        """
        Liefert eine requests.Session, die nur dem aufrufenden Thread gehoert.

        requests.Session ist nicht als threadsicher zugesichert. Solange alles
        sequenziell laeuft, teilen sich alle Aufrufe self.session; beim parallelen
        Abruf der Schulbesuchsdaten bekommt dagegen jeder Worker seine eigene
        Session mit identischer Auth-/TLS-Konfiguration.
        """
        session = getattr(self._local, 'session', None)
        if session is None:
            session = requests.Session()
            session.auth = self.session.auth
            session.verify = self.session.verify
            session.headers.update(self.session.headers)
            self._local.session = session
        return session

    @staticmethod
    def _raise_for_status(r):
        """Wie response.raise_for_status(), nimmt aber den Antwort-Body mit auf.

        Der SVWS-Server begruendet Fehler im Body; raise_for_status() wirft ihn
        weg und hinterlaesst nur 'HTTP 500'. Ohne den Grund ist ein Fehler kaum
        einzugrenzen — insbesondere wenn ein Reverse-Proxy dazwischenhaengt und
        gar nicht klar ist, wer den Fehler erzeugt hat.
        """
        if r.status_code < 400:
            return
        try:
            body = (r.text or '').strip()
        except Exception:
            body = ''
        if len(body) > 500:
            body = body[:500] + ' […]'
        detail = f" — Antwort des Servers: {body}" if body else " (Server sendete keinen Fehlertext)"
        raise requests.exceptions.HTTPError(
            f"HTTP {r.status_code} bei {r.url}{detail}", response=r)

    def _get(self, path, session=None):
        r = (session or self.session).get(self._db(path), timeout=self.timeout)
        self._raise_for_status(r)
        return r.json()

    def _post_json(self, path, body):
        r = self.session.post(self._db(path), json=body,
                              headers={"Content-Type": "application/json"},
                              timeout=self.timeout)
        self._raise_for_status(r)
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
            self._raise_for_status(r)
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

    def get_schueler_schulbesuch(self, schueler_id, session=None):
        """Einzel-Call für Entlassdatum (kein Bulk-Endpoint vorhanden).

        session: beim parallelen Abruf die thread-eigene Session (siehe
        _thread_session); ohne Angabe die gemeinsame Session wie bisher."""
        try:
            return self._get(f"/schueler/{schueler_id}/schulbesuch", session=session)
        except Exception:
            return {}

    # --- Vermerke (für Attestpflicht / Nachteilsausgleich) ---------------

    def get_vermerkarten(self):
        """Liefert den Katalog der Vermerkarten — [{id, bezeichnung, …}, …]."""
        try:
            return self._get("/schule/vermerkarten") or []
        except Exception:
            return []

    def get_schueler_ids_by_vermerk_bezeichnung(self, bezeichnung):
        """
        Liefert ein Set von Schüler-IDs (als String!), die einen Vermerk mit der
        angegebenen Bezeichnung haben. Vergleich case-insensitive nach Trim.
        Leere Bezeichnung → leeres Set (Funktion deaktiviert).
        """
        if not bezeichnung or not bezeichnung.strip():
            return set()
        target = bezeichnung.strip().lower()
        # 1) Vermerkarten-Katalog → ID finden
        vermerkarten = self.get_vermerkarten()
        match = next((v for v in vermerkarten
                      if (v.get('bezeichnung') or '').strip().lower() == target), None)
        if not match:
            return set()
        vermerkart_id = match.get('id')
        # 2) Vermerke mit dieser Art holen → Schüler-IDs extrahieren
        try:
            vermerke = self._get(f"/schueler/vermerke/vermerkart/{vermerkart_id}") or []
        except Exception:
            return set()
        return {str(v.get('idSchueler')) for v in vermerke if v.get('idSchueler')}

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

    def _fetch_entlassdaten(self, schueler_ids, workers, progress=None):
        """
        Holt die Entlassdaten aller Schüler und liefert {schueler_id: 'DD.MM.YYYY'}.

        Meldet den Fortschritt als progress(erledigt, gesamt, workers) — die
        Worker-Zahl geht mit, damit die Konsole zeigen kann, ob parallel
        gearbeitet wird und die Einstellung also gegriffen hat.

        workers <= 1  → sequenziell, exakt wie bisher.
        workers >  1  → so viele Abrufe gleichzeitig (auf SCHULBESUCH_WORKERS_MAX
                        begrenzt), jeder Worker mit eigener Session.

        Das Ergebnis ist in beiden Faellen identisch — nur die Reihenfolge der
        Requests unterscheidet sich, und ein Dict ist reihenfolgeunabhaengig.
        Fehler einzelner Abrufe schluckt get_schueler_schulbesuch wie gehabt,
        ein toter Schueler-Datensatz kippt also nicht den ganzen Lauf.
        """
        gesamt = len(schueler_ids)
        workers = max(1, min(int(workers or 1), SCHULBESUCH_WORKERS_MAX))
        if progress:
            progress(0, gesamt, workers)

        entlassdatum_by_id = {}
        erledigt = 0

        def _melde():
            if progress and (erledigt % SCHULBESUCH_PROGRESS_STEP == 0 or erledigt == gesamt):
                progress(erledigt, gesamt, workers)

        if workers <= 1 or gesamt <= 1:
            for sid in schueler_ids:
                sb = self.get_schueler_schulbesuch(sid)
                ed = sb.get('entlassungDatum')
                if ed:
                    entlassdatum_by_id[sid] = _to_csv_date(ed)
                erledigt += 1
                _melde()
            return entlassdatum_by_id

        def _hole(sid):
            # Läuft im Worker-Thread → eigene Session.
            return sid, self.get_schueler_schulbesuch(sid, session=self._thread_session())

        # Ergebnisse werden im Haupt-Thread eingesammelt (as_completed-Semantik
        # von Executor.map: die Iteration liefert der Reihe nach, die Requests
        # laufen trotzdem parallel). Damit bleibt das Dict-Schreiben single-
        # threaded und braucht kein Lock.
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for sid, sb in pool.map(_hole, schueler_ids):
                ed = sb.get('entlassungDatum')
                if ed:
                    entlassdatum_by_id[sid] = _to_csv_date(ed)
                erledigt += 1
                _melde()
        return entlassdatum_by_id

    @staticmethod
    def read_timeout_from_settings():
        """Liest [SchildAPI].timeout (Sekunden) aus settings.ini.

        Liefert die Sekundenzahl, oder None wenn der Wert <= 0 ist — dann wartet
        das Tool unbegrenzt. Ungueltige oder fehlende Werte ergeben DEFAULT_TIMEOUT.
        """
        import configparser
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read('settings.ini', encoding='utf-8-sig')
            raw = config.get('SchildAPI', 'timeout', fallback='').strip()
            if not raw:
                return DEFAULT_TIMEOUT
            wert = int(raw)
        except Exception:
            return DEFAULT_TIMEOUT
        return None if wert <= 0 else wert

    @staticmethod
    def _read_schulbesuch_workers_from_settings():
        """Liest [SchildAPI].schulbesuch_workers aus settings.ini.
        Default: SCHULBESUCH_WORKERS_DEFAULT (1 = sequenziell)."""
        import configparser
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read('settings.ini', encoding='utf-8-sig')
            raw = config.get('SchildAPI', 'schulbesuch_workers',
                             fallback=str(SCHULBESUCH_WORKERS_DEFAULT))
            return max(1, min(int(str(raw).strip()), SCHULBESUCH_WORKERS_MAX))
        except Exception:
            return SCHULBESUCH_WORKERS_DEFAULT

    def fetch_students(self, abschnitt_id=None, fetch_entlassdatum=True, allowed_statuses=None,
                       progress=None, workers=None):
        """
        Liefert (output_data_students, students_by_id) — exakt wie read_students()
        aus main.py es per CSV liefert. So kann der CSV-Pfad transparent ersetzt werden.

        Filter:
          - idSchuljahresabschnitt == aktueller Abschnitt
          - status in allowed_statuses (Default DEFAULT_ALLOWED_STATUSES)

        progress: optionales Callback progress(erledigt, gesamt, workers) fuer das
        Laden der Schulbesuchsdaten — der einzige Schritt, der pro Schueler einen
        eigenen Request braucht und bei grossen Schulen mehrere Minuten laeuft.
        Dieses Modul gibt bewusst selbst nichts aus (main.py haelt die Konsolen-
        Helfer); ohne Callback verhaelt sich alles wie bisher.

        workers: Anzahl paralleler Schulbesuch-Abrufe. None (Default) liest
        [SchildAPI].schulbesuch_workers aus der settings.ini; 1 bedeutet
        sequenziell wie bisher.
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
        #    Ein Request pro Schüler — bei grossen Schulen der mit Abstand
        #    laengste Schritt. Fortschritt wird nach aussen gemeldet, damit der
        #    Lauf nicht faelschlich als haengend wahrgenommen wird.
        entlassdatum_by_id = {}
        if fetch_entlassdatum:
            if workers is None:
                workers = self._read_schulbesuch_workers_from_settings()
            entlassdatum_by_id = self._fetch_entlassdaten(schueler_ids, workers, progress)

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
        config = configparser.ConfigParser(interpolation=None)
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
        config = configparser.ConfigParser(interpolation=None)
        try:
            config.read('settings.ini', encoding='utf-8-sig')
            raw = config.get('SchildAPI', 'allowed_statuses', fallback='')
            if not raw.strip():
                return set(DEFAULT_ALLOWED_STATUSES)
            return {int(s.strip()) for s in raw.split(',') if s.strip().isdigit()}
        except Exception:
            return set(DEFAULT_ALLOWED_STATUSES)
