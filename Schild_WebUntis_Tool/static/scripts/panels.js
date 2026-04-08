document.addEventListener("DOMContentLoaded", function () {
    console.log("Main DOMContentLoaded fired");
    // Unified Panel Configuration
    const panels = {
        settingsPanel: document.getElementById("settingsPanel"),
        emailEditor: document.getElementById("emailEditor"),
        shortcutCreator: document.getElementById("shortcutCreator"),
        uploadArea: document.getElementById("uploadArea"),
        historyPanel: document.getElementById("historyPanel"),
        warningsPanel: document.getElementById("warningsPanel"),
        dashboardPanel: document.getElementById("dashboardPanel"),
        adminPanel: document.getElementById("adminPanel"),
    };
    console.log("Panels:", panels);

    const toggleButtons = {
        toggleSettingsButton: document.getElementById("toggle-settings"),
        toggleEditorButton: document.getElementById("toggleEditor"),
        toggleShortcutButton: document.getElementById("toggleShortcutCreator"),
        toggleUploadButton: document.getElementById("toggleUploadArea"),
        toggleHistoryButton: document.getElementById("toggleHistory"),
        toggleWarningsButton: document.getElementById("toggleWarnings"),
        toggleDashboardButton: document.getElementById("toggleDashboard"),
        toggleAdminCheckButton: document.getElementById("toggleAdminCheck"),
    };

    const settingsTabs = document.querySelectorAll("#settingsPanel .nav-link");
    const settingsContentPanels = document.querySelectorAll("#settingsPanel .tab-content > .tab-pane");

    if (toggleButtons.toggleDashboardButton) {
        toggleButtons.toggleDashboardButton.addEventListener("click", () => {
            togglePanel("dashboardPanel");
            if (panels.dashboardPanel.style.display === "block") {
                loadDashboardData();
                loadClassList();
            }
        });
    }

    let charts = {}; // Globale Referenz für Chart-Instanzen

    let currentHotspotLimit = 5;

    async function loadDashboardData(fieldFilter = null, hotspotLimit = null) {
        if (hotspotLimit !== null) currentHotspotLimit = hotspotLimit;
        try {
            let url = `/api/history/stats?hotspot_limit=${currentHotspotLimit}`;
            if (fieldFilter) {
                url += `&field=${encodeURIComponent(fieldFilter)}`;
            }
            const response = await fetch(url);
            const data = await response.json();

            // Einfache Statistik-Karten
            const totalChanges = Object.values(data.categories).reduce((a, b) => a + b, 0);
            document.getElementById("stat-total-changes").innerText = totalChanges;
            document.getElementById("stat-class-changes").innerText = data.categories["Klasse"] || 0;
            document.getElementById("stat-active-students").innerText = data.categories["Status"] || 0;

            // 1. Monats-Trend (Line Chart)
            renderChart('chart-monthly', 'line', {
                labels: Object.keys(data.monthly),
                datasets: [{
                    label: 'Änderungen',
                    data: Object.values(data.monthly),
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    tension: 0.3,
                    fill: true
                }]
            });

            // 2. Kategorien (Pie Chart)
            renderChart('chart-categories', 'pie', {
                labels: Object.keys(data.categories),
                datasets: [{
                    data: Object.values(data.categories),
                    backgroundColor: ['#e74c3c', '#3498db', '#f1c40f', '#2ecc71', '#9b59b6', '#e67e22']
                }]
            }, { plugins: { legend: { position: 'right' } } });

            // 3. Hotspots (Horizontal Bar)
            renderChart('chart-hotspots', 'bar', {
                labels: Object.keys(data.hotspots),
                datasets: [{
                    label: 'Anzahl Änderungen',
                    data: Object.values(data.hotspots),
                    backgroundColor: '#e74c3c'
                }]
            }, { indexAxis: 'y' });

            // 4. Detail-Trends (Stacked Bar Chart)
            window.dashboardTrendData = data.trends;
            renderTrendChart('monthly');

        } catch (error) {
            console.error("Dashboard-Fehler:", error);
        }
    }

    function renderTrendChart(timeUnit) {
        const trendData = window.dashboardTrendData?.[timeUnit];
        if (!trendData) return;

        const labels = Object.keys(trendData).sort();
        const fields = new Set();
        labels.forEach(unit => Object.keys(trendData[unit]).forEach(f => fields.add(f)));

        // Wir nutzen die Top-Farben für die häufigsten Felder
        const colorPalette = ['#e74c3c', '#3498db', '#f1c40f', '#2ecc71', '#9b59b6', '#e67e22', '#1abc9c', '#34495e', '#7f8c8d'];

        const datasets = Array.from(fields).map((field, index) => {
            return {
                label: field,
                data: labels.map(unit => trendData[unit][field] || 0),
                backgroundColor: colorPalette[index % colorPalette.length],
                stack: 'combined'
            };
        });

        renderChart('chart-trends', 'bar', {
            labels: labels,
            datasets: datasets
        }, {
            scales: {
                x: { stacked: true },
                y: { stacked: true }
            },
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12 } }
            }
        });

        // Button-Styles aktualisieren
        document.getElementById('btn-trend-monthly').classList.toggle('active', timeUnit === 'monthly');
        document.getElementById('btn-trend-weekly').classList.toggle('active', timeUnit === 'weekly');
    }

    document.getElementById('btn-trend-monthly')?.addEventListener('click', () => renderTrendChart('monthly'));
    document.getElementById('btn-trend-weekly')?.addEventListener('click', () => renderTrendChart('weekly'));

    document.getElementById('hotspot-filter')?.addEventListener('change', (e) => {
        currentHotspotLimit = 5;
        const container = document.getElementById('chart-hotspots-container');
        if (container) container.style.height = '300px';
        loadDashboardData(e.target.value);
    });

    document.getElementById('btn-hotspot-more')?.addEventListener('click', () => {
        const fieldFilter = document.getElementById('hotspot-filter')?.value || null;
        const newLimit = currentHotspotLimit + 5;
        const container = document.getElementById('chart-hotspots-container');
        if (container) container.style.height = (300 + (newLimit - 5) * 40) + 'px';
        loadDashboardData(fieldFilter, newLimit);
    });

    // Handle dashboard tab changes to correctly resize charts
    $('#dashboardTabs a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        const targetId = e.target.getAttribute('href');
        document.querySelectorAll(targetId + ' canvas').forEach(canvas => {
            const chart = Chart.getChart(canvas);
            if (chart) chart.resize();
        });
    });

    async function loadClassList() {
        try {
            const response = await fetch("/api/history/classes");
            const classes = await response.json();
            const select = document.getElementById("dashboard-class-input");

            // Platzhalter-Option behalten, Rest neu befüllen
            select.innerHTML = '<option value="">Klasse wählen...</option>';
            classes.forEach(cls => {
                const opt = document.createElement("option");
                opt.value = cls;
                opt.textContent = cls;
                select.appendChild(opt);
            });

            window.availableClasses = classes;
        } catch (err) {
            console.error("Fehler beim Laden der Klassenliste:", err);
        }
    }

    document.getElementById("dashboard-class-input").addEventListener("change", function() {
        const className = this.value;
        if (className) {
            loadClassStats(className);
        } else {
            document.getElementById("class-stats-placeholder").style.display = "block";
            document.getElementById("class-stats-content").style.display = "none";
        }
    });

    async function loadClassStats(className) {
        try {
            const response = await fetch(`/api/history/class_stats/${encodeURIComponent(className)}`);
            const data = await response.json();

            document.getElementById("class-stats-placeholder").style.display = "none";
            document.getElementById("class-stats-content").style.display = "block";

            // Chart für Klassenkategorien
            renderChart('chart-class-categories', 'doughnut', {
                labels: Object.keys(data.categories),
                datasets: [{
                    data: Object.values(data.categories),
                    backgroundColor: ['#e74c3c', '#3498db', '#f1c40f', '#2ecc71', '#1abc9c', '#9b59b6']
                }]
            }, { plugins: { legend: { position: 'bottom' } } });

            // Table für Klassen-Timeline
            const tableBody = document.getElementById("class-history-table-body");
            tableBody.innerHTML = data.timeline.map(t => `
                <tr>
                    <td class="text-nowrap">${t.timestamp}</td>
                    <td><strong>${t.name}</strong></td>
                    <td>${t.field}</td>
                    <td><span class="text-danger">${t.old_value}</span> ➡️ <span class="text-success">${t.new_value}</span></td>
                </tr>
            `).join('');

            // Markierung für Kopierfunktion
            window.currentClassTimeline = data.timeline;
            window.currentClassName = className;

        } catch (err) {
            console.error("Fehler beim Laden der Klassenstats:", err);
        }
    }

    function renderChart(canvasId, type, data, options = {}) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        if (charts[canvasId]) charts[canvasId].destroy();
        charts[canvasId] = new Chart(ctx, {
            type: type,
            data: data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                ...options
            }
        });
    }

    // Historie Suche
    document.getElementById("btn-search-history").addEventListener("click", performSearch);
    document.getElementById("student-search-query").addEventListener("keypress", (e) => {
        if (e.key === "Enter") performSearch();
    });

    async function performSearch() {
        const q = document.getElementById("student-search-query").value;
        const resultsDiv = document.getElementById("student-history-results");
        if (q.length < 2) return;

        resultsDiv.innerHTML = "⌛ Suche...";
        const response = await fetch(`/api/history/search?q=${encodeURIComponent(q)}`);
        const data = await response.json();

        if (data.length === 0) {
            resultsDiv.innerHTML = "<p class='text-center mt-3'>Keine Einträge gefunden.</p>";
            return;
        }

        let html = "";
        data.forEach(item => {
            html += `
                <div class="card mb-3 shadow-sm border-left-info">
                    <div class="card-header bg-light d-flex justify-content-between align-items-center">
                        <span><strong>${item.student.name}</strong> (ID: ${item.student.id})</span>
                        <div>
                            <button class="btn btn-xs btn-outline-secondary py-0" style="font-size: 0.7rem;" onclick="copyStudentTimeline('${item.student.id}')">📋 Kopieren</button>
                            <button class="btn btn-xs btn-outline-success py-0 ml-1" style="font-size: 0.7rem;" onclick="exportStudentTimeline('${item.student.id}')">📊 Excel</button>
                        </div>
                    </div>
                    <div class="card-body p-2">
                        <table class="table table-sm mb-0" style="font-size: 0.85rem;">
                            <thead><tr><th>Datum</th><th>Feld</th><th>Änderung</th></tr></thead>
                            <tbody>
                                ${item.timeline.map(t => `
                                    <tr>
                                        <td class="text-nowrap">${t.timestamp}</td>
                                        <td>${t.field}</td>
                                        <td><span class="text-danger">${t.old_value}</span> ➡️ <span class="text-success">${t.new_value}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
        });
        resultsDiv.innerHTML = html;
        window.lastStudentSearchResults = data;
    }

    // Export Hilfsfunktionen
    window.copyClassTimeline = function() {
        if (!window.currentClassTimeline) return;
        let text = "Datum\tName\tID\tFeld\tAlt\tNeu\n";
        window.currentClassTimeline.forEach(t => {
            text += `${t.timestamp}\t${t.name}\t${t.student_id}\t${t.field}\t${t.old_value}\t${t.new_value}\n`;
        });
        navigator.clipboard.writeText(text);
        showToast("Klassen-Historie in Zwischenablage kopiert.");
    };

    window.exportClassTimeline = function() {
        if (!window.currentClassName) return;
        window.location.href = `/api/history/export/excel?type=class&id=${encodeURIComponent(window.currentClassName)}`;
    };

    window.copyStudentTimeline = function(studentId) {
        const item = window.lastStudentSearchResults.find(i => i.student.id === studentId);
        if (!item) return;
        let text = "Datum\tFeld\tAlt\tNeu\tQuelle\n";
        item.timeline.forEach(t => {
            text += `${t.timestamp}\t${t.field}\t${t.old_value}\t${t.new_value}\t${t.file_b}\n`;
        });
        navigator.clipboard.writeText(text);
        showToast(`Historie von ${item.student.name} kopiert.`);
    };

    window.exportStudentTimeline = function(studentId) {
        window.location.href = `/api/history/export/excel?type=student&id=${encodeURIComponent(studentId)}`;
    };

    function showToast(msg) {
        const toast = document.createElement("div");
        toast.style.position = "fixed";
        toast.style.bottom = "20px";
        toast.style.right = "20px";
        toast.style.backgroundColor = "#333";
        toast.style.color = "#fff";
        toast.style.padding = "10px 20px";
        toast.style.borderRadius = "5px";
        toast.style.zIndex = "9999";
        toast.innerText = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }

    // DB Management Buttons
    window.clearHistory = async function() {
        if (!confirm("Möchten Sie wirklich die gesamte Historie löschen? Dieser Vorgang kann nicht rückgängig gemacht werden.")) return;
        try {
            const response = await fetch("/api/history/clear", { method: 'POST' });
            const res = await response.json();
            if (res.success) {
                showToast("Historie erfolgreich gelöscht.");
                location.reload();
            }
        } catch (err) { alert("Fehler beim Löschen."); }
    };

    window.syncClasses = async function() {
        try {
            showToast("Synchronisiere Klassen-Daten...");
            const response = await fetch("/api/history/sync", { method: 'POST' });
            const res = await response.json();
            if (res.success) {
                showToast(res.message);
                loadClassList(); // Liste im Dashboard aktualisieren
            } else {
                alert(res.message);
            }
        } catch (err) { alert("Fehler bei der Synchronisierung."); }
    };

    document.getElementById("btn-reindex-history").addEventListener("click", async () => {
        const btn = document.getElementById("btn-reindex-history");
        btn.disabled = true;
        btn.innerText = "⌛ Indiziere...";
        const r = await fetch("/api/history/reindex", { method: "POST" });
        const data = await r.json();
        alert(data.message);
        btn.disabled = false;
        btn.innerText = "🔄 Bestehende Logs neu indizieren";
        loadDashboardData();
    });

    document.getElementById("btn-reset-history").addEventListener("click", async () => {
        if (!confirm("Historie wirklich zurücksetzen? Alle statistischen Daten werden unwiderruflich gelöscht.")) return;
        await fetch("/api/history/reset", { method: "POST" });
        alert("Historie wurde zurückgesetzt.");
        loadDashboardData();
    });

    function togglePanel(panelKey) {
        console.log("togglePanel called with:", panelKey);
        console.log("panels:", panels);
        Object.entries(panels).forEach(([key, panel]) => {
            if (!panel) {
                console.log("Panel not found:", key);
                return;
            }
            if (key === panelKey) {
                // Show the selected panel
                const isHidden = panel.style.display === "none" || panel.style.display === "";
                console.log("Panel", key, "isHidden:", isHidden, "current display:", panel.style.display);
                panel.style.display = isHidden ? "block" : "none";
                console.log("Set display to:", panel.style.display);

                if (isHidden) {
                    // Panel-Öffnung an Server melden
                    fetch('/api/panel_opened', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ panel: panelKey })
                    }).catch(() => {});

                    if (panelKey === "settingsPanel") {
                        activateFirstTab();
                    } else if (panelKey === "historyPanel") {
                        if (typeof window.loadHistory === "function") {
                            window.loadHistory(30);
                        }
                    }
                    // Automatisches Scrollen zum Bereich
                    setTimeout(() => {
                        panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 100);
                }
            } else {
                // Hide other panels
                panel.style.display = "none";
            }
        });
    }

    function activateFirstTab() {
        settingsTabs.forEach((tab) => tab.classList.remove("active"));
        settingsContentPanels.forEach((content) => content.classList.remove("show", "active"));
        if (settingsTabs.length > 0 && settingsContentPanels.length > 0) {
            settingsTabs[0].classList.add("active");
            settingsContentPanels[0].classList.add("show", "active");
        }
    }

    // Bind all toggle buttons
    if (toggleButtons.toggleShortcutButton) {
        toggleButtons.toggleShortcutButton.addEventListener("click", () => togglePanel("shortcutCreator"));
    }
    if (toggleButtons.toggleAdminCheckButton) {
        toggleButtons.toggleAdminCheckButton.addEventListener("click", () => togglePanel("adminPanel"));
    }
    if (toggleButtons.toggleSettingsButton) {
        toggleButtons.toggleSettingsButton.addEventListener("click", () => togglePanel("settingsPanel"));
    }
    if (toggleButtons.toggleEditorButton) {
        toggleButtons.toggleEditorButton.addEventListener("click", () => togglePanel("emailEditor"));
    }
    if (toggleButtons.toggleUploadButton) {
        toggleButtons.toggleUploadButton.addEventListener("click", () => togglePanel("uploadArea"));
    }
    if (toggleButtons.toggleHistoryButton) {
        toggleButtons.toggleHistoryButton.addEventListener("click", () => togglePanel("historyPanel"));
    }
    if (toggleButtons.toggleWarningsButton) {
        toggleButtons.toggleWarningsButton.addEventListener("click", () => togglePanel("warningsPanel"));
    }

    // Ensure all panels are initially hidden
    Object.values(panels).forEach((panel) => { if (panel) panel.style.display = "none"; });

    // Auto-open warnings if present
    const warningsPanel = document.getElementById("warningsPanel");
    if (warningsPanel && warningsPanel.getAttribute("data-has-warnings") === "true") {
        togglePanel("warningsPanel");
        warningsPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
});
