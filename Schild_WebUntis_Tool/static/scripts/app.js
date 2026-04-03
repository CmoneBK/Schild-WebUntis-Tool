document.addEventListener("DOMContentLoaded", function () {
    // --- Dark Mode Logic ---
    const darkModeToggle = document.getElementById("darkModeToggle");

    // Sync initial state if it was added to documentElement
    if (document.documentElement.classList.contains("dark-mode")) {
        document.body.classList.add("dark-mode");
        darkModeToggle.textContent = "☀️ Light Mode";
    }

    darkModeToggle.addEventListener("click", function () {
        document.body.classList.toggle("dark-mode");
        document.documentElement.classList.toggle("dark-mode");

        if (document.body.classList.contains("dark-mode")) {
            localStorage.setItem("darkMode", "enabled");
            darkModeToggle.textContent = "☀️ Light Mode";
        } else {
            localStorage.setItem("darkMode", "disabled");
            darkModeToggle.textContent = "🌙 Dark Mode";
        }
    });

    // Adjust Modal background style for dark mode
    $('#logViewerModal').on('show.bs.modal', function () {
        const pre = document.getElementById("logContentPre");
        if (document.body.classList.contains("dark-mode")) {
            pre.style.background = "#2a2a2a";
            pre.style.color = "#ddd";
        } else {
            pre.style.background = "#f8f9fa";
            pre.style.color = "#212529";
        }
    });

    // --- History Logic ---
    const loadAllHistoryBtn = document.getElementById("loadAllHistory");
    if (loadAllHistoryBtn) {
        loadAllHistoryBtn.addEventListener("click", () => {
            if (typeof window.loadHistory === "function") {
                window.loadHistory(0);
            }
        });
    }

    // Expose loadHistory globally so it can be called from unified toggle
    window.loadHistory = function (limit) {
        const tbody = document.querySelector("#historyTable tbody");
        tbody.innerHTML = "<tr><td colspan='3' class='text-center'>Lade Historie...</td></tr>";

        fetch(`/api/history?limit=${limit}`)
            .then(response => response.json())
            .then(data => {
                tbody.innerHTML = "";
                if (data.length === 0) {
                    tbody.innerHTML = "<tr><td colspan='3' class='text-center'>Keine Einträge gefunden.</td></tr>";
                    return;
                }

                data.forEach(entry => {
                    const tr = document.createElement("tr");

                    // Zeit
                    const tdTime = document.createElement("td");
                    tdTime.innerHTML = `<strong>${entry.display_time}</strong>`;
                    tr.appendChild(tdTime);

                    // Dateien
                    const tdFiles = document.createElement("td");
                    let fileHTML = "";
                    if (entry.log_file) fileHTML += `<div><span class="badge badge-info">LOG</span> ${entry.log_file}</div>`;
                    if (entry.xlsx_file) fileHTML += `<div><span class="badge badge-success">XLSX</span> ${entry.xlsx_file}</div>`;
                    tdFiles.innerHTML = fileHTML || "<em>Keine Dateien</em>";
                    tr.appendChild(tdFiles);

                    // Aktionen
                    const tdActions = document.createElement("td");
                    if (entry.log_file) {
                        const btn = document.createElement("button");
                        btn.className = "btn btn-sm btn-outline-primary";
                        btn.innerHTML = "📄 Log";
                        btn.onclick = () => viewLog(entry.log_file);
                        tdActions.appendChild(btn);
                    }
                    if (entry.xlsx_file) {
                        // Download Button
                        const btnDl = document.createElement("a");
                        btnDl.className = "btn btn-sm btn-outline-success ml-2";
                        btnDl.innerHTML = "📥 Excel";
                        btnDl.href = `/api/xlsx_download/${encodeURIComponent(entry.xlsx_file)}`;
                        btnDl.target = "_blank";
                        tdActions.appendChild(btnDl);

                        // View Button
                        const btnView = document.createElement("button");
                        btnView.className = "btn btn-sm btn-outline-info ml-1";
                        btnView.innerHTML = "🔍 View";
                        btnView.onclick = () => viewExcel(entry.xlsx_file);
                        tdActions.appendChild(btnView);
                    }
                    tr.appendChild(tdActions);

                    tbody.appendChild(tr);
                });
            })
            .catch(err => {
                console.error(err);
                tbody.innerHTML = `<tr><td colspan='3' class='text-danger'>Fehler beim Laden der Historie.</td></tr>`;
            });
    };
});

