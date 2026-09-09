// PrintCare - checkout.js
// Prevents placing an order without selecting an address, as a fast
// client-side check (the server independently validates this too).
document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("order-form");
    if (!form) return;
    form.addEventListener("submit", (e) => {
        const selected = form.querySelector('input[name="address_id"]:checked');
        if (!selected) {
            e.preventDefault();
            alert("Please select a delivery address.");
        }
    });
});
