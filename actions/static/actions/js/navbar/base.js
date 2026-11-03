document.addEventListener("DOMContentLoaded", function () {

    /* =========================================================
       SIDEBAR
       ========================================================= */

    const sidebar = document.getElementById("sidebar");

    if (sidebar) {

        sidebar.addEventListener("mouseenter", function () {
            sidebar.classList.add("hover-expanded");
        });

        sidebar.addEventListener("mouseleave", function () {

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
        const notificationList = notificationPanel.querySelector(".notification-list");
        const headerCount = document.getElementById("notificationHeaderCount");
        const visibleCount = document.getElementById("notificationVisibleCount");
        const totalCount = document.getElementById("notificationTotalCount");
        const moreMessage = document.getElementById("notificationMore");
        const emptyMessage = document.getElementById("notificationEmpty");
        const actionStatus = document.getElementById("notificationActionStatus");

        function setNotificationsOpen(isOpen) {
            notificationToggle.setAttribute("aria-expanded", String(isOpen));
            notificationPanel.hidden = !isOpen;
        }

        function updateNotificationCounts(removedUnread) {
            const unread = Math.max(
                0,
                Number(notificationToggle.dataset.unreadCount || 0) - (removedUnread ? 1 : 0),
            );
            const total = Math.max(
                0,
                Number(headerCount ? headerCount.textContent : 0) - 1,
            );
            const visible = notificationList ? notificationList.children.length : 0;

            if (headerCount) {
                headerCount.textContent = String(total);
            }
            if (visibleCount) {
                visibleCount.textContent = String(visible);
            }
            if (totalCount) {
                totalCount.textContent = String(total);
            }
            if (moreMessage) {
                moreMessage.hidden = total <= visible;
            }
            if (emptyMessage) {
                emptyMessage.hidden = visible > 0;
            }
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

        async function removeNotification(form) {
            const row = form.closest(".notification-row");
            if (!row || row.dataset.removing === "true") {
                return;
            }

            row.dataset.removing = "true";
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
                    throw new Error("Não foi possível remover esta notificação.");
                }

                const item = row.querySelector(".notification-item");
                const wasUnread = item && !item.classList.contains("notification-item-read");
                row.remove();
                updateNotificationCounts(wasUnread);
            } catch (error) {
                delete row.dataset.removing;
                if (actionStatus) {
                    actionStatus.textContent = error.message || "Erro ao remover a notificação. Tente novamente.";
                    actionStatus.hidden = false;
                }
            }
        }

        notificationToggle.addEventListener("click", function () {
            setNotificationsOpen(notificationPanel.hidden);
        });

        if (notificationList) {
            notificationList.querySelectorAll(".notification-delete-form").forEach(function (form) {
                form.addEventListener("submit", function (event) {
                    event.preventDefault();
                    removeNotification(form);
                });
            });
        }

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
    }
});