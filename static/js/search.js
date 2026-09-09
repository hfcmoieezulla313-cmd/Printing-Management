// PrintCare - search.js
// Progressive enhancement: nothing required for the search form to
// work (it's a plain GET form), this just avoids empty searches.
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".search-form");
    if (!form) return;
    form.addEventListener("submit", (e) => {
        const input = form.querySelector('input[name="q"]');
        if (input && !input.value.trim()) e.preventDefault();
    });
});
