"""
community_routes.py — Public forum and direct messaging blueprint.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, User, ForumPost, ForumReply, DirectMessage
from sqlalchemy import or_, and_

community_bp = Blueprint("community", __name__, url_prefix="/community")

FORUM_CATEGORIES = [
    ("general",     "General / Général"),
    ("disease",     "Disease & Pests / Maladies"),
    ("weather",     "Weather & Climate / Météo"),
    ("market",      "Market Prices / Prix du marché"),
    ("seeds",       "Seeds & Varieties / Semences"),
    ("fertilizer",  "Fertilizers / Engrais"),
    ("government",  "Government Programs / Programmes"),
    ("equipment",   "Tools & Equipment / Outils"),
]


# ── Forum ─────────────────────────────────────────────────────────────────────

@community_bp.route("/forum")
def forum():
    cat   = request.args.get("cat", "all")
    q     = request.args.get("q", "").strip()
    page  = int(request.args.get("page", 1))
    per_page = 20

    posts_q = ForumPost.query
    if cat != "all":
        posts_q = posts_q.filter_by(category=cat)
    if q:
        posts_q = posts_q.filter(
            or_(ForumPost.title.ilike(f"%{q}%"), ForumPost.body.ilike(f"%{q}%"))
        )
    posts_q = posts_q.order_by(ForumPost.is_pinned.desc(), ForumPost.updated_at.desc())
    total   = posts_q.count()
    posts   = posts_q.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = (total + per_page - 1) // per_page

    # Stats for sidebar
    total_posts   = ForumPost.query.count()
    total_replies = ForumReply.query.count()
    professionals = User.query.filter_by(is_verified_professional=True).all()

    return render_template("community/forum.html",
        posts=posts, categories=FORUM_CATEGORIES, current_cat=cat,
        q=q, page=page, total_pages=total_pages, total=total,
        total_posts=total_posts, total_replies=total_replies,
        professionals=professionals)


@community_bp.route("/forum/new", methods=["GET", "POST"])
@login_required
def forum_new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body  = request.form.get("body", "").strip()
        cat   = request.form.get("category", "general")
        crop  = request.form.get("crop_tag", "").strip()
        if not title or not body:
            flash("Title and message are required.", "error")
        else:
            post = ForumPost(user_id=current_user.id, title=title, body=body,
                             category=cat, crop_tag=crop or None)
            db.session.add(post)
            db.session.commit()
            flash("Post published.", "success")
            return redirect(url_for("community.forum_post", post_id=post.id))
    return render_template("community/forum_new.html", categories=FORUM_CATEGORIES)


@community_bp.route("/forum/<int:post_id>", methods=["GET", "POST"])
def forum_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Log in to reply.", "error")
            return redirect(url_for("auth_login"))
        body = request.form.get("body", "").strip()
        if not body:
            flash("Reply cannot be empty.", "error")
        else:
            reply = ForumReply(post_id=post_id, user_id=current_user.id, body=body)
            db.session.add(reply)
            from datetime import datetime
            post.updated_at = datetime.utcnow()
            db.session.commit()
            # Notify post author (if not replying to own post)
            if post.user_id != current_user.id:
                try:
                    from notifications import notify_forum_reply
                    notify_forum_reply(post.user_id, current_user.username,
                                       post.title, post_id)
                except Exception:
                    pass
            flash("Reply posted.", "success")
        return redirect(url_for("community.forum_post", post_id=post_id))
    return render_template("community/forum_post.html", post=post)


@community_bp.route("/forum/<int:post_id>/delete", methods=["POST"])
@login_required
def forum_delete(post_id):
    post = ForumPost.query.get_or_404(post_id)
    if post.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error")
        return redirect(url_for("community.forum"))
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted.", "success")
    return redirect(url_for("community.forum"))


@community_bp.route("/forum/reply/<int:reply_id>/solution", methods=["POST"])
@login_required
def mark_solution(reply_id):
    reply = ForumReply.query.get_or_404(reply_id)
    if reply.post.user_id != current_user.id and not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    reply.is_solution = not reply.is_solution
    db.session.commit()
    return jsonify({"is_solution": reply.is_solution})


@community_bp.route("/forum/reply/<int:reply_id>/delete", methods=["POST"])
@login_required
def reply_delete(reply_id):
    reply = ForumReply.query.get_or_404(reply_id)
    post_id = reply.post_id
    if reply.user_id != current_user.id and not current_user.is_admin:
        flash("Access denied.", "error")
    else:
        db.session.delete(reply)
        db.session.commit()
        flash("Reply deleted.", "success")
    return redirect(url_for("community.forum_post", post_id=post_id))


# ── Direct Messages ──────────────────────────────────────────────────────────

@community_bp.route("/messages")
@login_required
def inbox():
    """Show all conversations for the current user."""
    # Get all users this person has exchanged messages with
    sent_to   = db.session.query(DirectMessage.receiver_id).filter_by(sender_id=current_user.id)
    recv_from = db.session.query(DirectMessage.sender_id).filter_by(receiver_id=current_user.id)
    partner_ids = {r[0] for r in sent_to} | {r[0] for r in recv_from}

    conversations = []
    for uid in partner_ids:
        partner = User.query.get(uid)
        if not partner: continue
        last_msg = DirectMessage.query.filter(
            or_(
                and_(DirectMessage.sender_id==current_user.id, DirectMessage.receiver_id==uid),
                and_(DirectMessage.sender_id==uid, DirectMessage.receiver_id==current_user.id)
            )
        ).order_by(DirectMessage.created_at.desc()).first()
        unread = DirectMessage.query.filter_by(
            sender_id=uid, receiver_id=current_user.id, is_read=False
        ).count()
        conversations.append({
            "partner": partner,
            "last_msg": last_msg,
            "unread": unread,
        })
    conversations.sort(key=lambda x: x["last_msg"].created_at, reverse=True)

    # Professionals available to message
    professionals = User.query.filter(
        or_(User.is_verified_professional==True, User.role.in_(["admin","government"]))
    ).filter(User.id != current_user.id).all()

    total_unread = DirectMessage.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).count()

    return render_template("community/inbox.html",
        conversations=conversations, professionals=professionals,
        total_unread=total_unread)


@community_bp.route("/messages/<int:partner_id>", methods=["GET", "POST"])
@login_required
def conversation(partner_id):
    partner = User.query.get_or_404(partner_id)

    # Enforce: farmers can only DM verified professionals or government/admin
    # Professionals and admins can DM anyone
    if current_user.role == "farmer":
        can_dm = (partner.is_verified_professional or
                  partner.role in ("admin", "government"))
        if not can_dm:
            flash("You can only send direct messages to verified agronomists or government officials.", "error")
            return redirect(url_for("community.inbox"))

    if request.method == "POST":
        body = request.form.get("body", "").strip()
        if not body:
            flash("Message cannot be empty.", "error")
        else:
            msg = DirectMessage(sender_id=current_user.id,
                                receiver_id=partner_id, body=body)
            db.session.add(msg)
            db.session.commit()
        return redirect(url_for("community.conversation", partner_id=partner_id))

    # Load full conversation and mark as read
    messages = DirectMessage.query.filter(
        or_(
            and_(DirectMessage.sender_id==current_user.id, DirectMessage.receiver_id==partner_id),
            and_(DirectMessage.sender_id==partner_id, DirectMessage.receiver_id==current_user.id)
        )
    ).order_by(DirectMessage.created_at.asc()).all()

    # Mark incoming messages as read
    DirectMessage.query.filter_by(
        sender_id=partner_id, receiver_id=current_user.id, is_read=False
    ).update({"is_read": True})
    db.session.commit()

    return render_template("community/conversation.html",
        partner=partner, messages=messages)


@community_bp.route("/messages/new/<int:partner_id>")
@login_required
def new_conversation(partner_id):
    """Redirect straight to conversation thread (creates it implicitly)."""
    return redirect(url_for("community.conversation", partner_id=partner_id))


# ── Admin: toggle verified professional ──────────────────────────────────────

@community_bp.route("/admin/verify/<int:uid>", methods=["POST"])
@login_required
def toggle_verified(uid):
    if not current_user.is_admin:
        return jsonify({"error": "Admin only"}), 403
    user = User.query.get_or_404(uid)
    user.is_verified_professional = not user.is_verified_professional
    db.session.commit()
    return jsonify({"verified": user.is_verified_professional, "username": user.username})


# ── API: unread count (for nav badge) ────────────────────────────────────────

@community_bp.route("/api/unread")
@login_required
def api_unread():
    count = DirectMessage.query.filter_by(
        receiver_id=current_user.id, is_read=False
    ).count()
    return jsonify({"unread": count})
