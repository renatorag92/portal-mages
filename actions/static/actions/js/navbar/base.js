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
            }

        });

    }


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