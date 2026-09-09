// PrintCare - upload.js
// Client-side file size/type hint only. The server always re-validates
// extension, size and filename - this is just faster feedback for the user.
document.addEventListener("DOMContentLoaded", () => {
    const input = document.querySelector('input[type="file"][name="document"]');
    if (!input) return;
    const allowed = ["pdf", "doc", "docx", "jpg", "jpeg", "png"];

    input.addEventListener("change", () => {
        const file = input.files[0];
        if (!file) return;
        const ext = file.name.split(".").pop().toLowerCase();
        if (!allowed.includes(ext)) {
            alert("Unsupported file type. Allowed: PDF, DOC, DOCX, JPG, JPEG, PNG.");
            input.value = "";
            return;
        }
        if (file.size > 15 * 1024 * 1024) {
            alert("File is too large. Maximum size is 15MB.");
            input.value = "";
        }
    });
});
