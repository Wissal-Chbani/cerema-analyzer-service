"""
Nettoyage et normalisation du texte
"""
import re
from typing import List, Dict


class TextCleaner:
    """Nettoie et normalise le texte extrait"""
    
    def __init__(self):
        # Patterns de nettoyage
        self.patterns = {
            'multiple_spaces': re.compile(r' {2,}'),  # 2+ espaces
            'multiple_newlines': re.compile(r'\n{3,}'),
            'page_separator': re.compile(r'-{3,}\s*Page\s+\d+\s*-{3,}'),
        }
    
    def clean(self, text: str) -> str:
        """
        Nettoie le texte
        
        Args:
            text: Texte brut
            
        Returns:
            Texte nettoyé
        """
        if not text:
            return ""
        
        # Supprimer les séparateurs de page
        text = self.patterns['page_separator'].sub('\n', text)
        
        # Normaliser les espaces (mais garder les espaces multiples pour les tableaux)
        # On normalise seulement les espaces à la fin des lignes
        lines = text.split('\n')
        lines = [line.rstrip() for line in lines]
        text = '\n'.join(lines)
        
        # Normaliser les sauts de ligne excessifs
        text = self.patterns['multiple_newlines'].sub('\n\n', text)
        
        # Supprimer les caractères de contrôle problématiques
        text = text.replace('\x00', '')
        text = text.replace('\ufffd', '')
        text = text.replace('\r', '')
        
        # Normaliser les apostrophes et guillemets
        text = text.replace(''', "'").replace(''', "'")
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('â€™', "'")
        text = text.replace('Ã©', 'é')
        text = text.replace('Ã ', 'à')
        text = text.replace('Ã¨', 'è')
        
        # Nettoyer les espaces en début et fin
        text = text.strip()
        
        return text
    
    def extract_lines(self, text: str) -> List[str]:
        """
        Extrait les lignes non vides du texte
        
        Args:
            text: Texte à traiter
            
        Returns:
            Liste de lignes non vides
        """
        lines = [line.strip() for line in text.split('\n')]
        return [line for line in lines if line]
    
    def normalize_maritime_terms(self, text: str) -> str:
        """
        Normalise les termes maritimes
        
        Args:
            text: Texte à normaliser
            
        Returns:
            Texte avec termes normalisés
        """
        replacements = {
            r'\btribord\b': 'tribord',
            r'\bbâbord\b': 'bâbord',
            r'\bbabord\b': 'bâbord',
            r'\bcardinale\b': 'cardinale',
            r'\bphare\b': 'phare',
            r'\bbalise\b': 'balise',
            r'\bbouée\b': 'bouée',
            r'\bbouee\b': 'bouée',
            r'\btourelle\b': 'tourelle',
            r'\bespar\b': 'espar',
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        
        return text
    
    def remove_header_footer(self, text: str, header_keyword: str = None, 
                            footer_keyword: str = None) -> str:
        """
        Supprime les en-têtes et pieds de page
        
        Args:
            text: Texte complet
            header_keyword: Mot-clé marquant la fin de l'en-tête
            footer_keyword: Mot-clé marquant le début du pied de page
            
        Returns:
            Texte sans en-tête ni pied de page
        """
        lines = text.split('\n')
        
        # Trouver le début du contenu réel
        start_idx = 0
        if header_keyword:
            for i, line in enumerate(lines):
                if header_keyword.lower() in line.lower():
                    start_idx = i + 1
                    break
        
        # Trouver la fin du contenu réel
        end_idx = len(lines)
        if footer_keyword:
            for i in range(len(lines) - 1, -1, -1):
                if footer_keyword.lower() in lines[i].lower():
                    end_idx = i
                    break
        
        return '\n'.join(lines[start_idx:end_idx])
    
    def extract_key_value_pairs(self, text: str) -> Dict[str, str]:
        """
        Extrait les paires clé-valeur du texte (format "Clé : Valeur")
        
        Args:
            text: Texte à analyser
            
        Returns:
            Dictionnaire des paires clé-valeur
        """
        pairs = {}
        
        # Pattern pour "Clé : Valeur" ou "Clé: Valeur"
        pattern = re.compile(r'^([^:\n]+?)\s*:\s*(.+)$', re.MULTILINE)
        
        for match in pattern.finditer(text):
            key = match.group(1).strip()
            value = match.group(2).strip()
            
            # Nettoyer la clé
            key = key.lower().replace('  ', ' ')
            
            if key and value:
                pairs[key] = value
        
        return pairs
    
    def detect_encoding_issues(self, text: str) -> bool:
        """
        Détecte les problèmes d'encodage dans le texte
        
        Args:
            text: Texte à vérifier
            
        Returns:
            True si des problèmes sont détectés
        """
        # Caractères indicateurs de problèmes d'encodage
        problematic_patterns = [
            'Ã©', 'Ã ', 'Ã¨', 'Ã´', 'Ã®', 'Ã§',
            'â€™', 'â€œ', 'â€�', '\ufffd'
        ]
        
        for pattern in problematic_patterns:
            if pattern in text:
                return True
        
        return False