// Global function for onclick
function viewLog(filename) {
    const pre = document.getElementById("logContentPre");
    pre.textContent = "Lade Log-Datei...";
    $('#logViewerModal').modal('show');

    fetch(`/api/log_content/${encodeURIComponent(filename)}`)
        .then(response => {
            if (!response.ok) throw new Error("Netzwerkfehler oder Datei nicht gefunden");
            return response.text();
        })
        .then(text => {
            pre.textContent = text;
        })
        .catch(err => {
            pre.textContent = "Fehler beim Laden: " + err.message;
        });
}

// Global function for XLSX viewing
function viewExcel(filename) {
    const pre = document.getElementById("logContentPre");
    pre.innerHTML = "Lade Excel-Datei Vorschau...";
    $('#logViewerModal').modal('show');

    fetch(`/api/xlsx_view/${encodeURIComponent(filename)}`)
        .then(response => {
            if (!response.ok) throw new Error("Netzwerkfehler oder Datei nicht gefunden");
            return response.text();
        })
        .then(html => {
            pre.innerHTML = html;
        })
        .catch(err => {
            pre.textContent = "Fehler beim Laden: " + err.message;
        });
}

// --- Live Warning Status Polling ---
function refreshWarningStatuses() {
    const warningsPanel = document.getElementById("warningsPanel");
    // Poll only if there are warnings to track
    if (!warningsPanel || warningsPanel.getAttribute("data-has-warnings") !== "true") return;

    fetch('/api/get_warnings')
        .then(response => response.json())
        .then(warnings => {
            const rows = document.querySelectorAll("#warningsTableBody tr");
            warnings.forEach((w, index) => {
                if (rows[index]) {
                    const statusCell = rows[index].querySelector(".status-cell");
                    if (statusCell) {
                        const isSent = w.status === 'versendet';
                        const currentBadge = statusCell.querySelector(".badge");

                        // Only update if the status actually changed to avoid flickering
                        const newText = isSent ? '✅ Versendet' : '⏳ Offen';
                        if (currentBadge && currentBadge.textContent.trim() !== newText) {
                            const badgeClass = isSent ? 'badge-success' : 'badge-warning';
                            statusCell.innerHTML = `<span class="badge ${badgeClass}">${newText}</span>`;
                        }
                    }
                }
            });
        })
        .catch(err => console.debug("Status-Check im Hintergrund..."));
}

// --- Admin Refresh Logic ---
document.getElementById('btnRefreshAdminWarnings')?.addEventListener('click', function() {
    const content = document.getElementById('adminWarningContent');
    const loading = document.getElementById('adminWarningLoading');
    const tableBody = document.getElementById('adminWarningsTableBody');

    content.style.opacity = '0.5';
    loading.style.display = 'block';
    this.disabled = true;

    fetch('/api/refresh_admin_warnings', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            loading.style.display = 'none';
            content.style.opacity = '1';
            this.disabled = false;

            if (data.success) {
                window.showToast("System-Check abgeschlossen. " + data.count + " Warnungen gefunden.");
                // Refresh the UI with new warnings
                if (data.count > 0) {
                    let html = `
                    <div class="alert alert-warning">
                        <strong>Achtung:</strong> Es wurden Inkonsistenzen in den Stammdaten gefunden, die den Import nach WebUntis sowie die korrekte Warn-Funktionalität beeinträchtigen können.
                    </div>
                    <table class="table table-hover">
                        <thead class="thead-dark">
                            <tr>
                                <th>Typ</th>
                                <th>Details</th>
                                <th>Betroffene Schüler</th>
                            </tr>
                        </thead>
                        <tbody id="adminWarningsTableBody">`;

                    data.warnings.forEach(w => {
                        html += `
                        <tr>
                            <td><span class="badge badge-danger">${w.Typ}</span></td>
                            <td>${w.Details}</td>
                            <td>${w.Schüler || '-'}</td>
                        </tr>`;
                    });

                    html += `</tbody></table>`;
                    content.innerHTML = html;
                } else {
                    content.innerHTML = `
                    <div class="text-center py-5">
                        <h1 class="display-4 text-success">✅</h1>
                        <h3>Alles im grünen Bereich!</h3>
                        <p class="text-muted">Es wurden keine fehlerhaften Verknüpfungen oder fehlende Klassen/Lehrer gefunden.</p>
                    </div>`;
                }
            }
        })
        .catch(err => {
            loading.style.display = 'none';
            content.style.opacity = '1';
            this.disabled = false;
            window.showToast("Fehler beim System-Check: " + err);
        });
});

// Poll every 3 seconds while the page is open
setInterval(refreshWarningStatuses, 3000);
