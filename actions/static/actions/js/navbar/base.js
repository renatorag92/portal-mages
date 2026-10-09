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


    /* =========================================================
       MENU DO AVATAR
       ========================================================= */

    const avatarToggle = document.getElementById("avatarToggle");
    const avatarMenu = document.getElementById("avatarMenu");

    if (avatarToggle && avatarMenu) {

        avatarToggle.addEventListener("click", function (event) {

            event.stopPropagation();

            avatarMenu.classList.toggle("open");

        });

        document.addEventListener("click", function (event) {

            if (
                !event.target.closest("#avatarMenu") &&
                !event.target.closest("#avatarToggle")
            ) {

                avatarMenu.classList.remove("open");

            }

        });

    }

});