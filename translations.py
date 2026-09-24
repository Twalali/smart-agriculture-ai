"""
translations.py — Simple dictionary-based i18n for Smart Agriculture AI.

Supports: fr (French, default), kir (Kirundi), en (English).
Usage in templates: {{ t('nav.analyze') }}
Usage in Python:    from translations import t; t('nav.analyze', lang)
"""

SUPPORTED_LANGS = ["fr", "kir", "en"]
DEFAULT_LANG = "fr"

LANG_NAMES = {
    "fr": "Français",
    "kir": "Ikirundi",
    "en": "English",
}

# ── Translation strings ──────────────────────────────────────────────────────
# Structure: key -> {"fr": "...", "kir": "...", "en": "..."}
STRINGS = {

    # Navigation
    "nav.analyze":      {"fr": "Analyser", "kir": "Suzuma", "en": "Analyze"},
    "nav.farm_planning": {"fr": "Planification Agricole", "rn": "Igenamigambi ry'Itongo", "en": "Farm Planning"},
    "nav.calendar":     {"fr": "Calendrier", "kir": "Kalendari", "en": "Calendar"},
    "nav.diseases":     {"fr": "Maladies", "kir": "Indwara", "en": "Diseases"},
    "nav.map":          {"fr": "Carte", "kir": "Ikarata", "en": "Map"},
    "nav.about":        {"fr": "À propos", "kir": "Ivyerekeye", "en": "About"},
    "nav.dashboard":    {"fr": "Tableau de bord", "kir": "Ikibaho", "en": "Dashboard"},
    "nav.farm_map":     {"fr": "Carte des Fermes", "kir": "Ikarata y'Amatongo", "en": "Farm Map"},
    "nav.history":      {"fr": "Historique", "kir": "Amateka", "en": "History"},
    "nav.login":        {"fr": "Connexion", "kir": "Injira", "en": "Log In"},
    "nav.register":     {"fr": "S'inscrire", "kir": "Iyandikishe", "en": "Register"},
    "nav.profile":       {"fr": "Profil", "kir": "Umwirondoro", "en": "Profile"},
    "nav.logout":       {"fr": "Déconnexion", "kir": "Sohoka", "en": "Log Out"},
    "nav.beta":         {"fr": "Bêta", "kir": "Beta", "en": "Beta"},

    # Index / upload page
    "index.eyebrow":    {"fr": "Intelligence Agricole de Précision", "kir": "Ubuhinga bwa AI mu Buhinzi", "en": "Precision Farming Intelligence"},
    "index.title1":     {"fr": "Diagnostiquez vos", "kir": "Suzuma ibimera", "en": "Diagnose your"},
    "index.title2":     {"fr": "cultures avec l'IA", "kir": "vyawe ukoresheje AI", "en": "crops with AI"},
    "index.body":       {"fr": "Téléchargez une photo de votre culture et recevez une analyse détaillée de la santé de la plante, la détection de maladies, et des recommandations agronomiques.",
                          "rn": "Shikiriza ifoto y'igiterwa cawe maze uronke isuzuma ryimbitse ry'ubuzima bw'igiterwa, gutahura indwara, n'inama z'ubuhinzi.",
                          "en": "Upload a photograph of your crop and receive a detailed analysis of plant health, disease detection, and agronomic recommendations."},
    "index.upload_title": {"fr": "Soumettre une Image de Culture", "rn": "Shikiriza Ifoto y'Igiterwa", "en": "Submit Crop Image"},
    "index.upload_sub":   {"fr": "Formats acceptés : PNG, JPG, JPEG, WEBP — Max 10 Mo", "rn": "Uburyo bwemewe: PNG, JPG, JPEG, WEBP — Birenze 10 Mo", "en": "Supported: PNG, JPG, JPEG, WEBP — Max 10 MB"},
    "index.drop_label":   {"fr": "Glissez-déposez votre image ici", "rn": "Kurura kandi ushire ifoto hano", "en": "Drag and drop your image here"},
    "index.or":           {"fr": "ou", "kir": "canke", "en": "or"},
    "index.browse":       {"fr": "Choisir un Fichier", "kir": "Rondera Dosiye", "en": "Browse File"},
    "index.analyze_btn":  {"fr": "Analyser la Culture", "kir": "Suzuma Igiterwa", "en": "Analyze Crop"},
    "index.step1_title":  {"fr": "Téléverser", "kir": "Shikiriza", "en": "Upload"},
    "index.step1_body":   {"fr": "Photographiez votre culture sous bon éclairage et téléversez depuis votre appareil.", "rn": "Fata ifoto y'igiterwa cawe mu mucyo mwiza maze ushikirize uvuye ku gikoresho cawe.", "en": "Photograph your crop in good lighting and upload from your device."},
    "index.step2_title":  {"fr": "Traiter", "kir": "Gutunganya", "en": "Process"},
    "index.step2_body":   {"fr": "Le modèle de vision IA analyse l'image pour détecter les maladies et problèmes de santé.", "rn": "Ikoranabuhanga rya AI risuzuma ifoto kugira ngo ritahure indwara n'ingorane z'ubuzima.", "en": "The AI vision model analyses the image for diseases and health issues."},
    "index.step3_title":  {"fr": "Résultats", "kir": "Ibisubizo", "en": "Results"},
    "index.step3_body":   {"fr": "Recevez un rapport complet avec diagnostic, scores de confiance et recommandations.", "rn": "Ronka raporo yuzuye ifise isuzuma, amanota y'ukwizigirwa n'inama.", "en": "Receive a full report with diagnosis, confidence scores, and recommendations."},

    # Weather
    "weather.placeholder": {"fr": "Détection de votre position...", "rn": "Turondera aho uri...", "en": "Detecting your location..."},
    "weather.button":      {"fr": "Obtenir la Météo", "rn": "Ronka Ikirere", "en": "Get Weather"},
    "weather.humidity":    {"fr": "Humidité", "rn": "Ubuhehere", "en": "Humidity"},
    "weather.rain_now":    {"fr": "Pluie actuelle", "rn": "Imvura ubu", "en": "Rain now"},
    "weather.wind":        {"fr": "Vent", "rn": "Umuyaga", "en": "Wind"},
    "weather.forecast":    {"fr": "Prévisions sur 3 Jours", "rn": "Iteganyirizo ry'Iminsi 3", "en": "3-Day Forecast"},
    "weather.disease_risk":{"fr": "Risque de Maladie", "rn": "Ingorane y'Indwara", "en": "Disease Risk"},
    "weather.advice":      {"fr": "Conseils Agricoles Basés sur la Météo Actuelle", "rn": "Inama z'Ubuhinzi Zishingiye ku Kirere", "en": "Farming Advice Based on Current Weather"},

    # Result page
    "result.title":         {"fr": "Rapport d'Analyse de Culture", "rn": "Raporo y'Isuzuma ry'Igiterwa", "en": "Crop Analysis Report"},
    "result.health_score":  {"fr": "Score de Santé Global", "rn": "Amanota y'Ubuzima Bwose", "en": "Overall Health Score"},
    "result.detected":      {"fr": "Problèmes Détectés", "rn": "Ingorane Zitahuwe", "en": "Detected Issues"},
    "result.no_detections": {"fr": "Aucune maladie ou carence détectée.", "rn": "Nta ndwara canke ikibazo catahuwe.", "en": "No diseases or deficiencies detected."},
    "result.recommendations": {"fr": "Recommandations Agronomiques", "rn": "Inama z'Ubuhinzi", "en": "Agronomic Recommendations"},
    "result.print":          {"fr": "Imprimer le Rapport", "rn": "Sohora Raporo", "en": "Print Report"},
    "result.analyze_another":{"fr": "Analyser une Autre Culture", "rn": "Suzuma Ikindi Giterwa", "en": "Analyse Another Crop"},
    "result.ask_ai":          {"fr": "Demander à l'Agronome IA", "rn": "Baza Umuhinga AI", "en": "Ask the AI Agronomist"},

    # Status labels
    "status.healthy":  {"fr": "Saine", "rn": "Mubuzima", "en": "Healthy"},
    "status.at_risk":  {"fr": "À Risque", "rn": "Iri mu Kaga", "en": "At Risk"},
    "status.diseased": {"fr": "Malade", "rn": "Irwaye", "en": "Diseased"},
    "status.critical": {"fr": "Critique", "rn": "Bikomeye", "en": "Critical"},
    "status.unknown":  {"fr": "Inconnu", "rn": "Ntibizwi", "en": "Unknown"},

    # Auth
    "auth.login_title":      {"fr": "Bon retour", "rn": "Murakaza neza", "en": "Welcome back"},
    "auth.login_sub":        {"fr": "Connectez-vous à votre compte", "rn": "Injira muri konti yawe", "en": "Log in to your account"},
    "auth.username":         {"fr": "Nom d'utilisateur", "rn": "Izina ry'ukoresha", "en": "Username"},
    "auth.password":         {"fr": "Mot de passe", "rn": "Ijambo ry'ibanga", "en": "Password"},
    "auth.remember":         {"fr": "Rester connecté", "rn": "Numbure", "en": "Keep me logged in"},
    "auth.login_btn":        {"fr": "Se Connecter", "rn": "Injira", "en": "Log In"},
    "auth.no_account":       {"fr": "Pas de compte ?", "rn": "Ntugira konti?", "en": "No account?"},
    "auth.register_free":    {"fr": "Inscrivez-vous gratuitement", "rn": "Iyandikishe ku buntu", "en": "Register free"},
    "auth.register_title":   {"fr": "Créer votre compte", "rn": "Rema konti yawe", "en": "Create your account"},
    "auth.register_sub":     {"fr": "Gratuit pour tous les agriculteurs du Burundi", "rn": "Ku buntu ku barimyi bose b'Uburundi", "en": "Free for all Burundian farmers"},
    "auth.email":            {"fr": "E-mail", "rn": "Imeyili", "en": "Email"},
    "auth.confirm_password": {"fr": "Confirmer le Mot de Passe", "rn": "Emeza Ijambo ry'Ibanga", "en": "Confirm Password"},
    "auth.profile_optional": {"fr": "Profil Agriculteur (optionnel)", "rn": "Umwirondoro w'Umurimyi (si ngombwa)", "en": "Farmer Profile (optional)"},
    "auth.full_name":        {"fr": "Nom Complet", "rn": "Amazina Yuzuye", "en": "Full Name"},
    "auth.phone":            {"fr": "Téléphone", "rn": "Telefone", "en": "Phone"},
    "auth.province":         {"fr": "Province", "rn": "Intara", "en": "Province"},
    "auth.commune":          {"fr": "Commune", "rn": "Komine", "en": "Commune"},
    "auth.select_province":  {"fr": "Sélectionner la province...", "rn": "Hitamwo intara...", "en": "Select province..."},
    "auth.create_account":   {"fr": "Créer le Compte", "rn": "Rema Konti", "en": "Create Account"},
    "auth.already_registered": {"fr": "Déjà inscrit ?", "rn": "Wamaze kwiyandikisha?", "en": "Already registered?"},
    "auth.my_profile":       {"fr": "Mon Profil", "rn": "Umwirondoro Wanje", "en": "My Profile"},
    "auth.member_since":     {"fr": "Membre depuis", "rn": "Umunyamuryango kuva", "en": "Member since"},
    "auth.change_password":  {"fr": "Changer le Mot de Passe (laisser vide pour garder l'actuel)", "rn": "Hindura Ijambo ry'Ibanga (siga ubusa kugira usigaze irindi)", "en": "Change Password (leave blank to keep current)"},
    "auth.new_password":     {"fr": "Nouveau Mot de Passe", "rn": "Ijambo ry'Ibanga Rishasha", "en": "New Password"},
    "auth.save_changes":     {"fr": "Enregistrer les Modifications", "rn": "Bika Impinduka", "en": "Save Changes"},

    # Farm planning
    "farm.my_farms":        {"fr": "Mes Fermes", "rn": "Amatongo Yanje", "en": "My Farms"},
    "farm.new_farm":         {"fr": "+ Nouvelle Ferme", "rn": "+ Itongo Rishasha", "en": "+ New Farm"},
    "farm.farm_name":        {"fr": "Nom de la Ferme", "rn": "Izina ry'Itongo", "en": "Farm Name"},
    "farm.open_farm":        {"fr": "Ouvrir la Ferme", "rn": "Fungura Itongo", "en": "Open Farm"},
    "farm.total_area":       {"fr": "Superficie totale", "rn": "Ubugari bwose", "en": "Total area"},
    "farm.fields":           {"fr": "Champs", "rn": "Imirima", "en": "Fields"},
    "farm.add_field":        {"fr": "+ Ajouter un Champ sur la Carte", "rn": "+ Ongeraho Umurima ku Ikarata", "en": "+ Add Field on Map"},
    "farm.delete_farm":      {"fr": "Supprimer la Ferme", "rn": "Siba Itongo", "en": "Delete Farm"},
    "farm.no_farms_title":   {"fr": "Pas encore de fermes", "rn": "Nta tongo rirahaba", "en": "No farms yet"},
    "farm.no_farms_body":    {"fr": "Créez votre première ferme pour planifier des champs, calculer les semences et suivre les rendements.",
                               "rn": "Rema itongo ryawe rya mbere kugira ngo ugenamigambi imirima, ubare imbuto, kandi ukurikirane umwimbu.",
                               "en": "Create your first farm to start planning fields, calculating seeds, and tracking yields."},
    "farm.create_first":     {"fr": "Créer Votre Première Ferme", "rn": "Rema Itongo Ryawe rya Mbere", "en": "Create Your First Farm"},

    # Map / drawing tools
    "map.draw_tab":          {"fr": "Dessiner sur la Carte", "rn": "Shushanya ku Ikarata", "en": "Draw on Map"},
    "map.gps_tab":            {"fr": "Marcher Autour (GPS)", "rn": "Gendagenda Hose (GPS)", "en": "Walk Around (GPS)"},
    "map.manual_tab":         {"fr": "Saisir la Taille Manuellement", "rn": "Andika Ingano mu Ntoke", "en": "Enter Size Manually"},
    "map.find_location":     {"fr": "Trouver Ma Position", "rn": "Rondera Aho Ndi", "en": "Find My Location"},
    "map.draw_hint":          {"fr": "Utilisez l'outil polygone ou rectangle en haut à gauche &nbsp;&bull;&nbsp; Appuyez sur Trouver Ma Position pour centrer la carte",
                                "rn": "Koresha igikoresho c'inyuguti canke urukuta mu gice ca hejuru i bumoso &nbsp;&bull;&nbsp; Fyonda Rondera Aho Ndi kugira ngo ikarata yerekane aho uri",
                                "en": "Use the polygon or rectangle tool in the top-left corner &nbsp;&bull;&nbsp; Press Find My Location first to centre the map on you"},
    "map.start_recording":    {"fr": "Démarrer l'Enregistrement", "rn": "Tangura Kwandika", "en": "Start Recording"},
    "map.stop_recording":     {"fr": "Arrêter l'Enregistrement", "rn": "Hagarika Kwandika", "en": "Stop Recording"},
    "map.gps_points":         {"fr": "Points GPS", "rn": "Ahantu GPS", "en": "GPS Points"},
    "map.distance":           {"fr": "Distance", "rn": "Intera", "en": "Distance"},
    "map.field_area":         {"fr": "Superficie du Champ", "rn": "Ubugari bw'Umurima", "en": "Field Area"},
    "map.field_name":         {"fr": "Nom du Champ", "rn": "Izina ry'Umurima", "en": "Field Name"},
    "map.planned_crop":       {"fr": "Culture Prévue", "rn": "Igiterwa Categuwe", "en": "Planned Crop"},
    "map.season":             {"fr": "Saison", "rn": "Ibihe", "en": "Season"},
    "map.notes":              {"fr": "Notes", "rn": "Inyandiko", "en": "Notes"},
    "map.save_field":         {"fr": "Enregistrer le Champ", "rn": "Bika Umurima", "en": "Save Field"},
    "map.save_hint":          {"fr": "Mesurez d'abord votre champ", "rn": "Banza upime umurima wawe", "en": "Measure your field first"},
    "map.length_m":           {"fr": "Longueur (mètres)", "rn": "Uburebure (metero)", "en": "Length (metres)"},
    "map.width_m":            {"fr": "Largeur (mètres)", "rn": "Ubugari (metero)", "en": "Width (metres)"},
    "map.cost_section":       {"fr": "Coûts et Revenus (optionnel)", "rn": "Amafaranga n'Inyungu (si ngombwa)", "en": "Cost & Revenue Inputs (optional)"},
    "map.seed_cost":          {"fr": "Coût des Semences (BIF)", "rn": "Amafaranga y'Imbuto (BIF)", "en": "Seed Cost (BIF)"},
    "map.fertilizer_cost":    {"fr": "Coût des Engrais (BIF)", "rn": "Amafaranga y'Ifumbire (BIF)", "en": "Fertilizer Cost (BIF)"},
    "map.labor_cost":         {"fr": "Coût de la Main-d'Œuvre (BIF)", "rn": "Amafaranga y'Abakozi (BIF)", "en": "Labour Cost (BIF)"},
    "map.other_cost":         {"fr": "Autres Coûts (BIF)", "rn": "Andi Mafaranga (BIF)", "en": "Other Costs (BIF)"},
    "map.sale_price":         {"fr": "Votre Prix de Vente (BIF/kg)", "rn": "Igiciro Wagurisha (BIF/kg)", "en": "Your Sale Price (BIF/kg)"},
    "map.profit_prediction":  {"fr": "Prévision de Profit", "rn": "Iteganyirizo ry'Inyungu", "en": "Profit Prediction"},
    "map.expected_revenue":   {"fr": "Revenu Attendu", "rn": "Amafaranga Ateganijwe", "en": "Expected Revenue"},
    "map.total_costs":        {"fr": "Coûts Totaux", "rn": "Amafaranga Yose", "en": "Total Costs"},
    "map.net_profit":         {"fr": "Bénéfice Net", "rn": "Inyungu Nyezina", "en": "Net Profit"},
    "map.break_even":         {"fr": "Seuil de Rentabilité (kg à vendre)", "rn": "Ingano Ugomba Kugurisha (kg)", "en": "Break-even (kg to sell)"},

    # Seasons
    "season.a":       {"fr": "Saison A — Agatasi (Sep–Jan)", "rn": "Igihembwe A — Agatasi (Nzero–Mukurampera)", "en": "Season A — Agatasi (Sep–Jan)"},
    "season.b":       {"fr": "Saison B — Saison Principale (Fév–Juin)", "rn": "Igihembwe B — Igihembwe Nyamukuru (Ruhuhuma–Ruheshi)", "en": "Season B — Main Season (Feb–Jun)"},
    "season.c":       {"fr": "Saison C — Sèche/Irriguée, marais (Juin–Oct)", "rn": "Igihembwe C — Cumye/Cyatewemwo amazi, mu mariha (Ruheshi–Gitugutu)", "en": "Season C — Dry/Irrigated, marshes (Jun–Oct)"},

    # Admin
    "admin.dashboard_title":  {"fr": "Tableau de Bord Agricole National", "rn": "Ikibaho c'Igihugu c'Ubuhinzi", "en": "National Agriculture Dashboard"},
    "admin.manage_users":     {"fr": "Gérer les Utilisateurs", "rn": "Gucungera Abakoresha", "en": "Manage Users"},
    "admin.export_csv":       {"fr": "Exporter CSV", "rn": "Kura Imibare ya CSV", "en": "Export CSV"},
    "admin.total_analyses":   {"fr": "Analyses Totales", "rn": "Isuzuma Ryose", "en": "Total Analyses"},
    "admin.registered_farmers": {"fr": "Agriculteurs Enregistrés", "rn": "Abarimyi Bayandikishijwe", "en": "Registered Farmers"},
    "admin.recent_analyses":  {"fr": "Analyses Récentes", "rn": "Isuzuma Riheruka", "en": "Recent Analyses"},

    # Footer
    "footer.tagline":   {"fr": "Autonomiser les agriculteurs burundais avec l'IA et des données agricoles de précision.",
                          "rn": "Gushigikira abarimyi b'Uburundi tubakwirikiza ubuhanga bwa AI n'amakuru arambuye y'ubuhinzi.",
                          "en": "Empowering Burundian farmers with AI and precision agricultural data."},
    "footer.platform":  {"fr": "Plateforme", "rn": "Urubuga", "en": "Platform"},
    "footer.crops":     {"fr": "Cultures", "rn": "Ibiterwa", "en": "Crops"},
    "footer.seasons":   {"fr": "Saisons", "rn": "Ibihe", "en": "Seasons"},
}


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    """Translate a key into the given language. Falls back to French, then the raw key."""
    if lang not in SUPPORTED_LANGS:
        lang = DEFAULT_LANG
    entry = STRINGS.get(key)
    if not entry:
        return key  # untranslated key shown as-is, makes missing strings obvious during dev
    return entry.get(lang) or entry.get(DEFAULT_LANG) or key
