import os
import uuid
import json
from datetime import datetime, date

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify, session)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.utils import secure_filename

from models import db, User, Analysis, ChatLog
from auth import farmer_required, admin_required, dashboard_required, BURUNDI_PROVINCES
from analyzer import analyse_image, AnalysisResult, Detection
from weather import get_weather, get_weather_by_coords
from crop_calendar import (get_all_crops, get_current_month_activities,
                            get_categories, MONTH_NAMES, MONTH_SHORT)

# ── App setup ────────────────────────────────────────────────
UPLOAD_FOLDER      = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp", "tiff"}
MAX_CONTENT_LENGTH = 10 * 1024 * 1024

app = Flask(__name__)
app.secret_key             = os.environ.get("SECRET_KEY", "dev-secret-change-in-production")
app.config["UPLOAD_FOLDER"]        = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"]   = MAX_CONTENT_LENGTH
app.config["SQLALCHEMY_DATABASE_URI"]    = "sqlite:///agri.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view      = "auth_login"
login_manager.login_message   = "Please log in to access this page."
login_manager.login_message_category = "error"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── Helpers ──────────────────────────────────────────────────
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def unique_filename(filename):
    ext = filename.rsplit(".", 1)[1].lower()
    return f"{uuid.uuid4().hex}.{ext}"

def current_season():
    m = date.today().month
    return "A" if m >= 9 or m <= 1 else "B"

def result_to_dict(r):
    return {
        "health_score": r.health_score, "overall_status": r.overall_status,
        "crop_type": r.crop_type, "growth_stage": r.growth_stage,
        "detections": [{"name": d.name, "confidence": d.confidence,
                        "severity": d.severity, "description": d.description}
                       for d in r.detections],
        "recommendations": r.recommendations,
        "summary": r.summary, "error": r.error,
    }

def dict_to_result(d):
    return AnalysisResult(
        health_score=d["health_score"], overall_status=d["overall_status"],
        crop_type=d["crop_type"], growth_stage=d["growth_stage"],
        detections=[Detection(**det) for det in d["detections"]],
        recommendations=d["recommendations"],
        summary=d["summary"], error=d.get("error"),
    )


# ── Auth routes ──────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def auth_register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")
        full_name= request.form.get("full_name", "").strip()
        phone    = request.form.get("phone", "").strip()
        province = request.form.get("province", "").strip()
        commune  = request.form.get("commune", "").strip()

        if not all([username, email, password]):
            flash("Username, email and password are required.", "error")
            return render_template("auth/register.html", provinces=BURUNDI_PROVINCES)
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html", provinces=BURUNDI_PROVINCES)
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/register.html", provinces=BURUNDI_PROVINCES)
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("auth/register.html", provinces=BURUNDI_PROVINCES)
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html", provinces=BURUNDI_PROVINCES)

        user = User(username=username, email=email, role="farmer",
                    full_name=full_name, phone=phone,
                    province=province, commune=commune)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(f"Welcome, {username}! Your account has been created.", "success")
        return redirect(url_for("index"))

    return render_template("auth/register.html", provinces=BURUNDI_PROVINCES)


@app.route("/login", methods=["GET", "POST"])
def auth_login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash("Invalid username or password.", "error")
            return render_template("auth/login.html")
        if not user.is_active:
            flash("Your account has been deactivated. Contact admin.", "error")
            return render_template("auth/login.html")
        user.last_login = datetime.utcnow()
        db.session.commit()
        login_user(user, remember=remember)
        flash(f"Welcome back, {user.username}!", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("index"))
    return render_template("auth/login.html")


@app.route("/logout")
@login_required
def auth_logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def auth_profile():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", "").strip()
        current_user.phone     = request.form.get("phone", "").strip()
        current_user.province  = request.form.get("province", "").strip()
        current_user.commune   = request.form.get("commune", "").strip()
        new_password = request.form.get("new_password", "")
        if new_password:
            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "error")
                return render_template("auth/profile.html", provinces=BURUNDI_PROVINCES)
            current_user.set_password(new_password)
        db.session.commit()
        flash("Profile updated successfully.", "success")
    return render_template("auth/profile.html", provinces=BURUNDI_PROVINCES)


