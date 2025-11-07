"""
Moteur principal d'extraction des données maritimes
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from preprocessing.text_reader import TextReader
from preprocessing.text_cleaner import TextCleaner
from nlp.pipeline import NLPPipeline
from rules.rules import ExtractionRules
from rules.document_detector import DocumentTypeDetector
from nlp.models import (
    AideNavigationModel, FeuModel, AideSonoreModel, 
    BaliseRaconModel, DocumentSourceModel, BoueeExempleModel
)
from core.utils import (
    calculate_confidence_score, merge_extracted_data,
    format_extraction_metadata, create_extraction_warning
)

logger = logging.getLogger(__name__)


class MoteurExtraction:
    """Moteur principal d'extraction des informations maritimes"""
    
    def __init__(self):
        self.logger = logger
        self.text_reader = TextReader()
        self.text_cleaner = TextCleaner()
        self.nlp_pipeline = NLPPipeline()
        self.rules = ExtractionRules()
        self.type_detector = DocumentTypeDetector()
        self.methods_used = []
        self.warnings = []
    
    def extract_from_document(self, document: DocumentSourceModel) -> AideNavigationModel:
        """
        Extrait les informations d'un document source
        
        Args:
            document: Document source MongoDB
            
        Returns:
            Modèle d'aide à la navigation extrait
        """
        start_time = time.time()
        self.methods_used = []
        self.warnings = []
        
        self.logger.info(f"Traitement du document: {document.nom_fichier}")
        
        # 1. Extraction du texte
        texte = self._extract_text(document)
        if not texte:
            self.logger.error(f"Impossible d'extraire le texte de {document.nom_fichier}")
            return self._create_empty_aide(document, "Échec extraction texte")
        
        self.logger.info(f"Texte extrait: {len(texte)} caractères")
        
        # 2. Nettoyage du texte
        texte = self.text_cleaner.clean(texte)
        texte = self.text_cleaner.normalize_maritime_terms(texte)
        self.methods_used.append("text_cleaning")
        
        # Vérifier les problèmes d'encodage
        if self.text_cleaner.detect_encoding_issues(texte):
            self.warnings.append(create_extraction_warning("Problèmes d'encodage détectés"))
        
        # 3. Détection du type de document
        doc_info = self.type_detector.detect_type(texte)
        self.logger.info(f"Type détecté: {doc_info['type']} | Stratégie: {doc_info['strategy']}")
        
        # 4. Extraction selon la stratégie
        if doc_info['strategy'] == 'extract_all':
            aide = self._extract_full(document, texte, doc_info)
        elif doc_info['strategy'] == 'extract_partial':
            aide = self._extract_partial(document, texte, doc_info)
        else:  # metadata_only
            aide = self._extract_metadata_only(document, texte, doc_info)
        
        # 5. Métadonnées finales
        extraction_time = time.time() - start_time
        aide.extraction_date = datetime.now()
        aide.extraction_metadata = format_extraction_metadata(
            extraction_time,
            aide.extraction_confidence,
            self.methods_used,
            self.warnings
        )
        
        self.logger.info(
            f"Extraction terminée en {extraction_time:.2f}s "
            f"(confiance: {aide.extraction_confidence:.2f})"
        )
        
        return aide
    
    def _extract_text(self, document: DocumentSourceModel) -> Optional[str]:
        """Extrait le texte du document"""
        # Si le texte OCR est déjà stocké
        if hasattr(document, 'texte_ocr') and document.texte_ocr:
            return document.texte_ocr
        
        # Sinon lire depuis le fichier
        return self.text_reader.read_text_file(document.chemin_local)
    
    def _extract_full(self, document: DocumentSourceModel, texte: str, 
                     doc_info: Dict[str, Any]) -> AideNavigationModel:
        """
        Extraction complète (fiches individuelles, tableaux simples)
        
        Args:
            document: Document source
            texte: Texte nettoyé
            doc_info: Informations sur le type de document
            
        Returns:
            Aide à la navigation avec données complètes
        """
        self.logger.info("Extraction COMPLÈTE")
        
        # Extraction avec règles
        extracted_data = self.rules.extract_all_fields(texte)
        self.methods_used.append("full_rules_extraction")
        
        # Enrichissement avec NLP
        nlp_data = self.nlp_pipeline.extract_entities(texte)
        if nlp_data.get('nlp_used'):
            self.methods_used.append("nlp_extraction")
        
        extracted_data = merge_extracted_data(extracted_data, nlp_data)
        
        # Construire le modèle
        aide = self._build_aide_navigation_model(document, extracted_data, doc_info)
        
        # Score de confiance
        aide.extraction_confidence = calculate_confidence_score(
            extracted_data, doc_info['type']
        )
        aide.extraction_status = 'success'
        aide.voir_document_original = False
        
        return aide
    
    def _extract_partial(self, document: DocumentSourceModel, texte: str,
                        doc_info: Dict[str, Any]) -> AideNavigationModel:
        """
        Extraction partielle (tableaux complexes, arrêtés, courriers)
        
        Args:
            document: Document source
            texte: Texte nettoyé
            doc_info: Informations sur le type de document
            
        Returns:
            Aide à la navigation avec données partielles + lien vers original
        """
        self.logger.info("Extraction PARTIELLE")
        
        # Extraction patterns génériques uniquement
        extracted_data = self.rules.extract_generic_patterns(texte)
        self.methods_used.append("generic_patterns")
        
        # Pour les tableaux complexes, extraire quelques exemples
        if doc_info['type'] in ['tableau_complexe', 'tableau_simple']:
            table_data = self.rules.extract_from_table(texte)
            extracted_data = merge_extracted_data(extracted_data, table_data)
            self.methods_used.append("table_sampling")
        
        # Analyser le vocabulaire maritime
        vocab = self.nlp_pipeline.analyze_maritime_vocabulary(texte)
        extracted_data['maritime_terms_count'] = len(vocab)
        
        # Construire le modèle
        aide = self._build_aide_navigation_model(document, extracted_data, doc_info)
        
        # Marquer comme partiel
        aide.extraction_status = 'partial'
        aide.extraction_confidence = calculate_confidence_score(
            extracted_data, doc_info['type']
        )
        aide.voir_document_original = True
        aide.raison_reference_originale = self._get_partial_reason(doc_info)
        
        return aide
    
    def _extract_metadata_only(self, document: DocumentSourceModel, texte: str,
                               doc_info: Dict[str, Any]) -> AideNavigationModel:
        """
        Métadonnées uniquement (catalogues, documents non pertinents)
        
        Args:
            document: Document source
            texte: Texte nettoyé
            doc_info: Informations sur le type de document
            
        Returns:
            Aide à la navigation avec métadonnées uniquement
        """
        self.logger.info("MÉTADONNÉES UNIQUEMENT")
        
        aide = AideNavigationModel(
            nom_fichier=document.nom_fichier,
            chemin_local=document.chemin_local,
            cree_le=document.cree_le,
            mime_type=document.mime_type,
            taille=document.taille,
            extraction_status='skipped',
            extraction_confidence=0.0,
            type_document=doc_info['type'],
            nombre_aides=0,
            voir_document_original=True,
            raison_reference_originale=f"Document de type '{doc_info['type']}' - non pertinent pour l'extraction"
        )
        
        self.methods_used.append("metadata_only")
        
        return aide
    
    def _build_aide_navigation_model(self, document: DocumentSourceModel,
                                    extracted_data: Dict[str, Any],
                                    doc_info: Dict[str, Any]) -> AideNavigationModel:
        """
        Construit le modèle d'aide à la navigation
        
        Args:
            document: Document source
            extracted_data: Données extraites
            doc_info: Informations sur le type de document
            
        Returns:
            Modèle d'aide à la navigation
        """
        # Construire les sous-modèles
        feu = None
        if 'feu' in extracted_data and extracted_data['feu']:
            feu = FeuModel(**extracted_data['feu'])
        
        aide_sonore = None
        if 'aide_sonore' in extracted_data and extracted_data['aide_sonore']:
            aide_sonore = AideSonoreModel(**extracted_data['aide_sonore'])
        
        balise_racon = None
        if 'balise_racon' in extracted_data and extracted_data['balise_racon']:
            balise_racon = BaliseRaconModel(**extracted_data['balise_racon'])
        
        # Exemples de bouées (pour tableaux)
        exemples_bouees = None
        if 'exemples_bouees' in extracted_data and extracted_data['exemples_bouees']:
            exemples_bouees = [BoueeExempleModel(**b) for b in extracted_data['exemples_bouees']]
        
        # Construire le modèle principal
        aide_data = {
            'nom_fichier': document.nom_fichier,
            'chemin_local': document.chemin_local,
            'cree_le': document.cree_le,
            'mime_type': document.mime_type,
            'taille': document.taille,
            'type_document': doc_info['type'],
            'nombre_aides': doc_info['nombre_aides_estime'],
            'extraction_method': doc_info['strategy'],
            'n_sysi': extracted_data.get('n_sysi'),
            'nom_patrimoine': extracted_data.get('nom_patrimoine'),
            'nom_bapteme': extracted_data.get('nom_bapteme'),
            'position': extracted_data.get('position'),
            'systeme_geodesique': extracted_data.get('systeme_geodesique'),
            'zone': extracted_data.get('zone'),
            'nature_support': extracted_data.get('nature_support'),
            'hauteur_support': extracted_data.get('hauteur_support'),
            'altitude_base': extracted_data.get('altitude_base'),
            'marque': extracted_data.get('marque'),
            'caractere': extracted_data.get('caractere'),
            'fonction': extracted_data.get('fonction'),
            'classement': extracted_data.get('classement'),
            'validite': extracted_data.get('validite'),
            'marque_jour': extracted_data.get('marque_jour'),
            'voyant': extracted_data.get('voyant'),
            'bande_retro_reflechissante': extracted_data.get('bande_retro_reflechissante'),
            'reflecteur_radar': extracted_data.get('reflecteur_radar'),
            'feu': feu,
            'aide_sonore': aide_sonore,
            'ais_aton': extracted_data.get('ais_aton'),
            'balise_racon': balise_racon,
            'mode_acces': extracted_data.get('mode_acces'),
            'date_decision': extracted_data.get('date_decision'),
            'reference_arrete': extracted_data.get('reference_arrete'),
            'exemples_bouees': exemples_bouees,
        }
        
        return AideNavigationModel(**aide_data)
    
    def _create_empty_aide(self, document: DocumentSourceModel, error_msg: str) -> AideNavigationModel:
        """Crée un modèle vide en cas d'échec d'extraction"""
        return AideNavigationModel(
            nom_fichier=document.nom_fichier,
            chemin_local=document.chemin_local,
            cree_le=document.cree_le,
            mime_type=document.mime_type,
            taille=document.taille,
            extraction_status='failed',
            extraction_confidence=0.0,
            voir_document_original=True,
            raison_reference_originale=error_msg,
            extraction_date=datetime.now(),
            extraction_metadata={
                'error': error_msg,
                'version': '1.0.0'
            }
        )
    
    def _get_partial_reason(self, doc_info: Dict[str, Any]) -> str:
        """Génère la raison pour une extraction partielle"""
        reasons = {
            'tableau_complexe': f"Tableau complexe avec {doc_info['nombre_aides_estime']} entrées - consulter l'original pour tous les détails",
            'arrete_prefectoral': "Arrêté préfectoral - consulter l'original pour le texte complet",
            'courrier_administratif': "Courrier administratif - consulter l'original pour le contexte complet",
            'autre': "Document de structure complexe - consulter l'original pour plus de détails"
        }
        
        return reasons.get(doc_info['type'], "Extraction partielle - consulter l'original")
    
    def extract_batch(self, documents: list) -> list:
        """
        Extrait les informations de plusieurs documents
        
        Args:
            documents: Liste de documents sources
            
        Returns:
            Liste des aides à la navigation extraites
        """
        results = []
        total = len(documents)
        
        self.logger.info(f"Extraction batch de {total} documents")
        
        for i, doc in enumerate(documents, 1):
            self.logger.info(f"Traitement document {i}/{total}: {doc.nom_fichier}")
            try:
                aide = self.extract_from_document(doc)
                results.append(aide)
            except Exception as e:
                self.logger.error(f"Erreur traitement {doc.nom_fichier}: {e}", exc_info=True)
                results.append(self._create_empty_aide(doc, f"Erreur: {str(e)}"))
        
        self.logger.info(f"Extraction batch terminée: {len(results)} documents traités")
        return results