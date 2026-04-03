document.addEventListener("DOMContentLoaded", function () {
    // Handle the upload form submission
    const uploadForm = document.getElementById("uploadForm");
    if (uploadForm) {
        uploadForm.addEventListener("submit", function (event) {
            event.preventDefault();
            const formData = new FormData();

            // Append class data files
            const classDataFiles = document.getElementById("classDataFiles").files;
            for (let i = 0; i < classDataFiles.length; i++) {
                formData.append("class_data_files", classDataFiles[i]);
            }

            // Append teacher data files
            const teacherDataFiles = document.getElementById("teacherDataFiles").files;
            for (let i = 0; i < teacherDataFiles.length; i++) {
                formData.append("teacher_data_files", teacherDataFiles[i]);
            }

            // Append Schild-Export files
            const schildExportFiles = document.getElementById("schildExportFiles").files;
            for (let i = 0; i < schildExportFiles.length; i++) {
                formData.append("schild_export_files", schildExportFiles[i]);
            }

            fetch('/upload-files', {
                method: 'POST',
                body: formData
            })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                })
                .catch(error => {
                    console.error("Fehler beim Hochladen der Dateien:", error);
                    alert("Fehler beim Hochladen der Dateien.");
                });
        });
    }
});
