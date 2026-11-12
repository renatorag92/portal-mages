document.addEventListener("DOMContentLoaded", function () {
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
            if (!mobileViewport.matches) {
                sidebar.classList.add("hover-expanded");
            }
        });

        mobileNavToggle?.addEventListener("click", function () {
            setMobileNavigationOpen(!sidebar.classList.contains("mobile-open"));
        });

        sidebarBackdrop?.addEventListener("click", function () {
            setMobileNavigationOpen(false);
        });

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
            if (mobileViewport.matches || sidebar.classList.contains("expanded")) {
                return;
            }

            sidebar.classList.remove("hover-expanded");
            sidebar.querySelectorAll(".menu-group.open").forEach(function (group) {
                if (!group.querySelector(".submenu-item.active")) {
                    group.classList.remove("open");
                    group.querySelector(".menu-group-toggle")
                        ?.setAttribute("aria-expanded", "false");
                }
            });
        });
    }

    document.querySelectorAll(".menu-group-toggle").forEach(function (button) {
        const group = button.closest(".menu-group");
        if (!group) {
            return;
        }

        button.setAttribute("aria-expanded", String(group.classList.contains("open")));
        button.addEventListener("click", function () {
            const isOpen = group.classList.toggle("open");
            button.setAttribute("aria-expanded", String(isOpen));
        });
    });
});
