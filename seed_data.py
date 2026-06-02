"""
seed_data.py — Seed the database with realistic sample data for dashboard demo.
Run once: python seed_data.py
"""

from app import app, create_tables
from models import db, User, Analysis
from datetime import datetime, timedelta
import json, random

SAMPLE_ANALYSES = [
    # (crop, status, health, diseases, province, commune, season)
    ("Common Bean", "diseased",  42, ["Bean Rust", "Angular Leaf Spot"], "Gitega",   "Gitega",    "B"),
    ("Maize",       "at_risk",   68, ["Northern Leaf Blight"],           "Kayanza",  "Kayanza",   "A"),
    ("Arabica Coffee","healthy", 91, [],                                  "Kayanza",  "Muhanga",   "A"),
    ("Cassava",     "diseased",  35, ["Cassava Mosaic Disease"],         "Ngozi",    "Ngozi",     "A"),
    ("Common Bean", "healthy",   88, [],                                  "Gitega",   "Burguro",   "B"),
    ("Maize",       "critical",  22, ["Gray Leaf Spot","Armyworm"],      "Kirundo",  "Kirundo",   "A"),
    ("Banana",      "diseased",  48, ["Banana Xanthomonas Wilt (BXW)"], "Cibitoke",  "Cibitoke",  "A"),
    ("Sweet Potato","at_risk",   71, ["Sweet Potato Virus Disease"],     "Rumonge",  "Rumonge",   "B"),
    ("Rice",        "healthy",   85, [],                                  "Bujumbura Rural","Isale","A"),
    ("Arabica Coffee","at_risk", 74, ["Coffee Leaf Rust"],               "Ngozi",    "Ngozi",     "A"),
    ("Common Bean", "diseased",  39, ["Bean Mosaic Virus","Root Rot"],   "Muyinga",  "Muyinga",   "B"),
    ("Maize",       "healthy",   92, [],                                  "Bururi",   "Bururi",    "B"),
    ("Cassava",     "at_risk",   65, ["Cassava Brown Streak"],           "Ruyigi",   "Ruyigi",    "A"),
    ("Sorghum",     "healthy",   87, [],                                  "Kirundo",  "Vumbi",     "A"),
    ("Common Bean", "diseased",  44, ["Angular Leaf Spot"],              "Karuzi",   "Karuzi",    "B"),
    ("Arabica Coffee","diseased",51, ["Coffee Berry Disease"],           "Muramvya", "Muramvya",  "A"),
    ("Banana",      "healthy",   90, [],                                  "Bubanza",  "Bubanza",   "A"),
    ("Maize",       "at_risk",   66, ["Maize Streak Virus"],             "Cankuzo",  "Cankuzo",   "A"),
    ("Sweet Potato","healthy",   83, [],                                  "Makamba",  "Makamba",   "B"),
    ("Common Bean", "critical",  28, ["Bean Rust","Bean Mosaic Virus","Root Rot"], "Mwaro","Mwaro","B"),
    ("Rice",        "diseased",  55, ["Rice Blast"],                     "Bujumbura Rural","Kabezi","A"),
    ("Arabica Coffee","healthy", 94, [],                                  "Kayanza",  "Butaganzwa", "A"),
    ("Cassava",     "healthy",   89, [],                                  "Rutana",   "Rutana",    "A"),
    ("Maize",       "diseased",  47, ["Northern Leaf Blight","Armyworm"],"Gitega",   "Itaba",     "A"),
    ("Common Bean", "at_risk",   72, ["Bean Rust"],                      "Ngozi",    "Marangara", "B"),
]

def seed():
    create_tables()
    with app.app_context():
        # Create sample farmers
        farmers = []
        farmer_data = [
            ("jean_pierre", "jean@agri.bi",   "Jean Pierre Nkurunziza", "+25779123456", "Gitega",        "Gitega"),
            ("marie_grace", "marie@agri.bi",  "Marie Grace Niyonzima",  "+25771234567", "Kayanza",       "Kayanza"),
            ("pierre_noel", "pierre@agri.bi", "Pierre Noël Hakizimana", "+25772345678", "Ngozi",         "Ngozi"),
            ("espoir_farm", "espoir@agri.bi", "Espoir Ndayishimiye",    "+25773456789", "Bujumbura Rural","Isale"),
            ("alice_keza",  "alice@agri.bi",  "Alice Keza",             "+25774567890", "Kirundo",       "Kirundo"),
        ]
        for username, email, full_name, phone, province, commune in farmer_data:
            if not User.query.filter_by(username=username).first():
                u = User(username=username, email=email, role="farmer",
                         full_name=full_name, phone=phone,
                         province=province, commune=commune)
                u.set_password("farmer123")
                db.session.add(u)
                farmers.append(u)
        db.session.flush()

        # Create government user
        if not User.query.filter_by(username="minagrie").first():
            gov = User(username="minagrie", email="gov@agri.bi",
                       role="government", full_name="MINAGRIE Observer")
            gov.set_password("gov123")
            db.session.add(gov)

        db.session.commit()

        # Reload farmers
        farmers = User.query.filter_by(role="farmer").all()

        # Create analyses spread over the last 90 days
        base_date = datetime.utcnow()
        for i, (crop, status, health, diseases, province, commune, season) in enumerate(SAMPLE_ANALYSES):
            days_ago = random.randint(0, 90)
            created  = base_date - timedelta(days=days_ago)
            farmer   = farmers[i % len(farmers)]

            detections = json.dumps([
                {"name": d, "confidence": round(random.uniform(0.72, 0.97), 2),
                 "severity": "high" if health < 50 else "medium",
                 "description": f"{d} detected on crop leaves."}
                for d in diseases
            ])
            recs = json.dumps([
                "Apply appropriate fungicide or pesticide based on diagnosis.",
                "Remove and destroy infected plant material.",
                "Ensure proper field drainage and air circulation.",
                "Consult local ISABU agronomist for further guidance.",
            ])

            a = Analysis(
                user_id=farmer.id, filename=f"sample_{i:03d}.jpg",
                crop_type=crop, growth_stage="Vegetative",
                health_score=health, overall_status=status,
                summary=f"{crop} analysis completed. Status: {status}.",
                detections=detections, recommendations=recs,
                had_error=False, province=province,
                commune=commune, season=season,
                created_at=created,
            )
            db.session.add(a)

        db.session.commit()
        print("Sample data created successfully.")
        print("Farmer accounts: jean_pierre, marie_grace, pierre_noel, espoir_farm, alice_keza")
        print("Password for all farmers: farmer123")
        print("Government account: minagrie / gov123")

if __name__ == "__main__":
    seed()
