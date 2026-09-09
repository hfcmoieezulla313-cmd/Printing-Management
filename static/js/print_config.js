// PrintCare - print_config.js
// Lets the print-configuration screen show a live price preview by
// asking the server (never computing/trusting a price in the browser).

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("config-form");
    if (!form) return;

    const priceBox = document.getElementById("price-breakdown");
    const quoteUrl = priceBox ? priceBox.dataset.quoteUrl : null;
    const serviceId = form.dataset.serviceId;

    const fields = ["paper_size", "print_type", "print_side", "copies", "binding", "page_count"];

    async function refreshQuote() {
        if (!quoteUrl) return;
        const payload = { printing_service_id: serviceId };
        fields.forEach((f) => {
            const el = document.getElementById(f);
            if (el) payload[f] = el.value;
        });

        try {
            const res = await fetch(quoteUrl, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            if (!res.ok) return;
            const data = await res.json();

            const perPage = document.getElementById("pb-per-page");
            const subtotal = document.getElementById("pb-subtotal");
            const binding = document.getElementById("pb-binding");
            const total = document.getElementById("pb-total");

            if (perPage) perPage.textContent = `Rs. ${data.price_per_page.toFixed(2)}`;
            if (subtotal) subtotal.textContent = `Rs. ${data.printing_subtotal.toFixed(2)}`;
            if (binding) binding.textContent = `Rs. ${data.binding_cost.toFixed(2)}`;
            if (total) total.textContent = `Rs. ${data.total.toFixed(2)}`;
        } catch (err) {
            // Silently ignore - the server-side total on submit is authoritative anyway.
            console.error("Quote refresh failed", err);
        }
    }

    fields.forEach((f) => {
        const el = document.getElementById(f);
        if (el) el.addEventListener("change", refreshQuote);
    });
});
