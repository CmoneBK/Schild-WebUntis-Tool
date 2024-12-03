import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import configparser
import os
from oauth2client.service_account import ServiceAccountCredentials
import google.auth.transport.requests
import google.oauth2.service_account
import html2text
import time
import threading
import colorama
from colorama import Fore, Style, init

# Colorama initialisieren
init(autoreset=True)

# Thread-sicherer Zugriff
console_lock = threading.Lock()

def thread_safe_print(color, message):
    with console_lock:
        print(f"{color}{message}{Style.RESET_ALL}", flush=True)

# Hilfsfunktionen
def print_error(message):
    thread_safe_print(Fore.RED, message)

def print_warning(message):
    thread_safe_print(Fore.YELLOW, message)

def print_success(message):
    thread_safe_print(Fore.GREEN, message)

def print_info(message):
    thread_safe_print(Fore.CYAN, message)

def print_creation(message):
    thread_safe_print(Fore.WHITE, message)



def send_email(subject, body, to_addresses, attachment_path=None):
    # Konfigurationsdatei einlesen
    config = configparser.ConfigParser()
    config.read('email_settings.ini')
    smtp_server = config.get('Email', 'smtp_server')
    smtp_port = config.getint('Email', 'smtp_port')
    smtp_user = config.get('Email', 'smtp_user')
    smtp_password = config.get('Email', 'smtp_password', fallback=None)
    smtp_encryption = config.get('Email', 'smtp_encryption', fallback='starttls')
    use_oauth = config.getboolean('OAuth', 'use_oauth', fallback=False)
    access_token = None

    if use_oauth:
        credentials_path = config.get('OAuth', 'credentials_path')
        token_uri = config.get('OAuth', 'token_uri', fallback='https://oauth2.googleapis.com/token')
        client_id = config.get('OAuth', 'client_id')
        client_secret = config.get('OAuth', 'client_secret')

        # OAuth2 Token abrufen
        credentials = google.oauth2.service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/gmail.send"]
        )
        auth_request = google.auth.transport.requests.Request()
        credentials.refresh(auth_request)
        access_token = credentials.token

    # MIME Nachricht erstellen
    msg = MIMEMultipart()
    msg.add_header('MIME-Version', '1.0')
    msg.add_header('Content-Type', 'text/html; charset=utf-8')
    msg['From'] = smtp_user
    msg['To'] = ", ".join(to_addresses)
    msg['Subject'] = subject

    # Nachrichtentext hinzufügen
    msg.attach(MIMEText(body, 'html', _charset='utf-8'))

    # Anhang hinzufügen (falls vorhanden)
    if attachment_path:
        with open(attachment_path, 'rb') as attachment:
            part = MIMEApplication(attachment.read(), Name=os.path.basename(attachment_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(part)

    # SMTP Verbindung aufbauen und E-Mail senden
    try:
        if smtp_encryption.lower() == 'ssl':
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()

        if use_oauth and access_token:
            # Verwende OAuth2 zur Authentifizierung
            auth_string = f"user={smtp_user}\1auth=Bearer {access_token}\1\1"
            server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
        elif smtp_password:
            # Verwende Benutzername und Passwort zur Authentifizierung
            server.login(smtp_user, smtp_password)

        # Retry-Mechanismus bei temporären Fehlern (450er und 503er Fehler)
        retries = 3
        for i in range(retries):
            try:
                server.sendmail(smtp_user, to_addresses, msg.as_string())
                print_success("E-Mail erfolgreich gesendet!")
                break
            except smtplib.SMTPResponseException as e:
                if e.smtp_code in [450, 503]:
                    print_error(f"Temporärer Fehler ({e.smtp_code}): {e.smtp_error}. Versuch {i + 1} von {retries}.")
                    time.sleep(5)  # Wartezeit zwischen den Versuchen
                else:
                    raise e
        server.quit()
    except Exception as e:
        print_error(f"Fehler beim Senden der E-Mail: {e}")

def log_sent_email(subject, body, to_addresses):
    print_creation("Gesendete E-Mail:")
    print_creation(f"Empfänger: {', '.join(to_addresses)}")
    print_creation(f"Betreff: {subject}")
    print_creation("Inhalt:")
    print_creation(html2text.html2text(body))
