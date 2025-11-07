"""
Détecteur de type de document
"""
import re
import logging
from typing import Dict, Any
from config import (
    KEYWORDS_CATALOGUE, KEYWORDS_COURRIER, KEYWORDS_ARRETE,
    TABLE_SIZE_THRESHOLD
)

logger = logging.getLogger(__name__)


class DocumentTypeDetector:
    """Détecte le type de document et détermine la stratégie d'extraction"""
    
    def __init__(self):
        self.logger = logger
    
    def detect_type(self, text: str) -> Dict[str, Any]:
        """
        Détecte le type de document et retourne la stratégie d'extraction
        
        Args:
            text: Texte du document
            
        Returns:
            Dictionnaire avec type, stratégie, complexité, etc.
        """
        result = {
            'type': 'autre',
            'strategy': 'extract_partial',  # extract_all | extract_partial | metadata_only
            'complexity': 50,   # 0-100
            'nombre_aides_estime': 0,
            'confidence': 0.0
        }
        
        text_lower = text.lower()
        
        # 1. FICHE INDIVIDUELLE (haute priorité)
        if self._is_fiche_individuelle(text):
            result['type'] = 'fiche_individuelle'
            result['strategy'] = 'extract_all'
            result['complexity'] = 20
            result['nombre_aides_estime'] = 1
            result['confidence'] = 0.9
            self.logger.info("Document détecté : FICHE INDIVIDUELLE")
            return result
        
        # 2. CATALOGUE PRODUIT
        if self._is_catalogue(text_lower):
            result['type'] = 'catalogue_produit'
            result['strategy'] = 'metadata_only'
            result['complexity'] = 10
            result['nombre_aides_estime'] = 0
            result['confidence'] = 0.85
            self.logger.info("Document détecté : CATALOGUE PRODUIT")
            return result
        
        # 3. TABLEAU
        if self._is_tableau(text):
            nb_lignes = self._count_table_rows(text)
            result['type'] = 'tableau_complexe' if nb_lignes > TABLE_SIZE_THRESHOLD else 'tableau_simple'
            result['nombre_aides_estime'] = nb_lignes
            
            if nb_lignes <= TABLE_SIZE_THRESHOLD:
                result['strategy'] = 'extract_all'
                result['complexity'] = 40
                result['confidence'] = 0.8
                self.logger.info(f"Document détecté : TABLEAU SIMPLE ({nb_lignes} lignes)")
            else:
                result['strategy'] = 'extract_partial'
                result['complexity'] = 80
                result['confidence'] = 0.6
                self.logger.info(f"Document détecté : TABLEAU COMPLEXE ({nb_lignes} lignes)")
            return result
        
        # 4. ARRÊTÉ PRÉFECTORAL
        if self._is_arrete(text_lower):
            result['type'] = 'arrete_prefectoral'
            result['strategy'] = 'extract_partial'
            result['complexity'] = 50
            result['nombre_aides_estime'] = 1
            result['confidence'] = 0.75
            self.logger.info("Document détecté : ARRÊTÉ PRÉFECTORAL")
            return result
        
        # 5. COURRIER ADMINISTRATIF
        if self._is_courrier(text_lower):
            result['type'] = 'courrier_administratif'
            result['strategy'] = 'extract_partial'
            result['complexity'] = 30
            result['nombre_aides_estime'] = 0
            result['confidence'] = 0.7
            self.logger.info("Document détecté : COURRIER ADMINISTRATIF")
            return result
        
        # 6. AUTRE (par défaut)
        self.logger.info("Document détecté : AUTRE (type inconnu)")
        return result
    
    def _is_fiche_individuelle(self, text: str) -> bool:
        """
        Détecte une fiche individuelle d'aide à la navigation
        
        Indices :
        - Présence de "ESM N°" ou "SYSSI"
        - Format clé:valeur (plusieurs champs)
        - Document relativement court
        - Absence de tableau complexe
        """
        has_esm = bool(re.search(r'ESM\s*N°?\s*\d{7,8}', text, re.IGNORECASE))
        has_syssi = bool(re.search(r'SYSSI\s*[:N°]?\s*\d{7,8}', text, re.IGNORECASE))
        
        # Compter les paires clé:valeur
        key_value_count = len(re.findall(r'^[^:\n]{3,40}\s*:\s*.+$', text, re.MULTILINE))
        
        # Longueur du document
        lines = text.split('\n')
        is_short = len(lines) < 50
        
        # Présence de champs typiques
        has_typical_fields = any(keyword in text.lower() for keyword in [
            'nom de baptème', 'nom de baptême', 'mode d\'accès', 
            'caractère', 'fonction', 'système géodésique'
        ])
        
        return (has_esm or has_syssi) and key_value_count >= 3 and (is_short or has_typical_fields)
    
    def _is_tableau(self, text: str) -> bool:
        """
        Détecte un tableau structuré
        
        Indices :
        - Plusieurs lignes avec coordonnées GPS
        - Alignement régulier d'espaces
        - Répétition de motifs (Bouée, Balise, etc.)
        """
        lines = text.split('\n')
        
        # Compter les lignes avec coordonnées GPS
        gps_lines = sum(1 for line in lines if re.search(r'\d{2}°\s*\d{1,2}[,.\s]+\d{0,3}\s*[NS]', line))
        
        # Compter les lignes avec espaces multiples (colonnes)
        structured_lines = sum(1 for line in lines if re.search(r'\s{4,}', line))
        
        return gps_lines >= 5 or structured_lines >= 10
    
    def _count_table_rows(self, text: str) -> int:
        """
        Compte le nombre de lignes dans un tableau
        
        Returns:
            Nombre de lignes de données
        """
        lines = text.split('\n')
        
        # Compter les lignes avec coordonnées GPS (indicateur fort)
        gps_lines = sum(1 for line in lines if re.search(r'\d{2}°\s*\d{1,2}[,.\s]+\d{0,3}\s*[NS]', line))
        
        if gps_lines > 0:
            return gps_lines
        
        # Sinon compter les lignes structurées
        structured_lines = sum(1 for line in lines if re.search(r'\s{4,}', line) and len(line.strip()) > 10)
        
        return structured_lines
    
    def _is_catalogue(self, text_lower: str) -> bool:
        """
        Détecte un catalogue de produits
        
        Indices :
        - Mots-clés commerciaux (prix, tarif, EUR, kg, etc.)
        - Spécifications techniques répétitives
        - Absence de numéros ESM/SYSSI
        """
        score = sum(1 for keyword in KEYWORDS_CATALOGUE if keyword in text_lower)
        
        # Vérifier l'absence d'ESM/SYSSI (les catalogues n'en ont pas)
        has_no_esm = not bool(re.search(r'ESM\s*N°?\s*\d{7,8}', text_lower))
        
        return score >= 3 and has_no_esm
    
    def _is_courrier(self, text_lower: str) -> bool:
        """
        Détecte un courrier administratif
        
        Indices :
        - Formules de politesse
        - Structure de lettre
        - Absence de données techniques structurées
        """
        score = sum(1 for keyword in KEYWORDS_COURRIER if keyword in text_lower)
        
        return score >= 2
    
    def _is_arrete(self, text_lower: str) -> bool:
        """
        Détecte un arrêté préfectoral
        
        Indices :
        - Mentions légales
        - Articles numérotés
        - Structure administrative
        """
        score = sum(1 for keyword in KEYWORDS_ARRETE if keyword in text_lower)
        
        # Vérifier la présence d'articles numérotés
        has_articles = bool(re.search(r'article\s+\d+', text_lower))
        
        return score >= 2 or has_articles
    
    def get_extraction_strategy_description(self, strategy: str) -> str:
        """
        Retourne une description de la stratégie d'extraction
        
        Args:
            strategy: Stratégie (extract_all, extract_partial, metadata_only)
            
        Returns:
            Description textuelle
        """
        descriptions = {
            'extract_all': "Extraction complète de toutes les données",
            'extract_partial': "Extraction partielle - consulter le document original pour les détails",
            'metadata_only': "Métadonnées uniquement - document non pertinent pour l'extraction"
        }
        
        return descriptions.get(strategy, "Stratégie inconnue")