# ── Main routes ──────────────────────────────────────────────
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
    if "crop_image" not in request.files:
        return jsonify({"error": "No file provided."}), 400
    file = request.files["crop_image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type."}), 400

    filename  = unique_filename(secure_filename(file.filename))
    save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(save_path)

    result = analyse_image(save_path)

    # Save to database
    province = None
    commune  = None
    if current_user.is_authenticated:
        province = current_user.province
        commune  = current_user.commune

    analysis_record = Analysis(
        user_id        = current_user.id if current_user.is_authenticated else None,
        filename       = filename,
        crop_type      = result.crop_type,
        growth_stage   = result.growth_stage,
        health_score   = result.health_score,
        overall_status = result.overall_status,
        summary        = result.summary,
        detections     = json.dumps([{"name": d.name, "confidence": d.confidence,
                                      "severity": d.severity, "description": d.description}
                                     for d in result.detections]),
        recommendations= json.dumps(result.recommendations),
        had_error      = bool(result.error),
        province       = province,
        commune        = commune,
        season         = current_season(),
    )
    db.session.add(analysis_record)
    db.session.commit()

    session["last_analysis"]    = result_to_dict(result)
    session["last_filename"]    = filename
    session["last_analysis_id"] = analysis_record.id

    return jsonify({"redirect": url_for("result", filename=filename)})


@app.route("/upload", methods=["POST"])
def upload():
    flash("Please use the upload form on the home page.", "error")
    return redirect(url_for("index"))


@app.route("/result/<filename>")
def result(filename):
    safe_name  = secure_filename(filename)
    image_path = os.path.join(app.config["UPLOAD_FOLDER"], safe_name)
    if not os.path.isfile(image_path):
        flash("Image not found.", "error")
        return redirect(url_for("index"))

    cached = session.get("last_analysis")
    if cached and session.get("last_filename") == safe_name:
        analysis = dict_to_result(cached)
    else:
        analysis = analyse_image(image_path)

    image_url   = url_for("static", filename=f"uploads/{safe_name}")
    analysis_id = session.get("last_analysis_id")
    return render_template("result.html", image_url=image_url,
                           filename=safe_name, analysis=analysis,
                           analysis_id=analysis_id)


# ── Farm history ─────────────────────────────────────────────
@app.route("/history")
@login_required
def farm_history():
    analyses = (Analysis.query
                .filter_by(user_id=current_user.id)
                .order_by(Analysis.created_at.desc())
                .all())
    return render_template("history.html", analyses=analyses)


@app.route("/history/<int:analysis_id>")
@login_required
def history_detail(analysis_id):
    record = Analysis.query.get_or_404(analysis_id)
    if record.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error")
        return redirect(url_for("farm_history"))
    chats  = ChatLog.query.filter_by(analysis_id=analysis_id).order_by(ChatLog.created_at).all()
    image_url = url_for("static", filename=f"uploads/{record.filename}")

    # Reconstruct AnalysisResult for the template
    analysis = AnalysisResult(
        health_score   = record.health_score or 0,
        overall_status = record.overall_status or "unknown",
        crop_type      = record.crop_type or "Unknown",
        growth_stage   = record.growth_stage or "Unknown",
        detections     = [Detection(**d) for d in record.detections_list],
        recommendations= record.recommendations_list,
        summary        = record.summary or "",
        error          = None if not record.had_error else "Previous analysis had an error.",
    )
    return render_template("history_detail.html", record=record,
                           analysis=analysis, image_url=image_url, chats=chats)


@app.route("/history/<int:analysis_id>/delete", methods=["POST"])
@login_required
def history_delete(analysis_id):
    record = Analysis.query.get_or_404(analysis_id)
    if record.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error")
        return redirect(url_for("farm_history"))
    db.session.delete(record)
    db.session.commit()
    flash("Analysis deleted.", "success")
    return redirect(url_for("farm_history"))


