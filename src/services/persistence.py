"""
Service de persistance pour MongoDB
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId

from config import MONGODB_URI, DATABASE_NAME, COLLECTION_DOCUMENTS, COLLECTION_AIDES_NAVIGATION
from nlp.models import DocumentSourceModel, AideNavigationModel

logger = logging.getLogger(__name__)


class PersistenceService:
    """Service de persistance MongoDB pour les documents et aides à la navigation"""
    
    def __init__(self, mongodb_uri: str = MONGODB_URI, database_name: str = DATABASE_NAME):
        self.logger = logger
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Établit la connexion à MongoDB"""
        try:
            self.client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            # Test de connexion
            self.client.server_info()
            self.db = self.client[self.database_name]
            self.logger.info(f"Connexion MongoDB établie: {self.database_name}")
            self._create_indexes()
        except ConnectionFailure as e:
            self.logger.error(f"Échec connexion MongoDB: {e}")
            raise
    
    def _create_indexes(self):
        """Crée les index nécessaires"""
        try:
            # Index pour les documents sources
            self.db[COLLECTION_DOCUMENTS].create_index([("nom_fichier", ASCENDING)])
            self.db[COLLECTION_DOCUMENTS].create_index([("ajoute_le", DESCENDING)])
            
            # Index pour les aides à la navigation
            self.db[COLLECTION_AIDES_NAVIGATION].create_index([("n_sysi", ASCENDING)])
            self.db[COLLECTION_AIDES_NAVIGATION].create_index([("nom_patrimoine", ASCENDING)])
            self.db[COLLECTION_AIDES_NAVIGATION].create_index([("nature_support", ASCENDING)])
            self.db[COLLECTION_AIDES_NAVIGATION].create_index([("marque", ASCENDING)])
            self.db[COLLECTION_AIDES_NAVIGATION].create_index([("type_document", ASCENDING)])
            self.db[COLLECTION_AIDES_NAVIGATION].create_index([("extraction_status", ASCENDING)])
            
            self.logger.info("Index MongoDB créés")
        except Exception as e:
            self.logger.warning(f"Erreur création index: {e}")
    
    def close(self):
        """Ferme la connexion MongoDB"""
        if self.client:
            self.client.close()
            self.logger.info("Connexion MongoDB fermée")
    
    # ========== DOCUMENTS SOURCES ==========
    
    def get_documents(self, limit: int = 100, skip: int = 0, 
                     filters: Optional[Dict[str, Any]] = None) -> List[DocumentSourceModel]:
        """
        Récupère les documents sources
        
        Args:
            limit: Nombre maximum de documents
            skip: Nombre de documents à ignorer
            filters: Filtres de recherche
            
        Returns:
            Liste de documents sources
        """
        try:
            query = filters if filters else {}
            cursor = self.db[COLLECTION_DOCUMENTS].find(query).skip(skip).limit(limit)
            
            documents = []
            for doc in cursor:
                try:
                    documents.append(DocumentSourceModel(**doc))
                except Exception as e:
                    self.logger.warning(f"Erreur parsing document {doc.get('_id')}: {e}")
            
            return documents
        except Exception as e:
            self.logger.error(f"Erreur récupération documents: {e}")
            return []
    
    def get_document_by_id(self, doc_id: str) -> Optional[DocumentSourceModel]:
        """Récupère un document par son ID"""
        try:
            doc = self.db[COLLECTION_DOCUMENTS].find_one({"_id": ObjectId(doc_id)})
            if doc:
                return DocumentSourceModel(**doc)
            return None
        except Exception as e:
            self.logger.error(f"Erreur récupération document {doc_id}: {e}")
            return None
    
    def count_documents(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Compte les documents sources"""
        try:
            query = filters if filters else {}
            return self.db[COLLECTION_DOCUMENTS].count_documents(query)
        except Exception as e:
            self.logger.error(f"Erreur comptage documents: {e}")
            return 0
    
    # ========== AIDES À LA NAVIGATION ==========
    
    def save_aide_navigation(self, aide: AideNavigationModel) -> Optional[str]:
        """
        Enregistre une aide à la navigation
        
        Args:
            aide: Modèle d'aide à la navigation
            
        Returns:
            ID du document inséré ou None si échec
        """
        try:
            # Convertir en dictionnaire
            aide_dict = aide.dict(by_alias=True, exclude_none=False)
            
            # Retirer l'_id s'il est None
            if '_id' in aide_dict and aide_dict['_id'] is None:
                del aide_dict['_id']
            
            # Insérer dans MongoDB
            result = self.db[COLLECTION_AIDES_NAVIGATION].insert_one(aide_dict)
            self.logger.info(f"Aide navigation enregistrée: {result.inserted_id}")
            return str(result.inserted_id)
        
        except DuplicateKeyError:
            self.logger.warning(f"Aide navigation déjà existante")
            return None
        except Exception as e:
            self.logger.error(f"Erreur enregistrement aide: {e}")
            return None
    
    def save_aides_batch(self, aides: List[AideNavigationModel]) -> List[str]:
        """
        Enregistre plusieurs aides à la navigation
        
        Args:
            aides: Liste d'aides
            
        Returns:
            Liste des IDs insérés
        """
        inserted_ids = []
        
        for aide in aides:
            aide_id = self.save_aide_navigation(aide)
            if aide_id:
                inserted_ids.append(aide_id)
        
        self.logger.info(f"{len(inserted_ids)}/{len(aides)} aides enregistrées")
        return inserted_ids
    
    def get_aides_navigation(self, limit: int = 100, skip: int = 0,
                            filters: Optional[Dict[str, Any]] = None) -> List[AideNavigationModel]:
        """Récupère les aides à la navigation"""
        try:
            query = filters if filters else {}
            cursor = self.db[COLLECTION_AIDES_NAVIGATION].find(query).skip(skip).limit(limit)
            
            aides = []
            for doc in cursor:
                try:
                    aides.append(AideNavigationModel(**doc))
                except Exception as e:
                    self.logger.warning(f"Erreur parsing aide {doc.get('_id')}: {e}")
            
            return aides
        except Exception as e:
            self.logger.error(f"Erreur récupération aides: {e}")
            return []
    
    def get_aide_by_id(self, aide_id: str) -> Optional[AideNavigationModel]:
        """Récupère une aide par son ID"""
        try:
            doc = self.db[COLLECTION_AIDES_NAVIGATION].find_one({"_id": ObjectId(aide_id)})
            if doc:
                return AideNavigationModel(**doc)
            return None
        except Exception as e:
            self.logger.error(f"Erreur récupération aide {aide_id}: {e}")
            return None
    
    def get_aide_by_sysi(self, n_sysi: str) -> Optional[AideNavigationModel]:
        """Récupère une aide par son numéro SYSSI"""
        try:
            doc = self.db[COLLECTION_AIDES_NAVIGATION].find_one({"n_sysi": n_sysi})
            if doc:
                return AideNavigationModel(**doc)
            return None
        except Exception as e:
            self.logger.error(f"Erreur récupération aide SYSSI {n_sysi}: {e}")
            return None
    
    def count_aides(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Compte les aides à la navigation"""
        try:
            query = filters if filters else {}
            return self.db[COLLECTION_AIDES_NAVIGATION].count_documents(query)
        except Exception as e:
            self.logger.error(f"Erreur comptage aides: {e}")
            return 0
    
    def search_aides(self, search_term: str, fields: List[str] = None) -> List[AideNavigationModel]:
        """
        Recherche des aides par terme
        
        Args:
            search_term: Terme de recherche
            fields: Champs dans lesquels chercher
            
        Returns:
            Liste d'aides correspondantes
        """
        if not fields:
            fields = ['nom_patrimoine', 'nom_bapteme', 'nature_support', 'marque']
        
        try:
            query = {
                "$or": [
                    {field: {"$regex": search_term, "$options": "i"}} 
                    for field in fields
                ]
            }
            
            cursor = self.db[COLLECTION_AIDES_NAVIGATION].find(query).limit(50)
            
            aides = []
            for doc in cursor:
                try:
                    aides.append(AideNavigationModel(**doc))
                except Exception as e:
                    self.logger.warning(f"Erreur parsing aide: {e}")
            
            return aides
        except Exception as e:
            self.logger.error(f"Erreur recherche: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Récupère les statistiques globales"""
        try:
            stats = {
                'total_documents': self.count_documents(),
                'total_aides': self.count_aides(),
                'aides_by_status': self._aggregate_by_field('extraction_status'),
                'aides_by_type': self._aggregate_by_field('type_document'),
                'aides_by_nature': self._aggregate_by_field('nature_support'),
                'aides_by_marque': self._aggregate_by_field('marque'),
                'aides_with_feu': self.count_aides({'feu': {'$ne': None}}),
                'aides_with_ais': self.count_aides({'ais_aton': True}),
                'aides_with_racon': self.count_aides({'balise_racon.present': True}),
            }
            return stats
        except Exception as e:
            self.logger.error(f"Erreur statistiques: {e}")
            return {}
    
    def _aggregate_by_field(self, field: str) -> Dict[str, int]:
        """Agrège les données par champ"""
        try:
            pipeline = [
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 20}  # Limiter à 20 résultats
            ]
            
            results = self.db[COLLECTION_AIDES_NAVIGATION].aggregate(pipeline)
            return {str(doc['_id']): doc['count'] for doc in results if doc['_id']}
        except Exception as e:
            self.logger.error(f"Erreur agrégation {field}: {e}")
            return {}