"""
Configuration du système d'extraction CEREMA
"""
import os
from pathlib import Path

# MongoDB
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ocr_database")
COLLECTION_DOCUMENTS = "fichiers_drive"
COLLECTION_AIDES_NAVIGATION = "aides_navigation"

# Chemins
BASE_DIR = Path(__file__).parent.parent
MODELS_DIR = BASE_DIR / "models"
LOGS_DIR = BASE_DIR / "logs"

# NLP
SPACY_MODEL = "fr_core_news_lg"  # Modèle français de spaCy
MAX_TEXT_LENGTH = 1000000  # Limite de texte pour spaCy

# API
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Extraction
CONFIDENCE_THRESHOLD = 0.6  # Seuil de confiance minimum
TABLE_SIZE_THRESHOLD = 10  # Nombre de lignes pour considérer un tableau comme complexe

# Patterns regex
PATTERNS = {
    "n_sysi": r'\b\d{7,8}\b',
    "esm": r'ESM\s*N°?\s*(\d{7,8})',
    "position_coords": r'\d{1,2}[°\s]*\d{1,2}[,.\s]*\d{0,3}\s*[\'′]?\s*[NS]\s*,?\s*\d{1,3}[°\s]*\d{1,2}[,.\s]*\d{0,3}\s*[\'′]?\s*[EWO]',
    "position_decimal": r'\d{1,2}\.\d{4,}\s*[NS]\s*,?\s*\d{1,3}\.\d{4,}\s*[EWO]',
    "date": r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
    "portee": r'\d+\s*[Mm](?:illes)?',
    "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
}

# Vocabulaire maritime
NATURES_SUPPORT = [
    "Phare", "Feu", "Tourelle", "Balise", "Espar", "Bouée", "Panneau",
    "Bouée conique", "Bouée cylindrique", "Bouée sphérique",
    "Bouée charpente", "Bouée fuseau", "Bouée tronconique",
    "Balise à flotteur immergé", "Balise/espar",
    "Coffre d'amarrage", "Éolienne fixe", "Éolienne flottante",
    "Duc d'albe", "AIS virtuel"
]

MARQUES = [
    "Latérale tribord", "Latérale bâbord", "Latérale babord", "Latéral tribord", "Latéral bâbord", "Latéral babord",
    "Latérale tribord modifiée", "Latérale bâbord modifiée",
    "Cardinale Nord", "Cardinale Est", "Cardinale Sud", "Cardinale Ouest",
    "Danger isolé", "Eaux saines", "Marque spéciale", "Marque d'eaux saines",
    "Feu d'atterrissage", "Feu de jalonnement", "Feu d'alignement",
    "Marque d'alignement", "Feu à secteur"
]

FONCTIONS = [
    "Atterrissage", "Jalonnement", "Chenalage", "Alignement",
    "Secteur", "Danger", "Signalisation"
]

COULEURS_FEU = ["Blanc", "Vert", "Rouge", "Jaune"]
COULEURS_MARQUE = ["Rouge", "Vert", "Blanc", "Jaune", "Noir", "Bleu"]

RYTHMES_FEU = {
    "eclats": ["Fl", "LFl", "Fl(2)", "Fl(3)", "Fl(4)", "Fl(5)", "Fl(6)", "Fl(2+1)"],
    "occultations": ["Oc", "Oc(2)", "Oc(3)", "Oc(4)"],
    "isophase": ["Iso"],
    "scintillant": ["Q", "Q(3)", "Q(6)+LFl", "Q(9)"],
    "scintillant_rapide": ["VQ", "VQ(3)", "VQ(6)+LFl", "VQ(9)"]
}

TYPES_AIDE_SONORE = ["Cloche", "Sifflet", "Sirène", "Vibrateur", "Corne de brume"]

TYPES_VOYANT = ["Cône", "Cylindre", "Sphère", "Croix de Saint-André", "Triangle", "Rectangle"]

# Types de documents
TYPES_DOCUMENTS = [
    "fiche_individuelle",
    "tableau_simple",
    "tableau_complexe",
    "courrier_administratif",
    "catalogue_produit",
    "arrete_prefectoral",
    "autre"
]

# Mots-clés pour détecter les types de documents
KEYWORDS_CATALOGUE = ['prix', 'tarif', 'kg', 'poids', 'volume', 'matériaux', 'EUR', '€']
KEYWORDS_COURRIER = ['monsieur', 'madame', 'objet', 'référence', 'signé', 'affaire suivie']
KEYWORDS_ARRETE = ['arrêté', 'préfet', 'article', 'considérant', 'vu le décret']