# ── Admin dashboard ──────────────────────────────────────────
@app.route("/admin")
@dashboard_required
def admin_dashboard():
    from datetime import timedelta, date as date_type
    import json

    now_str        = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
    total_users    = User.query.filter_by(role="farmer").count()
    total_analyses = Analysis.query.count()
    recent         = (Analysis.query
                      .order_by(Analysis.created_at.desc())
                      .limit(20).all())

    all_analyses   = Analysis.query.filter_by(had_error=False).all()

    disease_counts = {}
    province_counts= {}
    crop_counts    = {}
    status_counts  = {"healthy": 0, "at_risk": 0, "diseased": 0, "critical": 0}
    season_a = season_b = 0
    health_scores  = []
    critical_count = 0

    for a in all_analyses:
        # Diseases
        for d in a.detections_list:
            name = d.get("name", "Unknown")
            disease_counts[name] = disease_counts.get(name, 0) + 1
        # Provinces
        if a.province:
            province_counts[a.province] = province_counts.get(a.province, 0) + 1
        # Crops
        if a.crop_type:
            crop_counts[a.crop_type] = crop_counts.get(a.crop_type, 0) + 1
        # Status
        s = a.overall_status or "unknown"
        if s in status_counts:
            status_counts[s] += 1
        if s == "critical":
            critical_count += 1
        # Season
        if a.season == "A":
            season_a += 1
        elif a.season == "B":
            season_b += 1
        # Health
        if a.health_score is not None:
            health_scores.append(a.health_score)

    top_diseases  = sorted(disease_counts.items(),  key=lambda x: x[1], reverse=True)[:10]
    top_provinces = sorted(province_counts.items(), key=lambda x: x[1], reverse=True)
    top_crops     = sorted(crop_counts.items(),     key=lambda x: x[1], reverse=True)[:8]
    avg_health    = f"{sum(health_scores)/len(health_scores):.0f}/100" if health_scores else "—"
    total_diseases= len(disease_counts)
    total_provinces= len(province_counts)

    # Timeline — analyses per day for last 30 days
    today      = datetime.utcnow().date()
    date_range = [(today - timedelta(days=i)) for i in range(29, -1, -1)]
    day_counts = {d: 0 for d in date_range}
    for a in Analysis.query.filter(
            Analysis.created_at >= datetime.utcnow() - timedelta(days=30)).all():
        d = a.created_at.date()
        if d in day_counts:
            day_counts[d] += 1
    timeline_dates  = [d.strftime("%d %b") for d in date_range]
    timeline_counts = [day_counts[d] for d in date_range]

    return render_template("admin/dashboard.html",
        now=now_str,
        total_users=total_users,
        total_analyses=total_analyses,
        total_diseases=total_diseases,
        total_provinces=total_provinces,
        critical_count=critical_count,
        avg_health=avg_health,
        recent=recent,
        top_diseases=top_diseases,
        top_provinces=top_provinces,
        top_crops=top_crops,
        status_counts=status_counts,
        season_a=season_a,
        season_b=season_b,
        timeline_dates=timeline_dates,
        timeline_counts=timeline_counts,
    )


@app.route("/admin/users")
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@app.route("/admin/users/<int:user_id>/role", methods=["POST"])
@admin_required
def admin_change_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.form.get("role")
    if new_role in ("farmer", "admin", "government"):
        user.role = new_role
        db.session.commit()
        flash(f"{user.username} role changed to {new_role}.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@admin_required
def admin_toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status = "activated" if user.is_active else "deactivated"
    flash(f"{user.username} has been {status}.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/dataset/export")
@admin_required
def admin_export_dataset():
    """Export all analyses as CSV for research."""
    import csv, io
    analyses = Analysis.query.filter_by(had_error=False).all()
    output   = io.StringIO()
    writer   = csv.writer(output)
    writer.writerow(["id","date","crop_type","growth_stage","health_score",
                     "overall_status","diseases","province","commune","season"])
    for a in analyses:
        diseases = "|".join(d.get("name","") for d in a.detections_list)
        writer.writerow([a.id, a.created_at.strftime("%Y-%m-%d"),
                         a.crop_type, a.growth_stage, a.health_score,
                         a.overall_status, diseases,
                         a.province, a.commune, a.season])
    from flask import Response
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=agri_dataset.csv"}
    )


