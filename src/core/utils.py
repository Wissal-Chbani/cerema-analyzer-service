"""
Fonctions utilitaires générales
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Configure le système de logging
    
    Args:
        log_level: Niveau de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Chemin vers le fichier de log (optionnel)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def calculate_confidence_score(extracted_data: Dict[str, Any], doc_type: str) -> float:
    """
    Calcule un score de confiance pour les données extraites
    
    Args:
        extracted_data: Données extraites
        doc_type: Type de document
        
    Returns:
        Score de confiance entre 0 et 1
    """
    # Champs critiques
    critical_fields = ['n_sysi', 'nom_patrimoine', 'nom_bapteme', 'nature_support', 'position']
    
    # Champs importants
    important_fields = ['marque', 'fonction', 'reflecteur_radar']
    
    # Compter les champs remplis
    critical_filled = sum(1 for field in critical_fields if extracted_data.get(field))
    important_filled = sum(1 for field in important_fields if extracted_data.get(field))
    
    # Score de base selon le type de document
    base_score = {
        'fiche_individuelle': 0.9,
        'tableau_simple': 0.8,
        'tableau_complexe': 0.6,
        'arrete_prefectoral': 0.7,
        'courrier_administratif': 0.5,
        'catalogue_produit': 0.1,
        'autre': 0.5
    }.get(doc_type, 0.5)
    
    # Ajuster selon les champs remplis
    critical_ratio = critical_filled / len(critical_fields)
    important_ratio = important_filled / len(important_fields) if important_fields else 0
    
    # Score final
    final_score = base_score * (0.7 * critical_ratio + 0.3 * important_ratio)
    
    return round(min(final_score, 1.0), 2)


def merge_extracted_data(base_data: Dict[str, Any], 
                        new_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fusionne deux dictionnaires de données extraites
    
    Args:
        base_data: Données de base
        new_data: Nouvelles données à fusionner
        
    Returns:
        Données fusionnées (priorité aux données de base)
    """
    merged = base_data.copy()
    
    for key, value in new_data.items():
        # Ne remplacer que si le champ n'existe pas ou est None
        if key not in merged or merged[key] is None:
            merged[key] = value
        # Pour les dictionnaires, fusionner récursivement
        elif isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key] = {**merged[key], **value}
        # Pour les listes, combiner
        elif isinstance(value, list) and isinstance(merged[key], list):
            merged[key] = merged[key] + [v for v in value if v not in merged[key]]
    
    return merged


def format_extraction_metadata(extraction_time: float, 
                               confidence: float,
                               methods_used: list,
                               warnings: list = None) -> Dict[str, Any]:
    """
    Formate les métadonnées d'extraction
    
    Args:
        extraction_time: Temps d'extraction en secondes
        confidence: Score de confiance
        methods_used: Liste des méthodes utilisées
        warnings: Liste des avertissements
        
    Returns:
        Dictionnaire de métadonnées
    """
    return {
        'extraction_date': datetime.now(),
        'extraction_time_seconds': round(extraction_time, 2),
        'confidence_score': confidence,
        'methods_used': methods_used,
        'warnings': warnings or [],
        'version': '1.0.0'
    }


def sanitize_filename(filename: str) -> str:
    """
    Nettoie un nom de fichier
    
    Args:
        filename: Nom de fichier à nettoyer
        
    Returns:
        Nom de fichier nettoyé
    """
    # Supprimer les caractères non autorisés
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    return filename.strip()


def create_extraction_warning(message: str, field: str = None) -> str:
    """
    Crée un message d'avertissement formaté
    
    Args:
        message: Message d'avertissement
        field: Champ concerné (optionnel)
        
    Returns:
        Message formaté
    """
    if field:
        return f"[{field}] {message}"
    return message


def validate_coordinates(position: str) -> bool:
    """
    Valide des coordonnées géographiques
    
    Args:
        position: Chaîne de coordonnées
        
    Returns:
        True si les coordonnées semblent valides
    """
    if not position:
        return False
    
    # Vérifier la présence de N/S et E/W/O
    has_lat = any(c in position.upper() for c in ['N', 'S'])
    has_lon = any(c in position.upper() for c in ['E', 'W', 'O'])
    
    # Vérifier la présence de chiffres
    import re
    has_numbers = bool(re.search(r'\d', position))
    
    return has_lat and has_lon and has_numbers


def extract_department_from_sysi(n_sysi: str) -> Optional[str]:
    """
    Extrait le numéro de département du numéro SYSSI
    
    Args:
        n_sysi: Numéro SYSSI
        
    Returns:
        Numéro de département ou None
    """
    if not n_sysi or len(n_sysi) < 2:
        return None
    
    # Les 2 ou 3 premiers chiffres
    if len(n_sysi) >= 3 and n_sysi[0] != '0':
        return n_sysi[:3] if n_sysi[:3].isdigit() else n_sysi[:2]
    
    return n_sysi[:2]