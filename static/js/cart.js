// PrintCare - cart.js
// Quantity +/- buttons submit their own small form (see cart.html);
// this file just disables double-submits for a smoother feel.
document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".qty-form").forEach((form) => {
        form.addEventListener("submit", () => {
            form.querySelectorAll("button").forEach((b) => (b.disabled = true));
        });
    });
});
