"""
features_routes.py — Planting advice, notifications, and market prices.
"""
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, Notification, MarketPrice, Analysis
from auth import BURUNDI_PROVINCES
from crop_calendar import get_all_crops

features_bp = Blueprint("features", __name__)

CROPS_LIST = [c.name for c in get_all_crops()]

# ── AI Planting Advice ────────────────────────────────────────────────────────

@features_bp.route("/advice", methods=["GET", "POST"])
def planting_advice():
    advice_result = None
    selected_crop     = request.form.get("crop", "")
    selected_province = request.form.get("province", "")
    selected_season   = request.form.get("season", "")

    if request.method == "POST" and selected_crop and selected_province:
        # Get current weather for the province
        from weather import get_weather
        from crop_calendar import get_all_crops as _get_crops, MONTH_NAMES
        from datetime import date

        weather = get_weather(f"{selected_province}, Burundi")
        crop_info = next((c for c in _get_crops() if c.name == selected_crop), None)
        current_month = date.today().month
        month_name = MONTH_NAMES[current_month]

        # Determine current season
        if current_month in (9,10,11,12,1): current_season = "A"
        elif current_month in (2,3,4,5): current_season = "B"
        else: current_season = "C"

        # Build AI prompt
        weather_summary = ""
        if not weather.error:
            weather_summary = (
                f"Current weather in {selected_province}: "
                f"{weather.temperature}°C, humidity {weather.humidity}%, "
                f"rain {weather.precipitation}mm, condition: {weather.condition}. "
                f"3-day forecast rain: {sum(weather.rain_3days):.1f}mm total. "
                f"Disease risk: {weather.farming_risk}."
            )

        crop_summary = ""
        if crop_info:
            events_this_month = [e for e in crop_info.events if e.month == current_month]
            crop_summary = (
                f"Crop: {crop_info.name} ({crop_info.local_name}). "
                f"Ideal seasons: {', '.join(crop_info.seasons)}. "
                f"Ideal temp: {crop_info.ideal_temp}. "
                f"Ideal rainfall: {crop_info.ideal_rain}. "
                f"Days to harvest: {crop_info.duration_days}. "
                f"This month ({month_name}) normal activities: "
                f"{', '.join([e.label+': '+e.note for e in events_this_month]) or 'No specific activity this month'}."
            )

        prompt = f"""You are an expert agronomist for Burundi. A farmer in {selected_province} province 
wants advice about planting {selected_crop} in Season {selected_season or current_season} (current month: {month_name}).

{weather_summary}
{crop_summary}

Provide a detailed, practical planting recommendation in French. Structure your response as:
1. DÉCISION (one of: PLANTEZ MAINTENANT / ATTENDEZ / DÉCONSEILLÉ CE MOIS) with a clear reason
2. TIMING OPTIMAL: Exact best timing for this province
3. PRÉPARATION DU SOL: 3-4 specific soil preparation steps
4. SEMENCES: Recommended seed rate and depth
5. RISQUES ACTUELS: Current disease/weather risks based on conditions above
6. CONSEILS SPÉCIAUX: 2-3 tips specific to {selected_province}

Be specific, practical, and concise. Respond in French."""

        # Call Gemini
        try:
            from analyzer import _get_client, _extract_text
            import google.genai.types as gtypes
            import time

            client = _get_client()
            MODELS = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
            reply = ""
            for i, model in enumerate(MODELS):
                try:
                    resp = client.models.generate_content(
                        model=model,
                        contents=[{"role": "user", "parts": [{"text": prompt}]}],
                        config=gtypes.GenerateContentConfig(
                            max_output_tokens=2048, temperature=0.3)
                    )
                    reply = _extract_text(resp) or ""
                    if reply: break
                except Exception as e:
                    err = str(e)
                    if ("503" in err or "429" in err) and i < len(MODELS)-1:
                        time.sleep(2); continue
                    break

            advice_result = {
                "crop": selected_crop,
                "province": selected_province,
                "season": selected_season or current_season,
                "month": month_name,
                "weather": weather if not weather.error else None,
                "text": reply or "Impossible d'obtenir une réponse de l'IA. Vérifiez votre connexion.",
                "generated_at": datetime.utcnow().strftime("%d %b %Y %H:%M"),
            }
        except Exception as e:
            advice_result = {
                "crop": selected_crop, "province": selected_province,
                "season": selected_season or current_season, "month": month_name,
                "weather": None,
                "text": f"Erreur: {str(e)}",
                "generated_at": datetime.utcnow().strftime("%d %b %Y %H:%M"),
            }

    all_crops = get_all_crops()
    return render_template("features/advice.html",
        crops=all_crops, provinces=BURUNDI_PROVINCES,
        advice=advice_result,
        selected_crop=selected_crop,
        selected_province=selected_province,
        selected_season=selected_season)


# ── Notifications ─────────────────────────────────────────────────────────────

@features_bp.route("/notifications")
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc()).limit(50).all()
    unread = sum(1 for n in notifs if not n.is_read)
    return render_template("features/notifications.html",
        notifications=notifs, unread=unread)


@features_bp.route("/notifications/read/<int:nid>", methods=["POST"])
@login_required
def mark_notification_read(nid):
    n = Notification.query.filter_by(id=nid, user_id=current_user.id).first_or_404()
    n.is_read = True
    db.session.commit()
    if request.is_json:
        return jsonify({"success": True})
    if n.link:
        return redirect(n.link)
    return redirect(url_for("features.notifications"))


@features_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({"is_read": True})
    db.session.commit()
    return redirect(url_for("features.notifications"))


