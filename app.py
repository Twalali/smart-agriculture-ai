import os
import uuid
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename

from analyzer import analyse_image, AnalysisResult, Detection
from weather import get_weather, get_weather_by_coords
from crop_calendar import get_all_crops, get_current_month_activities, get_categories, MONTH_NAMES, MONTH_SHORT

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def unique_filename(filename: str) -> str:
    ext = filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"


def result_to_dict(r: AnalysisResult) -> dict:
    return {
        "health_score":    r.health_score,
        "overall_status":  r.overall_status,
        "crop_type":       r.crop_type,
        "growth_stage":    r.growth_stage,
        "detections":      [{"name": d.name, "confidence": d.confidence,
                             "severity": d.severity, "description": d.description}
                            for d in r.detections],
        "recommendations": r.recommendations,
        "summary":         r.summary,
        "error":           r.error,
    }


def dict_to_result(d: dict) -> AnalysisResult:
    return AnalysisResult(
        health_score=d["health_score"],
        overall_status=d["overall_status"],
        crop_type=d["crop_type"],
        growth_stage=d["growth_stage"],
        detections=[Detection(**det) for det in d["detections"]],
        recommendations=d["recommendations"],
        summary=d["summary"],
        error=d.get("error"),
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/weather")
def weather_api():
    location = request.args.get("location", "").strip()
    if not location:
        return jsonify({"error": "No location provided."}), 400
    data = get_weather(location)
    if data.error:
        return jsonify({"error": data.error}), 400
    return jsonify({
        "location": data.location, "country": data.country,
        "temperature": data.temperature, "humidity": data.humidity,
        "precipitation": data.precipitation, "wind_speed": data.wind_speed,
        "condition": data.condition, "weather_code": data.weather_code,
        "rain_3days": data.rain_3days, "temp_max": data.temp_max,
        "temp_min": data.temp_min, "farming_risk": data.farming_risk,
        "farming_advice": data.farming_advice,
    })


@app.route("/api/weather/coords")
def weather_coords_api():
    try:
        lat = float(request.args.get("lat", ""))
        lon = float(request.args.get("lon", ""))
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid coordinates."}), 400
    data = get_weather_by_coords(lat, lon)
    if data.error:
        return jsonify({"error": data.error}), 400
    return jsonify({
        "location": data.location, "country": data.country,
        "temperature": data.temperature, "humidity": data.humidity,
        "precipitation": data.precipitation, "wind_speed": data.wind_speed,
        "condition": data.condition, "weather_code": data.weather_code,
        "rain_3days": data.rain_3days, "temp_max": data.temp_max,
        "temp_min": data.temp_min, "farming_risk": data.farming_risk,
        "farming_advice": data.farming_advice,
    })


@app.route("/upload/ajax", methods=["POST"])
def upload_ajax():
    """AJAX upload endpoint — returns JSON {redirect: url} or {error: msg}"""
    if "crop_image" not in request.files:
        return jsonify({"error": "No file provided."}), 400

    file = request.files["crop_image"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Please upload PNG, JPG, JPEG, or WEBP."}), 400

    filename = unique_filename(secure_filename(file.filename))
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(save_path)

    result = analyse_image(save_path)
    session["last_analysis"] = result_to_dict(result)
    session["last_filename"] = filename

    return jsonify({"redirect": url_for("result", filename=filename)})


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

    # Run AI analysis ONCE here — store in session to avoid re-running on result page
    result = analyse_image(save_path)
    session["last_analysis"] = result_to_dict(result)
    session["last_filename"] = filename

    return redirect(url_for("result", filename=filename))


@app.route("/result/<filename>")
def result(filename: str):
    safe_name = secure_filename(filename)
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)

    if not os.path.isfile(image_path):
        flash("Image not found.", "error")
        return redirect(url_for("index"))

    # Use cached analysis from session if available — avoids double AI call
    cached = session.get("last_analysis")
    if cached and session.get("last_filename") == safe_name:
        analysis = dict_to_result(cached)
    else:
        # Direct URL access — re-run analysis
        analysis = analyse_image(image_path)

    image_url = url_for("static", filename=f"uploads/{safe_name}")
    return render_template("result.html", image_url=image_url,
                           filename=safe_name, analysis=analysis)


@app.route("/calendar")
def calendar():
    import datetime
    current_month = datetime.date.today().month
    crops         = get_all_crops()
    activities    = get_current_month_activities(current_month)
    categories    = get_categories()
    return render_template("calendar.html", crops=crops, activities=activities,
                           categories=categories, current_month=current_month,
                           month_name=MONTH_NAMES[current_month],
                           month_names=MONTH_NAMES, month_short=MONTH_SHORT)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/diseases")
def disease_library():
    disease_map = {}
    for crop in get_all_crops():
        for disease in crop.disease_risks:
            if disease not in disease_map:
                disease_map[disease] = []
            disease_map[disease].append({
                "name": crop.name, "local_name": crop.local_name,
                "category": crop.category,
            })
    diseases = sorted(disease_map.items())
    return render_template("diseases.html", diseases=diseases)


@app.errorhandler(413)
def too_large(e):
    flash("File too large. Maximum size is 10 MB.", "error")
    return redirect(url_for("index"))


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
