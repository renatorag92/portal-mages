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
  const confirmTitle = document.getElementById("statusConfirmTitle");
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
      const itemType = triggerButton.dataset.confirmType || "status";
      const itemName = triggerButton.dataset.statusName;
      confirmTitle.textContent = `Excluir ${itemType}?`;
      confirmText.textContent = itemName
        ? `Tem certeza de que deseja excluir o ${itemType} "${itemName}"? Esta ação não pode ser desfeita.`
        : `Tem certeza de que deseja excluir este ${itemType}? Esta ação não pode ser desfeita.`;
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
