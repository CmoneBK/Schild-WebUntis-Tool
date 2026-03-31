import requests
import json
import os

class WebUntisClient:
    def __init__(self, server_url, school, user, password, client_name="Schild-WebUntis-Tool"):
        self.server_url = server_url.rstrip('/')
        if not self.server_url.endswith('jsonrpc.do'):
            self.server_url += '/WebUntis/jsonrpc.do'
        
        self.school = school
        self.user = user
        self.password = password
        self.client_name = client_name
        self.session_id = None

    def _post(self, method, params=None):
        if params is None:
            params = {}
        
        payload = {
            "id": "1",
            "method": method,
            "params": params,
            "jsonrpc": "2.0"
        }
        
        headers = {'Content-Type': 'application/json'}
        cookies = {}
        if self.session_id:
            cookies = {'JSESSIONID': self.session_id}
            
        params_url = {'school': self.school}
        
        try:
            response = requests.post(
                self.server_url, 
                params=params_url, 
                json=payload, 
                headers=headers, 
                cookies=cookies,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            if 'error' in result:
                raise Exception(f"WebUntis API Fehler: {result['error'].get('message', 'Unbekannter Fehler')}")
            
            return result.get('result')
        except requests.exceptions.RequestException as e:
            raise Exception(f"Verbindungsfehler zu WebUntis: {e}")

    def authenticate(self):
        params = {
            "user": self.user,
            "password": self.password,
            "client": self.client_name
        }
        result = self._post("authenticate", params)
        if result and 'sessionId' in result:
            self.session_id = result['sessionId']
            return True
        return False

    def logout(self):
        if self.session_id:
            try:
                self._post("logout")
            except:
                pass
            self.session_id = None

    def get_teachers(self):
        if not self.session_id:
            self.authenticate()
        return self._post("getTeachers")

    def get_classes(self):
        if not self.session_id:
            self.authenticate()
        return self._post("getKlassen") # Method name in docs was sometimes getKlassen

    def test_connection(self):
        try:
            if self.authenticate():
                self.logout()
                return True, "Verbindung erfolgreich!"
            return False, "Authentifizierung fehlgeschlagen."
        except Exception as e:
            return False, str(e)
