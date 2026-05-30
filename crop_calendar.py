"""
crop_calendar.py — Burundi crop planting and harvest calendar.

Covers the two main growing seasons:
  Season A: September – January  (long rains)
  Season B: February – June      (short rains)

Data sourced from ISABU (Institut des Sciences Agronomiques du Burundi)
and FAO Burundi agricultural reports.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class CropEvent:
    month: int          # 1-12
    label: str          # "Planting", "Harvest", "Fertilize", etc.
    note:  str          # short description


@dataclass
class CropInfo:
    name:         str
    local_name:   str          # Kirundi name
    category:     str          # "Cereals", "Legumes", "Roots", etc.
    seasons:      list[str]    # ["Season A", "Season B"]
    events:       list[CropEvent]
    duration_days: int         # days from planting to harvest
    ideal_temp:   str          # temperature range
    ideal_rain:   str          # mm range
    description:  str
    disease_risks: list[str]   # common diseases to watch
    tips:         list[str]    # 2-3 key farming tips


# ---------------------------------------------------------------------------
# Calendar data — Burundi
# ---------------------------------------------------------------------------

CROPS: list[CropInfo] = [

    CropInfo(
        name="Common Bean",
        local_name="Ibishyimbo",
        category="Legumes",
        seasons=["Season A", "Season B"],
        events=[
            CropEvent(2,  "Planting",    "Season B — plant after first rains"),
            CropEvent(3,  "Fertilize",   "Apply phosphorus fertilizer at flowering"),
            CropEvent(5,  "Harvest",     "Season B — harvest when pods dry"),
            CropEvent(9,  "Planting",    "Season A — main season planting"),
            CropEvent(10, "Fertilize",   "Top-dress with urea at flowering stage"),
            CropEvent(12, "Harvest",     "Season A — harvest before heavy rains"),
        ],
        duration_days=90,
        ideal_temp="16–24°C",
        ideal_rain="300–500 mm/season",
        description="Most important food crop in Burundi. High protein, grows in most provinces.",
        disease_risks=["Bean Rust", "Angular Leaf Spot", "Bean Mosaic Virus", "Root Rot"],
        tips=[
            "Rotate with maize every season to reduce soil-borne disease.",
            "Never plant beans in waterlogged areas — root rot kills quickly.",
            "Inoculate seeds with Rhizobium before planting to fix nitrogen.",
        ],
    ),

    CropInfo(
        name="Maize",
        local_name="Ibigori",
        category="Cereals",
        seasons=["Season A", "Season B"],
        events=[
            CropEvent(2,  "Planting",    "Season B — plant with first rains"),
            CropEvent(3,  "Fertilize",   "Apply NPK at planting, urea at knee height"),
            CropEvent(6,  "Harvest",     "Season B — harvest when husks are dry"),
            CropEvent(9,  "Planting",    "Season A — main season"),
            CropEvent(10, "Fertilize",   "Top-dress with urea 4–6 weeks after emergence"),
            CropEvent(1,  "Harvest",     "Season A — harvest December–January"),
        ],
        duration_days=120,
        ideal_temp="18–27°C",
        ideal_rain="500–800 mm/season",
        description="Staple cereal crop. Critical for food security in all 18 provinces.",
        disease_risks=["Northern Leaf Blight", "Gray Leaf Spot", "Maize Streak Virus", "Armyworm"],
        tips=[
            "Plant at 75cm x 25cm spacing for optimal yields.",
            "Scout weekly for fall armyworm — early detection saves the crop.",
            "Intercrop with beans to maximize land use and fix nitrogen.",
        ],
    ),

    CropInfo(
        name="Cassava",
        local_name="Imanioka",
        category="Roots & Tubers",
        seasons=["Season A"],
        events=[
            CropEvent(9,  "Planting",    "Plant stem cuttings at start of rains"),
            CropEvent(11, "Weed",        "First weeding — critical period"),
            CropEvent(2,  "Weed",        "Second weeding if needed"),
            CropEvent(9,  "Harvest",     "Harvest 9–18 months after planting"),
        ],
        duration_days=365,
        ideal_temp="20–30°C",
        ideal_rain="600–1200 mm/year",
        description="Drought-tolerant staple. Key food security crop in dry zones of Burundi.",
        disease_risks=["Cassava Mosaic Disease", "Cassava Brown Streak", "Cassava Mealybug"],
        tips=[
            "Only use certified mosaic-resistant cuttings from ISABU.",
            "Cassava tolerates drought but not waterlogging — ensure drainage.",
            "Leave in ground as natural storage — harvest as needed.",
        ],
    ),

    CropInfo(
        name="Arabica Coffee",
        local_name="Ikawa",
        category="Cash Crops",
        seasons=["Perennial"],
        events=[
            CropEvent(9,  "Planting",    "Plant seedlings at start of rains"),
            CropEvent(3,  "Flowering",   "Main flowering period — critical for yield"),
            CropEvent(4,  "Fertilize",   "Apply coffee-specific NPK after flowering"),
            CropEvent(6,  "Prune",       "Light pruning after harvest"),
            CropEvent(9,  "Harvest",     "Selective red cherry picking begins"),
            CropEvent(11, "Harvest",     "Peak harvest — pick only red cherries"),
            CropEvent(12, "Harvest",     "Late harvest and field cleanup"),
        ],
        duration_days=365,
        ideal_temp="15–24°C",
        ideal_rain="1200–2000 mm/year",
        description="Burundi's most important export crop. Grown in Kayanza, Ngozi, Gitega highlands.",
        disease_risks=["Coffee Leaf Rust", "Coffee Berry Disease", "Antestia Bug"],
        tips=[
            "Pick only fully red cherries — unripe cherries destroy cup quality and price.",
            "Shade trees reduce leaf rust risk and improve bean quality.",
            "Wash and ferment within 12 hours of picking for specialty grade.",
        ],
    ),

    CropInfo(
        name="Sweet Potato",
        local_name="Ibijumba",
        category="Roots & Tubers",
        seasons=["Season A", "Season B"],
        events=[
            CropEvent(2,  "Planting",    "Season B — plant vine cuttings"),
            CropEvent(5,  "Harvest",     "Season B — harvest 3–4 months after planting"),
            CropEvent(9,  "Planting",    "Season A — main season"),
            CropEvent(12, "Harvest",     "Season A harvest"),
        ],
        duration_days=105,
        ideal_temp="20–28°C",
        ideal_rain="400–700 mm/season",
        description="Fast-growing food security crop. Orange-flesh varieties rich in Vitamin A.",
        disease_risks=["Sweet Potato Virus Disease", "Weevil", "Alternaria Leaf Spot"],
        tips=[
            "Plant orange-flesh varieties for improved nutrition — VITA variety recommended.",
            "Form ridges or mounds before planting for good tuber development.",
            "Harvest before heavy rains to prevent tuber rot.",
        ],
    ),

    CropInfo(
        name="Banana",
        local_name="Igitoke",
        category="Fruits & Perennials",
        seasons=["Perennial"],
        events=[
            CropEvent(9,  "Planting",    "Best planted at start of main rains"),
            CropEvent(3,  "Fertilize",   "Apply organic matter and potassium"),
            CropEvent(6,  "Sucker",      "Remove excess suckers — keep 1–2 per stool"),
            CropEvent(9,  "Harvest",     "Harvest 9–12 months after planting"),
            CropEvent(12, "Harvest",     "Peak harvest period"),
        ],
        duration_days=300,
        ideal_temp="20–30°C",
        ideal_rain="1000–2000 mm/year",
        description="Important food and income crop. Also brewed into urwagwa (local banana beer).",
        disease_risks=["Banana Xanthomonas Wilt (BXW)", "Fusarium Wilt", "Banana Weevil"],
        tips=[
            "BXW is devastating — uproot and burn infected plants immediately.",
            "Mulch heavily around base to retain moisture and prevent weevil.",
            "Never use same cutting tools between plants without disinfecting.",
        ],
    ),

    CropInfo(
        name="Rice",
        local_name="Umuceri",
        category="Cereals",
        seasons=["Season A"],
        events=[
            CropEvent(9,  "Nursery",     "Prepare nursery beds at start of rains"),
            CropEvent(10, "Transplant",  "Transplant seedlings to paddy at 3–4 weeks"),
            CropEvent(11, "Fertilize",   "Apply nitrogen fertilizer at tillering"),
            CropEvent(1,  "Harvest",     "Harvest when 80% of grains are golden"),
        ],
        duration_days=120,
        ideal_temp="20–35°C",
        ideal_rain="Irrigated or wetland",
        description="Grown in lowland marshes (marais). Imbo plain and Ruzizi valley are main zones.",
        disease_risks=["Rice Blast", "Bacterial Leaf Blight", "Brown Planthopper"],
        tips=[
            "Level the field carefully — uneven paddies waste water and reduce yield.",
            "Drain field 2 weeks before harvest for easier cutting and better grain quality.",
            "Use certified seed from ISABU for blast-resistant varieties.",
        ],
    ),

    CropInfo(
        name="Sorghum",
        local_name="Amasaka",
        category="Cereals",
        seasons=["Season A"],
        events=[
            CropEvent(9,  "Planting",    "Plant at start of Season A rains"),
            CropEvent(10, "Thin",        "Thin to 2 plants per hole at 3 weeks"),
            CropEvent(11, "Fertilize",   "Top-dress with urea"),
            CropEvent(1,  "Harvest",     "Harvest when grain hard and dry"),
        ],
        duration_days=120,
        ideal_temp="25–35°C",
        ideal_rain="300–600 mm/season",
        description="Drought-tolerant cereal for dry zones. Used for food and local beer (impeke).",
        disease_risks=["Sorghum Downy Mildew", "Striga (witch weed)", "Grain Mold"],
        tips=[
            "Plant in dry zones where maize struggles — sorghum thrives in heat.",
            "Hand-pull Striga early before it sets seed — one plant = 50,000 seeds.",
            "Bird scaring is essential during grain filling stage.",
        ],
    ),
]

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_SHORT = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
]


def get_all_crops() -> list[CropInfo]:
    return CROPS


def get_crop_by_name(name: str) -> CropInfo | None:
    name_lower = name.lower()
    for crop in CROPS:
        if (crop.name.lower() == name_lower
                or crop.local_name.lower() == name_lower):
            return crop
    return None


def get_crops_by_category(category: str) -> list[CropInfo]:
    return [c for c in CROPS if c.category == category]


def get_current_month_activities(month: int) -> list[dict]:
    """Return all planting/harvest events happening in a given month."""
    activities = []
    for crop in CROPS:
        for event in crop.events:
            if event.month == month:
                activities.append({
                    "crop":       crop.name,
                    "local_name": crop.local_name,
                    "category":   crop.category,
                    "event":      event.label,
                    "note":       event.note,
                })
    return activities


def get_categories() -> list[str]:
    seen = []
    for c in CROPS:
        if c.category not in seen:
            seen.append(c.category)
    return seen
