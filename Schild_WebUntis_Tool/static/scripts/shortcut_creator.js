document.addEventListener("DOMContentLoaded", function () {
    const exePathInput = document.getElementById("exePath");
    const argsInput = document.getElementById("args");
    const availableArgs = document.getElementById("availableArgs");
    const argDescription = document.getElementById("argDescription");
    const browseButton = document.getElementById("browseExePath");
    const validationMessage = document.getElementById("fileValidationMessage");
    let argumentCache = [];

    // Fetch the executable path from the server
    fetch('/get-executable-path')
        .then(response => response.json())
        .then(data => {
            if (data.exePath) {
                exePathInput.value = data.exePath;
                validationMessage.textContent = "Ausführungspfad geladen.";
                validationMessage.classList.remove("text-danger");
                validationMessage.classList.add("text-success");
            } else {
                validationMessage.textContent = "Ausführungspfad konnte nicht ermittelt werden.";
                validationMessage.classList.add("text-danger");
            }
        })
        .catch(error => {
            console.error("Fehler beim Laden des Ausführungspfads:", error);
            validationMessage.textContent = "Fehler beim Laden des Ausführungspfads.";
            validationMessage.classList.add("text-danger");
        });

    // Fetch available arguments and descriptions from the backend
    fetch("/get-arguments")
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                argumentCache = data.arguments; // Cache arguments for later use
                data.arguments.forEach((arg) => {
                    const option = document.createElement("option");
                    option.value = arg.name;
                    option.textContent = `${arg.name}`;
                    availableArgs.appendChild(option);
                });

                // Set initial description
                argDescription.textContent =
                    data.arguments[0]?.description || "Select an argument to see its description.";
            } else {
                console.error("Failed to fetch arguments:", data.error);
            }
        });

    // Update the argument description on selection
    availableArgs.addEventListener("change", function () {
        const selectedArg = availableArgs.value;
        const argDetails = argumentCache.find((arg) => arg.name === selectedArg);
        argDescription.textContent = argDetails?.description || "Description not available.";
    });

    // Add selected argument to the args input field
    document.getElementById("addArg").addEventListener("click", function () {
        const selectedArg = availableArgs.value;
        if (selectedArg) {
            argsInput.value = argsInput.value ? `${argsInput.value} ${selectedArg}` : selectedArg;
        }
    });

    // Generate the command
    document.getElementById("generateCommand").addEventListener("click", function () {
        const command = `"${exePathInput.value}" ${argsInput.value}`;
        document.getElementById("outputCommand").value = command;
    });

    // Create the shortcut
    document.getElementById("createShortcut").addEventListener("click", function () {
        const exePathValue = exePathInput.value;
        const argsValue = argsInput.value;

        if (exePathValue) {
            fetch("/create-shortcut", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ exePath: exePathValue, args: argsValue }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (data.success) {
                        alert("Shortcut created successfully!");
                    } else {
                        alert("Error creating shortcut: " + data.error);
                    }
                });
        } else {
            alert("Please provide the path to the executable file.");
        }
    });
});
