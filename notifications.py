"""
notifications.py — Helper functions to create and deliver in-app notifications.
"""
from models import db, Notification, User, Analysis


def notify(user_id, type_, title, body=None, link=None):
    """Create a single notification for one user."""
    n = Notification(user_id=user_id, type=type_,
                     title=title, body=body, link=link)
    db.session.add(n)
    db.session.commit()
    return n


def notify_province_disease_alert(province, disease_name, risk_level, analysis_count):
    """Alert all farmers in a province when disease risk rises."""
    farmers = User.query.filter_by(province=province, role="farmer").all()
    for farmer in farmers:
        notify(
            user_id=farmer.id,
            type_="disease_alert",
            title=f"Alerte Maladie — {province}",
            body=f"{disease_name} détecté(e) dans votre province ({analysis_count} cas). Risque: {risk_level.upper()}.",
            link="/map"
        )
    return len(farmers)


def notify_forum_reply(post_author_id, replier_username, post_title, post_id):
    """Notify a post author when someone replies."""
    notify(
        user_id=post_author_id,
        type_="forum_reply",
        title=f"{replier_username} a répondu à votre sujet",
        body=f"Nouveau commentaire sur : « {post_title[:80]} »",
        link=f"/community/forum/{post_id}"
    )


def notify_announcement(title, body, link=None):
    """Send an announcement to ALL farmers."""
    farmers = User.query.filter_by(role="farmer").all()
    for farmer in farmers:
        notify(user_id=farmer.id, type_="announcement",
               title=title, body=body, link=link)
    return len(farmers)


def notify_market_price(crop_name, province, price_bif, poster_username):
    """Notify farmers in a province about a new market price."""
    farmers = User.query.filter_by(province=province, role="farmer").all()
    for farmer in farmers:
        notify(
            user_id=farmer.id,
            type_="market",
            title=f"Nouveau prix — {crop_name}",
            body=f"{crop_name}: {price_bif:,.0f} BIF/kg à {province} (par {poster_username})",
            link="/market"
        )
    return len(farmers)


def check_and_alert_disease_outbreaks():
    """
    Check recent analyses and send alerts if a province has rising disease cases.
    Called after each new analysis is saved.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from models import Analysis

    cutoff = datetime.utcnow() - timedelta(days=7)
    # Find provinces with 3+ diseased/critical analyses in last 7 days
    results = db.session.query(
        Analysis.province,
        Analysis.detections,
        func.count(Analysis.id).label("cnt")
    ).filter(
        Analysis.created_at >= cutoff,
        Analysis.overall_status.in_(["diseased", "critical"]),
        Analysis.province.isnot(None)
    ).group_by(Analysis.province).having(func.count(Analysis.id) >= 3).all()

    for row in results:
        province = row.province
        count = row.cnt
        # Find top disease in this province
        import json
        all_detections = db.session.query(Analysis.detections).filter(
            Analysis.created_at >= cutoff,
            Analysis.province == province,
            Analysis.overall_status.in_(["diseased", "critical"])
        ).all()
        disease_counts = {}
        for (det_json,) in all_detections:
            try:
                dets = json.loads(det_json or "[]")
                for d in dets:
                    n = d.get("name", "Unknown")
                    disease_counts[n] = disease_counts.get(n, 0) + 1
            except Exception:
                pass
        top_disease = max(disease_counts, key=disease_counts.get) if disease_counts else "Maladie inconnue"
        risk = "high" if count >= 5 else "medium"
        notify_province_disease_alert(province, top_disease, risk, count)
