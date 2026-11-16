document.addEventListener("DOMContentLoaded", function () {
    const wrapper = document.querySelector(".user-menu-wrapper");
    const toggle = document.getElementById("userMenuToggle");
    const menu = document.getElementById("userMenu");
    const securityLink = document.getElementById("userMenuSecurity");
    const confirmation = document.getElementById("userMenuConfirm");
    const cancelConfirmation = document.getElementById("userMenuConfirmCancel");
    const continueToSecurity = document.getElementById("userMenuConfirmContinue");

    if (!wrapper || !toggle || !menu || !securityLink || !confirmation || !cancelConfirmation || !continueToSecurity) {
        return;
    }

    function setMenuOpen(isOpen) {
        toggle.setAttribute("aria-expanded", String(isOpen));

        if (isOpen) {
            menu.hidden = false;
            window.requestAnimationFrame(function () {
                if (!menu.hidden) {
                    menu.classList.add("is-open");
                }
            });
            return;
        }

        menu.classList.remove("is-open");
        menu.hidden = true;
    }

    function closeConfirmation() {
        confirmation.hidden = true;
        toggle.focus();
    }

    securityLink.addEventListener("click", function (event) {
        event.preventDefault();
        setMenuOpen(false);
        confirmation.hidden = false;
        cancelConfirmation.focus();
    });

    cancelConfirmation.addEventListener("click", closeConfirmation);

    continueToSecurity.addEventListener("click", function () {
        window.location.assign(securityLink.href);
    });

    confirmation.addEventListener("click", function (event) {
        if (event.target === confirmation) {
            closeConfirmation();
        }
    });

    confirmation.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            event.preventDefault();
            closeConfirmation();
            return;
        }

        if (event.key === "Tab") {
            event.preventDefault();
            const focusedButton = document.activeElement === cancelConfirmation
                ? continueToSecurity
                : cancelConfirmation;
            focusedButton.focus();
        }
    });

    toggle.addEventListener("click", function () {
        setMenuOpen(menu.hidden);
    });

    document.addEventListener("click", function (event) {
        if (!wrapper.contains(event.target)) {
            setMenuOpen(false);
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !menu.hidden) {
            setMenuOpen(false);
            toggle.focus();
        }
    });

    menu.addEventListener("click", function (event) {
        if (event.target.closest('[role="menuitem"]')) {
            setMenuOpen(false);
        }
    });
});