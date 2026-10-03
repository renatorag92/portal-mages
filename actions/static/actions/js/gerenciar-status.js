document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".status-message").forEach(function (message) {
    window.setTimeout(function () {
      message.classList.add("is-leaving");
      window.setTimeout(function () {
        message.remove();
      }, 200);
    }, 6000);
  });

  document.querySelectorAll(".status-message-close").forEach(function (button) {
    button.addEventListener("click", function () {
      button.closest(".status-message").remove();
    });
  });

  const modal = document.getElementById("statusConfirmModal");
  const cancelButton = document.getElementById("statusConfirmCancel");
  const deleteButton = document.getElementById("statusConfirmDelete");
  const confirmText = document.getElementById("statusConfirmText");
  const deleteForms = document.querySelectorAll(".status-delete-form");

  if (!modal || !cancelButton || !deleteButton || !confirmText) {
    return;
  }

  let formToDelete = null;
  let triggerButton = null;

  function closeModal() {
    modal.hidden = true;
    formToDelete = null;
    if (triggerButton) {
      triggerButton.focus();
      triggerButton = null;
    }
  }

  deleteForms.forEach(function (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      formToDelete = form;
      triggerButton = form.querySelector(".status-delete-button");
      const statusName = triggerButton.dataset.statusName;
      confirmText.textContent = statusName
        ? `Tem certeza de que deseja excluir o status "${statusName}"? Esta ação não pode ser desfeita.`
        : "Tem certeza de que deseja excluir este status? Esta ação não pode ser desfeita.";
      modal.hidden = false;
      cancelButton.focus();
    });
  });

  cancelButton.addEventListener("click", closeModal);

  deleteButton.addEventListener("click", function () {
    if (formToDelete) {
      formToDelete.submit();
    }
  });

  modal.addEventListener("click", function (event) {
    if (event.target === modal) {
      closeModal();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hidden) {
      closeModal();
    }
  });
});
