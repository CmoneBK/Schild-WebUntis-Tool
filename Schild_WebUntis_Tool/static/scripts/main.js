// Ensure class_change_recipients is submitted with the main form
const mainForm = document.querySelector("form[method='post']");
if (mainForm) {
    mainForm.addEventListener("submit", async function (e) {
        // If this is a re-submission after check, don't re-check
        if (this.dataset.validated === "true") {
            this.dataset.validated = "false";
            return;
        }

        // Check for open warnings
        const openWarnings = document.querySelectorAll("#warningsTableBody .badge-warning");
        if (openWarnings.length > 0) {
            const message = "Es sind noch offene (nicht versendete) Warnungen vorhanden. Wenn Sie nun neu verarbeiten, werden diese Warnungen überschrieben und tauchen nicht mehr auf. Möchten Sie trotzdem fortfahren?";
            if (!confirm(message)) {
                e.preventDefault();
                return;
            }
        }

        // Perform a quick pre-check via API
        e.preventDefault();
        try {
            const response = await fetch('/api/validate_imports');
            const report = await response.json();

            if (!report.success) {
                let errorMsg = "Die Vorab-Prüfung der Dateien hat Fehler ergeben:\n";
                for (const [file, res] of Object.entries(report.files)) {
                    if (res.status === 'error') {
                        errorMsg += `- ${file}: ${res.message || res.messages[0]}\n`;
                    }
                }
                errorMsg += "\nMöchten Sie trotz dieser Fehler verarbeiten? (Dies kann zu Fehlern führen)";
                if (!confirm(errorMsg)) {
                    return;
                }
            } else {
                // Check for warnings even if success
                let hasWarnings = false;
                let warnMsg = "Hinweise zur Dateiprüfung:\n";
                for (const [file, res] of Object.entries(report.files)) {
                    if (res.status === 'warning') {
                        hasWarnings = true;
                        warnMsg += `- ${file}:\n  * ${res.messages.join('\n  * ')}\n`;
                    }
                }
                if (hasWarnings) {
                    warnMsg += "\nMöchten Sie trotzdem fortfahren?";
                    if (!confirm(warnMsg)) return;
                }
            }
        } catch (err) {
            console.error("Validierungsfehler:", err);
        }

        // Reset E-Mail Generation Button
        const generateEmailsBtn = document.getElementById("generateEmails");
        if (generateEmailsBtn) {
            generateEmailsBtn.innerHTML = "✍ Emails Generieren";
            generateEmailsBtn.classList.remove("btn-warning");
            generateEmailsBtn.classList.add("btn-info");
        }

        let hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "class_change_recipients";
        let selectElem = document.getElementById("class_change_recipients");
        if (selectElem) {
            hiddenInput.value = selectElem.value;
            this.appendChild(hiddenInput);
        }

        this.dataset.validated = "true";
        this.submit();
    });
}

// --- Validate Files Button Logic ---
document.getElementById("validateImports")?.addEventListener("click", function() {
    const container = document.getElementById("validationReportContainer");
    const btn = this;
    btn.innerHTML = "⌛ Prüfe...";
    btn.disabled = true;

    fetch('/api/validate_imports')
        .then(r => r.json())
        .then(report => {
            btn.innerHTML = "🔍 Dateien prüfen";
            btn.disabled = false;
            container.innerHTML = ""; // Clear old reports

            if (report.success && Object.values(report.files).every(f => f.status === 'success')) {
                container.innerHTML = `<div class="alert alert-success alert-dismissible fade show">
                    ✅ Alle Dateien erfolgreich geprüft!
                    <button type="button" class="close" data-dismiss="alert">&times;</button>
                </div>`;
                return;
            }

            for (const [fileName, result] of Object.entries(report.files)) {
                if (result.status !== 'success') {
                    const alertClass = result.status === 'error' ? 'danger' : 'warning';
                    let html = `<div class="alert alert-${alertClass} alert-dismissible fade show">
                        <strong>${fileName}:</strong> ${result.message || ''}`;

                    if (result.messages && result.messages.length > 0) {
                        html += `<ul class="mb-0">`;
                        result.messages.forEach(m => html += `<li>${m}</li>`);
                        html += `</ul>`;
                    }

                    html += `<button type="button" class="close" data-dismiss="alert">&times;</button></div>`;
                    container.innerHTML += html;
                }
            }
        })
        .catch(err => {
            btn.innerHTML = "🔍 Dateien prüfen";
            btn.disabled = false;
            alert("Fehler bei der Prüfung: " + err);
        });
});

// --- Unified Email Logic ---
function updateGenerateEmailButtons(hasEmails) {
    const btns = [document.getElementById("generateEmails"), document.getElementById("headerGenerateEmails")];
    btns.forEach(btn => {
        if (!btn) return;
        if (hasEmails) {
            btn.innerHTML = "🔍 Generierte Mails anzeigen";
            btn.classList.remove("btn-info");
            btn.classList.add("btn-warning");
        } else {
            btn.innerHTML = "✍ Emails Generieren";
            btn.classList.remove("btn-warning");
            btn.classList.add("btn-info");
        }
    });
}

// On page load, check status
fetch("/api/check_emails_status")
    .then(response => response.json())
    .then(data => {
        updateGenerateEmailButtons(data.has_emails);
    });

async function handleEmailGeneration(button) {
    // Falls die Emails bereits generiert wurden, leiten wir weiter
    if (button.textContent.includes("anzeigen")) {
        window.location.href = "/view_generated_emails";
        return;
    }

    const originalHTML = button.innerHTML;
    const allGenerateBtns = [document.getElementById("generateEmails"), document.getElementById("headerGenerateEmails")];

    allGenerateBtns.forEach(b => { if(b) { b.disabled = true; b.innerHTML = "⌛ Generiere..."; } });

    try {
        const response = await fetch("/generate_emails", { method: "POST" });
        const data = await response.json();

        allGenerateBtns.forEach(b => { if(b) b.disabled = false; });
        alert(data.message);

        if (data.emails) {
            updateGenerateEmailButtons(true);
        } else {
            updateGenerateEmailButtons(false);
        }
    } catch (err) {
        allGenerateBtns.forEach(b => { if(b) { b.disabled = false; b.innerHTML = "✍ Emails Generieren"; } });
        alert("Fehler bei der Generierung: " + err);
    }
}

document.getElementById("generateEmails")?.addEventListener("click", function() { handleEmailGeneration(this); });
document.getElementById("headerGenerateEmails")?.addEventListener("click", function() { handleEmailGeneration(this); });

function handleSendEmails() {
    fetch("/send_emails", {
        method: "POST"
    }).then(response => response.json()).then(data => {
        alert(data.message);
    });
}

document.getElementById("sendEmails")?.addEventListener("click", handleSendEmails);
document.getElementById("headerSendEmails")?.addEventListener("click", handleSendEmails);

document.getElementById("testApiConnection")?.addEventListener("click", function() {
    const data = {
        server_url: document.getElementById("server_url").value,
        school: document.getElementById("school").value,
        user: document.getElementById("user").value,
        password: document.getElementById("password").value,
        client_name: document.getElementById("client_name").value
    };

    this.disabled = true;
    this.textContent = "⌛ Teste...";

    fetch("/test_api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        this.disabled = false;
        this.textContent = "🔍 Verbindung testen";
    })
    .catch(err => {
        alert("Fehler beim Verbindungstest: " + err);
        this.disabled = false;
        this.textContent = "🔍 Verbindung testen";
    });
});
