document.addEventListener("DOMContentLoaded", function () {
    const settingsPanel = document.getElementById("settingsPanel");
    const saveSettingsButton = document.getElementById("saveSettings");
    const toggleSettingsButton = document.getElementById("toggle-settings");
    const directoryPicker = document.getElementById("directory-picker");

    async function selectDirectory(inputId) {
        if (window.showDirectoryPicker) {
            try {
                const directoryHandle = await window.showDirectoryPicker();
                const formData = new FormData();
                formData.append("directoryName", directoryHandle.name);

                // Optional: Sende den vollständigen Pfad an das Backend
                const response = await fetch("/process-directory", {
                    method: "POST",
                    body: formData,
                });

                if (response.ok) {
                    const result = await response.json();
                    const directoryPath = result.fullPath || directoryHandle.name;

                    // Konvertiere Backslashes in Forward Slashes (INI-kompatibel)
                    const formattedPath = directoryPath.replace(/\\/g, "/");
                    document.getElementById(inputId).value = formattedPath; // Aktualisiere das Eingabefeld
                } else {
                    console.error("Error processing directory:", response.statusText);
                }
            } catch (error) {
                console.error("Directory selection was cancelled or failed:", error);
            }
        } else {
            alert("Your browser does not support the directory picker. Please enter manually.");
        }
    }

    // Tabs und Inhalte initialisieren
    const tabs = [
        { id: "directories", form: "form-directories" },
        { id: "processing", form: "form-processing" },
        { id: "warnings", form: "form-warnings" },
        { id: "console", form: "form-console" },
        { id: "smtp", form: "form-smtp" },
        { id: "oauth", form: "form-oauth" },
        { id: "admin", form: "form-admin" },
        { id: "webuntis", form: "form-webuntis" },
    ];

    // Einstellungen laden
    async function loadSettings() {
        try {
            const response = await fetch("/load-settings");
            if (response.ok) {
                const settings = await response.json();

                // Map keys to forms
                const keyToFormId = {
                    // Directories
                    "classes_directory": "form-directories",
                    "teachers_directory": "form-directories",
                    "log_directory": "form-directories",
                    "xlsx_directory": "form-directories",
                    "import_directory": "form-directories",
                    "schildexport_directory": "form-directories",
                    "class_size_directory": "form-directories",
                    "attest_file_directory": "form-directories",
                    "nachteilsausgleich_file_directory": "form-directories",
                    "nachteilsausgleich_excel_directory": "form-directories",
                    // ProcessingOptions
                    "use_abschlussdatum": "form-processing",
                    "create_second_file": "form-processing",
                    "create_class_size_file": "form-processing",
                    "enable_attestpflicht_column": "form-processing",
                    "enable_nachteilsausgleich_column": "form-processing",
                    "treat_status_6_as_active": "form-processing",
                    "disable_import_file_creation": "form-processing",
                    "disable_import_file_if_admin_warning": "form-processing",
                    // Warnings
                    "warn_entlassdatum": "form-warnings",
                    "warn_aufnahmedatum": "form-warnings",
                    "warn_klassenwechsel": "form-warnings",
                    "class_change_recipients": "form-warnings",
                    "warn_new_students": "form-warnings",
                    "warn_karteileichen": "form-warnings",
                    // Console
                    "timeframe_hours": "form-console",
                    // Email settings
                    "smtp_server": "form-smtp",
                    "smtp_port": "form-smtp",
                    "smtp_user": "form-smtp",
                    "smtp_password": "form-smtp",
                    "smtp_encryption": "form-smtp",
                    // OAuth
                    "use_oauth": "form-oauth",
                    "credentials_path": "form-oauth",
                    // Admin
                    "admin_email": "form-admin",
                    // WebUntis API
                    "use_api": "form-webuntis",
                    "server_url": "form-webuntis",
                    "school": "form-webuntis",
                    "user": "form-webuntis",
                    "password": "form-webuntis",
                    "client_name": "form-webuntis",
                };

                // Loop over settings and populate forms
                Object.entries(settings).forEach(([section, sectionValues]) => {
                    Object.entries(sectionValues).forEach(([key, value]) => {
                        const formId = keyToFormId[key];
                        if (formId) {
                            const form = document.getElementById(formId);
                            if (form) {
                                const input = form.querySelector(`[name="${key}"]`);
                                if (input) {
                                    input.value = value;
                                }
                            }
                        }
                    });
                });
            } else {
                console.error("Fehler beim Laden der Einstellungen:", response.statusText);
            }
        } catch (error) {
            console.error("Fehler beim Laden der Einstellungen:", error);
        }
    }

    document.getElementById("saveSettings").addEventListener("click", saveSettings);

    // Einstellungen speichern
    async function saveSettings() {
        const settings = {};

        // Map keys to sections
        const keyToSection = {
            // Directories
            "classes_directory": "Directories",
            "teachers_directory": "Directories",
            "log_directory": "Directories",
            "xlsx_directory": "Directories",
            "import_directory": "Directories",
            "schildexport_directory": "Directories",
            "class_size_directory": "Directories",
            "attest_file_directory": "Directories",
            "nachteilsausgleich_file_directory": "Directories",
            "nachteilsausgleich_excel_directory": "Directories",
            // ProcessingOptions
            "use_abschlussdatum": "ProcessingOptions",
            "create_second_file": "ProcessingOptions",
            "warn_entlassdatum": "ProcessingOptions",
            "warn_aufnahmedatum": "ProcessingOptions",
            "warn_klassenwechsel": "ProcessingOptions",
            "class_change_recipients": "ProcessingOptions",
            "warn_new_students": "ProcessingOptions",
            "warn_karteileichen": "ProcessingOptions",
            "create_class_size_file": "ProcessingOptions",
            "timeframe_hours": "ProcessingOptions",
            "enable_attestpflicht_column": "ProcessingOptions",
            "enable_nachteilsausgleich_column": "ProcessingOptions",
            "treat_status_6_as_active": "ProcessingOptions",
            "disable_import_file_creation": "ProcessingOptions",
            "disable_import_file_if_admin_warning": "ProcessingOptions",
            // Email settings
            "smtp_server": "Email",
            "smtp_port": "Email",
            "smtp_user": "Email",
            "smtp_password": "Email",
            "smtp_encryption": "Email",
            // OAuth
            "use_oauth": "OAuth",
            "credentials_path": "OAuth",
            // Admin
            "admin_email": "Email", // Since admin_email is under [Email] section
            // WebUntis API
            "use_api": "WebUntisAPI",
            "server_url": "WebUntisAPI",
            "school": "WebUntisAPI",
            "user": "WebUntisAPI",
            "password": "WebUntisAPI",
            "client_name": "WebUntisAPI",
        };

        // Collect data from all forms
        tabs.forEach((tab) => {
            const form = document.getElementById(tab.form);
            if (form) {
                const formData = new FormData(form);
                formData.forEach((value, key) => {
                    const section = keyToSection[key];
                    if (section) {
                        if (!settings[section]) settings[section] = {};
                        settings[section][key] = value;
                    }
                });
            }
        });

        try {
            // Send settings to server
            const response = await fetch("/save-settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ settings }),
            });
            if (!response.ok) {
                console.error("Fehler beim Speichern der Einstellungen:", response.statusText);
                alert("Fehler beim Speichern der Einstellungen.");
            } else {
                alert("Einstellungen erfolgreich gespeichert!");
            }
        } catch (error) {
            console.error("Fehler beim Speichern der Einstellungen:", error);
            alert("Fehler beim Speichern der Einstellungen.");
        }
    }

    // Load settings when the page loads
    loadSettings();
});

