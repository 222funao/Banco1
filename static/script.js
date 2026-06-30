document.addEventListener("DOMContentLoaded", function () {
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const today = new Date().toISOString().split("T")[0];

    dateInputs.forEach(function (input) {
        if (!input.value) {
            input.value = today;
        }
    });

    const confirmLinks = document.querySelectorAll("[data-confirm]");
    confirmLinks.forEach(function (link) {
        link.addEventListener("click", function (event) {
            const message = link.getAttribute("data-confirm");
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
});
