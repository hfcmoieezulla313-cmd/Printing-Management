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
)

from werkzeug.utils import secure_filename

from models import db, UploadedDocument

from services.cart_service import add_passport_photo_item_to_cart

from services.pricing_service import compute_passport_photo_price

from utils import login_required, current_user


passport_photo_bp = Blueprint(
    "passport_photo",
    __name__,
    url_prefix="/passport-photo"
)


PASSPORT_ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
}


def _allowed_passport_file(filename):
    """Check whether the uploaded file is an allowed image."""

    if "." not in filename:
        return False, ""

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return (
        extension in PASSPORT_ALLOWED_EXTENSIONS,
        extension
    )


def _get_user_document(document_id):
    """Return a document belonging to the logged-in user."""

    user = current_user()

    return UploadedDocument.query.filter_by(
        id=document_id,
        user_id=user.id
    ).first()


# ============================================================
# PASSPORT PHOTO UPLOAD
# ============================================================

@passport_photo_bp.route(
    "/",
    methods=["GET", "POST"]
)
@login_required
def upload_passport_photo():

    user = current_user()

    if request.method == "POST":

        file = request.files.get("photo")

        if not file or not file.filename:

            flash(
                "Please choose a passport photo to upload.",
                "danger"
            )

            return render_template(
                "customer/passport_photo_upload.html"
            )

        original_name = secure_filename(
            file.filename
        )

        if not original_name:

            flash(
                "Invalid filename.",
                "danger"
            )

            return render_template(
                "customer/passport_photo_upload.html"
            )

        allowed, extension = _allowed_passport_file(
            original_name
        )

        if not allowed:

            flash(
                "Please upload a JPG, JPEG or PNG image.",
                "danger"
            )

            return render_template(
                "customer/passport_photo_upload.html"
            )

        upload_folder = current_app.config[
            "UPLOAD_FOLDER"
        ]

        os.makedirs(
            upload_folder,
            exist_ok=True
        )

        stored_name = (
            f"{uuid.uuid4().hex}.{extension}"
        )

        destination = os.path.join(
            upload_folder,
            stored_name
        )

        try:

            file.save(destination)

            file_size = os.path.getsize(
                destination
            )

            document = UploadedDocument(
                user_id=user.id,
                original_filename=original_name,
                stored_filename=stored_name,
                file_extension=extension,
                file_size_bytes=file_size,
                page_count=1,
            )

            db.session.add(document)
            db.session.commit()

        except Exception:

            db.session.rollback()

            try:
                if os.path.exists(destination):
                    os.remove(destination)
            except OSError:
                pass

            current_app.logger.exception(
                "Failed to upload passport photo."
            )

            flash(
                "Something went wrong while uploading the passport photo.",
                "danger"
            )

            return render_template(
                "customer/passport_photo_upload.html"
            )

        flash(
            "Passport photo uploaded successfully.",
            "success"
        )

        return redirect(
            url_for(
                "passport_photo.configure_passport_photo",
                document_id=document.id
            )
        )

    return render_template(
        "customer/passport_photo_upload.html"
    )


# ============================================================
# PASSPORT PHOTO CONFIGURATION
# ============================================================

@passport_photo_bp.route(
    "/configure/<int:document_id>",
    methods=["GET", "POST"]
)
@login_required
def configure_passport_photo(document_id):

    document = _get_user_document(
        document_id
    )

    if not document:

        flash(
            "Passport photo not found.",
            "danger"
        )

        return redirect(
            url_for(
                "passport_photo.upload_passport_photo"
            )
        )

    if request.method == "POST":

        quantity = request.form.get(
            "quantity",
            1,
            type=int
        ) or 1

        quantity = max(
            1,
            min(12, quantity)
        )

        breakdown = compute_passport_photo_price(
            quantity
        )

        add_passport_photo_item_to_cart(
            user=current_user(),
            document=document,
            quantity=quantity,
            computed_total=breakdown["total"],
        )

        flash(
            "Passport photo added to your cart successfully.",
            "success"
        )

        return redirect(
            url_for("cart.view_cart")
        )

    quantity = 1

    breakdown = compute_passport_photo_price(
        quantity
    )

    return render_template(
        "customer/passport_photo_configure.html",
        document=document,
        breakdown=breakdown,
        quantity=quantity,
    )