// Printify AI - print_config.js
//
// Handles:
// - Total page calculation for all uploaded files
// - Live server-side price calculation
// - A4 / A3
// - B&W / Color
// - Single / Double side
// - Copies
// - Binding
//
// Prices are always calculated by Flask.
// The browser never calculates the final price itself.

document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("config-form");
    const priceBox = document.getElementById("price-breakdown");

    if (!form || !priceBox) {
        console.error("Print configuration elements not found.");
        return;
    }

    const quoteUrl = priceBox.dataset.quoteUrl;

    if (!quoteUrl) {
        console.error("Quote URL not found.");
        return;
    }


    /* =====================================================
       GET SELECTED RADIO VALUE
    ===================================================== */

    function getRadioValue(name, fallback) {

        const selected = form.querySelector(
            `input[name="${name}"]:checked`
        );

        return selected
            ? selected.value
            : fallback;
    }


    /* =====================================================
       GET TOTAL PAGES
    ===================================================== */

    function getPageInputs() {

        return Array.from(
            form.querySelectorAll(
                'input[name^="page_count_"]'
            )
        );
    }


    function getTotalPages() {

        let totalPages = 0;

        const pageInputs = getPageInputs();

        pageInputs.forEach((input) => {

            let pages = parseInt(
                input.value,
                10
            );

            if (Number.isNaN(pages) || pages < 1) {
                pages = 1;
            }

            totalPages += pages;
        });

        return Math.max(
            1,
            totalPages
        );
    }


    /* =====================================================
       UPDATE TOTAL PAGES ON SCREEN
    ===================================================== */

    function updateTotalPages() {

        const totalPages = getTotalPages();

        const pagesElement =
            document.getElementById("pb-pages");

        if (pagesElement) {
            pagesElement.textContent = totalPages;
        }

        return totalPages;
    }


    /* =====================================================
       MONEY FORMAT
    ===================================================== */

    function formatMoney(value) {

        const number = Number(value);

        if (!Number.isFinite(number)) {
            return "Rs. 0.00";
        }

        return `Rs. ${number.toFixed(2)}`;
    }


    /* =====================================================
       REFRESH PRICE
    ===================================================== */

    let requestCounter = 0;

    async function refreshQuote() {

        const requestId = ++requestCounter;

        const paperSize = getRadioValue(
            "paper_size",
            "A4"
        );

        const printType = getRadioValue(
            "print_type",
            "BW"
        );

        const printSide = getRadioValue(
            "print_side",
            "SINGLE"
        );

        const bindingInput =
            document.getElementById("binding");

        const copiesInput =
            document.getElementById("copies");


        const binding = bindingInput
            ? bindingInput.value
            : "NONE";


        let copies = copiesInput
            ? parseInt(
                copiesInput.value,
                10
            )
            : 1;


        if (Number.isNaN(copies) || copies < 1) {
            copies = 1;
        }


        const totalPages =
            updateTotalPages();


        const payload = {
            paper_size: paperSize,
            print_type: printType,
            print_side: printSide,
            copies: copies,
            binding: binding,
            page_count: totalPages
        };


        try {

            const response = await fetch(
                quoteUrl,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",

                        "Accept":
                            "application/json"
                    },

                    body: JSON.stringify(payload)
                }
            );


            const data =
                await response.json();


            /*
             * Ignore an old response if a newer
             * request has already been sent.
             */
            if (requestId !== requestCounter) {
                return;
            }


            if (!response.ok) {

                console.error(
                    "Quote request failed:",
                    data.error
                );

                return;
            }


            const perPage =
                document.getElementById(
                    "pb-per-page"
                );

            const subtotal =
                document.getElementById(
                    "pb-subtotal"
                );

            const bindingCost =
                document.getElementById(
                    "pb-binding"
                );

            const total =
                document.getElementById(
                    "pb-total"
                );


            if (perPage) {

                perPage.textContent =
                    formatMoney(
                        data.price_per_page
                    );
            }


            if (subtotal) {

                subtotal.textContent =
                    formatMoney(
                        data.printing_subtotal
                    );
            }


            if (bindingCost) {

                bindingCost.textContent =
                    formatMoney(
                        data.binding_cost
                    );
            }


            if (total) {

                total.textContent =
                    formatMoney(
                        data.total
                    );
            }


            /*
             * Update total pages one more time after
             * the server responds.
             */
            updateTotalPages();


        } catch (error) {

            console.error(
                "Unable to refresh print quote:",
                error
            );
        }
    }


    /* =====================================================
       ONE EVENT HANDLER FOR THE WHOLE FORM
    ===================================================== */

    form.addEventListener(
        "input",
        (event) => {

            if (
                event.target.matches(
                    'input[name^="page_count_"], #copies'
                )
            ) {
                refreshQuote();
            }
        }
    );


    form.addEventListener(
        "change",
        (event) => {

            if (
                event.target.matches(
                    'input[name^="page_count_"], ' +
                    'input[name="paper_size"], ' +
                    'input[name="print_type"], ' +
                    'input[name="print_side"], ' +
                    '#copies, #binding'
                )
            ) {
                refreshQuote();
            }
        }
    );


    /* =====================================================
       FIRST QUOTE
    ===================================================== */

    updateTotalPages();
    refreshQuote();

});