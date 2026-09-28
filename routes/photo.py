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

from services.cart_service import add_photo_item_to_cart

from services.pricing_service import compute_photo_price

from utils import login_required, current_user


photo_bp = Blueprint(
    "photo",
    __name__,
    url_prefix="/photo"
)


# ============================================================
# SETTINGS
# ============================================================

PHOTO_ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
}


# ============================================================
# HELPERS
# ============================================================

def _allowed_photo_file(filename):
    """Check whether the uploaded file is an allowed image."""

    if "." not in filename:
        return False, ""

    extension = filename.rsplit(
        ".",
        1
    )[1].lower()

    return (
        extension in PHOTO_ALLOWED_EXTENSIONS,
        extension
    )


def _get_user_document(document_id):
    """Return a document only if it belongs to the logged-in user."""

    user = current_user()

    return UploadedDocument.query.filter_by(
        id=document_id,
        user_id=user.id
    ).first()


# ============================================================
# PHOTO UPLOAD
# ============================================================

@photo_bp.route(
    "/",
    methods=["GET", "POST"]
)
@login_required
def upload_photo():

    user = current_user()

    if request.method == "POST":

        file = request.files.get("photo")

        if not file or not file.filename:

            flash(
                "Please choose a photo to upload.",
                "danger"
            )

            return render_template(
                "customer/photo_upload.html"
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
                "customer/photo_upload.html"
            )

        allowed, extension = _allowed_photo_file(
            original_name
        )

        if not allowed:

            flash(
                "Please upload a JPG, JPEG or PNG image.",
                "danger"
            )

            return render_template(
                "customer/photo_upload.html"
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
                "Failed to upload photo."
            )

            flash(
                "Something went wrong while uploading the photo.",
                "danger"
            )

            return render_template(
                "customer/photo_upload.html"
            )

        flash(
            "Photo uploaded successfully. Configure your photo.",
            "success"
        )

        return redirect(
            url_for(
                "photo.configure_photo",
                document_id=document.id
            )
        )

    return render_template(
        "customer/photo_upload.html"
    )


# ============================================================
# PHOTO CONFIGURATION
# ============================================================

@photo_bp.route(
    "/configure/<int:document_id>",
    methods=["GET", "POST"]
)
@login_required
def configure_photo(document_id):

    document = _get_user_document(
        document_id
    )

    if not document:

        flash(
            "Photo not found.",
            "danger"
        )

        return redirect(
            url_for("photo.upload_photo")
        )

    if request.method == "POST":

        photo_size = request.form.get(
            "photo_size",
            "4x6"
        )

        frame = request.form.get(
            "frame",
            "NONE"
        )

        quantity = request.form.get(
            "quantity",
            1,
            type=int
        ) or 1

        quantity = max(
            1,
            min(100, quantity)
        )

        try:

            breakdown = compute_photo_price(
                photo_size,
                frame,
                quantity
            )

        except ValueError as e:

            flash(
                str(e),
                "danger"
            )

            return render_template(
                "customer/photo_configure.html",
                document=document,
                breakdown=None,
                selected_size=photo_size,
                selected_frame=frame,
                quantity=quantity,
            )

        add_photo_item_to_cart(
            user=current_user(),
            document=document,
            photo_size=photo_size,
            frame=frame,
            quantity=quantity,
            computed_total=breakdown["total"],
        )

        flash(
            "Photo added to your cart successfully.",
            "success"
        )

        return redirect(
            url_for("cart.view_cart")
        )

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    photo_size = "4x6"
    frame = "NONE"
    quantity = 1

    breakdown = compute_photo_price(
        photo_size,
        frame,
        quantity
    )

    return render_template(
        "customer/photo_configure.html",
        document=document,
        breakdown=breakdown,
        selected_size=photo_size,
        selected_frame=frame,
        quantity=quantity,
    )