# ── Chat API ─────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided."}), 400
    user_message  = data.get("message", "").strip()
    context       = data.get("context", {})
    history       = data.get("history", [])
    analysis_id   = data.get("analysis_id")
    if not user_message:
        return jsonify({"error": "Empty message."}), 400

    from analyzer import _get_client
    import google.genai.types as gtypes
    import time

    detections_text = ", ".join(context.get("detections", [])) or "none detected"
    recs_text = "\n".join(f"- {r}" for r in context.get("recommendations", []))

    system_prompt = f"""You are an expert agronomist and farming advisor for Burundi.
You are helping a farmer who just received an AI analysis of their crop.

CROP ANALYSIS CONTEXT:
- Crop: {context.get('crop_type', 'Unknown')}
- Growth stage: {context.get('growth_stage', 'Unknown')}
- Health score: {context.get('health_score', 0)}/100
- Status: {context.get('overall_status', 'Unknown')}
- Summary: {context.get('summary', '')}
- Detected issues: {detections_text}
- Recommendations already given:
{recs_text}

INSTRUCTIONS:
- Answer the farmer's question directly and practically.
- Keep answers clear, short, and actionable.
- Use simple language appropriate for rural farmers in Burundi.
- If relevant, mention specific products or methods available in Burundi/East Africa.
- Respond in the same language the farmer uses (English, French, or Kirundi)."""

    if not history:
        contents = [{"role": "user", "parts": [{"text": system_prompt + "\n\nFarmer question: " + user_message}]}]
    else:
        contents = (
            [{"role": "user",  "parts": [{"text": system_prompt}]},
             {"role": "model", "parts": [{"text": "Understood. I am ready to help."}]}]
            + [{"role": m["role"], "parts": [{"text": m["content"]}]} for m in history[-8:]]
            + [{"role": "user",  "parts": [{"text": user_message}]}]
        )

    _CHAT_MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
    last_error   = ""
    reply_text   = ""

    try:
        client = _get_client()
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

    for attempt, model in enumerate(_CHAT_MODELS):
        try:
            response = client.models.generate_content(
                model=model, contents=contents,
                config=gtypes.GenerateContentConfig(max_output_tokens=2048, temperature=0.4),
            )
            for part in (response.candidates[0].content.parts if response.candidates else []):
                if hasattr(part, "thought") and part.thought:
                    continue
                if isinstance(part.text, str):
                    reply_text += part.text
            break
        except Exception as exc:
            last_error = str(exc)
            is_retriable = ("503" in last_error or "unavailable" in last_error.lower()
                            or "429" in last_error or "quota" in last_error.lower())
            if is_retriable and attempt < len(_CHAT_MODELS) - 1:
                time.sleep(2)
                continue
            break

    if not reply_text.strip():
        return jsonify({"error": f"AI error: {last_error}"}), 500

    # Save chat to database if we have an analysis_id
    if analysis_id:
        try:
            db.session.add(ChatLog(analysis_id=analysis_id, role="user",    content=user_message))
            db.session.add(ChatLog(analysis_id=analysis_id, role="model",   content=reply_text.strip()))
            db.session.commit()
        except Exception:
            pass  # Chat saving failure should not break the response

    return jsonify({"reply": reply_text.strip()})


# ── Other pages ──────────────────────────────────────────────
@app.route("/calendar")
def calendar():
    current_month = date.today().month
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
            disease_map[disease].append({"name": crop.name,
                                          "local_name": crop.local_name,
                                          "category": crop.category})
    diseases = sorted(disease_map.items())
    return render_template("diseases.html", diseases=diseases)


@app.errorhandler(413)
def too_large(e):
    flash("File too large. Maximum size is 10 MB.", "error")
    return redirect(url_for("index"))

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ── DB init ──────────────────────────────────────────────────
def create_tables():
    with app.app_context():
        db.create_all()
        # Create default admin if none exists
        if not User.query.filter_by(role="admin").first():
            admin = User(username="admin", email="admin@agri.bi",
                         role="admin", full_name="System Administrator")
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: username=admin password=admin123")
            print("IMPORTANT: Change the admin password after first login!")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
