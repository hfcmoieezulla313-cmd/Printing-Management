import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
)
from werkzeug.utils import secure_filename

from models import db, UploadedDocument, PrintingService
from services.cart_service import add_printing_item_to_cart
from services.pricing_service import compute_print_price
from utils import login_required, current_user


upload_bp = Blueprint("upload", __name__)


# =========================================================
# HELPERS
# =========================================================

PRINT_DOCUMENT_SESSION_KEY = "print_document_ids"


def _allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_UPLOAD_EXTENSIONS"], ext


def _get_print_documents(user, fallback_document_id=None):
    """
    Get the documents belonging to the current print session.

    The normal flow uses document IDs stored in the session.
    A fallback document ID keeps the old single-document flow working.
    """
    document_ids = session.get(PRINT_DOCUMENT_SESSION_KEY, [])

    if not document_ids and fallback_document_id:
        document_ids = [fallback_document_id]

    if not document_ids:
        return []

    documents = (
        UploadedDocument.query
        .filter(
            UploadedDocument.user_id == user.id,
            UploadedDocument.id.in_(document_ids),
        )
        .order_by(UploadedDocument.id.asc())
        .all()
    )

    return documents


# =========================================================
# GENERAL PRINT UPLOAD
# =========================================================

@upload_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_document():

    user = current_user()

    if request.method == "POST":

        # New multiple-file upload field.
        files = request.files.getlist("documents")

        # Backward compatibility with the old single-file field.
        if not files:
            old_file = request.files.get("document")
            if old_file:
                files = [old_file]

        files = [
            file for file in files
            if file and file.filename and file.filename.strip()
        ]

        if not files:
            flash(
                "Please choose at least one file to upload.",
                "danger"
            )
            return render_template("customer/upload.html")

        # -------------------------------------------------
        # Validate every file BEFORE saving anything.
        # -------------------------------------------------

        prepared_files = []

        for file in files:

            original_name = secure_filename(file.filename)

            if not original_name:
                flash(
                    "One of the selected files has an invalid filename.",
                    "danger"
                )
                return render_template("customer/upload.html")

            ok, ext = _allowed_file(original_name)

            if not ok:
                flash(
                    f"Unsupported file: {original_name}. "
                    "Allowed: PDF, DOC, DOCX, JPG, JPEG, PNG.",
                    "danger"
                )
                return render_template("customer/upload.html")

            prepared_files.append(
                {
                    "file": file,
                    "original_name": original_name,
                    "extension": ext,
                }
            )

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)

        created_documents = []
        saved_paths = []

        try:

            # -------------------------------------------------
            # Save every uploaded file.
            # -------------------------------------------------

            for item in prepared_files:

                file = item["file"]
                original_name = item["original_name"]
                ext = item["extension"]

                stored_name = f"{uuid.uuid4().hex}.{ext}"

                dest_path = os.path.join(
                    upload_folder,
                    stored_name
                )

                file.save(dest_path)
                saved_paths.append(dest_path)

                file_size = os.path.getsize(dest_path)

                document = UploadedDocument(
                    user_id=user.id,
                    original_filename=original_name,
                    stored_filename=stored_name,
                    file_extension=ext,
                    file_size_bytes=file_size,

                    # Page count can be adjusted on the
                    # configuration screen.
                    page_count=1,
                )

                db.session.add(document)
                created_documents.append(document)

            db.session.commit()

        except Exception:
            db.session.rollback()

            # Remove files if the database operation fails.
            for path in saved_paths:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass

            current_app.logger.exception(
                "Failed to save uploaded print files."
            )

            flash(
                "Something went wrong while uploading your files. "
                "Please try again.",
                "danger"
            )

            return render_template("customer/upload.html")

        # -------------------------------------------------
        # Store all document IDs for the configuration step.
        # -------------------------------------------------

        document_ids = [
            document.id
            for document in created_documents
        ]

        session[PRINT_DOCUMENT_SESSION_KEY] = document_ids

        flash(
            f"{len(created_documents)} file"
            f"{'' if len(created_documents) == 1 else 's'} "
            "uploaded successfully. Configure your print.",
            "success"
        )

        # Use the first document ID in the URL.
        # The configuration route will load all documents
        # from the session.
        return redirect(
            url_for(
                "upload.configure_print",
                document_id=document_ids[0]
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

    documents = _get_print_documents(
        user,
        fallback_document_id=document_id
    )

    if not documents:
        flash(
            "Your uploaded files could not be found.",
            "danger"
        )

        session.pop(PRINT_DOCUMENT_SESSION_KEY, None)

        return redirect(
            url_for("upload.upload_document")
        )

    # Make sure the URL document belongs to this print session.
    document_ids = {document.id for document in documents}

    if document_id not in document_ids:
        document_id = documents[0].id

    primary_document = next(
        (
            document
            for document in documents
            if document.id == document_id
        ),
        documents[0]
    )

    # -----------------------------------------------------
    # POST: apply the same print configuration to all files
    # -----------------------------------------------------

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

        copies = max(1, copies)

        # -------------------------------------------------
        # Find the correct printing service.
        # -------------------------------------------------

        service = PrintingService.query.filter_by(
            paper_size=paper_size,
            print_type=print_type,
            is_active=True
        ).first()

        if not service:

            flash(
                f"No printing service is available for "
                f"{paper_size} "
                f"{'Color' if print_type == 'COLOR' else 'B&W'}.",
                "danger"
            )

            return render_template(
                "customer/configure_print.html",
                document=primary_document,
                documents=documents,
                service=None,
                breakdown=None
            )

        # -------------------------------------------------
        # Read page count for each uploaded file.
        #
        # New configuration page can submit:
        # page_count_<document_id>
        #
        # The old configuration page's:
        # page_count
        #
        # is also supported for compatibility.
        # -------------------------------------------------

        total_page_count = 0

        for document in documents:

            field_name = f"page_count_{document.id}"

            page_count = request.form.get(
                field_name,
                type=int
            )

            # Backward compatibility with old template.
            if page_count is None:
                page_count = request.form.get(
                    "page_count",
                    document.page_count,
                    type=int
                )

            page_count = max(
                1,
                page_count or document.page_count or 1
            )

            document.page_count = page_count

            total_page_count += page_count

        # -------------------------------------------------
        # Calculate total preview price for all uploaded files.
        # -------------------------------------------------

        breakdown = compute_print_price(
            service,
            paper_size,
            print_type,
            print_side,
            copies,
            binding,
            total_page_count
        )

        # -------------------------------------------------
        # Add every uploaded document to the cart.
        # -------------------------------------------------

        for document in documents:

            add_printing_item_to_cart(
                user,
                document,
                service,
                paper_size,
                print_type,
                print_side,
                copies,
                binding,
                document.page_count
            )

        db.session.commit()

        # Print session is complete.
        session.pop(PRINT_DOCUMENT_SESSION_KEY, None)

        flash(
            f"{len(documents)} print file"
            f"{'' if len(documents) == 1 else 's'} "
            "added to your cart successfully.",
            "success"
        )

        return redirect(
            url_for("cart.view_cart")
        )

    # -----------------------------------------------------
    # GET: default configuration.
    # -----------------------------------------------------

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

    total_page_count = sum(
        max(1, document.page_count or 1)
        for document in documents
    )

    breakdown = None

    if service:

        breakdown = compute_print_price(
            service,
            paper_size,
            print_type,
            print_side,
            copies,
            binding,
            total_page_count
        )

    return render_template(
        "customer/configure_print.html",
        document=primary_document,
        documents=documents,
        service=service,
        breakdown=breakdown
    )


# =========================================================
# OLD SERVICE-BASED UPLOAD
# =========================================================
# Kept so existing printing-service routes continue working.
# It still supports a single file.

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

        # Support both new and old upload field names.
        files = request.files.getlist("documents")

        if not files:
            old_file = request.files.get("document")

            if old_file:
                files = [old_file]

        files = [
            file for file in files
            if file and file.filename and file.filename.strip()
        ]

        if not files:

            flash(
                "Please choose a file to upload.",
                "danger"
            )

            return render_template(
                "customer/upload.html",
                service=service
            )

        # The old service route remains a single-document flow.
        file = files[0]

        original_name = secure_filename(
            file.filename
        )

        if not original_name:

            flash(
                "Invalid filename.",
                "danger"
            )

            return render_template(
                "customer/upload.html",
                service=service
            )

        ok, ext = _allowed_file(original_name)

        if not ok:

            flash(
                "Unsupported file type. "
                "Allowed: PDF, DOC, DOCX, JPG, JPEG, PNG.",
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

        try:

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

        except Exception:

            db.session.rollback()

            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
            except OSError:
                pass

            current_app.logger.exception(
                "Failed to upload service document."
            )

            flash(
                "Something went wrong while uploading the file.",
                "danger"
            )

            return render_template(
                "customer/upload.html",
                service=service
            )

        # Store this document as the active print session.
        session[PRINT_DOCUMENT_SESSION_KEY] = [document.id]

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