"""
Pipeline de traitement NLP pour l'extraction d'entités
"""
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class NLPPipeline:
    """Pipeline de traitement NLP (simplifié sans spaCy pour démarrer)"""
    
    def __init__(self):
        self.logger = logger
        self.nlp = None
        self._try_load_spacy()
    
    def _try_load_spacy(self):
        """Essaie de charger spaCy (optionnel)"""
        try:
            import spacy
            from config import SPACY_MODEL
            self.nlp = spacy.load(SPACY_MODEL)
            self.logger.info(f"Modèle spaCy chargé: {SPACY_MODEL}")
        except (ImportError, OSError) as e:
            self.logger.warning(f"spaCy non disponible: {e}. Mode basique activé.")
            self.nlp = None
    
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extrait des entités depuis le texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire avec les entités extraites
        """
        if not text:
            return {}
        
        data = {}
        
        if self.nlp:
            # Mode avancé avec spaCy
            data = self._extract_with_spacy(text)
        else:
            # Mode basique sans spaCy
            data = self._extract_basic(text)
        
        return data
    
    def _extract_with_spacy(self, text: str) -> Dict[str, Any]:
        """Extraction avec spaCy"""
        from config import MAX_TEXT_LENGTH
        
        if len(text) > MAX_TEXT_LENGTH:
            text = text[:MAX_TEXT_LENGTH]
        
        try:
            doc = self.nlp(text)
            
            entities = {}
            for ent in doc.ents:
                if ent.label_ not in entities:
                    entities[ent.label_] = []
                entities[ent.label_].append(ent.text)
            
            return {
                'entites_nlp': entities,
                'nlp_used': True
            }
        except Exception as e:
            self.logger.error(f"Erreur spaCy: {e}")
            return {'nlp_used': False}
    
    def _extract_basic(self, text: str) -> Dict[str, Any]:
        """Extraction basique sans NLP"""
        import re
        
        data = {'nlp_used': False}
        
        # Chercher des noms propres (mots en majuscules)
        noms_propres = re.findall(r'\b[A-ZÀ-Ÿ][a-zà-ÿ]+(?:\s+[A-ZÀ-Ÿ][a-zà-ÿ]+)*\b', text)
        if noms_propres:
            data['noms_detectes'] = list(set(noms_propres))[:10]  # Limiter à 10
        
        # Chercher des nombres
        nombres = re.findall(r'\b\d+(?:[.,]\d+)?\b', text)
        if nombres:
            data['nombres_detectes'] = list(set(nombres))[:10]
        
        return data
    
    def analyze_maritime_vocabulary(self, text: str) -> Dict[str, int]:
        """
        Analyse le vocabulaire maritime dans le texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire des termes et leur fréquence
        """
        maritime_terms = [
            'phare', 'balise', 'bouée', 'feu', 'voyant', 'marque',
            'tribord', 'bâbord', 'babord', 'cardinale', 'latérale',
            'racon', 'radar', 'ais', 'tourelle', 'espar',
            'secteur', 'portée', 'éclat', 'occultation',
            'navigation', 'maritime', 'nautique', 'chenalage',
            'atterrissage', 'jalonnement'
        ]
        
        term_counts = {}
        text_lower = text.lower()
        
        for term in maritime_terms:
            count = text_lower.count(term)
            if count > 0:
                term_counts[term] = count
        
        return term_counts