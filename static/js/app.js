/* =====================================================
   KAGENDO FARM MANAGEMENT SYSTEM
   app.js
   ===================================================== */





document.addEventListener("DOMContentLoaded", () => {

    if ("Notification" in window &&
    Notification.permission !== "granted") {

    Notification.requestPermission();

}

    /* ==========================================
   ANDROID BACK BUTTON SUPPORT
    ========================================== */

    // Create an initial history state
    history.replaceState({ page: "current" }, "");


    /* ==========================================
       SIDEBAR DRAWER
    ========================================== */

    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("overlay");
    const menuToggle = document.getElementById("menu-toggle");

    if (sidebar && overlay && menuToggle) {

        // Open / Close drawer
     menuToggle.addEventListener("click", () => {

    const opening = !sidebar.classList.contains("open");

    sidebar.classList.toggle("open");
    overlay.classList.toggle("show");

    if (opening) {
        history.pushState({ sidebar: true }, "");
    }

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

        e.stopPropagation();

        const opening = !quickMenu.classList.contains("show");

        quickMenu.classList.toggle("show");

        fab.innerHTML =
            quickMenu.classList.contains("show")
                ? "✕"
                : "+";

        if (opening) {
            history.pushState({ fab: true }, "");
        }

    });

    quickMenu.querySelectorAll("a").forEach(link => {

        link.addEventListener("click", () => {

            quickMenu.classList.remove("show");
            fab.innerHTML = "+";

        });

    });

}
/* ==========================================
   HANDLE ANDROID BACK BUTTON
========================================== */

window.addEventListener("popstate", function () {

    // Close sidebar first
    if (sidebar && sidebar.classList.contains("open")) {

        sidebar.classList.remove("open");
        overlay.classList.remove("show");

        return;
    }

    // Close floating menu
    if (quickMenu && quickMenu.classList.contains("show")) {

        quickMenu.classList.remove("show");

        if (fab) {
            fab.innerHTML = "+";
        }

        return;
    }

    // If nothing is open, the browser handles normal back navigation.
});



/* ==========================================
   REMINDER CHECKER
========================================== */

async function checkReminders() {

    try {

        const response = await fetch("/check-reminders");
        const data = await response.json();

        data.reminders.forEach(r => {

            if (Notification.permission === "granted") {

                new Notification(r.title, {
                    body: r.description,
                    icon: "/static/icon.png"
                });

            }

        });

    }
    catch (err) {

        console.error(err);

    }

}

/* ==========================================
   FEED PURCHASE CALCULATOR
========================================== */

function calculateFeedQuantity() {

    const bags = document.getElementById("bags");
    const bagSize = document.getElementById("bag_size");
    const quantity = document.getElementById("quantity");

    if (!bags || !bagSize || !quantity) return;

    const total =
        (parseFloat(bags.value) || 0) *
        (parseFloat(bagSize.value) || 0);

    quantity.value = total.toFixed(2);
}

document.addEventListener("DOMContentLoaded", calculateFeedQuantity);

document.addEventListener("input", function (e) {

    if (
        e.target.id === "bags" ||
        e.target.id === "bag_size"
    ) {
        calculateFeedQuantity();
    }

});


/* ==========================
   CREDIT SALES
========================== */

document.addEventListener("DOMContentLoaded", function () {

    const credit = document.getElementById("on_credit");
    const customerBox = document.getElementById("customerBox");

    if (!credit || !customerBox) return;

    function toggleCustomer() {
        customerBox.style.display =
            credit.checked ? "block" : "none";
    }

    credit.addEventListener("change", toggleCustomer);

    toggleCustomer();

});



// Check immediately
checkReminders();

// Then every minute
setInterval(checkReminders, 60000);

});   // <-- closes DOMContentLoaded ONLY