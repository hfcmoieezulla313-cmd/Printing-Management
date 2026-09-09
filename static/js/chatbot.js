// PrintCare - chatbot.js
// Drives the PrintCare AI floating chat widget. Talks only to
// POST /api/chat and GET /api/chat/suggestions on our own server -
// the AI provider key never touches the browser.

document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("chatbot-toggle");
    const closeBtn = document.getElementById("chatbot-close");
    const windowEl = document.getElementById("chatbot-window");
    const messagesEl = document.getElementById("chatbot-messages");
    const suggestionsEl = document.getElementById("chatbot-suggestions");
    const typingEl = document.getElementById("chatbot-typing");
    const formEl = document.getElementById("chatbot-form");
    const inputEl = document.getElementById("chatbot-input");

    if (!toggleBtn || !windowEl) return;

    let sessionId = null;
    let suggestionsLoaded = false;

    function openChat() {
        windowEl.classList.remove("hidden");
        if (!suggestionsLoaded) loadSuggestions();
        inputEl.focus();
    }
    function closeChat() {
        windowEl.classList.add("hidden");
    }

    toggleBtn.addEventListener("click", () => {
        windowEl.classList.contains("hidden") ? openChat() : closeChat();
    });
    closeBtn.addEventListener("click", closeChat);

    function addBubble(text, sender) {
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble chat-bubble-${sender === "user" ? "user" : "ai"}`;
        bubble.textContent = text;
        messagesEl.appendChild(bubble);
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function loadSuggestions() {
        try {
            const res = await fetch("/api/chat/suggestions");
            const data = await res.json();
            (data.suggestions || []).forEach((q) => {
                const chip = document.createElement("button");
                chip.type = "button";
                chip.className = "chatbot-suggestion-chip";
                chip.textContent = q;
                chip.addEventListener("click", () => sendMessage(q));
                suggestionsEl.appendChild(chip);
            });
            suggestionsLoaded = true;
        } catch (err) {
            console.error("Failed to load chatbot suggestions", err);
        }
    }

    async function sendMessage(text) {
        if (!text || !text.trim()) return;
        addBubble(text, "user");
        inputEl.value = "";
        typingEl.classList.remove("hidden");

        try {
            const res = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, session_id: sessionId }),
            });
            const data = await res.json();
            typingEl.classList.add("hidden");

            if (!res.ok) {
                addBubble(data.error || "Sorry, something went wrong. Please try again.", "ai");
                return;
            }

            sessionId = data.session_id;
            addBubble(data.reply, "ai");
        } catch (err) {
            typingEl.classList.add("hidden");
            addBubble("Sorry, I couldn't reach the server. Please try again in a moment.", "ai");
        }
    }

    formEl.addEventListener("submit", (e) => {
        e.preventDefault();
        sendMessage(inputEl.value);
    });
});
