"""Seed database with sample data."""
from app import app, db
from models import User, Analysis, CropRequirements
from datetime import datetime, timedelta
import json, random

CROP_DATA = [
    ("Common Bean","Ibishyimbo",80,100,50,40,10,1.5,2500,3,90,"February–May / Sep–Dec"),
    ("Maize","Ibigori",25,200,100,75,25,3.0,1800,5,120,"Sep–Jan / Feb–Jun"),
    ("Cassava","Imanioka",0,80,40,100,100,12.0,800,10,365,"September"),
    ("Arabica Coffee","Ikawa",0,150,60,300,300,1.2,15000,5,365,"Perennial"),
    ("Sweet Potato","Ibijumba",0,80,30,60,30,8.0,1200,8,105,"Feb–May / Sep–Dec"),
    ("Banana","Igitoke",0,120,50,300,300,15.0,1000,20,300,"Perennial"),
    ("Rice","Umuceri",60,120,80,20,20,3.5,2000,2,120,"June–October (Season C)"),
    ("Sorghum","Amasaka",10,80,40,75,15,2.0,1200,3,120,"September–January"),
    ("Wheat","Ingano",120,150,80,20,5,2.5,2000,4,135,"March–July"),
    ("Soybean","Isoya",60,60,0,45,10,2.0,3000,3,90,"February–May"),
    ("Irish Potato","Ikirayi",1500,120,60,75,30,15.0,1000,10,100,"Feb–Jun / Jun–Oct (Season C)"),
]

def seed_crop_requirements():
    with app.app_context():
        added=0
        for c in CROP_DATA:
            if not CropRequirements.query.filter_by(crop_name=c[0]).first():
                db.session.add(CropRequirements(
                    crop_name=c[0],local_name=c[1],seed_rate_kg_ha=c[2],
                    npk_rate_kg_ha=c[3],urea_rate_kg_ha=c[4],row_spacing_cm=c[5],
                    plant_spacing_cm=c[6],yield_ton_ha=c[7],market_price_bif_kg=c[8],
                    planting_depth_cm=c[9],days_to_harvest=c[10],best_season=c[11]))
                added+=1
        db.session.commit()
        print(f"Crop requirements: {added} crops added.")

SAMPLE = [
    ("Common Bean","diseased",42,["Bean Rust","Angular Leaf Spot"],"Gitega","Gitega","B"),
    ("Maize","at_risk",68,["Northern Leaf Blight"],"Kayanza","Kayanza","A"),
    ("Arabica Coffee","healthy",91,[],"Kayanza","Muhanga","A"),
    ("Cassava","diseased",35,["Cassava Mosaic Disease"],"Ngozi","Ngozi","A"),
    ("Common Bean","healthy",88,[],"Gitega","Burguro","B"),
    ("Maize","critical",22,["Gray Leaf Spot","Armyworm"],"Kirundo","Kirundo","A"),
    ("Banana","diseased",48,["Banana Xanthomonas Wilt (BXW)"],"Cibitoke","Cibitoke","A"),
    ("Sweet Potato","at_risk",71,["Sweet Potato Virus Disease"],"Rumonge","Rumonge","B"),
    ("Rice","healthy",85,[],"Bujumbura Rural","Isale","C"),
    ("Arabica Coffee","at_risk",74,["Coffee Leaf Rust"],"Ngozi","Ngozi","A"),
    ("Common Bean","diseased",39,["Bean Mosaic Virus","Root Rot"],"Muyinga","Muyinga","B"),
    ("Maize","healthy",92,[],"Bururi","Bururi","B"),
    ("Irish Potato","healthy",81,[],"Kayanza","Butaganzwa","C"),
]

