/* =====================================================
   KAGENDO FARM MANAGEMENT SYSTEM
   app.js
   ===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ==========================================
       SIDEBAR
    ========================================== */

    const sidebar = document.getElementById("sidebar");
    const content = document.getElementById("content");
    const menuToggle = document.getElementById("menu-toggle");

    if (menuToggle && sidebar) {

        // Restore previous state
        if (localStorage.getItem("sidebarCollapsed") === "true") {
            sidebar.classList.add("collapsed");

            if (content) {
                content.classList.add("expanded");
            }
        }

        menuToggle.addEventListener("click", () => {

            sidebar.classList.toggle("collapsed");

            if (content) {
                content.classList.toggle("expanded");
            }

            localStorage.setItem(
                "sidebarCollapsed",
                sidebar.classList.contains("collapsed")
            );

        });

    }


    /* ==========================================
       NOTIFICATIONS
    ========================================== */

    const notificationBtn = document.getElementById("notification-btn");
    const notificationDropdown = document.getElementById("notification-dropdown");

    if (notificationBtn && notificationDropdown) {

        notificationBtn.addEventListener("click", function (e) {

            e.stopPropagation();

            notificationDropdown.classList.toggle("show");

            if (quickMenu) {
                quickMenu.classList.remove("show");
                fab.innerHTML = "+";
            }

        });

    }


    /* ==========================================
       QUICK ACTION MENU
    ========================================== */

    const fab = document.getElementById("fab");
    const quickMenu = document.getElementById("quickMenu");

    if (fab && quickMenu) {

        fab.addEventListener("click", function (e) {

            e.stopPropagation();

            quickMenu.classList.toggle("show");

            notificationDropdown?.classList.remove("show");

            if (quickMenu.classList.contains("show")) {

                fab.innerHTML = "✕";

            } else {

                fab.innerHTML = "+";

            }

        });

    }


    /* ==========================================
       CLOSE MENUS WHEN CLICKING OUTSIDE
    ========================================== */

    document.addEventListener("click", function () {

        if (notificationDropdown) {
            notificationDropdown.classList.remove("show");
        }

        if (quickMenu) {
            quickMenu.classList.remove("show");
        }

        if (fab) {
            fab.innerHTML = "+";
        }

    });


    /* ==========================================
       PLACEHOLDERS FOR FUTURE FEATURES
    ========================================== */

    // Search

    // Charts

    // Dark Mode

    // Profile Menu

});