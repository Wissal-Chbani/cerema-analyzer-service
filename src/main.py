"""
Application principale CEREMA Analyzer Service
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from config import API_HOST, API_PORT, LOG_LEVEL
from core.utils import setup_logging
from api.routes import router

# Configuration du logging
setup_logging(log_level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# Création de l'application FastAPI
app = FastAPI(
    title="CEREMA Analyzer Service",
    description="""
    Service d'extraction et d'analyse de données maritimes pour les aides à la navigation.
    
    ## Fonctionnalités
    
    * **Extraction automatique** : Extrait les informations des fichiers TXT
    * **Détection intelligente** : Adapte la stratégie selon le type de document
    * **Stockage MongoDB** : Sauvegarde structurée des données
    * **API REST** : Consultation et recherche des données extraites
    
    ## Types de documents supportés
    
    * Fiches individuelles (extraction complète)
    * Tableaux simples (extraction complète)
    * Tableaux complexes (extraction partielle + lien vers original)
    * Arrêtés préfectoraux (extraction partielle)
    * Courriers administratifs (métadonnées)
    * Catalogues produits (ignorés)
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routes
app.include_router(router, prefix="/api/v1", tags=["CEREMA Extraction"])


@app.on_event("startup")
async def startup_event():
    """Actions au démarrage de l'application"""
    logger.info("=" * 70)
    logger.info("🚢 CEREMA Analyzer Service - Démarrage")
    logger.info("=" * 70)
    logger.info(f"🌐 API accessible sur: http://{API_HOST}:{API_PORT}")
    logger.info(f"📚 Documentation: http://{API_HOST}:{API_PORT}/docs")
    logger.info(f"📊 Statistiques: http://{API_HOST}:{API_PORT}/api/v1/statistics")
    logger.info("=" * 70)


@app.on_event("shutdown")
async def shutdown_event():
    """Actions à l'arrêt de l'application"""
    logger.info("🛑 Arrêt du service CEREMA Analyzer")


@app.get("/")
async def root():
    """Endpoint racine"""
    return {
        "service": "CEREMA Analyzer Service",
        "version": "1.0.0",
        "status": "running",
        "description": "Service d'extraction de données maritimes",
        "documentation": "/docs",
        "api_prefix": "/api/v1",
        "endpoints": {
            "extraction": "/api/v1/extract/*",
            "consultation": "/api/v1/aides",
            "recherche": "/api/v1/aides/search",
            "statistiques": "/api/v1/statistics",
            "santé": "/api/v1/health"
        }
    }


@app.get("/health")
async def health():
    """Endpoint de santé global"""
    return {
        "status": "healthy",
        "service": "CEREMA Analyzer Service",
        "version": "1.0.0"
    }


def main():
    """Point d'entrée principal"""
    logger.info("🚀 Lancement du serveur CEREMA Analyzer...")
    
    uvicorn.run(
        "main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,  # Mode développement - désactiver en production
        log_level=LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()