def seed():
    with app.app_context():
        farmers_data=[
            ("jean_pierre","jean@agri.bi","Jean Pierre Nkurunziza","+25779123456","Gitega","Gitega"),
            ("marie_grace","marie@agri.bi","Marie Grace Niyonzima","+25771234567","Kayanza","Kayanza"),
            ("pierre_noel","pierre@agri.bi","Pierre Noël Hakizimana","+25772345678","Ngozi","Ngozi"),
            ("espoir_farm","espoir@agri.bi","Espoir Ndayishimiye","+25773456789","Bujumbura Rural","Isale"),
            ("alice_keza","alice@agri.bi","Alice Keza","+25774567890","Kirundo","Kirundo"),
        ]
        farmers=[]
        for username,email,full_name,phone,province,commune in farmers_data:
            if not User.query.filter_by(username=username).first():
                u=User(username=username,email=email,role="farmer",full_name=full_name,phone=phone,province=province,commune=commune,language="rn")
                u.set_password("farmer123"); db.session.add(u); farmers.append(u)
        if not User.query.filter_by(username="minagrie").first():
            g=User(username="minagrie",email="gov@agri.bi",role="government",full_name="MINAGRIE Observer",language="fr")
            g.set_password("gov123"); db.session.add(g)
        db.session.commit()
        farmers=User.query.filter_by(role="farmer").all()
        base=datetime.utcnow()
        for i,(crop,status,health,diseases,province,commune,season) in enumerate(SAMPLE):
            farmer=farmers[i%len(farmers)]
            detections=json.dumps([{"name":d,"confidence":round(random.uniform(0.72,0.97),2),"severity":"high" if health<50 else "medium","description":f"{d} detected."} for d in diseases])
            recs=json.dumps(["Apply appropriate fungicide.","Remove infected material.","Improve drainage.","Consult ISABU agronomist."])
            a=Analysis(user_id=farmer.id,filename=f"sample_{i:03d}.jpg",crop_type=crop,growth_stage="Vegetative",
                health_score=health,overall_status=status,summary=f"{crop} — {status}.",
                detections=detections,recommendations=recs,had_error=False,province=province,
                commune=commune,season=season,created_at=base-timedelta(days=random.randint(0,90)))
            db.session.add(a)
        db.session.commit()
        print("Sample data seeded.")
        print("Farmers: jean_pierre, marie_grace, pierre_noel, espoir_farm, alice_keza (password: farmer123)")

        # Seed sample farms and fields so government map has data to show
        from models import Farm, Field
        FARM_SEED = [
            # (username, farm_name, province, commune, fields_data)
            # fields_data: list of (name, crop, season, area_m2, lat, lng) — lat/lng None = no GPS
            ("jean_pierre","Ferme Nkurunziza","Gitega","Gitega",[
                ("Champ Nord","Common Bean","B",4800,-3.415,29.942),
                ("Champ Est","Maize","A",6200,-3.412,29.946),
            ]),
            ("marie_grace","Ferme Niyonzima","Kayanza","Kayanza",[
                ("Parcelle Principale","Arabica Coffee","A",8500,-2.935,29.638),
                ("Bas-fond","Rice","C",3200,-2.940,29.631),
            ]),
            ("pierre_noel","Ferme Hakizimana","Ngozi","Ngozi",[
                ("Grand Champ","Maize","B",9100,-2.918,29.825),
                ("Petit Champ","Common Bean","B",2400,None,None),  # manual entry, no GPS
            ]),
            ("espoir_farm","Ferme Ndayishimiye","Bujumbura Rural","Isale",[
                ("Marais Isale","Rice","C",5500,-3.395,29.318),
            ]),
            ("alice_keza","Ferme Keza","Kirundo","Kirundo",[
                ("Champ Famille","Common Bean","A",3800,-2.582,30.088),
                ("Champ Maïs","Maize","A",4200,-2.578,30.093),
                ("Tubercules","Sweet Potato","B",2100,None,None),
            ]),
        ]
        for username, farm_name, province, commune, fields_data in FARM_SEED:
            farmer = User.query.filter_by(username=username).first()
            if not farmer: continue
            if Farm.query.filter_by(user_id=farmer.id, name=farm_name).first(): continue
            farm = Farm(user_id=farmer.id, name=farm_name, province=province, commune=commune)
            db.session.add(farm)
            db.session.commit()
            for fname, crop, season, area_m2, lat, lng in fields_data:
                field = Field(
                    farm_id=farm.id, name=fname, crop=crop, season=season,
                    location_method='draw' if lat else 'manual',
                    area_m2=area_m2, area_ha=round(area_m2/10000,4),
                    center_lat=lat, center_lng=lng,
                    seed_required=round(area_m2/10000*80,1),
                    expected_yield=round(area_m2/10000*1.5,2),
                )
                db.session.add(field)
            db.session.commit()
        print("Sample farms and fields seeded — government map now has data.")
        print("Government: minagrie / gov123")

if __name__=="__main__":
    seed(); seed_crop_requirements()
