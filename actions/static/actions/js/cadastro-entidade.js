document.addEventListener("DOMContentLoaded", function () {
  const page = document.getElementById("entityPage");
  const form = document.getElementById("entityForm");
  if (!page || !form) return;

  const editButton = document.getElementById("entityEdit");
  const saveButton = document.getElementById("entitySave");
  const cancelButton = document.getElementById("entityCancel");
  const errorBox = document.getElementById("entityErrors");
  const dialog = document.getElementById("discardDialog");
  const keepButton = document.getElementById("keepEditing");
  const discardButton = document.getElementById("discardChanges");
  const inputs = Array.from(form.querySelectorAll("[data-input]"));
  let existing = page.dataset.existing === "true";
  let baseline = [];
  let toastTimer;

  function maskCnpj(value) {
    const digits = value.replace(/\D/g, "").slice(0, 14);
    let result = digits.slice(0, 2);
    if (digits.length > 2) result += "." + digits.slice(2, 5);
    if (digits.length > 5) result += "." + digits.slice(5, 8);
    if (digits.length > 8) result += "/" + digits.slice(8, 12);
    if (digits.length > 12) result += "-" + digits.slice(12, 14);
    return result;
  }

  const cnpjInput = form.querySelector("[data-cnpj-mask]");
  if (cnpjInput) {
    cnpjInput.value = maskCnpj(cnpjInput.value);
    cnpjInput.addEventListener("input", function () {
      const cursor = cnpjInput.selectionStart;
      const before = cnpjInput.value.length;
      cnpjInput.value = maskCnpj(cnpjInput.value);
      const after = cnpjInput.value.length;
      const position = Math.max(0, cursor + after - before);
      cnpjInput.setSelectionRange(position, position);
    });
  }

  function setEditing(editing) {
    inputs.forEach(function (input) {
      input.hidden = !editing;
      const display = form.querySelector('[data-display="' + input.dataset.input + '"]');
      if (display) display.hidden = editing;
    });
    editButton.hidden = editing;
    saveButton.hidden = !editing;
    cancelButton.hidden = !editing || !existing;
    if (!editing) errorBox.hidden = true;
  }

  function snapshot() {
    return inputs.map(function (input) { return input.value; });
  }

  function restore(values) {
    inputs.forEach(function (input, index) {
      input.value = values[index];
    });
  }

  function openDiscardDialog() {
    dialog.hidden = false;
    keepButton.focus();
  }

  function closeDiscardDialog() {
    dialog.hidden = true;
    cancelButton.focus();
  }

  function showErrors(errors) {
    const list = document.createElement("ul");
    Object.values(errors || {}).flat().forEach(function (message) {
      const item = document.createElement("li");
      item.textContent = message;
      list.appendChild(item);
    });
    errorBox.replaceChildren(list);
    errorBox.hidden = false;
    errorBox.focus();
  }

  function showToast(message) {
    document.querySelectorAll(".status-messages").forEach(function (container) { container.remove(); });
    window.clearTimeout(toastTimer);
    const container = document.createElement("div");
    container.className = "status-messages";
    container.setAttribute("aria-live", "polite");
    container.setAttribute("aria-atomic", "false");

    const toast = document.createElement("div");
    toast.className = "status-message status-message-success";
    toast.setAttribute("role", "status");

    const icon = document.createElement("span");
    icon.className = "status-message-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.innerHTML = '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m5 12 4 4L19 6"/></svg>';

    const text = document.createElement("span");
    text.className = "status-message-text";
    text.textContent = message;

    const close = document.createElement("button");
    close.type = "button";
    close.className = "status-message-close";
    close.setAttribute("aria-label", "Fechar notificação");
    close.textContent = "×";

    const progress = document.createElement("span");
    progress.className = "status-message-progress";
    progress.setAttribute("aria-hidden", "true");

    toast.append(icon, text, close, progress);
    container.appendChild(toast);
    document.body.appendChild(container);

    function dismiss() {
      window.clearTimeout(toastTimer);
      toast.classList.add("is-leaving");
      window.setTimeout(function () {
        container.remove();
      }, 200);
    }

    close.addEventListener("click", dismiss);
    toastTimer = window.setTimeout(dismiss, 6000);
  }

  function updateDisplay(registro) {
    Object.entries(registro).forEach(function (entry) {
      const key = entry[0];
      const display = form.querySelector('[data-display="' + key + '"]');
      const input = form.querySelector('[data-input="' + key + '"]');
      if (display) display.textContent = key === "cnpj" ? registro.cnpj_formatado : entry[1];
      if (input && key !== "prefeitura") input.value = key === "cnpj" ? registro.cnpj_formatado : entry[1];
    });
    const prefeituraDisplay = form.querySelector('[data-display="prefeitura"]');
    const prefeituraInput = form.querySelector('[data-input="prefeitura"]');
    if (prefeituraDisplay && registro.prefeitura_nome) prefeituraDisplay.textContent = registro.prefeitura_nome;
    if (prefeituraInput && registro.prefeitura_id) prefeituraInput.value = registro.prefeitura_id;
  }

  editButton.addEventListener("click", function () {
    baseline = snapshot();
    setEditing(true);
    inputs[0].focus();
  });

  cancelButton.addEventListener("click", function () {
    const changed = snapshot().some(function (value, index) { return value !== baseline[index]; });
    if (changed) {
      openDiscardDialog();
    } else {
      setEditing(false);
    }
  });

  keepButton.addEventListener("click", closeDiscardDialog);
  discardButton.addEventListener("click", function () {
    restore(baseline);
    closeDiscardDialog();
    setEditing(false);
  });
  dialog.addEventListener("click", function (event) {
    if (event.target === dialog) closeDiscardDialog();
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !dialog.hidden) closeDiscardDialog();
  });

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    errorBox.hidden = true;
    saveButton.disabled = true;
    const payload = {};
    inputs.forEach(function (input) { payload[input.dataset.input] = input.value; });
    if (page.dataset.recordId) payload.id = page.dataset.recordId;

    try {
      const response = await fetch(page.dataset.saveUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": form.querySelector('[name="csrfmiddlewaretoken"]').value
        },
        body: JSON.stringify(payload)
      });
      const result = await response.json();
      if (!response.ok || !result.success) {
        showErrors(result.errors || { __all__: ["Não foi possível salvar os dados."] });
        return;
      }

      updateDisplay(result.registro);
      page.dataset.recordId = result.registro.id;
      page.dataset.existing = "true";
      baseline = snapshot();
      existing = true;
      setEditing(false);
      showToast("Dados salvos com sucesso.");
    } catch (error) {
      showErrors({ __all__: ["Não foi possível comunicar com o servidor. Tente novamente."] });
    } finally {
      saveButton.disabled = false;
    }
  });

  if (existing) setEditing(false);
});