document.addEventListener("DOMContentLoaded", function () {
    // Initialisiere WYSIWYG-Editoren
    // Register style attributor for inline styles (compatible with emails)
    const AlignStyle = Quill.import('attributors/style/align');
    Quill.register(AlignStyle, true);

    const quillOptions = {
        theme: 'snow',
        modules: {
            clipboard: {
                matchers: [
                    ['BR', (node, delta) => {
                        return delta.insert('\n');
                    }]
                ]
            }
        }
    };

    const editorBodyEntlassdatum = new Quill('#editorBodyEntlassdatum', quillOptions);
    const editorBodyAufnahmedatum = new Quill('#editorBodyAufnahmedatum', quillOptions);
    const editorBodyKlassenwechsel = new Quill('#editorBodyKlassenwechsel', quillOptions);
    const editorBodyNewStudent = new Quill('#editorBodyNewStudent', quillOptions);
    const editorBodyKarteileiche = new Quill('#editorBodyKarteileiche', quillOptions);
    const editorBodyInfoNotification = new Quill('#editorBodyInfoNotification', quillOptions);

    // Store editors in a global map for access
    window.editors = {
        'entlassdatum':       editorBodyEntlassdatum,
        'aufnahmedatum':      editorBodyAufnahmedatum,
        'klassenwechsel':     editorBodyKlassenwechsel,
        'new_student':        editorBodyNewStudent,
        'karteileiche':       editorBodyKarteileiche,
        'info_notification':  editorBodyInfoNotification,
    };

    // Toast Notification System
    window.showToast = function(message) {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = 'custom-toast';
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.5s ease-out';
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    };

    // Helfer: Text in HTML-Absätze konvertieren
    function textToHtml(text) {
        if (!text) return "";
        // Wir konvertieren \r\n und \n zwingend in <br>, um Zeilenumbrüche sichtbar zu machen
        // Auch wenn bereits Tags wie <strong> vorhanden sind.
        let html = text.replace(/\n/g, "<br>");
        // Falls bereits <p> enthalten ist, lassen wir es so, fügen aber die <br> hinzu
        return html;
    }

    window.resetTemplate = async function(type) {
        if (!confirm("Soll diese Vorlage wirklich auf den Standard zurückgesetzt werden?")) return;
        try {
            const response = await fetch(`/api/templates/default/${type}`);
            const data = await response.json();
            if (data.subject && data.body) {
                const subjectInputId = {
                    'entlassdatum':      'subjectEntlassdatum',
                    'aufnahmedatum':     'subjectAufnahmedatum',
                    'klassenwechsel':    'subjectKlassenwechsel',
                    'new_student':       'subjectNewStudent',
                    'karteileiche':      'subjectKarteileiche',
                    'info_notification': 'subjectInfoNotification',
                }[type];
                document.getElementById(subjectInputId).value = data.subject || "";
                window.editors[type].clipboard.dangerouslyPasteHTML(textToHtml(data.body || ""));
                window.showToast("Standard-Vorlage geladen.");
            }
        } catch (err) {
            console.error(err);
            alert("Fehler beim Laden der Standard-Vorlage.");
        }
    };

    // Load templates dynamically
    fetch("/get_templates")
        .then(response => response.json())
        .then(data => {
            // Populate subject fields
            document.getElementById("subjectEntlassdatum").value = data.subject_entlassdatum || "";
            document.getElementById("subjectAufnahmedatum").value = data.subject_aufnahmedatum || "";
            document.getElementById("subjectKlassenwechsel").value = data.subject_klassenwechsel || "";
            document.getElementById("subjectNewStudent").value = data.subject_new_student || "";
            document.getElementById("subjectKarteileiche").value = data.subject_karteileiche || "";
            document.getElementById("subjectInfoNotification").value = data.subject_info_notification || "";

            // Populate body fields in Quill editors with auto-conversion
            // Use dangerouslyPasteHTML so Quill's internal delta state is updated correctly,
            // even when the editor container is inside a hidden panel.
            editorBodyEntlassdatum.clipboard.dangerouslyPasteHTML(textToHtml(data.body_entlassdatum || ""));
            editorBodyAufnahmedatum.clipboard.dangerouslyPasteHTML(textToHtml(data.body_aufnahmedatum || ""));
            editorBodyKlassenwechsel.clipboard.dangerouslyPasteHTML(textToHtml(data.body_klassenwechsel || ""));
            editorBodyNewStudent.clipboard.dangerouslyPasteHTML(textToHtml(data.body_new_student || ""));
            editorBodyKarteileiche.clipboard.dangerouslyPasteHTML(textToHtml(data.body_karteileiche || ""));
            editorBodyInfoNotification.clipboard.dangerouslyPasteHTML(textToHtml(data.body_info_notification || ""));

            // Show/Hide class change hint based on initial value
            const classChangeSelect = document.getElementById("class_change_recipients");
            const classChangeHint = document.getElementById("class_change_both_hint");
            if (classChangeSelect && classChangeHint) {
                classChangeHint.style.display = classChangeSelect.value === "both" ? "block" : "none";
                classChangeSelect.addEventListener("change", function() {
                    classChangeHint.style.display = this.value === "both" ? "block" : "none";
                });
            }
        })
        .catch(error => {
            console.error("Error loading email templates:", error);
            alert("Fehler beim Laden der E-Mail-Vorlagen.");
        });

    // Save templates
    document.getElementById("saveEmailTemplates").addEventListener("click", function () {
        // Synchronisiere Quill-Inhalte
        document.getElementById('bodyEntlassdatum').value = editorBodyEntlassdatum.root.innerHTML;
        document.getElementById('bodyAufnahmedatum').value = editorBodyAufnahmedatum.root.innerHTML;
        document.getElementById('bodyKlassenwechsel').value = editorBodyKlassenwechsel.root.innerHTML;
        document.getElementById('bodyNewStudent').value = editorBodyNewStudent.root.innerHTML;
        document.getElementById('bodyKarteileiche').value = editorBodyKarteileiche.root.innerHTML;
        document.getElementById('bodyInfoNotification').value = editorBodyInfoNotification.root.innerHTML;

        const formData = new FormData();
        formData.append("subject_entlassdatum", document.getElementById("subjectEntlassdatum").value);
        formData.append("body_entlassdatum", document.getElementById("bodyEntlassdatum").value);
        formData.append("subject_aufnahmedatum", document.getElementById("subjectAufnahmedatum").value);
        formData.append("body_aufnahmedatum", document.getElementById("bodyAufnahmedatum").value);
        formData.append("subject_klassenwechsel", document.getElementById("subjectKlassenwechsel").value);
        formData.append("body_klassenwechsel", document.getElementById("bodyKlassenwechsel").value);
        formData.append("subject_new_student", document.getElementById("subjectNewStudent").value);
        formData.append("body_new_student", document.getElementById("bodyNewStudent").value);
        formData.append("subject_karteileiche", document.getElementById("subjectKarteileiche").value);
        formData.append("body_karteileiche", document.getElementById("bodyKarteileiche").value);
        formData.append("subject_info_notification", document.getElementById("subjectInfoNotification").value);
        formData.append("body_info_notification", document.getElementById("bodyInfoNotification").value);

        fetch("/update_templates", {
            method: "POST",
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
            })
            .catch(error => {
                console.error("Error saving email templates:", error);
                alert("Fehler beim Speichern der E-Mail-Vorlagen.");
            });
    });

    // Tabs für den E-Mail-Editor initialisieren
    const emailTabs = document.querySelectorAll('#emailTabs .nav-link');
    emailTabs.forEach(tab => {
        tab.addEventListener("click", function (e) {
            e.preventDefault();

            // Aktive Tabs wechseln
            emailTabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");

            // Content-Panels wechseln (Scoped to email editor)
            const tabContainer = document.querySelector('#emailEditor .tab-content');
            const allPanels = tabContainer.querySelectorAll(".tab-pane");
            allPanels.forEach(panel => panel.classList.remove("show", "active"));
            const targetPanel = document.querySelector(tab.getAttribute("href"));
            if (targetPanel) {
                targetPanel.classList.add("show", "active");
            }
        });
    });
});
