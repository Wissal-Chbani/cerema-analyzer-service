"""
Application principale CEREMA Analyzer Service
"""
import uvicorn
import traceback
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.requests import Request
import logging

from config import API_HOST, API_PORT, LOG_LEVEL
from core.utils import setup_logging
from api.routes import router

# Créer le dossier logs s'il n'existe pas
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "cerema.log"

# Configuration du logging avec fichier
setup_logging(log_level="DEBUG", log_file=str(log_file))
logger = logging.getLogger(__name__)

logger.info("=" * 70)
logger.info("🔧 Configuration du logging")
logger.info(f"📁 Fichier de log: {log_file}")
logger.info("=" * 70)

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


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Capture toutes les erreurs non gérées et les loggue."""
    error_detail = traceback.format_exc()
    
    logger.error("=" * 70)
    logger.error("❌ ERREUR NON GÉRÉE")
    logger.error("=" * 70)
    logger.error(f"URL: {request.url}")
    logger.error(f"Méthode: {request.method}")
    logger.error(f"Erreur: {exc}")
    logger.error("Traceback complet:")
    logger.error(error_detail)
    logger.error("=" * 70)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "details": error_detail
        },
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
    logger.info(f"📁 Fichier de log: {log_file}")
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