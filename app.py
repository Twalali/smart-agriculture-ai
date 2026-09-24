import os, uuid, json
from datetime import datetime, date, timedelta
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify, session, Response)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Analysis, ChatLog, Farm, Field, CropRequirements
from auth import admin_required, dashboard_required, BURUNDI_PROVINCES
from analyzer import analyse_image, AnalysisResult, Detection
from weather import get_weather, get_weather_by_coords
from crop_calendar import get_all_crops, get_current_month_activities, get_categories, MONTH_NAMES, MONTH_SHORT
from farm_routes import farm_bp
from community_routes import community_bp
from features_routes import features_bp
from translations import t, SUPPORTED_LANGS, DEFAULT_LANG, LANG_NAMES

UPLOAD_FOLDER = os.path.join("static","uploads")
ALLOWED_EXTENSIONS = {"png","jpg","jpeg","webp","bmp","tiff"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY","dev-secret-change-in-production")
app.config["UPLOAD_FOLDER"]              = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"]         = 10*1024*1024
app.config["SQLALCHEMY_DATABASE_URI"]    = "sqlite:///agri.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth_login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "error"
app.register_blueprint(farm_bp)
app.register_blueprint(community_bp)
app.register_blueprint(features_bp)

@login_manager.user_loader
def load_user(uid): return User.query.get(int(uid))

def allowed_file(f): return "." in f and f.rsplit(".",1)[1].lower() in ALLOWED_EXTENSIONS
def unique_filename(f): return f"{uuid.uuid4().hex}.{f.rsplit('.',1)[1].lower()}"

def current_season():
    """
    Burundi has 3 agricultural seasons:
    Season A (Agatasi):       Sep-Nov planting -> Jan-Feb harvest. ~35% of production.
    Season B (main season):   Feb-Mar planting -> Jun-Jul harvest. ~50% of production.
    Season C (dry/irrigated): Jun-Jul planting -> Sep-Oct harvest. ~15%, marshes/valleys.
    """
    m = date.today().month
    if m in (9, 10, 11, 12, 1):
        return "A"
    elif m in (2, 3, 4, 5):
        return "B"
    else:
        return "C"

# ── Language handling ───────────────────────────────────────────────────────
def get_current_lang():
    """Priority: logged-in user's saved preference > session override > default (fr)."""
    if current_user.is_authenticated and current_user.language in SUPPORTED_LANGS:
        return current_user.language
    return session.get("lang", DEFAULT_LANG)

def get_current_theme():
    """Priority: logged-in user > session > default (dark)."""
    if current_user.is_authenticated and current_user.theme in ("dark","light"):
        return current_user.theme
    return session.get("theme", "dark")

@app.context_processor
def inject_translation():
    lang  = get_current_lang()
    theme = get_current_theme()
    return {"t": lambda key: t(key, lang), "current_lang": lang,
            "lang_names": LANG_NAMES, "supported_langs": SUPPORTED_LANGS,
            "current_theme": theme}

@app.route("/set-language/<lang_code>", methods=["POST"])
def set_language(lang_code):
    if lang_code not in SUPPORTED_LANGS:
        return jsonify({"error": "Unsupported language."}), 400
    session["lang"] = lang_code
    if current_user.is_authenticated:
        current_user.language = lang_code
        db.session.commit()
    return jsonify({"success": True, "lang": lang_code})

@app.route("/set-theme/<theme>", methods=["POST"])
def set_theme(theme):
    if theme not in ("dark", "light"):
        return jsonify({"error": "Invalid theme."}), 400
    session["theme"] = theme
    if current_user.is_authenticated:
        current_user.theme = theme
        db.session.commit()
    return jsonify({"success": True, "theme": theme})


def result_to_dict(r):
    return {"health_score":r.health_score,"overall_status":r.overall_status,"crop_type":r.crop_type,
        "growth_stage":r.growth_stage,"detections":[{"name":d.name,"confidence":d.confidence,
        "severity":d.severity,"description":d.description} for d in r.detections],
        "recommendations":r.recommendations,"summary":r.summary,"error":r.error}

def dict_to_result(d):
    return AnalysisResult(health_score=d["health_score"],overall_status=d["overall_status"],
        crop_type=d["crop_type"],growth_stage=d["growth_stage"],
        detections=[Detection(**det) for det in d["detections"]],
        recommendations=d["recommendations"],summary=d["summary"],error=d.get("error"))

# ── Auth ──────────────────────────────────────────────────────────────────────
@app.route("/register", methods=["GET","POST"])
def auth_register():
    if current_user.is_authenticated: return redirect(url_for("index"))
    if request.method == "POST":
        u=request.form.get("username","").strip(); e=request.form.get("email","").strip().lower()
        p=request.form.get("password",""); c=request.form.get("confirm_password","")
        if not all([u,e,p]): flash("Username, email and password required.","error")
        elif p!=c: flash("Passwords do not match.","error")
        elif len(p)<6: flash("Password must be at least 6 characters.","error")
        elif User.query.filter_by(username=u).first(): flash("Username taken.","error")
        elif User.query.filter_by(email=e).first(): flash("Email already registered.","error")
        else:
            user=User(username=u,email=e,role="farmer",
                full_name=request.form.get("full_name","").strip(),
                phone=request.form.get("phone","").strip(),
                province=request.form.get("province","").strip(),
                commune=request.form.get("commune","").strip(),
                language=session.get("lang", DEFAULT_LANG))
            user.set_password(p); db.session.add(user); db.session.commit()
            login_user(user); flash(f"Welcome, {u}!","success")
            return redirect(url_for("index"))
    return render_template("auth/register.html", provinces=BURUNDI_PROVINCES)

@app.route("/login", methods=["GET","POST"])
def auth_login():
    if current_user.is_authenticated: return redirect(url_for("index"))
    if request.method == "POST":
        user=User.query.filter_by(username=request.form.get("username","").strip()).first()
        if not user or not user.check_password(request.form.get("password","")) or not user.is_active:
            flash("Invalid credentials or account deactivated.","error")
        else:
            user.last_login=datetime.utcnow(); db.session.commit()
            login_user(user, remember=bool(request.form.get("remember")))
            flash(f"Welcome back, {user.username}!","success")
            return redirect(request.args.get("next") or url_for("index"))
    return render_template("auth/login.html")

@app.route("/logout")
@login_required
def auth_logout():
    logout_user(); flash("Logged out.","success"); return redirect(url_for("index"))

@app.route("/profile", methods=["GET","POST"])
@login_required
def auth_profile():
    if request.method == "POST":
        current_user.full_name=request.form.get("full_name","").strip()
        current_user.phone=request.form.get("phone","").strip()
        current_user.province=request.form.get("province","").strip()
        current_user.commune=request.form.get("commune","").strip()
        lang_choice = request.form.get("language","")
        if lang_choice in SUPPORTED_LANGS:
            current_user.language = lang_choice
        theme_choice = request.form.get("theme","")
        if theme_choice in ("dark","light"):
            current_user.theme = theme_choice
        np=request.form.get("new_password","")
        if np:
            if len(np)<6: flash("Password min 6 chars.","error"); return render_template("auth/profile.html",provinces=BURUNDI_PROVINCES)
            current_user.set_password(np)
        db.session.commit(); flash("Profile updated.","success")
    return render_template("auth/profile.html", provinces=BURUNDI_PROVINCES)

# ── Main pages ────────────────────────────────────────────────────────────────
@app.route("/landing")
def landing():
    return render_template("landing.html")

@app.route("/")
def index(): return render_template("index.html")

@app.route("/api/weather")
def weather_api():
    loc=request.args.get("location","").strip()
    if not loc: return jsonify({"error":"No location provided."}),400
    d=get_weather(loc)
    if d.error: return jsonify({"error":d.error}),400
    return jsonify({"location":d.location,"country":d.country,"temperature":d.temperature,
        "humidity":d.humidity,"precipitation":d.precipitation,"wind_speed":d.wind_speed,
        "condition":d.condition,"weather_code":d.weather_code,"rain_3days":d.rain_3days,
        "temp_max":d.temp_max,"temp_min":d.temp_min,"farming_risk":d.farming_risk,
        "farming_advice":d.farming_advice})

@app.route("/api/weather/coords")
def weather_coords_api():
    try: lat=float(request.args.get("lat","")); lon=float(request.args.get("lon",""))
    except: return jsonify({"error":"Invalid coordinates."}),400
    d=get_weather_by_coords(lat,lon)
    if d.error: return jsonify({"error":d.error}),400
    return jsonify({"location":d.location,"country":d.country,"temperature":d.temperature,
        "humidity":d.humidity,"precipitation":d.precipitation,"wind_speed":d.wind_speed,
        "condition":d.condition,"weather_code":d.weather_code,"rain_3days":d.rain_3days,
        "temp_max":d.temp_max,"temp_min":d.temp_min,"farming_risk":d.farming_risk,
        "farming_advice":d.farming_advice})

@app.route("/upload/ajax", methods=["POST"])
def upload_ajax():
    if "crop_image" not in request.files: return jsonify({"error":"No file."}),400
    file=request.files["crop_image"]
    if not file.filename or not allowed_file(file.filename): return jsonify({"error":"Invalid file."}),400
    filename=unique_filename(secure_filename(file.filename))
    save_path=os.path.join(app.config["UPLOAD_FOLDER"],filename)
    os.makedirs(app.config["UPLOAD_FOLDER"],exist_ok=True)
    file.save(save_path)
    result=analyse_image(save_path, lang=get_current_lang())
    province=current_user.province if current_user.is_authenticated else None
    commune=current_user.commune if current_user.is_authenticated else None
    rec=Analysis(user_id=current_user.id if current_user.is_authenticated else None,
        filename=filename,crop_type=result.crop_type,growth_stage=result.growth_stage,
        health_score=result.health_score,overall_status=result.overall_status,
        summary=result.summary,
        detections=json.dumps([{"name":d.name,"confidence":d.confidence,"severity":d.severity,"description":d.description} for d in result.detections]),
        recommendations=json.dumps(result.recommendations),had_error=bool(result.error),
        province=province,commune=commune,season=current_season())
    db.session.add(rec); db.session.commit()
    # Check if this province now has rising disease cases → send alerts
    if rec.province and rec.overall_status in ("diseased","critical"):
        try:
            from notifications import check_and_alert_disease_outbreaks
            check_and_alert_disease_outbreaks()
        except Exception:
            pass
    session["last_analysis"]=result_to_dict(result)
    session["last_filename"]=filename; session["last_analysis_id"]=rec.id
    return jsonify({"redirect":url_for("result",filename=filename)})

@app.route("/upload", methods=["POST"])
def upload(): flash("Use the upload form on the home page.","error"); return redirect(url_for("index"))

@app.route("/result/<filename>")
def result(filename):
    safe=secure_filename(filename)
    if not os.path.isfile(os.path.join(app.config["UPLOAD_FOLDER"],safe)):
        flash("Image not found.","error"); return redirect(url_for("index"))
    cached=session.get("last_analysis")
    analysis=dict_to_result(cached) if cached and session.get("last_filename")==safe else analyse_image(os.path.join(app.config["UPLOAD_FOLDER"],safe), lang=get_current_lang())
    return render_template("result.html",image_url=url_for("static",filename=f"uploads/{safe}"),
        filename=safe,analysis=analysis,analysis_id=session.get("last_analysis_id"))

@app.route("/history")
@login_required
def farm_history():
    analyses=Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
    return render_template("history.html",analyses=analyses)

@app.route("/history/<int:analysis_id>")
@login_required
def history_detail(analysis_id):
    record=Analysis.query.get_or_404(analysis_id)
    if record.user_id!=current_user.id and not current_user.is_admin:
        flash("Access denied.","error"); return redirect(url_for("farm_history"))
    chats=ChatLog.query.filter_by(analysis_id=analysis_id).order_by(ChatLog.created_at).all()
    analysis=AnalysisResult(health_score=record.health_score or 0,overall_status=record.overall_status or "unknown",
        crop_type=record.crop_type or "Unknown",growth_stage=record.growth_stage or "Unknown",
        detections=[Detection(**d) for d in record.detections_list],
        recommendations=record.recommendations_list,summary=record.summary or "",
        error=None if not record.had_error else "Previous analysis had an error.")
    return render_template("history_detail.html",record=record,analysis=analysis,
        image_url=url_for("static",filename=f"uploads/{record.filename}"),chats=chats)

@app.route("/history/<int:analysis_id>/delete", methods=["POST"])
@login_required
def history_delete(analysis_id):
    record=Analysis.query.get_or_404(analysis_id)
    if record.user_id!=current_user.id and not current_user.is_admin:
        flash("Access denied.","error"); return redirect(url_for("farm_history"))
    db.session.delete(record); db.session.commit()
    flash("Analysis deleted.","success"); return redirect(url_for("farm_history"))

@app.route("/api/chat", methods=["POST"])
def chat_api():
    data=request.get_json()
    if not data: return jsonify({"error":"No data."}),400
    msg=data.get("message","").strip()
    if not msg: return jsonify({"error":"Empty message."}),400
    context=data.get("context",{}); history=data.get("history",[]); analysis_id=data.get("analysis_id")
    lang = get_current_lang()
    lang_name = {"fr":"French","rn":"Kirundi","en":"English"}.get(lang,"French")
    from analyzer import _get_client
    import google.genai.types as gtypes, time
    det_text=", ".join(context.get("detections",[])) or "none"
    recs_text="\n".join(f"- {r}" for r in context.get("recommendations",[]))
    sys=f"""You are an expert agronomist for Burundi. Crop: {context.get('crop_type','Unknown')},
Stage: {context.get('growth_stage','Unknown')}, Health: {context.get('health_score',0)}/100,
Status: {context.get('overall_status','Unknown')}, Issues: {det_text}.
Recommendations given: {recs_text}
Answer directly and practically. Use simple language. Respond in {lang_name}, regardless of what language the farmer's question is written in, unless they explicitly ask you to switch."""
    if not history:
        contents = [{"role":"user","parts":[{"text":sys+"\n\nFarmer: "+msg}]}]
    else:
        contents = (
            [{"role":"user","parts":[{"text":sys}]},{"role":"model","parts":[{"text":"Ready to help."}]}]
            +[{"role":m["role"],"parts":[{"text":m["content"]}]} for m in history[-8:]]
            +[{"role":"user","parts":[{"text":msg}]}])
    try: client=_get_client()
    except Exception as e: return jsonify({"error":str(e)}),500
    CHAT_MODELS=["gemini-2.5-flash","gemini-2.0-flash","gemini-2.0-flash-lite"]
    reply=""; last_err=""
    for i,model in enumerate(CHAT_MODELS):
        try:
            from analyzer import _extract_text
            resp=client.models.generate_content(model=model,contents=contents,
                config=gtypes.GenerateContentConfig(max_output_tokens=2048,temperature=0.4))
            reply=_extract_text(resp) or ""
            if reply: break
        except Exception as e:
            last_err=str(e)
            if ("503" in last_err or "429" in last_err or "unavailable" in last_err.lower()) and i<len(CHAT_MODELS)-1:
                time.sleep(2); continue
            break
    if not reply: return jsonify({"error":f"AI error: {last_err}"}),500
    if analysis_id:
        try:
            db.session.add(ChatLog(analysis_id=analysis_id,role="user",content=msg))
            db.session.add(ChatLog(analysis_id=analysis_id,role="model",content=reply))
            db.session.commit()
        except: pass
    return jsonify({"reply":reply})

@app.route("/calendar")
def calendar():
    m=date.today().month
    return render_template("calendar.html",crops=get_all_crops(),activities=get_current_month_activities(m),
        categories=get_categories(),current_month=m,month_name=MONTH_NAMES[m],
        month_names=MONTH_NAMES,month_short=MONTH_SHORT)

@app.route("/about")
def about(): return render_template("about.html")

@app.route("/diseases")
def disease_library():
    dm={}
    for crop in get_all_crops():
        for d in crop.disease_risks:
            if d not in dm: dm[d]=[]
            dm[d].append({"name":crop.name,"local_name":crop.local_name,"category":crop.category})
    return render_template("diseases.html",diseases=sorted(dm.items()))

@app.route("/map")
def outbreak_map():
    all_a=Analysis.query.filter_by(had_error=False).all()
    pd={}
    for a in all_a:
        if not a.province: continue
        if a.province not in pd:
            pd[a.province]={"province":a.province,"total":0,"healthy":0,"at_risk":0,"diseased":0,"critical":0,"diseases":{},"crops":{}}
        p=pd[a.province]; p["total"]+=1
        s=a.overall_status or "unknown"
        if s in p: p[s]+=1
        for d in a.detections_list:
            n=d.get("name","Unknown"); p["diseases"][n]=p["diseases"].get(n,0)+1
        if a.crop_type: p["crops"][a.crop_type]=p["crops"].get(a.crop_type,0)+1
    for p in pd.values():
        total=p["total"] or 1
        rs=(p["critical"]*3+p["diseased"]*2+p["at_risk"])/total
        p["risk"]="high" if rs>=2 else "medium" if rs>=0.8 else "low"
        p["top_disease"]=max(p["diseases"],key=p["diseases"].get) if p["diseases"] else None
        p["top_diseases"]=sorted(p["diseases"].items(),key=lambda x:x[1],reverse=True)[:3]
    return render_template("map.html",province_data=list(pd.values()),
        province_json=json.dumps(pd),total_analyses=len(all_a))

@app.route("/gov/farms")
@dashboard_required
def gov_farm_map():
    farms  = Farm.query.order_by(Farm.created_at.desc()).all()
    fields = Field.query.all()

    # Province centroids for fallback markers
    PROVINCE_COORDS = {
        "Bubanza":[-3.083,29.383],"Bujumbura Mairie":[-3.387,29.363],
        "Bujumbura Rural":[-3.4,29.3],"Bururi":[-3.949,29.623],
        "Cankuzo":[-3.221,30.555],"Cibitoke":[-2.889,29.120],
        "Gitega":[-3.427,29.926],"Karuzi":[-3.101,30.163],
        "Kayanza":[-2.930,29.631],"Kirundo":[-2.576,30.094],
        "Makamba":[-4.138,29.804],"Muramvya":[-3.267,29.617],
        "Muyinga":[-2.848,30.336],"Mwaro":[-3.5,29.65],
        "Ngozi":[-2.909,29.830],"Rumonge":[-3.975,29.438],
        "Rutana":[-3.928,29.992],"Ruyigi":[-3.477,30.243],
    }

    import random
    all_features = []

    # 1. Exact GPS pins — fields with real coordinates
    for field in fields:
        if field.center_lat and field.center_lng:
            crops_on_farm = [f.crop for f in field.farm.fields if f.crop]
            all_features.append({
                "type": "Feature",
                "geometry": {"type":"Point","coordinates":[field.center_lng, field.center_lat]},
                "properties": {
                    "kind":       "exact",
                    "field_name": field.name,
                    "farm_name":  field.farm.name,
                    "farmer":     field.farm.owner.username,
                    "full_name":  field.farm.owner.full_name or "",
                    "province":   field.farm.province or "Unknown",
                    "commune":    field.farm.commune or "",
                    "crop":       field.crop or "Non défini",
                    "all_crops":  list(set(crops_on_farm)),
                    "area_ha":    round(field.area_ha or 0, 4),
                    "area_m2":    int(field.area_m2 or 0),
                    "season":     field.season or "",
                    "total_fields": field.farm.total_fields,
                    "total_area_ha": round(field.farm.total_area_ha, 2),
                }
            })

    # 2. Province-level pins — farms with NO gps fields at all
    #    One pin per FARM (not per province) so government sees each farmer individually
    #    Slight random offset so pins don't stack exactly on top of each other
    for farm in farms:
        has_any_gps = any(f.center_lat and f.center_lng for f in farm.fields)
        if has_any_gps:
            continue  # already shown via exact pins
        prov = farm.province or "Unknown"
        coords = PROVINCE_COORDS.get(prov)
        if not coords:
            continue
        # Small random offset (±0.05 degrees ≈ 5km) so pins spread out within province
        random.seed(farm.id)
        lat = coords[0] + (random.random() - 0.5) * 0.10
        lng = coords[1] + (random.random() - 0.5) * 0.10
        crops_on_farm = list(set(f.crop for f in farm.fields if f.crop))
        all_features.append({
            "type": "Feature",
            "geometry": {"type":"Point","coordinates":[lng, lat]},
            "properties": {
                "kind":         "province",
                "farm_name":    farm.name,
                "farmer":       farm.owner.username,
                "full_name":    farm.owner.full_name or "",
                "province":     prov,
                "commune":      farm.commune or "",
                "all_crops":    crops_on_farm,
                "crop":         crops_on_farm[0] if crops_on_farm else "Non défini",
                "total_fields": farm.total_fields,
                "total_area_ha":round(farm.total_area_ha, 2),
                "area_ha":      round(farm.total_area_ha, 2),
            }
        })

    # 3. Farms with NO fields yet — show at province centroid with note
    for farm in farms:
        if farm.total_fields == 0:
            prov = farm.province or "Unknown"
            coords = PROVINCE_COORDS.get(prov)
            if not coords: continue
            random.seed(farm.id + 10000)
            lat = coords[0] + (random.random() - 0.5) * 0.12
            lng = coords[1] + (random.random() - 0.5) * 0.12
            all_features.append({
                "type": "Feature",
                "geometry": {"type":"Point","coordinates":[lng, lat]},
                "properties": {
                    "kind":         "no_fields",
                    "farm_name":    farm.name,
                    "farmer":       farm.owner.username,
                    "full_name":    farm.owner.full_name or "",
                    "province":     prov,
                    "commune":      farm.commune or "",
                    "all_crops":    [],
                    "crop":         "Aucun champ",
                    "total_fields": 0,
                    "total_area_ha":0,
                    "area_ha":      0,
                }
            })

    # Province sidebar summary
    prov_data = {}
    for farm in farms:
        prov = farm.province or "Unknown"
        if prov not in prov_data:
            prov_data[prov] = {"farms":0,"fields":0,"area_ha":0,"crops":set(),"farmers":set(),"gps_fields":0}
        prov_data[prov]["farms"]   += 1
        prov_data[prov]["fields"]  += farm.total_fields
        prov_data[prov]["area_ha"] += farm.total_area_ha
        prov_data[prov]["farmers"].add(farm.owner.username)
        for field in farm.fields:
            if field.crop: prov_data[prov]["crops"].add(field.crop)
            if field.center_lat and field.center_lng: prov_data[prov]["gps_fields"] += 1

    prov_list = []
    for prov, d in sorted(prov_data.items()):
        prov_list.append({
            "province":     prov,
            "farms":        d["farms"],
            "fields":       d["fields"],
            "gps_fields":   d["gps_fields"],
            "no_gps_fields":d["fields"] - d["gps_fields"],
            "area_ha":      round(d["area_ha"], 2),
            "crops":        list(d["crops"]),
            "farmer_count": len(d["farmers"]),
        })

    gps_fields  = sum(1 for f in fields if f.center_lat and f.center_lng)

    return render_template("gov_farm_map.html",
        farms=farms, fields=fields,
        features_json=json.dumps({"type":"FeatureCollection","features":all_features}),
        province_summary=prov_list,
        total_farms=len(farms),
        total_fields=len(fields),
        gps_fields=gps_fields,
        no_gps_fields=len(fields) - gps_fields,
        total_area=round(sum(f.area_ha or 0 for f in fields), 2))

@app.route("/admin")
@dashboard_required
def admin_dashboard():
    now_str=datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
    total_users=User.query.filter_by(role="farmer").count()
    total_analyses=Analysis.query.count()
    recent=Analysis.query.order_by(Analysis.created_at.desc()).limit(20).all()
    all_a=Analysis.query.filter_by(had_error=False).all()
    dc={};pc={};cc={};sc={"healthy":0,"at_risk":0,"diseased":0,"critical":0}
    sa=sb=sc_=0; hs=[]; crit=0
    for a in all_a:
        for d in a.detections_list:
            n=d.get("name","Unknown"); dc[n]=dc.get(n,0)+1
        if a.province: pc[a.province]=pc.get(a.province,0)+1
        if a.crop_type: cc[a.crop_type]=cc.get(a.crop_type,0)+1
        s=a.overall_status or "unknown"
        if s in sc: sc[s]+=1
        if s=="critical": crit+=1
        if a.season=="A": sa+=1
        elif a.season=="B": sb+=1
        elif a.season=="C": sc_+=1
        if a.health_score is not None: hs.append(a.health_score)
    td=sorted(dc.items(),key=lambda x:x[1],reverse=True)[:10]
    tp=sorted(pc.items(),key=lambda x:x[1],reverse=True)
    tc=sorted(cc.items(),key=lambda x:x[1],reverse=True)[:8]
    avg=f"{sum(hs)/len(hs):.0f}/100" if hs else "—"
    today=datetime.utcnow().date()
    dr=[(today-timedelta(days=i)) for i in range(29,-1,-1)]
    dmap={d:0 for d in dr}
    for a in Analysis.query.filter(Analysis.created_at>=datetime.utcnow()-timedelta(days=30)).all():
        d=a.created_at.date()
        if d in dmap: dmap[d]+=1
    return render_template("admin/dashboard.html",now=now_str,total_users=total_users,
        total_analyses=total_analyses,total_diseases=len(dc),total_provinces=len(pc),
        critical_count=crit,avg_health=avg,recent=recent,top_diseases=td,top_provinces=tp,
        top_crops=tc,status_counts=sc,season_a=sa,season_b=sb,season_c=sc_,
        timeline_dates=[d.strftime("%d %b") for d in dr],
        timeline_counts=[dmap[d] for d in dr])

@app.route("/admin/users")
@admin_required
def admin_users():
    return render_template("admin/users.html",users=User.query.order_by(User.created_at.desc()).all())

@app.route("/admin/users/<int:uid>/role", methods=["POST"])
@admin_required
def admin_change_role(uid):
    user=User.query.get_or_404(uid); role=request.form.get("role")
    if role in ("farmer","admin","government"): user.role=role; db.session.commit(); flash(f"{user.username} → {role}.","success")
    return redirect(url_for("admin_users"))

@app.route("/admin/users/<int:uid>/toggle", methods=["POST"])
@admin_required
def admin_toggle_user(uid):
    user=User.query.get_or_404(uid); user.is_active=not user.is_active; db.session.commit()
    flash(f"{user.username} {'activated' if user.is_active else 'deactivated'}.","success")
    return redirect(url_for("admin_users"))

@app.route("/admin/dataset/export")
@admin_required
def admin_export_dataset():
    import csv,io
    analyses=Analysis.query.filter_by(had_error=False).all()
    out=io.StringIO(); w=csv.writer(out)
    w.writerow(["id","date","crop_type","growth_stage","health_score","overall_status","diseases","province","commune","season"])
    for a in analyses:
        w.writerow([a.id,a.created_at.strftime("%Y-%m-%d"),a.crop_type,a.growth_stage,a.health_score,
            a.overall_status,"|".join(d.get("name","") for d in a.detections_list),a.province,a.commune,a.season])
    return Response(out.getvalue(),mimetype="text/csv",
        headers={"Content-Disposition":"attachment; filename=agri_dataset.csv"})

@app.errorhandler(413)
def too_large(e): flash("File too large. Max 10 MB.","error"); return redirect(url_for("index"))

@app.errorhandler(404)
def not_found(e): return render_template("404.html"),404

def create_tables():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(role="admin").first():
            admin=User(username="admin",email="admin@agri.bi",role="admin",full_name="System Administrator",language="fr")
            admin.set_password("admin123"); db.session.add(admin); db.session.commit()
            print("Admin created: admin / admin123 — CHANGE THIS PASSWORD!")
        if not CropRequirements.query.first():
            from seed_data import seed_crop_requirements
            seed_crop_requirements()

if __name__=="__main__":
    create_tables(); app.run(debug=True)
