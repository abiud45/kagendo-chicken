/* =====================================================
   KAGENDO FARM MANAGEMENT SYSTEM
   app.js
   ===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    /* ==========================================
       SIDEBAR DRAWER
    ========================================== */

    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");
    const menuToggle = document.getElementById("menu-toggle");

    if (sidebar && overlay && menuToggle) {

        // Open / Close drawer
        menuToggle.addEventListener("click", () => {

            sidebar.classList.toggle("open");
            overlay.classList.toggle("show");

        });

        // Tap outside to close
        overlay.addEventListener("click", () => {

            sidebar.classList.remove("open");
            overlay.classList.remove("show");

        });

        // Close drawer after navigation
        document.querySelectorAll(".sidebar-link").forEach(link => {

            link.addEventListener("click", () => {

                sidebar.classList.remove("open");
                overlay.classList.remove("show");

            });

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
   FLOATING QUICK MENU
========================================== */

const fab = document.getElementById("fab");
const quickMenu = document.getElementById("quickMenu");

if (fab && quickMenu) {

    fab.addEventListener("click", function (e) {

         console.log("FAB CLICKED");

        e.stopPropagation();

        quickMenu.classList.toggle("show");

        fab.innerHTML =
            quickMenu.classList.contains("show")
                ? "✕"
                : "+";
    });

    quickMenu.querySelectorAll("a").forEach(link => {

        link.addEventListener("click", () => {

            quickMenu.classList.remove("show");
            fab.innerHTML = "+";

        });

    });

}





/* ==========================================
   PLACEHOLDERS FOR FUTURE FEATURES
========================================== */

// Search
// Charts
// Dark Mode
// Profile Menu

});