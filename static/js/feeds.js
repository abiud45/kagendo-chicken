/* =====================================================
   KAGENDO CHICKEN
   Feed Management
===================================================== */

document.addEventListener("DOMContentLoaded", function () {

    /* ==========================================
       MODAL
    ========================================== */

    const modal = document.getElementById("feedModal");
    const openBtn = document.getElementById("openFeedModal");
    const closeBtn = document.getElementById("closeFeedModal");

    if (openBtn && modal) {

        openBtn.addEventListener("click", function () {

            modal.style.display = "flex";

        });

    }

    if (closeBtn && modal) {

        closeBtn.addEventListener("click", function () {

            modal.style.display = "none";

        });

    }

    window.addEventListener("click", function (e) {

        if (e.target === modal) {

            modal.style.display = "none";

        }

    });

    /* ==========================================
       SEARCH
    ========================================== */

    const search = document.getElementById("feedSearch");

    if (search) {

        search.addEventListener("keyup", function () {

            const value = this.value.toLowerCase();

            document.querySelectorAll(".feed-card").forEach(function (card) {

                card.style.display =
                    card.innerText.toLowerCase().includes(value)
                        ? ""
                        : "none";

            });

        });

    }

    /* ==========================================
       FILTERS
    ========================================== */

    const filters = document.querySelectorAll(".filter");

    filters.forEach(function (button) {

        button.addEventListener("click", function () {

            filters.forEach(function (btn) {

                btn.classList.remove("active");

            });

            this.classList.add("active");

            const filter = this.dataset.filter;

            document.querySelectorAll(".feed-card").forEach(function (card) {

                if (filter === "all") {

                    card.style.display = "";

                    return;

                }

                card.style.display =
                    card.dataset.feed === filter
                        ? ""
                        : "none";

            });

        });

    });

    /* ==========================================
       ANIMATE PROGRESS BARS
    ========================================== */

    document.querySelectorAll(".progress-fill").forEach(function (bar) {

        const width = bar.style.width;

        bar.style.width = "0%";

        setTimeout(function () {

            bar.style.width = width;

        }, 200);

    });

    /* ==========================================
       LOW STOCK HIGHLIGHT
    ========================================== */

    document.querySelectorAll(".feed-card").forEach(function (card) {

        const text = card.innerText;

        const match = text.match(/([\d.]+)\s*\/\s*([\d.]+)\s*kg/);

        if (!match) return;

        const remaining = parseFloat(match[1]);
        const total = parseFloat(match[2]);

        if (remaining === 0) {

            card.style.borderLeft = "8px solid #D32F2F";

        }
        else if (remaining <= total * 0.20) {

            card.style.borderLeft = "8px solid #F57C00";

        }
        else {

            card.style.borderLeft = "8px solid #43A047";

        }

    });

});