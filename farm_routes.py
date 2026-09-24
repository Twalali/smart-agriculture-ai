"""Farm Planning Blueprint."""
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Farm, Field, CropRequirements
from auth import BURUNDI_PROVINCES

farm_bp = Blueprint("farm", __name__, url_prefix="/farm")

def calculate_field(area_ha, req):
    if not req or area_ha <= 0:
        return None
    row_m = req.row_spacing_cm / 100
    plant_m = req.plant_spacing_cm / 100
    plants_per_ha = int(10000 / (row_m * plant_m)) if row_m > 0 and plant_m > 0 else 0
    yield_tons = round(area_ha * req.yield_ton_ha, 2)
    revenue = round(yield_tons * 1000 * (req.market_price_bif_kg or 0), 0)
    return {
        "seed_kg":        round(area_ha * req.seed_rate_kg_ha, 1),
        "npk_kg":         round(area_ha * req.npk_rate_kg_ha, 1),
        "urea_kg":        round(area_ha * req.urea_rate_kg_ha, 1),
        "yield_tons":     yield_tons,
        "yield_kg":       int(yield_tons * 1000),
        "yield_bags_50kg":int(yield_tons * 1000 / 50),
        "revenue_bif":    int(revenue),
        "total_plants":   int(plants_per_ha * area_ha),
        "plants_per_ha":  plants_per_ha,
        "total_rows":     int((100 / row_m) * area_ha) if row_m > 0 else 0,
        "row_spacing":    req.row_spacing_cm,
        "plant_spacing":  req.plant_spacing_cm,
        "planting_depth": req.planting_depth_cm,
        "days_to_harvest":req.days_to_harvest,
        "best_season":    req.best_season,
        "risk_level":     "low" if area_ha <= 1 else "medium" if area_ha <= 5 else "high",
    }

@farm_bp.route("/")
@login_required
def farm_list():
    farms = Farm.query.filter_by(user_id=current_user.id).order_by(Farm.created_at.desc()).all()
    return render_template("farm/list.html", farms=farms)

@farm_bp.route("/new", methods=["GET","POST"])
@login_required
def farm_new():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        if not name:
            flash("Farm name is required.", "error")
            return render_template("farm/new.html", provinces=BURUNDI_PROVINCES)
        farm = Farm(user_id=current_user.id, name=name,
                    province=request.form.get("province","").strip(),
                    commune=request.form.get("commune","").strip(),
                    description=request.form.get("description","").strip())
        db.session.add(farm); db.session.commit()
        flash(f"Farm '{name}' created.", "success")
        return redirect(url_for("farm.farm_detail", farm_id=farm.id))
    return render_template("farm/new.html", provinces=BURUNDI_PROVINCES)

