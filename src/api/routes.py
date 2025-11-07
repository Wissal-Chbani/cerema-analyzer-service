"""
Routes API FastAPI pour l'extraction de données maritimes
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from core.moteur import MoteurExtraction
from services.persistence import PersistenceService
from nlp.models import AideNavigationModel

router = APIRouter()

# Services globaux
moteur = MoteurExtraction()
persistence = PersistenceService()


# ========== MODÈLES DE REQUÊTE/RÉPONSE ==========

class ExtractionRequest(BaseModel):
    """Requête d'extraction pour un document"""
    document_id: str


class BatchExtractionRequest(BaseModel):
    """Requête d'extraction batch"""
    document_ids: Optional[List[str]] = None
    limit: Optional[int] = 10


class SearchRequest(BaseModel):
    """Requête de recherche"""
    search_term: str
    fields: Optional[List[str]] = None


class ExtractionResponse(BaseModel):
    """Réponse d'extraction"""
    success: bool
    aide_id: Optional[str] = None
    message: str
    extraction_status: Optional[str] = None
    confidence: Optional[float] = None


# ========== ENDPOINTS EXTRACTION ==========

@router.post("/extract/single", response_model=ExtractionResponse)
async def extract_single_document(request: ExtractionRequest):
    """
    Extrait les données d'un seul document
    """
    try:
        # Récupérer le document source
        document = persistence.get_document_by_id(request.document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document non trouvé")
        
        # Extraire les informations
        aide = moteur.extract_from_document(document)
        
        # Sauvegarder
        aide_id = persistence.save_aide_navigation(aide)
        
        if aide_id:
            return ExtractionResponse(
                success=True,
                aide_id=aide_id,
                message=f"Extraction réussie pour {document.nom_fichier}",
                extraction_status=aide.extraction_status,
                confidence=aide.extraction_confidence
            )
        else:
            return ExtractionResponse(
                success=False,
                message="Échec de sauvegarde",
                extraction_status=aide.extraction_status,
                confidence=aide.extraction_confidence
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/batch", response_model=dict)
async def extract_batch_documents(request: BatchExtractionRequest):
    """
    Extrait les données de plusieurs documents
    """
    try:
        # Si des IDs spécifiques sont fournis
        if request.document_ids:
            documents = []
            for doc_id in request.document_ids:
                doc = persistence.get_document_by_id(doc_id)
                if doc:
                    documents.append(doc)
        else:
            # Sinon récupérer les premiers N documents
            documents = persistence.get_documents(limit=request.limit)
        
        if not documents:
            raise HTTPException(status_code=404, detail="Aucun document trouvé")
        
        # Extraire les informations
        aides = moteur.extract_batch(documents)
        
        # Sauvegarder
        aide_ids = persistence.save_aides_batch(aides)
        
        # Statistiques
        status_counts = {}
        for aide in aides:
            status = aide.extraction_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "success": True,
            "total_processed": len(aides),
            "total_saved": len(aide_ids),
            "status_breakdown": status_counts,
            "aide_ids": aide_ids
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract/all")
async def extract_all_documents(limit: int = Query(100, le=1000)):
    """
    Extrait tous les documents (avec limite)
    """
    try:
        # Récupérer les documents
        documents = persistence.get_documents(limit=limit)
        
        if not documents:
            raise HTTPException(status_code=404, detail="Aucun document trouvé")
        
        # Extraire
        aides = moteur.extract_batch(documents)
        
        # Sauvegarder
        aide_ids = persistence.save_aides_batch(aides)
        
        # Statistiques
        status_counts = {}
        for aide in aides:
            status = aide.extraction_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "success": True,
            "total_processed": len(aides),
            "total_saved": len(aide_ids),
            "status_breakdown": status_counts,
            "message": f"Extraction terminée pour {len(aides)} documents"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== ENDPOINTS CONSULTATION ==========

@router.get("/aides", response_model=List[AideNavigationModel])
async def get_aides(
    limit: int = Query(50, le=200),
    skip: int = Query(0, ge=0),
    status: Optional[str] = None,
    type_document: Optional[str] = None
):
    """
    Récupère la liste des aides à la navigation
    """
    try:
        filters = {}
        if status:
            filters['extraction_status'] = status
        if type_document:
            filters['type_document'] = type_document
        
        aides = persistence.get_aides_navigation(limit=limit, skip=skip, filters=filters)
        return aides
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aides/{aide_id}", response_model=AideNavigationModel)
async def get_aide_by_id(aide_id: str):
    """
    Récupère une aide par son ID
    """
    try:
        aide = persistence.get_aide_by_id(aide_id)
        if not aide:
            raise HTTPException(status_code=404, detail="Aide non trouvée")
        return aide
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/aides/sysi/{n_sysi}", response_model=AideNavigationModel)
async def get_aide_by_sysi(n_sysi: str):
    """
    Récupère une aide par son numéro SYSSI
    """
    try:
        aide = persistence.get_aide_by_sysi(n_sysi)
        if not aide:
            raise HTTPException(status_code=404, detail="Aide non trouvée")
        return aide
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/aides/search", response_model=List[AideNavigationModel])
async def search_aides(request: SearchRequest):
    """
    Recherche des aides par terme
    """
    try:
        aides = persistence.search_aides(
            search_term=request.search_term,
            fields=request.fields
        )
        return aides
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== ENDPOINTS STATISTIQUES ==========

@router.get("/statistics")
async def get_statistics():
    """
    Récupère les statistiques globales
    """
    try:
        stats = persistence.get_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count")
async def get_counts():
    """
    Récupère les comptages
    """
    try:
        return {
            "documents": persistence.count_documents(),
            "aides": persistence.count_aides()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== ENDPOINTS SANTÉ ==========

@router.get("/health")
async def health_check():
    """
    Vérification de l'état du service
    """
    try:
        # Tester la connexion MongoDB
        doc_count = persistence.count_documents()
        
        return {
            "status": "healthy",
            "service": "CEREMA Analyzer Service",
            "version": "1.0.0",
            "database_connected": True,
            "documents_count": doc_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "CEREMA Analyzer Service",
            "version": "1.0.0",
            "database_connected": False,
            "error": str(e)
        }