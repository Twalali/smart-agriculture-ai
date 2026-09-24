"""Burundi crop calendar data — 3 real agricultural seasons."""
from dataclasses import dataclass

@dataclass
class CropEvent:
    month:int; label:str; note:str

@dataclass
class CropInfo:
    name:str; local_name:str; category:str; seasons:list
    events:list; duration_days:int; ideal_temp:str; ideal_rain:str
    description:str; disease_risks:list; tips:list

CROPS = [
    CropInfo("Common Bean","Ibishyimbo","Legumes",["Season A","Season B"],
        [CropEvent(2,"Planting","Season B — plant after first rains"),CropEvent(3,"Fertilize","Apply phosphorus at flowering"),
         CropEvent(5,"Harvest","Season B harvest"),CropEvent(9,"Planting","Season A planting"),
         CropEvent(10,"Fertilize","Top-dress with urea"),CropEvent(12,"Harvest","Season A harvest")],
        90,"16–24°C","300–500 mm/season","Most important food crop in Burundi.",
        ["Bean Rust","Angular Leaf Spot","Bean Mosaic Virus","Root Rot"],
        ["Rotate with maize every season.","Never plant in waterlogged areas.","Inoculate seeds with Rhizobium."]),
    CropInfo("Maize","Ibigori","Cereals",["Season A","Season B"],
        [CropEvent(2,"Planting","Season B"),CropEvent(3,"Fertilize","NPK at planting"),
         CropEvent(6,"Harvest","Season B"),CropEvent(9,"Planting","Season A"),
         CropEvent(10,"Fertilize","Urea top-dress"),CropEvent(1,"Harvest","Season A")],
        120,"18–27°C","500–800 mm/season","Staple cereal crop.",
        ["Northern Leaf Blight","Gray Leaf Spot","Armyworm"],
        ["Plant at 75cm x 25cm spacing.","Scout weekly for armyworm.","Intercrop with beans."]),
    CropInfo("Cassava","Imanioka","Roots & Tubers",["Season A"],
        [CropEvent(9,"Planting","Plant stem cuttings"),CropEvent(11,"Weed","First weeding"),
         CropEvent(9,"Harvest","9–18 months after planting")],
        365,"20–30°C","600–1200 mm/year","Drought-tolerant staple.",
        ["Cassava Mosaic Disease","Cassava Brown Streak","Cassava Mealybug"],
        ["Use certified mosaic-resistant cuttings.","Ensure drainage.","Harvest as needed."]),
    CropInfo("Arabica Coffee","Ikawa","Cash Crops",["Perennial"],
        [CropEvent(9,"Planting","Plant seedlings"),CropEvent(3,"Flowering","Main flowering"),
         CropEvent(9,"Harvest","Selective red cherry picking"),CropEvent(11,"Harvest","Peak harvest")],
        365,"15–24°C","1200–2000 mm/year","Burundi's most important export crop.",
        ["Coffee Leaf Rust","Coffee Berry Disease","Antestia Bug"],
        ["Pick only fully red cherries.","Shade trees reduce leaf rust.","Wash within 12 hours."]),
    CropInfo("Sweet Potato","Ibijumba","Roots & Tubers",["Season A","Season B"],
        [CropEvent(2,"Planting","Season B"),CropEvent(5,"Harvest","Season B"),
         CropEvent(9,"Planting","Season A"),CropEvent(12,"Harvest","Season A")],
        105,"20–28°C","400–700 mm/season","Fast-growing food security crop.",
        ["Sweet Potato Virus Disease","Weevil"],
        ["Plant orange-flesh varieties for nutrition.","Form ridges before planting."]),
    CropInfo("Banana","Igitoke","Fruits & Perennials",["Perennial"],
        [CropEvent(9,"Planting","Start of main rains"),CropEvent(6,"Sucker","Remove excess suckers"),
         CropEvent(9,"Harvest","9–12 months after planting")],
        300,"20–30°C","1000–2000 mm/year","Important food and income crop.",
        ["Banana Xanthomonas Wilt (BXW)","Fusarium Wilt"],
        ["Uproot BXW-infected plants immediately.","Mulch heavily around base."]),
    CropInfo("Rice","Umuceri","Cereals",["Season C"],
        [CropEvent(6,"Nursery","Prepare nursery beds in marshes/valleys"),CropEvent(7,"Transplant","Transplant at 3–4 weeks"),
         CropEvent(9,"Harvest","When 80% of grains are golden, Sep–Oct")],
        120,"20–35°C","Irrigated marshes and valleys","Grown in lowland marshes during the dry season (Season C), when irrigated water is available.",
        ["Rice Blast","Bacterial Leaf Blight"],
        ["Level the field carefully.","Drain 2 weeks before harvest.","Best suited to managed marshes (marais) and valley bottoms with irrigation."]),
    CropInfo("Sorghum","Amasaka","Cereals",["Season A"],
        [CropEvent(9,"Planting","Season A"),CropEvent(1,"Harvest","When grain hard and dry")],
        120,"25–35°C","300–600 mm/season","Drought-tolerant cereal.",
        ["Sorghum Downy Mildew","Striga"],
        ["Plant in dry zones.","Hand-pull Striga early."]),
    CropInfo("Irish Potato","Ikirayi","Roots & Tubers",["Season B","Season C"],
        [CropEvent(2,"Planting","Season B planting"),CropEvent(6,"Harvest","Season B harvest"),
         CropEvent(6,"Planting","Season C — irrigated valleys/marshes"),CropEvent(9,"Harvest","Season C harvest")],
        100,"15–20°C","600–800 mm or irrigated","Important cash crop grown at altitude and in irrigated valleys during the dry season.",
        ["Late Blight","Bacterial Wilt"],
        ["Use certified disease-free seed tubers.","Rotate fields every season.","Hill soil around stems as they grow."]),
]

MONTH_NAMES=["","January","February","March","April","May","June","July","August","September","October","November","December"]
MONTH_SHORT=["","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

def get_all_crops(): return CROPS
def get_current_month_activities(month):
    acts=[]
    for crop in CROPS:
        for ev in crop.events:
            if ev.month==month:
                acts.append({"crop":crop.name,"local_name":crop.local_name,"category":crop.category,"event":ev.label,"note":ev.note})
    return acts
def get_categories():
    seen=[]
    for c in CROPS:
        if c.category not in seen: seen.append(c.category)
    return seen
