"""
PrintCare AI - customer care chatbot backend logic.

Design:
- The API key NEVER reaches the browser; it is read from config/.env
  and used only in this server-side module.
- We build a small, safe "context" string from the database (current
  prices, settings, and - if the user is authenticated - only THEIR
  own latest order) and hand that to the AI provider as part of the
  prompt, so answers reflect real current data instead of the model's
  guesses.
- If the AI provider is not configured or a network/API call fails,
  we fall back to a local, rule-based FAQ answerer that still reads
  live prices/settings from the database.
"""
import re
from google import genai
from flask import current_app

from models import db, PrintingService, Setting, Order, ChatSession, ChatMessage


# ---------------------------------------------------------------------------
# Context building (database-aware, privacy-safe)
# ---------------------------------------------------------------------------

def _printing_price_lines():
    services = PrintingService.query.filter_by(is_active=True).all()
    lines = []
    for s in services:
        if s.is_configurable:
            lines.append(f"- {s.name}: Rs. {s.price_per_page}/page"
                          + (f" (+Rs. {s.double_side_extra}/page for double-sided)" if s.double_side_extra else ""))
        else:
            lines.append(f"- {s.name}: Rs. {s.flat_price}")
    return lines


def _settings_lines():
    min_order = Setting.get("minimum_order_value", "100")
    free_delivery = Setting.get("free_delivery_threshold", "100")
    delivery_charge = Setting.get("delivery_charge", "30")
    support_phone = Setting.get("support_phone", "N/A")
    support_email = Setting.get("support_email", "N/A")
    return [
        f"- Minimum order value: Rs. {min_order}",
        f"- Free delivery on orders of Rs. {free_delivery} or more, else delivery charge is Rs. {delivery_charge}",
        f"- Support phone: {support_phone}, Support email: {support_email}",
    ]


def _users_own_latest_order_line(user):
    """Only ever looks up the CURRENTLY AUTHENTICATED user's own order.
    Never accepts an order number/user id from the message itself, so
    the chatbot cannot be tricked into revealing someone else's data."""
    if not user:
        return "- The visitor is not logged in, so no order information is available. " \
               "Ask them to log in to check order status."
    order = (Order.query.filter_by(user_id=user.id)
             .order_by(Order.created_at.desc()).first())
    if not order:
        return f"- {user.full_name} has no orders yet."
    return (f"- {user.full_name}'s most recent order is {order.order_number}, "
            f"status: '{order.status}', total Rs. {order.total_amount}.")


def build_context(user):
    lines = ["Current printing prices (from database):"]
    lines += _printing_price_lines()
    lines.append("")
    lines.append("Current store settings:")
    lines += _settings_lines()
    lines.append("")
    lines.append("Authenticated customer's own order info (do not reveal any other customer's data):")
    lines.append(_users_own_latest_order_line(user))
    return "\n".join(lines)


SYSTEM_PROMPT_TEMPLATE = """You are PrintCare AI, the friendly customer-care assistant for an \
online printing and stationery delivery service. Answer briefly and helpfully. \
Only use the store information given below; if something isn't covered, tell the \
customer to contact support. Never invent prices - use only the numbers given. \
Never discuss or guess any other customer's orders or personal data.

Store information:
{context}
"""


# ---------------------------------------------------------------------------
# AI provider call
# ---------------------------------------------------------------------------

def _call_ai_provider(user_message, context):
    api_key = current_app.config.get("GEMINI_API_KEY")

    if not api_key:
        return None

    model = current_app.config.get("AI_MODEL", "gemini-3.6-flash")
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
{system_prompt}

Customer message:
{user_message}

Answer the customer briefly and helpfully.
"""

        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )

        text = (response.text or "").strip()
        return text or None

    except Exception:
        current_app.logger.exception(
            "Gemini API call failed, using fallback FAQ."
        )
        return None
# ---------------------------------------------------------------------------
# Local fallback FAQ (works with zero external dependencies)
# ---------------------------------------------------------------------------

def _fallback_answer(user_message, user):
    msg = user_message.lower()

    def price_reply():
        lines = _printing_price_lines()
        return "Here are our current printing prices:\n" + "\n".join(lines)

    if any(k in msg for k in ["price", "cost", "how much", "rate"]):
        return price_reply()

    if "upload" in msg and "document" in msg or ("upload" in msg and "how" in msg):
        return ("To upload a document: go to Printing Services, choose a service, "
                "then use 'Upload Document' to pick your PDF/DOC/DOCX/JPG/PNG file. "
                "You can then configure paper size, color, sides, copies and binding.")

    if "where is my order" in msg or ("order" in msg and "track" in msg) or "order status" in msg:
        return _users_own_latest_order_line(user).lstrip("- ")

    if "delivery" in msg or "shipping" in msg:
        lines = _settings_lines()
        return "Delivery info:\n" + "\n".join(l for l in lines if "delivery" in l.lower() or "minimum" in l.lower())

    if "minimum order" in msg or "min order" in msg:
        min_order = Setting.get("minimum_order_value", "100")
        return f"Our minimum order value is Rs. {min_order}."

    if "stationery" in msg:
        return ("We stock Pens & Pencils, Notebooks, Files & Folders and Office Supplies. "
                "Browse them under the Stationery tab.")

    if "cancel" in msg and "order" in msg:
        return ("You can request cancellation from 'My Orders' > order details if it hasn't "
                "been dispatched yet, or contact support and we'll help right away.")

    if "coupon" in msg or "discount" in msg or "promo" in msg:
        return ("You can apply a coupon code at checkout in the 'Apply Coupon' box. "
                "We'll validate it and show the discount before you pay.")

    if any(k in msg for k in ["complaint", "support", "help", "problem", "issue"]):
        return ("I'm sorry you're running into trouble. You can raise a complaint from the "
                "Support page and our team will get back to you, or reply here with more details.")

    return ("I can help with printing prices, document upload, stationery, cart, coupons, "
            "delivery, order tracking, cancellations and complaints. Could you tell me a bit "
            "more about what you need?")


def get_quick_suggestions():
    return [
        "How much is A4 B&W printing?",
        "How do I upload a document?",
        "Where is my order?",
        "How much is delivery?",
        "What stationery do you have?",
        "How can I cancel my order?",
    ]


# ---------------------------------------------------------------------------
# Public entry point used by routes/chatbot.py
# ---------------------------------------------------------------------------

def handle_chat_message(user, session_id, user_message):
    user_message = (user_message or "").strip()
    if not user_message:
        raise ValueError("Message cannot be empty.")
    if len(user_message) > 1000:
        user_message = user_message[:1000]

    session = ChatSession.query.get(session_id) if session_id else None
    if not session:
        session = ChatSession(user_id=user.id if user else None)
        db.session.add(session)
        db.session.commit()

    db.session.add(ChatMessage(session_id=session.id, sender="user", message=user_message))
    db.session.commit()

    context = build_context(user)
    ai_reply = _call_ai_provider(user_message, context)
    used_fallback = ai_reply is None
    reply_text = ai_reply if ai_reply else _fallback_answer(user_message, user)

    db.session.add(ChatMessage(session_id=session.id, sender="ai", message=reply_text))
    db.session.commit()

    return {
        "session_id": session.id,
        "reply": reply_text,
        "used_fallback": used_fallback,
    }
