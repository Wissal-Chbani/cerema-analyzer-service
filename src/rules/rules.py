"""
Règles d'extraction basées sur des patterns et du vocabulaire maritime
"""
import re
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from config import (
    PATTERNS, NATURES_SUPPORT, MARQUES, COULEURS_FEU,
    RYTHMES_FEU, TYPES_AIDE_SONORE, TYPES_VOYANT, FONCTIONS, COULEURS_MARQUE
)

logger = logging.getLogger(__name__)


class ExtractionRules:
    """Règles d'extraction pour les aides à la navigation"""
    
    def __init__(self):
        self.logger = logger
        self.patterns = PATTERNS
        self.natures_support = NATURES_SUPPORT
        self.marques = MARQUES
        self.fonctions = FONCTIONS
        self.couleurs_feu = COULEURS_FEU
        self.couleurs_marque = COULEURS_MARQUE
        self.rythmes_feu = RYTHMES_FEU
        self.types_aide_sonore = TYPES_AIDE_SONORE
        self.types_voyant = TYPES_VOYANT
    
    def extract_all_fields(self, text: str) -> Dict[str, Any]:
        """
        Extrait tous les champs possibles (pour fiches individuelles)
        
        Args:
            text: Texte du document
            
        Returns:
            Dictionnaire avec tous les champs extraits
        """
        data = {}
        
        # Identification
        data['n_sysi'] = self.extract_n_sysi(text)
        data['nom_patrimoine'] = self.extract_nom_patrimoine(text)
        data['nom_bapteme'] = self.extract_nom_bapteme(text)
        
        # Localisation
        data['position'] = self.extract_position(text)
        data['systeme_geodesique'] = self.extract_systeme_geodesique(text)
        data['zone'] = self.extract_zone(text)
        
        # Support
        data['nature_support'] = self.extract_nature_support(text)
        data['hauteur_support'] = self.extract_hauteur(text)
        data['altitude_base'] = self.extract_altitude(text)
        
        # Signalisation
        data['marque'] = self.extract_marque(text)
        data['caractere'] = data['marque']  # Alias
        data['fonction'] = self.extract_fonction(text)
        data['classement'] = self.extract_classement(text)
        data['validite'] = self.extract_validite(text)
        data['marque_jour'] = self.extract_marque_jour(text)
        data['voyant'] = self.extract_voyant(text)
        data['bande_retro_reflechissante'] = self.extract_boolean_field(text, ['bande rétro', 'retro-reflechissante'])
        data['reflecteur_radar'] = self.extract_reflecteur_radar(text)
        
        # Feu
        feu_data = self.extract_feu_data(text)
        if feu_data:
            data['feu'] = feu_data
        
        # Aide sonore
        aide_sonore = self.extract_aide_sonore(text)
        if aide_sonore:
            data['aide_sonore'] = aide_sonore
        
        # Électronique
        data['ais_aton'] = self.extract_ais_aton(text)
        balise_racon = self.extract_balise_racon(text)
        if balise_racon:
            data['balise_racon'] = balise_racon
        
        # Mode d'accès
        data['mode_acces'] = self.extract_mode_acces(text)
        
        # Dates et références
        data['date_decision'] = self.extract_date(text)
        data['reference_arrete'] = self.extract_reference_arrete(text)
        
        return data
    
    def extract_generic_patterns(self, text: str) -> Dict[str, Any]:
        """
        Extrait les patterns génériques (fonctionne sur tous les documents)
        
        Args:
            text: Texte du document
            
        Returns:
            Dictionnaire avec les champs extraits
        """
        data = {}
        
        # Champs simples
        data['n_sysi'] = self.extract_n_sysi(text)
        data['position'] = self.extract_position(text)
        data['nature_support'] = self.extract_nature_support(text)
        data['marque'] = self.extract_marque(text)
        data['date_decision'] = self.extract_date(text)
        
        return data
    
    def extract_n_sysi(self, text: str) -> Optional[str]:
        """Extrait le numéro SYSSI ou ESM"""
        # Chercher ESM N° (prioritaire)
        match = re.search(self.patterns['esm'], text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Chercher SYSSI
        match = re.search(r'SYSSI\s*[:N°]?\s*(\d{7,8})', text, re.IGNORECASE)
        if match:
            return match.group(1)
        
        # Chercher un nombre de 7-8 chiffres commençant par un département
        matches = re.findall(self.patterns['n_sysi'], text)
        for num in matches:
            if num[:2] in ['85', '44', '56', '29', '22', '35', '50', '76', '62', '59', '80', '17', '33', '64', '40', '66', '34', '13', '83', '06']:
                return num
        
        return None
    
    def extract_position(self, text: str) -> Optional[str]:
        """Extrait la position géographique"""
        # Coordonnées en degrés minutes
        match = re.search(self.patterns['position_coords'], text)
        if match:
            return match.group(0).strip()
        
        # Coordonnées décimales
        match = re.search(self.patterns['position_decimal'], text)
        if match:
            return match.group(0).strip()
        
        return None
    
    def extract_systeme_geodesique(self, text: str) -> Optional[str]:
        """Extrait le système géodésique"""
        match = re.search(r'Système géodésique\s*:\s*([A-Z0-9\s]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Chercher WGS 84 directement
        if re.search(r'WGS\s*84', text, re.IGNORECASE):
            return "WGS 84"
        
        return None
    
    def extract_zone(self, text: str) -> Optional[str]:
        """Extrait la zone géographique"""
        # Chercher dans les descriptions
        patterns = [
            r'(?:zone|secteur|estuaire|chenal)\s+(?:de|du|d\')\s+([A-ZÀ-Ÿ][a-zà-ÿ\-\s]+)',
            r'([A-ZÀ-Ÿ][a-zà-ÿ\-\s]+)\s+(?:estuaire|chenal|goulet)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_nature_support(self, text: str) -> Optional[str]:
        """Extrait la nature du support"""
        text_lower = text.lower()
        
        # Chercher la nature la plus spécifique en premier
        for nature in sorted(self.natures_support, key=len, reverse=True):
            if nature.lower() in text_lower:
                return nature
        
        return None
    
    def extract_hauteur(self, text: str) -> Optional[float]:
        """Extrait la hauteur du support"""
        match = re.search(r'Hauteur du support\s*:\s*(\d+(?:[.,]\d+)?)\s*m', text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', '.'))
        
        return None
    
    def extract_altitude(self, text: str) -> Optional[float]:
        """Extrait l'altitude de la base"""
        match = re.search(r'Altitude de la base\s*:\s*(\d+(?:[.,]\d+)?)\s*m', text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(',', '.'))
        
        return None
    
    def extract_marque(self, text: str) -> Optional[str]:
        """Extrait le type de marque"""
        text_lower = text.lower()
        
        # Chercher "Caractère :" suivi de la marque
        match = re.search(r'Caractère\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            marque_candidate = match.group(1).strip()
            # Vérifier si c'est une marque connue
            for marque in self.marques:
                if marque.lower() in marque_candidate.lower():
                    return marque
        
        # Sinon chercher dans tout le texte
        for marque in self.marques:
            if marque.lower() in text_lower:
                return marque
        
        return None
    
    def extract_fonction(self, text: str) -> Optional[str]:
        """Extrait la fonction de l'aide"""
        match = re.search(r'Fonction\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        # Chercher dans les fonctions connues
        text_lower = text.lower()
        for fonction in self.fonctions:
            if fonction.lower() in text_lower:
                return fonction
        
        return None
    
    def extract_classement(self, text: str) -> Optional[str]:
        """Extrait le classement"""
        match = re.search(r'Classement\s+dominant\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def extract_validite(self, text: str) -> Optional[str]:
        """Extrait la validité"""
        match = re.search(r'Validité\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def extract_marque_jour(self, text: str) -> Optional[str]:
        """Extrait les couleurs de la marque de jour"""
        couleurs = []
        text_lower = text.lower()
        
        for couleur in self.couleurs_marque:
            if couleur.lower() in text_lower:
                if couleur not in couleurs:
                    couleurs.append(couleur)
        
        return '/'.join(couleurs) if couleurs else None
    
    def extract_boolean_field(self, text: str, keywords: List[str]) -> Optional[bool]:
        """Extrait un champ booléen basé sur des mots-clés"""
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                context = self._get_context(text_lower, keyword.lower())
                if any(neg in context for neg in ['non', 'sans', 'pas', 'aucun', 'absent']):
                    return False
                return True
        
        return None
    
    def extract_voyant(self, text: str) -> Optional[bool]:
        """Extrait la présence d'un voyant"""
        return self.extract_boolean_field(text, self.types_voyant + ['voyant'])
    
    def extract_reflecteur_radar(self, text: str) -> Optional[bool]:
        """Extrait la présence d'un réflecteur radar"""
        return self.extract_boolean_field(text, ['réflecteur radar', 'reflecteur radar'])
    
    def extract_feu_data(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrait les données du feu"""
        feu_data = {}
        
        # Couleur du feu
        for couleur in self.couleurs_feu:
            if re.search(rf'\bfeu\s+{couleur.lower()}\b', text, re.IGNORECASE):
                feu_data['couleur'] = couleur
                break
        
        # Rythme
        for categorie, rythmes in self.rythmes_feu.items():
            for rythme in rythmes:
                rythme_escaped = re.escape(rythme)
                if re.search(rf'\b{rythme_escaped}\b', text, re.IGNORECASE):
                    feu_data['rythme'] = rythme
                    break
            if 'rythme' in feu_data:
                break
        
        # Portée nominale
        portee_match = re.search(r'portée?\s*:?\s*(\d+)\s*[Mm]', text, re.IGNORECASE)
        if portee_match:
            feu_data['portee_nominale'] = int(portee_match.group(1))
        
        # Secteurs
        if '360' in text or 'tout horizon' in text.lower():
            feu_data['secteurs'] = '360°'
        elif 'sectoriel' in text.lower() or 'secteur' in text.lower():
            feu_data['secteurs'] = 'Sectoriel'
        
        return feu_data if feu_data else None
    
    def extract_aide_sonore(self, text: str) -> Optional[Dict[str, str]]:
        """Extrait les données de l'aide sonore"""
        for type_sonore in self.types_aide_sonore:
            if type_sonore.lower() in text.lower():
                return {'type': type_sonore}
        
        return None
    
    def extract_ais_aton(self, text: str) -> Optional[bool]:
        """Extrait la présence d'AIS AtoN"""
        return self.extract_boolean_field(text, ['AIS', 'AtoN', 'AIS AtoN'])
    
    def extract_balise_racon(self, text: str) -> Optional[Dict[str, Any]]:
        """Extrait les données de la balise Racon"""
        if not self.extract_boolean_field(text, ['Racon', 'balise racon']):
            return None
        
        racon = {'present': True}
        
        # Chercher la lettre morse
        morse_match = re.search(r'racon.*?([A-Z])\b', text, re.IGNORECASE)
        if morse_match:
            racon['lettre_morse'] = morse_match.group(1).upper()
        
        return racon
    
    def extract_mode_acces(self, text: str) -> Optional[str]:
        """Extrait le mode d'accès"""
        match = re.search(r'Mode d\'Accès\s*:\s*([^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def extract_date(self, text: str) -> Optional[datetime]:
        """Extrait une date"""
        date_match = re.search(self.patterns['date'], text)
        if not date_match:
            return None
        
        date_str = date_match.group(0)
        
        # Essayer différents formats
        formats = ['%d/%m/%Y', '%d-%m-%Y', '%d/%m/%y', '%d-%m-%y']
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def extract_reference_arrete(self, text: str) -> Optional[str]:
        """Extrait la référence d'arrêté"""
        match = re.search(r'Arrêté\s+n°?[\s:]*([\w\-/]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def extract_nom_patrimoine(self, text: str) -> Optional[str]:
        """Extrait le nom de patrimoine"""
        patterns = [
            r'(?:nom\s+de\s+)?patrimoine\s*:?\s*([A-ZÀ-Ÿ][^\n]+)',
            r'nom\s+officiel\s*:?\s*([A-ZÀ-Ÿ][^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def extract_nom_bapteme(self, text: str) -> Optional[str]:
        """Extrait le nom de baptême"""
        match = re.search(r'Nom de Bapt[èê]me\s*:?\s*([A-ZÀ-Ÿ][^\n]+)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def extract_from_table(self, text: str) -> Dict[str, Any]:
        """
        Extrait des données depuis un tableau
        
        Args:
            text: Texte contenant un tableau
            
        Returns:
            Dictionnaire avec exemples de bouées
        """
        data = {'exemples_bouees': []}
        
        # Pattern pour une ligne de bouée/balise avec coordonnées
        pattern = r'(Bouée|Balise)\s+(babord|tribord|bâbord)\s+(\d+)?[^\d]*(\d{2}°\s*\d{1,2}[,.\s]+\d{0,3}\s*[NS])[^\d]*(\d{1,3}°\s*\d{1,2}[,.\s]+\d{0,3}\s*[EWO])'
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            bouee = {
                'nom': f"{match.group(1)} {match.group(2)} {match.group(3) or ''}".strip(),
                'marque': f"Latérale {match.group(2)}",
                'position': f"{match.group(4)}, {match.group(5)}",
                'numero': match.group(3)
            }
            data['exemples_bouees'].append(bouee)
            
            # Limiter à 5 exemples
            if len(data['exemples_bouees']) >= 5:
                break
        
        return data
    
    def _get_context(self, text: str, keyword: str, window: int = 50) -> str:
        """Récupère le contexte autour d'un mot-clé"""
        idx = text.find(keyword)
        if idx == -1:
            return ""
        
        start = max(0, idx - window)
        end = min(len(text), idx + len(keyword) + window)
        
        return text[start:end]