// Label tooltip logic (runs immediately, not on DOMContentLoaded)
const labels = {
    use_abschlussdatum: "...falls dieses früher liegt oder kein Entlassdatum existiert",
    enable_attestpflicht_column: "Analysiert Daten aus dem Attestpflicht-Datei-Verzeichnis für eine zusätzliche Ja/Nein Spalte",
    enable_nachteilsausgleich_column: "Analysiert Daten aus dem Nachteilsausgleich-Datei-Verzeichnis für eine zusätzliche Ja/Nein Spalte",
    treat_status_6_as_active: "Schild-Status 6 entspricht externen Schülern. Wenn aktiviert, werden sie wie reguläre aktive Schüler behandelt (Klassengrößen, keine Karteileichen-Meldung).",
    create_second_file: "Abgänger und Abschlüsse ohne...",
    create_class_size_file: "Nützlich für Stundenplaner und das Vertretungsteam",
    warn_entlassdatum: "Von der (Stand jetzt) Vergangneheit auf dem Zeitstrahl nach rechts (generiert Dokumentationslücke)",
    warn_aufnahmedatum: "z.B. von einer weniger weiten Vergangenheit in eine weite(re) Vergangenheit (generiert Dokumentationslücke)",
    warn_klassenwechsel: "z.B. zur Information wegen Schülergruppenzuweisung oder auch Nachdokumentation/Korrektur des Wechseldatums",
    class_change_recipients: "Bestimmen Sie, wer im Fall eines Klassenwechsels die Benachrichtigung erhält.",
    warn_new_students: "z.B.: zur Information wegen Schülergruppenzuweisung",
    timeframe_hours: "Zeitfenster in Stunden für die Vergleiche.",
    import_directory: "Verzeichnis, in dem die Import-Dateien für WebUntis gespeichert werden.",
    schildexport_directory: "Verzeichnis, aus dem die Schild-Exporte abgerufen werden.",
    classes_directory: "Verzeichnis für die Klassendaten. Sie werden für die Klassenlehrkraft-Zuordnung für die Warnungs-Funktion benötigt.",
    teachers_directory: "Verzeichnis für die Lehrerdaten. Sie werden für die Namensermittlung und Email-Adressen-Ermittlung für die Warnungs-Funktion benötigt.",
    log_directory: "Verzeichnis für die Log-Dateien. Darunter Änderungs-Logs zwischen der neuesten und vorherigen Import-Datei, aber auch Logs für den Logs-Versand an die Admin-Email Adresse.",
    xlsx_directory: "Verzeichnis für die Excel-Dateien. Dies sind ebenfalls Log-Datein aber als ganze Tabelle mit markierten Änderungen.",
    class_size_directory: "Verzeichnis für eine separat generierte Klassengrößendatei zur Verwendung durch Stundenplaner und Vertretungsteam",
    attest_file_directory: "Verzeichnis für eine ImportDatei, die nur die Schüler mit Attestpflicht enthält zur Verwendung Attestpflicht-Spalte",
    nachteilsausgleich_file_directory: "Verzeichnis für eine ImportDatei, die nur die Schüler mit Nachteilsausgleich enthält zur Verwendung Nachteilsausgleich-Spalte",
    nachteilsausgleich_excel_directory: "Verzeichnis, in dem die Excel-Arbeitsdatei für Sonderpädagogen (Nachteilsausgleichdetails) gespeichert wird.",
    smtp_server: "SMTP-Server-Adresse für den E-Mail-Versand.",
    smtp_port: "Port des SMTP-Servers (z. B. 587 für STARTTLS).",
    smtp_user: "Benutzername für den SMTP-Server.",
    smtp_password: "Passwort für den SMTP-Server.",
    admin_email: "E-Mail-Adresse des Administrators für Benachrichtigungen. Darunter Admin-Warnungen bei im Vergleich zum Schild-Export fehlenden Klassen- und Lehrkraftdaten, aber auch zum Versand von Log-Emails und -Datein."
};

function getLabel(key) {
    return labels[key] || key; // Fallback auf den Key, falls kein Label existiert
}

document.querySelectorAll("label").forEach(label => {
    const key = label.getAttribute("for");
    if (key && labels[key]) {
        label.innerHTML += `<small class="text-muted"> (${getLabel(key)})</small>`;
    }
});
