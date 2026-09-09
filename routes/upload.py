import os
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename

from models import db, UploadedDocument, PrintingService
from services.cart_service import add_printing_item_to_cart
from services.pricing_service import compute_print_price
from utils import login_required, current_user

upload_bp = Blueprint("upload", __name__)


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_UPLOAD_EXTENSIONS"], ext


@upload_bp.route("/upload/<slug>", methods=["GET", "POST"])
@login_required
def upload_document(slug):
    service = PrintingService.query.filter_by(slug=slug, is_active=True).first_or_404()
    user = current_user()

    if request.method == "POST":
        file = request.files.get("document")
        if not file or file.filename == "":
            flash("Please choose a file to upload.", "danger")
            return render_template("customer/upload.html", service=service)

        original_name = secure_filename(file.filename)
        ok, ext = _allowed_file(original_name)
        if not ok:
            flash("Unsupported file type. Allowed: PDF, DOC, DOCX, JPG, JPEG, PNG.", "danger")
            return render_template("customer/upload.html", service=service)

        # Secure, unpredictable storage name so uploaded files can never
        # collide or be guessed/executed as something else.
        stored_name = f"{uuid.uuid4().hex}.{ext}"
        dest_path = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
        os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(dest_path)
        file_size = os.path.getsize(dest_path)

        document = UploadedDocument(
            user_id=user.id,
            original_filename=original_name,
            stored_filename=stored_name,
            file_extension=ext,
            file_size_bytes=file_size,
            page_count=request.form.get("page_count", 1, type=int) or 1,
        )
        db.session.add(document)
        db.session.commit()

        flash("Document uploaded. Now configure your print.", "success")
        return redirect(url_for("upload.configure_print", slug=slug, document_id=document.id))

    return render_template("customer/upload.html", service=service)


@upload_bp.route("/configure/<slug>/<int:document_id>", methods=["GET", "POST"])
@login_required
def configure_print(slug, document_id):
    service = PrintingService.query.filter_by(slug=slug, is_active=True).first_or_404()
    user = current_user()
    document = UploadedDocument.query.filter_by(id=document_id, user_id=user.id).first_or_404()

    if request.method == "POST":
        paper_size = request.form.get("paper_size", "A4")
        print_type = request.form.get("print_type", "BW")
        print_side = request.form.get("print_side", "SINGLE")
        copies = request.form.get("copies", 1, type=int) or 1
        binding = request.form.get("binding", "NONE")
        page_count = request.form.get("page_count", document.page_count, type=int) or 1

        add_printing_item_to_cart(user, document, service, paper_size, print_type,
                                   print_side, copies, binding, page_count)
        flash("Added to cart.", "success")
        return redirect(url_for("cart.view_cart"))

    breakdown = compute_print_price(service, "A4", "BW", "SINGLE", 1, "NONE", document.page_count)
    return render_template("customer/configure_print.html", service=service, document=document,
                            breakdown=breakdown)
