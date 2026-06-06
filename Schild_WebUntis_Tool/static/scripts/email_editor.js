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
    // KL-Mail-Editor (Ausbilder-Workflow): nur initialisieren wenn das Container-
    // Element vorhanden ist. Sonst wirft new Quill(...) eine Exception und der
    // Rest des Editors initialisiert sich nicht (Schueler-Editor waere kaputt).
    const klMailEditorEl = document.getElementById('editorBodyAusbilderKlUebersicht');
    const editorBodyAusbilderKlUebersicht = klMailEditorEl
        ? new Quill('#editorBodyAusbilderKlUebersicht', quillOptions)
        : null;
    // KL-Mail-Editor (Erzieher-Workflow), symmetrisch zum Ausbilder-Editor.
    const erzKlMailEditorEl = document.getElementById('editorBodyErzieherKlUebersicht');
    const editorBodyErzieherKlUebersicht = erzKlMailEditorEl
        ? new Quill('#editorBodyErzieherKlUebersicht', quillOptions)
        : null;

    // Store editors in a global map for access
    window.editors = {
        'entlassdatum':       editorBodyEntlassdatum,
        'aufnahmedatum':      editorBodyAufnahmedatum,
        'klassenwechsel':     editorBodyKlassenwechsel,
        'new_student':        editorBodyNewStudent,
        'karteileiche':       editorBodyKarteileiche,
        'info_notification':  editorBodyInfoNotification,
    };
    if (editorBodyAusbilderKlUebersicht) {
        window.editors['ausbilder_kl_uebersicht'] = editorBodyAusbilderKlUebersicht;
    }
    if (editorBodyErzieherKlUebersicht) {
        window.editors['erzieher_kl_uebersicht'] = editorBodyErzieherKlUebersicht;
    }

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
                    'entlassdatum':            'subjectEntlassdatum',
                    'aufnahmedatum':           'subjectAufnahmedatum',
                    'klassenwechsel':          'subjectKlassenwechsel',
                    'new_student':             'subjectNewStudent',
                    'karteileiche':            'subjectKarteileiche',
                    'info_notification':       'subjectInfoNotification',
                    'ausbilder_kl_uebersicht': 'subjectAusbilderKlUebersicht',
                    'erzieher_kl_uebersicht':  'subjectErzieherKlUebersicht',
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
            // KL-Mail-Vorlage (Ausbilder-Workflow) — nur befuellen wenn der
            // entsprechende Editor existiert (Element nur in der Ausbilder-
            // Workflow-Section vorhanden). Defensives Pruefen jedes Targets,
            // damit das Befuellen nicht reisst, falls jemand das Markup
            // partiell entfernt.
            const klSubj = document.getElementById('subjectAusbilderKlUebersicht');
            if (klSubj) klSubj.value = data.subject_ausbilder_kl_uebersicht || '';
            if (editorBodyAusbilderKlUebersicht) {
                editorBodyAusbilderKlUebersicht.clipboard.dangerouslyPasteHTML(
                    textToHtml(data.body_ausbilder_kl_uebersicht || ""));
            }
            // KL-Mail-Vorlage (Erzieher-Workflow)
            const erzKlSubj = document.getElementById('subjectErzieherKlUebersicht');
            if (erzKlSubj) erzKlSubj.value = data.subject_erzieher_kl_uebersicht || '';
            if (editorBodyErzieherKlUebersicht) {
                editorBodyErzieherKlUebersicht.clipboard.dangerouslyPasteHTML(
                    textToHtml(data.body_erzieher_kl_uebersicht || ""));
            }

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

    // KL-Mail-Vorlage (Ausbilder-Workflow) speichern — eigener Endpoint, der
    // NUR diese eine Vorlage anfasst. Wuerde der bestehende /update_templates
    // genutzt, wuerden die anderen Vorlagen (die im KL-Mail-Editor gar nicht
    // existieren) als leere Strings ueberschrieben werden — daher diese
    // dedizierte Save-Route.
    const klMailSaveBtn = document.getElementById('saveAusbilderKlMailTemplate');
    if (klMailSaveBtn && editorBodyAusbilderKlUebersicht) {
        klMailSaveBtn.addEventListener('click', function () {
            const subjEl   = document.getElementById('subjectAusbilderKlUebersicht');
            const bodyEl   = document.getElementById('bodyAusbilderKlUebersicht');
            const resultEl = document.getElementById('ausbilderKlMailTemplateResult');
            if (!subjEl || !bodyEl) return;
            // Quill-Inhalt in das Hidden-Textarea spiegeln (gleiches Muster
            // wie beim Haupt-Save oben), damit FormData den HTML-Body
            // mitnimmt.
            bodyEl.value = editorBodyAusbilderKlUebersicht.root.innerHTML;
            const fd = new FormData();
            fd.append('subject_ausbilder_kl_uebersicht', subjEl.value);
            fd.append('body_ausbilder_kl_uebersicht',    bodyEl.value);
            klMailSaveBtn.disabled = true;
            const orig = klMailSaveBtn.textContent;
            klMailSaveBtn.textContent = '⌛ Speichere…';
            if (resultEl) resultEl.textContent = '';
            fetch('/api/ausbilder/update_kl_mail_template', { method: 'POST', body: fd })
                .then(r => r.json())
                .then(d => {
                    if (resultEl) resultEl.textContent = d.message || '';
                    if (typeof showToast === 'function') showToast(d.message || 'Gespeichert.');
                })
                .catch(err => {
                    console.error(err);
                    alert('Fehler beim Speichern der KL-Mail-Vorlage.');
                })
                .finally(() => {
                    klMailSaveBtn.disabled = false;
                    klMailSaveBtn.textContent = orig;
                });
        });
    }

    // KL-Mail-Vorlage (Erzieher-Workflow) speichern — eigener Endpoint,
    // analog zum Ausbilder-Save (Begruendung dort).
    const erzKlMailSaveBtn = document.getElementById('saveErzieherKlMailTemplate');
    if (erzKlMailSaveBtn && editorBodyErzieherKlUebersicht) {
        erzKlMailSaveBtn.addEventListener('click', function () {
            const subjEl   = document.getElementById('subjectErzieherKlUebersicht');
            const bodyEl   = document.getElementById('bodyErzieherKlUebersicht');
            const resultEl = document.getElementById('erzieherKlMailTemplateResult');
            if (!subjEl || !bodyEl) return;
            bodyEl.value = editorBodyErzieherKlUebersicht.root.innerHTML;
            const fd = new FormData();
            fd.append('subject_erzieher_kl_uebersicht', subjEl.value);
            fd.append('body_erzieher_kl_uebersicht',    bodyEl.value);
            erzKlMailSaveBtn.disabled = true;
            const orig = erzKlMailSaveBtn.textContent;
            erzKlMailSaveBtn.textContent = '⌛ Speichere…';
            if (resultEl) resultEl.textContent = '';
            fetch('/api/erzieher/update_kl_mail_template', { method: 'POST', body: fd })
                .then(r => r.json())
                .then(d => {
                    if (resultEl) resultEl.textContent = d.message || '';
                    if (typeof showToast === 'function') showToast(d.message || 'Gespeichert.');
                })
                .catch(err => {
                    console.error(err);
                    alert('Fehler beim Speichern der Erzieher-KL-Mail-Vorlage.');
                })
                .finally(() => {
                    erzKlMailSaveBtn.disabled = false;
                    erzKlMailSaveBtn.textContent = orig;
                });
        });
    }

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
