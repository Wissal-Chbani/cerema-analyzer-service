# CEREMA Analyzer Service

Service d'extraction et d'analyse automatique de données maritimes pour les aides à la navigation (balises, phares, bouées, etc.) à partir de documents PDF.

## 🎯 Objectif

Extraire automatiquement les informations structurées des aides à la navigation maritime depuis des documents PDF et les stocker dans MongoDB selon un schéma normalisé.

## 🏗️ Architecture

```
CEREMA-ANALYZER-SERVICE/
├── src/
│   ├── api/              # API REST FastAPI
│   ├── core/             # Moteur d'extraction et utilitaires
│   ├── nlp/              # Pipeline NLP et modèles de données
│   ├── preprocessing/    # OCR et nettoyage de texte
│   ├── rules/            # Règles d'extraction basées sur patterns
│   ├── services/         # Services (MongoDB, etc.)
│   ├── config.py         # Configuration
│   └── main.py           # Point d'entrée
├── requirements.txt      # Dépendances Python
└── README.md
```

## 🚀 Installation

### 1. Prérequis

- Python 3.9+
- MongoDB 4.4+
- pip

### 2. Installation des dépendances

```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Installer le modèle spaCy français
python -m spacy download fr_core_news_lg
```

### 3. Configuration

Créer un fichier `.env` à la racine :

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=cerema_db

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### 4. Lancement

```bash
cd src
python main.py
```

L'API sera accessible sur `http://localhost:8000`
Documentation interactive : `http://localhost:8000/docs`

## 📊 Schéma de données

### Document source (MongoDB)
```json
{
  "_id": ObjectId,
  "nom_fichier": "85_Parc éolien YN_Phase travaux01.pdf",
  "chemin_local": "G:\\...\\85_Parc éolien YN_Phase travaux01.pdf",
  "cree_le": ISODate,
  "mime_type": "application/pdf",
  "taille": 169028,
  "modifie_le": ISODate,
  "ajoute_le": ISODate
}
```

### Aide à la navigation (extrait)
```json
{
  "_id": ObjectId,
  "nom_fichier": "...",
  "n_sysi": "8512345",
  "nom_patrimoine": "Phare du Sud",
  "nom_bapteme": "Phare Sud",
  "position": "48.1234 N, 2.5678 E",
  "nature_support": "Phare",
  "marque": "Latérale tribord",
  "marque_jour": "Rouge/Vert",
  "voyant": true,
  "feu": {
    "couleur": "Blanc",
    "rythme": "Fl",
    "portee_nominale": 10,
    "secteurs": "360°"
  },
  "ais_aton": true,
  "balise_racon": {
    "present": true,
    "lettre_morse": "A"
  },
  "extraction_metadata": {
    "confidence_score": 0.85,
    "extraction_date": ISODate,
    "methods_used": ["rule_based", "nlp"]
  }
}
```

## 🔌 API Endpoints

### Extraction

- `POST /api/v1/extract/single` - Extraire un document
- `POST /api/v1/extract/batch` - Extraire plusieurs documents
- `POST /api/v1/extract/all` - Extraire tous les documents

### Consultation

- `GET /api/v1/aides` - Liste des aides
- `GET /api/v1/aides/{aide_id}` - Détail d'une aide
- `GET /api/v1/aides/sysi/{n_sysi}` - Recherche par numéro SYSSI
- `POST /api/v1/aides/search` - Recherche textuelle

### Statistiques

- `GET /api/v1/statistics` - Statistiques globales
- `GET /api/v1/count` - Comptages

### Exemples de requêtes

```bash
# Extraire un document
curl -X POST "http://localhost:8000/api/v1/extract/single" \
  -H "Content-Type: application/json" \
  -d '{"document_id": "6904fe20692c597d5ab9961b"}'

# Lister les aides
curl "http://localhost:8000/api/v1/aides?limit=10"

# Rechercher une aide
curl -X POST "http://localhost:8000/api/v1/aides/search" \
  -H "Content-Type: application/json" \
  -d '{"search_term": "Phare", "fields": ["nom_patrimoine"]}'

# Statistiques
curl "http://localhost:8000/api/v1/statistics"
```

## 🧠 Méthodes d'extraction

Le système utilise une approche hybride :

1. **Extraction OCR** : PyPDF2 et pdfplumber pour extraire le texte des PDFs
2. **Nettoyage** : Normalisation du texte, termes maritimes
3. **Règles (Regex)** : Patterns pour SYSSI, coordonnées, dates, etc.
4. **NLP (spaCy)** : Extraction d'entités nommées, analyse syntaxique
5. **Fusion** : Combinaison des résultats avec score de confiance

### Vocabulaire maritime reconnu

- **Supports** : Phare, Balise, Bouée, Tourelle, Espar
- **Marques** : Latérale, Cardinale (N/S/E/O), Danger isolé, Eaux saines
- **Feux** : Couleurs (Blanc, Vert, Rouge, Jaune), Rythmes (Fl, Oc, Q, VQ, Iso)
- **Équipements** : AIS AtoN, Racon, Réflecteur radar, Aide sonore

## 🔧 Configuration avancée

### Ajuster les patterns d'extraction

Modifier `src/config.py` :

```python
PATTERNS = {
    "n_sysi": r'\b\d{7,8}\b',
    "position_coords": r'...',
    # ...
}
```

### Ajouter du vocabulaire maritime

```python
NATURES_SUPPORT = [
    "Phare", "Balise", "Bouée",
    # Ajouter vos types ici
]
```

## 📈 Performances

- **Extraction** : ~2-5 secondes par document PDF
- **Confiance moyenne** : 70-85% selon la qualité des documents
- **Batch** : Traitement parallèle possible (future amélioration)

## 🐛 Débogage

```bash
# Mode DEBUG
export LOG_LEVEL=DEBUG
python main.py

# Logs détaillés
tail -f logs/cerema_analyzer.log
```

## 🧪 Tests

```bash
pytest tests/
```

## 📝 Améliorations futures

- [ ] Support OCR pour PDFs scannés (Tesseract)
- [ ] Extraction des tableaux structurés
- [ ] Validation des coordonnées géographiques
- [ ] Export CSV/Excel des données extraites
- [ ] Interface web de visualisation
- [ ] Traitement asynchrone avec Celery
- [ ] Support de formats supplémentaires (DOCX, images)

## 📄 Licence

Projet CEREMA - Usage interne

## 👥 Auteurs

Service Littoral et Maritime - CEREMA

## 🆘 Support

Pour toute question : [votre-email@cerema.fr]