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


# =========================================================
# GENERAL PRINT UPLOAD
# =========================================================

@upload_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_document():
    user = current_user()

    if request.method == "POST":
        file = request.files.get("document")

        if not file or file.filename == "":
            flash("Please choose a document to upload.", "danger")
            return render_template("customer/upload.html")

        original_name = secure_filename(file.filename)

        ok, ext = _allowed_file(original_name)

        if not ok:
            flash(
                "Unsupported file type. Allowed: PDF, DOC, DOCX, JPG, JPEG, PNG.",
                "danger"
            )
            return render_template("customer/upload.html")

        # Create unique filename
        stored_name = f"{uuid.uuid4().hex}.{ext}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]

        os.makedirs(upload_folder, exist_ok=True)

        dest_path = os.path.join(upload_folder, stored_name)

        file.save(dest_path)

        file_size = os.path.getsize(dest_path)

        # Create database record
        document = UploadedDocument(
            user_id=user.id,
            original_filename=original_name,
            stored_filename=stored_name,
            file_extension=ext,
            file_size_bytes=file_size,
            page_count=request.form.get(
                "page_count",
                1,
                type=int
            ) or 1,
        )

        db.session.add(document)
        db.session.commit()

        flash(
            "Document uploaded successfully. Configure your print.",
            "success"
        )

        return redirect(
            url_for(
                "upload.configure_print",
                document_id=document.id
            )
        )

    return render_template("customer/upload.html")


# =========================================================
# CONFIGURE PRINT
# =========================================================

@upload_bp.route(
    "/configure/<int:document_id>",
    methods=["GET", "POST"]
)
@login_required
def configure_print(document_id):

    user = current_user()

    document = UploadedDocument.query.filter_by(
        id=document_id,
        user_id=user.id
    ).first_or_404()

    if request.method == "POST":

        paper_size = request.form.get(
            "paper_size",
            "A4"
        )

        print_type = request.form.get(
            "print_type",
            "BW"
        )

        print_side = request.form.get(
            "print_side",
            "SINGLE"
        )

        copies = request.form.get(
            "copies",
            1,
            type=int
        ) or 1

        binding = request.form.get(
            "binding",
            "NONE"
        )

        page_count = request.form.get(
            "page_count",
            document.page_count,
            type=int
        ) or 1

        # Find the correct printing service
        service = PrintingService.query.filter_by(
            paper_size=paper_size,
            print_type=print_type,
            is_active=True
        ).first()

        if not service:

            flash(
                f"No printing service is available for "
                f"{paper_size} {'Color' if print_type == 'COLOR' else 'B&W'}.",
                "danger"
            )

            return render_template(
                "customer/configure_print.html",
                document=document,
                breakdown=None
            )

        # Calculate price on server
        breakdown = compute_print_price(
            service,
            paper_size,
            print_type,
            print_side,
            copies,
            binding,
            page_count
        )

        # Add item to cart
        add_printing_item_to_cart(
            user,
            document,
            service,
            paper_size,
            print_type,
            print_side,
            copies,
            binding,
            page_count
        )

        flash(
            "Print added to cart successfully.",
            "success"
        )

        return redirect(
            url_for("cart.view_cart")
        )

    # Default configuration
    paper_size = "A4"
    print_type = "BW"
    print_side = "SINGLE"
    copies = 1
    binding = "NONE"

    service = PrintingService.query.filter_by(
        paper_size=paper_size,
        print_type=print_type,
        is_active=True
    ).first()

    breakdown = None

    if service:
        breakdown = compute_print_price(
            service,
            paper_size,
            print_type,
            print_side,
            copies,
            binding,
            document.page_count
        )

    return render_template(
        "customer/configure_print.html",
        document=document,
        service=service,
        breakdown=breakdown
    )


# =========================================================
# OLD SERVICE-BASED UPLOAD
# =========================================================
# Keep this route so your existing printing-service pages
# continue working.

@upload_bp.route(
    "/upload/<slug>",
    methods=["GET", "POST"]
)
@login_required
def upload_service_document(slug):

    service = PrintingService.query.filter_by(
        slug=slug,
        is_active=True
    ).first_or_404()

    user = current_user()

    if request.method == "POST":

        file = request.files.get("document")

        if not file or file.filename == "":
            flash(
                "Please choose a file to upload.",
                "danger"
            )

            return render_template(
                "customer/upload.html",
                service=service
            )

        original_name = secure_filename(
            file.filename
        )

        ok, ext = _allowed_file(original_name)

        if not ok:
            flash(
                "Unsupported file type. Allowed: PDF, DOC, DOCX, JPG, JPEG, PNG.",
                "danger"
            )

            return render_template(
                "customer/upload.html",
                service=service
            )

        stored_name = f"{uuid.uuid4().hex}.{ext}"

        upload_folder = current_app.config["UPLOAD_FOLDER"]

        os.makedirs(upload_folder, exist_ok=True)

        dest_path = os.path.join(
            upload_folder,
            stored_name
        )

        file.save(dest_path)

        file_size = os.path.getsize(dest_path)

        document = UploadedDocument(
            user_id=user.id,
            original_filename=original_name,
            stored_filename=stored_name,
            file_extension=ext,
            file_size_bytes=file_size,
            page_count=request.form.get(
                "page_count",
                1,
                type=int
            ) or 1,
        )

        db.session.add(document)
        db.session.commit()

        flash(
            "Document uploaded. Now configure your print.",
            "success"
        )

        return redirect(
            url_for(
                "upload.configure_print",
                document_id=document.id
            )
        )

    return render_template(
        "customer/upload.html",
        service=service
    )