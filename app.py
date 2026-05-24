import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename


UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg","jpeg", "webp", "bmp", "tiff"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024 # 10 MB

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_filename(filename: str) -> str:
    ext = filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "crop_image" not in request.files:
        flash("No file field in the request.", "error")
        return redirect(url_for("index"))
    
    file = request.files["crop_image"]

    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))
    
    if not allowed_file(file.filename):
        flash("Unsupported file type. Please upload a PNG, JPG, JPEG, WEBP, BMP, or TIFF image.", "error")
        return redirect(url_for("index"))
    
    filename = unique_filename(secure_filename(file.filename))
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(save_path)

    return redirect(url_for("result", filename=filename))

@app.route("/result/<filename>")
def result(filename: str):
    safe_name = secure_filename(filename)
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)

    if not os.path.isfile(image_path):
        flash("Image not found.", "error")
        return redirect(url_for("index"))
    
    image_url = url_for("static", filename=f"uploads/{safe_name}")
    return render_template("result.html", image_url=image_url, filename=safe_name)

@app.errorhandler(413)
def too_large(e):
    flash("File too large. Maximum size is 10 MB.", "error")
    return redirect(url_for("index"))

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
        