@features_bp.route("/api/notifications/unread")
@login_required
def api_notifications_unread():
    count = Notification.query.filter_by(
        user_id=current_user.id, is_read=False).count()
    return jsonify({"unread": count})


@features_bp.route("/admin/announce", methods=["POST"])
@login_required
def admin_announce():
    """Admin/government posts an announcement to all farmers."""
    if current_user.role not in ("admin", "government"):
        return jsonify({"error": "Access denied"}), 403
    data = request.get_json()
    title = data.get("title", "").strip()
    body  = data.get("body", "").strip()
    link  = data.get("link", "").strip() or None
    if not title:
        return jsonify({"error": "Title required"}), 400
    from notifications import notify_announcement
    count = notify_announcement(title, body, link)
    return jsonify({"success": True, "notified": count})


# ── Market Prices ─────────────────────────────────────────────────────────────

@features_bp.route("/market")
def market():
    province = request.args.get("province", "all")
    crop_filter = request.args.get("crop", "all")

    prices_q = MarketPrice.query
    if province != "all":
        prices_q = prices_q.filter_by(province=province)
    if crop_filter != "all":
        prices_q = prices_q.filter_by(crop_name=crop_filter)

    prices = prices_q.order_by(MarketPrice.created_at.desc()).limit(100).all()

    # Latest price per crop per province (for summary table)
    summary = {}
    all_prices = MarketPrice.query.order_by(MarketPrice.created_at.desc()).all()
    for p in all_prices:
        key = (p.crop_name, p.province)
        if key not in summary:
            summary[key] = p

    # Crops with any price data
    crops_with_prices = list({p.crop_name for p in all_prices})
    crops_with_prices.sort()

    # Price trend for each crop (last 7 days avg)
    trends = {}
    cutoff = datetime.utcnow() - timedelta(days=7)
    for crop in crops_with_prices:
        recent = MarketPrice.query.filter(
            MarketPrice.crop_name == crop,
            MarketPrice.created_at >= cutoff
        ).all()
        if recent:
            trends[crop] = {
                "avg": round(sum(p.price_bif for p in recent) / len(recent), 0),
                "min": min(p.price_bif for p in recent),
                "max": max(p.price_bif for p in recent),
                "count": len(recent),
            }

    can_post = (current_user.is_authenticated and
                (current_user.is_verified_professional or
                 current_user.role in ("admin", "government")))

    return render_template("features/market.html",
        prices=prices, summary=list(summary.values()),
        provinces=BURUNDI_PROVINCES, all_crops=get_all_crops(),
        crops_with_prices=crops_with_prices, trends=trends,
        current_province=province, current_crop=crop_filter,
        can_post=can_post)


@features_bp.route("/market/post", methods=["GET", "POST"])
@login_required
def market_post():
    # Only verified professionals, government, and admin can post prices
    if not (current_user.is_verified_professional or
            current_user.role in ("admin", "government")):
        flash("Seuls les agronomes vérifiés et le gouvernement peuvent publier des prix.", "error")
        return redirect(url_for("features.market"))

    if request.method == "POST":
        crop_name = request.form.get("crop_name", "").strip()
        price_str = request.form.get("price_bif", "").strip()
        province  = request.form.get("province", "").strip()
        market_nm = request.form.get("market", "").strip()
        notes     = request.form.get("notes", "").strip()

        if not crop_name or not price_str or not province:
            flash("Culture, prix et province sont requis.", "error")
        else:
            try:
                price_bif = float(price_str)
                if price_bif <= 0: raise ValueError
            except ValueError:
                flash("Prix invalide.", "error")
                return render_template("features/market_post.html",
                    provinces=BURUNDI_PROVINCES, crops=get_all_crops())

            # Get local name from crop calendar if known
            all_crops = get_all_crops()
            crop_obj = next((c for c in all_crops if c.name == crop_name), None)
            local_name = crop_obj.local_name if crop_obj else ""

            mp = MarketPrice(
                crop_name=crop_name, local_name=local_name,
                price_bif=price_bif, province=province,
                market=market_nm or None, notes=notes or None,
                posted_by=current_user.id
            )
            db.session.add(mp)
            db.session.commit()

            # Notify farmers in that province
            from notifications import notify_market_price
            notify_market_price(crop_name, province, price_bif, current_user.username)

            flash(f"Prix publié: {crop_name} à {price_bif:,.0f} BIF/kg — {province}", "success")
            return redirect(url_for("features.market"))

    return render_template("features/market_post.html",
        provinces=BURUNDI_PROVINCES, crops=get_all_crops())


@features_bp.route("/market/delete/<int:price_id>", methods=["POST"])
@login_required
def market_delete(price_id):
    mp = MarketPrice.query.get_or_404(price_id)
    if mp.posted_by != current_user.id and not current_user.is_admin:
        flash("Accès refusé.", "error")
        return redirect(url_for("features.market"))
    db.session.delete(mp)
    db.session.commit()
    flash("Prix supprimé.", "success")
    return redirect(url_for("features.market"))


@features_bp.route("/api/market/prices")
def api_market_prices():
    """JSON endpoint for chart data."""
    crop = request.args.get("crop", "")
    if not crop:
        return jsonify({"error": "crop required"}), 400
    prices = MarketPrice.query.filter_by(crop_name=crop)\
        .order_by(MarketPrice.created_at.asc()).limit(30).all()
    return jsonify([{
        "date": p.created_at.strftime("%d %b"),
        "price": p.price_bif,
        "province": p.province,
        "market": p.market or "",
    } for p in prices])