@farm_bp.route("/<int:farm_id>")
@login_required
def farm_detail(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    if farm.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error"); return redirect(url_for("farm.farm_list"))
    crops = CropRequirements.query.order_by(CropRequirements.crop_name).all()
    return render_template("farm/detail.html", farm=farm, crops=crops)

@farm_bp.route("/<int:farm_id>/delete", methods=["POST"])
@login_required
def farm_delete(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    if farm.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error"); return redirect(url_for("farm.farm_list"))
    name = farm.name; db.session.delete(farm); db.session.commit()
    flash(f"Farm '{name}' deleted.", "success")
    return redirect(url_for("farm.farm_list"))

@farm_bp.route("/<int:farm_id>/field/map")
@login_required
def field_map(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    if farm.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error"); return redirect(url_for("farm.farm_list"))
    crops = CropRequirements.query.order_by(CropRequirements.crop_name).all()
    return render_template("farm/map.html", farm=farm, crops=crops)

@farm_bp.route("/<int:farm_id>/field/save", methods=["POST"])
@login_required
def field_save(farm_id):
    farm = Farm.query.get_or_404(farm_id)
    if farm.user_id != current_user.id:
        return jsonify({"error": "Access denied."}), 403
    data = request.get_json()
    area_m2  = float(data.get("area_m2", 0))
    area_ha  = round(area_m2 / 10000, 4)
    crop     = data.get("crop","").strip()
    req      = CropRequirements.query.filter_by(crop_name=crop).first()
    calc     = calculate_field(area_ha, req)
    field = Field(
        farm_id=farm_id, name=data.get("name","Field").strip() or "Field",
        crop=crop, season=data.get("season",""), location_method=data.get("location_method","draw"),
        length_m=data.get("length_m"), width_m=data.get("width_m"),
        geojson=json.dumps(data.get("geojson")) if data.get("geojson") else None,
        area_m2=area_m2, area_ha=area_ha,
        center_lat=data.get("center_lat"), center_lng=data.get("center_lng"),
        notes=data.get("notes","").strip(),
        seed_required=calc["seed_kg"] if calc else None,
        fertilizer_npk=calc["npk_kg"] if calc else None,
        fertilizer_urea=calc["urea_kg"] if calc else None,
        plant_population=calc["total_plants"] if calc else None,
        expected_yield=calc["yield_tons"] if calc else None,
        expected_revenue=calc["revenue_bif"] if calc else None,
        market_price=req.market_price_bif_kg if req else None,
        risk_level=calc["risk_level"] if calc else None,
    )
    db.session.add(field); db.session.commit()
    return jsonify({"success": True, "field_id": field.id,
                    "redirect": url_for("farm.farm_detail", farm_id=farm_id)})

@farm_bp.route("/field/<int:field_id>")
@login_required
def field_detail(field_id):
    field = Field.query.get_or_404(field_id)
    if field.farm.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error"); return redirect(url_for("farm.farm_list"))
    req  = CropRequirements.query.filter_by(crop_name=field.crop).first()
    calc = calculate_field(field.area_ha or 0, req)
    return render_template("farm/field_detail.html", field=field, farm=field.farm, calc=calc)

@farm_bp.route("/field/<int:field_id>/delete", methods=["POST"])
@login_required
def field_delete(field_id):
    field = Field.query.get_or_404(field_id)
    farm_id = field.farm_id
    if field.farm.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error"); return redirect(url_for("farm.farm_list"))
    db.session.delete(field); db.session.commit()
    flash("Field deleted.", "success")
    return redirect(url_for("farm.farm_detail", farm_id=farm_id))

@farm_bp.route("/api/calculate", methods=["POST"])
@login_required
def api_calculate():
    data    = request.get_json()
    crop    = data.get("crop","")
    area_ha = float(data.get("area_ha", 0))
    seed_cost_bif   = float(data.get("seed_cost_bif", 0))
    fertilizer_cost = float(data.get("fertilizer_cost", 0))
    labor_cost      = float(data.get("labor_cost", 0))
    other_cost      = float(data.get("other_cost", 0))
    sale_price_bif  = float(data.get("sale_price_bif", 0))

    if area_ha <= 0: return jsonify({"error": "Area must be > 0."}), 400

    req = CropRequirements.query.filter_by(crop_name=crop).first()
    if req:
        calc = calculate_field(area_ha, req)
        market_price = req.market_price_bif_kg or 0
    else:
        calc = {
            "seed_kg":0,"npk_kg":0,"urea_kg":0,"yield_tons":0,"yield_kg":0,
            "yield_bags_50kg":0,"revenue_bif":0,"total_plants":0,"plants_per_ha":0,
            "total_rows":0,"row_spacing":0,"plant_spacing":0,"planting_depth":0,
            "days_to_harvest":0,"best_season":"Consult local agronomist","risk_level":"medium",
        }
        market_price = 0

    effective_price  = sale_price_bif if sale_price_bif > 0 else market_price
    yield_kg         = calc["yield_kg"]
    expected_revenue = round(yield_kg * effective_price)
    total_costs      = round(seed_cost_bif + fertilizer_cost + labor_cost + other_cost)
    net_profit       = expected_revenue - total_costs
    profit_margin    = round(net_profit / expected_revenue * 100, 1) if expected_revenue > 0 else 0
    roi              = round(net_profit / total_costs * 100, 1) if total_costs > 0 else 0
    break_even_kg    = round(total_costs / effective_price) if effective_price > 0 else 0

    calc.update({
        "crop":crop,"area_ha":area_ha,"area_m2":round(area_ha*10000),
        "local_name":req.local_name if req else "",
        "market_price":effective_price,"expected_revenue":expected_revenue,
        "total_costs":total_costs,"net_profit":net_profit,
        "profit_margin":profit_margin,"roi":roi,"is_known_crop":req is not None,
        "break_even_kg":break_even_kg,
    })
    return jsonify(calc)

@farm_bp.route("/api/crops")
@login_required
def api_crops():
    crops = CropRequirements.query.order_by(CropRequirements.crop_name).all()
    return jsonify([{"name":c.crop_name,"local_name":c.local_name,"seed_rate":c.seed_rate_kg_ha,
        "npk_rate":c.npk_rate_kg_ha,"urea_rate":c.urea_rate_kg_ha,"row_spacing":c.row_spacing_cm,
        "plant_spacing":c.plant_spacing_cm,"yield_ton_ha":c.yield_ton_ha,
        "market_price":c.market_price_bif_kg,"days_to_harvest":c.days_to_harvest,
        "best_season":c.best_season} for c in crops])
