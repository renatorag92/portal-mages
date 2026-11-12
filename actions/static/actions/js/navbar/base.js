document.addEventListener("DOMContentLoaded", function () {

    /* =========================================================
       SIDEBAR
       ========================================================= */

    const sidebar = document.getElementById("sidebar");

    if (sidebar) {
        const mobileNavToggle = document.getElementById("mobileNavToggle");
        const sidebarBackdrop = document.getElementById("sidebarBackdrop");
        const mobileViewport = window.matchMedia("(max-width: 767px)");

        function setMobileNavigationOpen(isOpen) {
            sidebar.classList.toggle("mobile-open", isOpen);
            if (sidebarBackdrop) {
                sidebarBackdrop.hidden = !isOpen;
            }
            if (mobileNavToggle) {
                mobileNavToggle.setAttribute("aria-expanded", String(isOpen));
                mobileNavToggle.setAttribute(
                    "aria-label",
                    isOpen ? "Fechar navegação" : "Abrir navegação",
                );
            }
        }

        sidebar.addEventListener("mouseenter", function () {
            if (mobileViewport.matches) {
                return;
            }
            sidebar.classList.add("hover-expanded");
        });

        if (mobileNavToggle) {
            mobileNavToggle.addEventListener("click", function () {
                setMobileNavigationOpen(!sidebar.classList.contains("mobile-open"));
            });
        }

        if (sidebarBackdrop) {
            sidebarBackdrop.addEventListener("click", function () {
                setMobileNavigationOpen(false);
            });
        }

        sidebar.addEventListener("click", function (event) {
            if (mobileViewport.matches && event.target.closest("a[href]")) {
                setMobileNavigationOpen(false);
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && sidebar.classList.contains("mobile-open")) {
                setMobileNavigationOpen(false);
                mobileNavToggle?.focus();
            }
        });

        mobileViewport.addEventListener("change", function (event) {
            if (!event.matches) {
                setMobileNavigationOpen(false);
            }
        });

        sidebar.addEventListener("mouseleave", function () {
            if (mobileViewport.matches) {
                return;
            }

            if (!sidebar.classList.contains("expanded")) {

                sidebar.classList.remove("hover-expanded");

                // Fecha grupos que não contêm a página atual
                sidebar.querySelectorAll(".menu-group.open").forEach(function (group) {

                    if (!group.querySelector(".submenu-item.active")) {
                        group.classList.remove("open");

                        const toggle = group.querySelector(".menu-group-toggle");
                        if (toggle) {
                            toggle.setAttribute("aria-expanded", "false");
                        }
                    }

                });

            }

        });

    }


    /* =========================================================
       GRUPOS DO MENU (PAINEL ADMIN)
       ========================================================= */

    document.querySelectorAll(".menu-group-toggle").forEach(function (btn) {

        const group = btn.closest(".menu-group");

        btn.setAttribute("aria-expanded", group.classList.contains("open"));

        btn.addEventListener("click", function () {

            const isOpen = group.classList.toggle("open");
            btn.setAttribute("aria-expanded", isOpen);

        });

    });

    const notificationWrapper = document.querySelector(".notification-wrapper");
    const notificationToggle = document.getElementById("notificationToggle");
    const notificationPanel = document.getElementById("notificationPanel");

    if (notificationWrapper && notificationToggle && notificationPanel) {
        let notificationList = notificationPanel.querySelector(".notification-list");
        const headerCount = document.getElementById("notificationHeaderCount");
        const visibleCount = document.getElementById("notificationVisibleCount");
        const totalCount = document.getElementById("notificationTotalCount");
        const moreMessage = document.getElementById("notificationMore");
        const emptyMessage = document.getElementById("notificationEmpty");
        const actionStatus = document.getElementById("notificationActionStatus");
        const toastContainer = document.getElementById("notificationToasts");
        const refreshUrl = notificationToggle.dataset.refreshUrl;
        const csrfToken = function () {
            return document.querySelector('meta[name="csrf-token"]')?.content
                || document.querySelector('input[name="csrfmiddlewaretoken"]')?.value
                || "";
        };
        const knownNotifications = new Set(
            Array.from(notificationPanel.querySelectorAll(".notification-row"))
                .map(function (row) { return row.dataset.notificationId; })
                .filter(Boolean),
        );
        let hasPolled = false;
        let polling = false;
        let lastRenderedState = "";

        function setNotificationsOpen(isOpen) {
            notificationToggle.setAttribute("aria-expanded", String(isOpen));
            notificationPanel.hidden = !isOpen;
        }

        function updateUnreadCount(unread) {
            notificationToggle.dataset.unreadCount = String(unread);
            let badge = notificationToggle.querySelector(".notification-badge");
            if (unread > 0) {
                if (!badge) {
                    badge = document.createElement("span");
                    badge.className = "notification-badge";
                    badge.setAttribute("aria-hidden", "true");
                    notificationToggle.appendChild(badge);
                }
                badge.textContent = String(unread);
            } else if (badge) {
                badge.remove();
            }
            notificationToggle.setAttribute("aria-label", "Notificações: " + unread);
        }

        function createReadForm(notification) {
            const form = document.createElement("form");
            form.className = "notification-reset-read-form";
            form.action = notification.url;
            form.method = "post";
            const token = csrfToken();
            if (token) {
                const csrfInput = document.createElement("input");
                csrfInput.type = "hidden";
                csrfInput.name = "csrfmiddlewaretoken";
                csrfInput.value = token;
                form.appendChild(csrfInput);
            }
            const button = document.createElement("button");
            button.type = "submit";
            button.className = "notification-delete-button notification-mark-read-button";
            button.setAttribute("aria-label", "Marcar notificação como lida");
            button.title = "Marcar como lida";
            const icon = document.createElement("i");
            icon.className = "bi bi-check2";
            icon.setAttribute("aria-hidden", "true");
            button.appendChild(icon);
            form.appendChild(button);
            return form;
        }

        function createNotificationRow(notification) {
            const row = document.createElement("li");
            row.className = "notification-row";
            row.dataset.notificationId = notification.id;
            if (notification.lida) {
                row.classList.add("notification-row-read");
            }

            const isPasswordRequest = notification.alvo_tipo === "solicitacao_senha";
            let item;
            if (isPasswordRequest) {
                item = document.createElement("a");
                item.href = notification.destino_url;
            } else {
                const form = document.createElement("form");
                form.className = "notification-form";
                form.action = notification.url;
                form.method = "post";
                const token = csrfToken();
                if (token) {
                    const csrfInput = document.createElement("input");
                    csrfInput.type = "hidden";
                    csrfInput.name = "csrfmiddlewaretoken";
                    csrfInput.value = token;
                    form.appendChild(csrfInput);
                }
                item = document.createElement("button");
                item.type = "submit";
                item.setAttribute(
                    "aria-label",
                    `${notification.titulo}. ${notification.mensagem}${notification.lida ? " Já lida." : " Marcar como lida e abrir o kanban."}`,
                );
                form.appendChild(item);
                row.appendChild(form);
            }

            item.className = `notification-item${notification.lida ? " notification-item-read" : ""}`;
            const indicator = document.createElement("span");
            indicator.className = `notification-indicator notification-indicator-${notification.tipo}`;
            indicator.setAttribute("aria-hidden", "true");
            const indicatorIcon = document.createElement("i");
            indicatorIcon.className = notification.alvo_tipo === "solicitacao_senha"
                ? "bi bi-key-fill"
                : `bi bi-${notification.tipo === "danger" ? "exclamation-circle" : "clock"}-fill`;
            indicator.appendChild(indicatorIcon);

            const copy = document.createElement("span");
            copy.className = "notification-copy";
            const title = document.createElement("strong");
            title.textContent = notification.titulo;
            const message = document.createElement("span");
            message.textContent = notification.mensagem;
            const dateTime = document.createElement("span");
            dateTime.className = "notification-date-time";
            const time = document.createElement("time");
            time.dateTime = notification.criado_em;
            time.setAttribute("aria-label", "Horário da notificação");
            time.textContent = new Date(notification.criado_em).toLocaleString("pt-BR", {
                timeZone: "America/Sao_Paulo",
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            });
            dateTime.appendChild(time);
            copy.append(title, message, dateTime);

            const readIcon = document.createElement("span");
            readIcon.className = `notification-read-icon${notification.lida ? " notification-read-icon-read" : ""}`;
            readIcon.title = notification.lida ? "Lida" : "Não lida";
            readIcon.setAttribute("aria-hidden", "true");
            const readGlyph = document.createElement("i");
            readGlyph.className = `bi bi-envelope${notification.lida ? "-open" : "-fill"}`;
            readIcon.appendChild(readGlyph);
            item.append(indicator, copy, readIcon);
            if (isPasswordRequest) {
                row.appendChild(item);
                if (!notification.lida) {
                    row.appendChild(createReadForm(notification));
                }
            } else {
                row.querySelector(".notification-form").appendChild(item);
                const deleteForm = document.createElement("form");
                deleteForm.className = "notification-delete-form";
                deleteForm.action = notification.remover_url;
                deleteForm.method = "post";
                const token = csrfToken();
                if (token) {
                    const csrfInput = document.createElement("input");
                    csrfInput.type = "hidden";
                    csrfInput.name = "csrfmiddlewaretoken";
                    csrfInput.value = token;
                    deleteForm.appendChild(csrfInput);
                }
                const deleteButton = document.createElement("button");
                deleteButton.type = "submit";
                deleteButton.className = "notification-delete-button";
                deleteButton.setAttribute("aria-label", `Remover ${notification.titulo}`);
                deleteButton.title = "Remover notificação";
                const deleteIcon = document.createElement("i");
                deleteIcon.className = "bi bi-trash3";
                deleteIcon.setAttribute("aria-hidden", "true");
                deleteButton.appendChild(deleteIcon);
                deleteForm.appendChild(deleteButton);
                row.appendChild(deleteForm);
            }
            return row;
        }

        function renderNotifications(data) {
            if (!notificationList) {
                notificationList = document.createElement("ul");
                notificationList.className = "notification-list";
                notificationPanel.insertBefore(notificationList, moreMessage);
            }
            notificationList.replaceChildren(
                ...data.notifications.map(createNotificationRow),
            );
            if (headerCount) {
                headerCount.textContent = String(data.total_count);
            }
            if (visibleCount) {
                visibleCount.textContent = String(data.notifications.length);
            }
            if (totalCount) {
                totalCount.textContent = String(data.total_count);
            }
            if (moreMessage) {
                moreMessage.hidden = data.total_count <= data.notifications.length;
            }
            if (emptyMessage) {
                emptyMessage.hidden = data.notifications.length > 0;
            }
            updateUnreadCount(data.unread_count);
        }

        function showToast(notification) {
            const toast = document.createElement("article");
            toast.className = `notification-toast notification-toast-${notification.tipo}`;
            toast.setAttribute("role", "status");
            const icon = document.createElement("span");
            icon.className = "notification-toast-icon";
            icon.innerHTML = notification.alvo_tipo === "solicitacao_senha"
                ? '<i class="bi bi-key-fill" aria-hidden="true"></i>'
                : notification.tipo === "danger"
                    ? '<i class="bi bi-exclamation-circle-fill" aria-hidden="true"></i>'
                    : '<i class="bi bi-bell-fill" aria-hidden="true"></i>';
            const copy = document.createElement("span");
            copy.className = "notification-toast-copy";
            const title = document.createElement("strong");
            title.textContent = notification.titulo;
            const message = document.createElement("span");
            message.textContent = notification.mensagem;
            copy.append(title, message);
            const close = document.createElement("button");
            close.className = "notification-toast-close";
            close.type = "button";
            close.setAttribute("aria-label", "Fechar notificação");
            close.innerHTML = "&times;";
            toast.append(icon, copy, close);
            toastContainer.appendChild(toast);
            notificationToggle.classList.remove("notification-toggle-new");
            void notificationToggle.offsetWidth;
            notificationToggle.classList.add("notification-toggle-new");
            window.setTimeout(function () {
                notificationToggle.classList.remove("notification-toggle-new");
            }, 700);
            close.addEventListener("click", function () {
                dismissToast(toast);
            });
            window.setTimeout(function () { dismissToast(toast); }, 6500);
        }

        function dismissToast(toast) {
            if (!toast.isConnected || toast.classList.contains("notification-toast-leaving")) {
                return;
            }
            toast.classList.add("notification-toast-leaving");
            toast.addEventListener("animationend", function () { toast.remove(); }, {once: true});
        }

        async function refreshNotifications() {
            if (polling || document.visibilityState === "hidden") {
                return;
            }
            polling = true;
            try {
                const response = await fetch(refreshUrl, {
                    credentials: "same-origin",
                    headers: {"X-Requested-With": "XMLHttpRequest"},
                });
                if (!response.ok) {
                    throw new Error("Não foi possível atualizar as notificações.");
                }
                const data = await response.json();
                if (!Array.isArray(data.notifications)) {
                    throw new Error("A resposta de notificações é inválida.");
                }
                const state = JSON.stringify({
                    notifications: data.notifications,
                    unread_count: data.unread_count,
                    total_count: data.total_count,
                });
                const currentIds = new Set(data.notifications.map(function (item) { return item.id; }));
                if (hasPolled) {
                    data.notifications.forEach(function (item) {
                        if (!knownNotifications.has(item.id) && !item.lida) {
                            showToast(item);
                        }
                    });
                }
                knownNotifications.clear();
                currentIds.forEach(function (id) { knownNotifications.add(id); });
                hasPolled = true;
                if (state !== lastRenderedState) {
                    renderNotifications(data);
                    lastRenderedState = state;
                }
            } catch (error) {
                console.error(error);
                if (actionStatus && !notificationPanel.hidden) {
                    actionStatus.textContent = "Não foi possível atualizar as notificações.";
                    actionStatus.hidden = false;
                }
            } finally {
                polling = false;
            }
        }

        async function submitNotificationForm(form) {
            const row = form.closest(".notification-row");
            if (row?.dataset.submitting === "true") {
                return;
            }
            if (row) {
                row.dataset.submitting = "true";
            }
            if (actionStatus) {
                actionStatus.hidden = true;
                actionStatus.textContent = "";
            }
            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form),
                    credentials: "same-origin",
                    headers: {"X-Requested-With": "XMLHttpRequest"},
                });
                const result = await response.json();
                if (!response.ok || !result.success) {
                    throw new Error("Não foi possível atualizar esta notificação.");
                }
                await refreshNotifications();
            } catch (error) {
                if (row) {
                    delete row.dataset.submitting;
                }
                if (actionStatus) {
                    actionStatus.textContent = error.message || "Erro ao atualizar a notificação. Tente novamente.";
                    actionStatus.hidden = false;
                }
            }
        }

        notificationToggle.addEventListener("click", function () {
            setNotificationsOpen(notificationPanel.hidden);
        });

        notificationPanel.addEventListener("submit", function (event) {
            const form = event.target.closest(".notification-reset-read-form, .notification-delete-form");
            if (!form) {
                return;
            }
            event.preventDefault();
            submitNotificationForm(form);
        });

        document.addEventListener("click", function (event) {
            if (!notificationWrapper.contains(event.target)) {
                setNotificationsOpen(false);
            }
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !notificationPanel.hidden) {
                setNotificationsOpen(false);
                notificationToggle.focus();
            }
        });

        refreshNotifications();
        window.setInterval(refreshNotifications, 10000);
    }
});