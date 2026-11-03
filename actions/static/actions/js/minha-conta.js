document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("accountForm");
    const dialog = document.getElementById("profilePhotoDialog");
    const openButtons = [
        document.getElementById("openProfilePhoto"),
        document.getElementById("openProfilePhotoOptions"),
    ];
    const closeButton = document.getElementById("closeProfilePhoto");
    const cancelButton = document.getElementById("cancelProfilePhoto");
    const chooseButton = document.getElementById("chooseProfilePhoto");
    const removeButton = document.getElementById("removeProfilePhoto");
    const saveButton = document.getElementById("saveProfilePhoto");
    const fileInput = document.getElementById("id_foto");
    const clearInput = document.querySelector('input[name="foto-clear"]');
    const preview = document.getElementById("profilePhotoPreview");
    const placeholder = document.getElementById("profilePhotoPlaceholder");
    const pendingMessage = document.getElementById("profilePhotoPending");

    if (
        !form || !dialog || !closeButton || !cancelButton || !chooseButton ||
        !saveButton || !fileInput || !preview || !placeholder || !pendingMessage
    ) {
        return;
    }

    let activeTrigger = null;
    let selectedPreviewUrl = null;
    let originalPhotoUrl = preview.hidden ? null : preview.src;

    function updatePreview(source) {
        if (source) {
            preview.src = source;
            preview.hidden = false;
            placeholder.hidden = true;
            return;
        }

        preview.removeAttribute("src");
        preview.hidden = true;
        placeholder.hidden = false;
    }

    function setDialogOpen(isOpen, trigger) {
        if (isOpen) {
            activeTrigger = trigger;
            dialog.hidden = false;
            closeButton.focus();
            return;
        }

        dialog.hidden = true;
        if (activeTrigger) {
            activeTrigger.focus();
        }
    }

    function resetPhotoSelection() {
        if (selectedPreviewUrl) {
            URL.revokeObjectURL(selectedPreviewUrl);
            selectedPreviewUrl = null;
        }
        fileInput.value = "";
        if (clearInput) {
            clearInput.checked = false;
        }
        updatePreview(originalPhotoUrl);
        saveButton.disabled = true;
        pendingMessage.hidden = true;
        pendingMessage.textContent = "";
        if (removeButton) {
            removeButton.hidden = false;
        }
    }

    openButtons.forEach(function (button) {
        if (button) {
            button.addEventListener("click", function () {
                setDialogOpen(true, button);
            });
        }
    });

    closeButton.addEventListener("click", function () {
        setDialogOpen(false);
    });
    cancelButton.addEventListener("click", function () {
        resetPhotoSelection();
        setDialogOpen(false);
    });

    chooseButton.addEventListener("click", function () {
        fileInput.click();
    });

    fileInput.addEventListener("change", function () {
        const file = fileInput.files && fileInput.files[0];
        if (!file) {
            return;
        }

        if (selectedPreviewUrl) {
            URL.revokeObjectURL(selectedPreviewUrl);
        }
        selectedPreviewUrl = URL.createObjectURL(file);
        if (clearInput) {
            clearInput.checked = false;
        }
        updatePreview(selectedPreviewUrl);
        saveButton.disabled = false;
        pendingMessage.textContent = "Prévia da nova foto. Salve para confirmar.";
        pendingMessage.hidden = false;
        if (removeButton) {
            removeButton.hidden = true;
        }
    });

    if (removeButton && clearInput) {
        removeButton.addEventListener("click", function () {
            fileInput.value = "";
            clearInput.checked = true;
            updatePreview(null);
            saveButton.disabled = false;
            pendingMessage.textContent = "A foto será removida ao salvar.";
            pendingMessage.hidden = false;
            removeButton.hidden = true;
        });
    }

    dialog.addEventListener("click", function (event) {
        if (event.target === dialog) {
            resetPhotoSelection();
            setDialogOpen(false);
        }
    });

    dialog.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            event.preventDefault();
            resetPhotoSelection();
            setDialogOpen(false);
            return;
        }

        if (event.key === "Tab") {
            const focusable = Array.from(dialog.querySelectorAll(
                'button:not([disabled]):not([hidden])',
            ));
            const first = focusable[0];
            const last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        }
    });

    form.addEventListener("submit", function () {
        if (selectedPreviewUrl) {
            URL.revokeObjectURL(selectedPreviewUrl);
        }
    });
});
