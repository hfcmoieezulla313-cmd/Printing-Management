// PrintCare - main.js
// Small shared behaviors used across every page.

document.addEventListener("DOMContentLoaded", () => {
    // Auto-dismiss flash messages after a few seconds.
    document.querySelectorAll(".flash").forEach((el, i) => {
        setTimeout(() => {
            el.style.transition = "opacity 0.4s ease";
            el.style.opacity = "0";
            setTimeout(() => el.remove(), 400);
        }, 4000 + i * 300);
    });
});
