"""
Lecteur de fichiers texte
"""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TextReader:
    """Lit le contenu des fichiers texte"""
    
    def __init__(self):
        self.logger = logger
    
    def read_text_file(self, file_path: str) -> Optional[str]:
        """
        Lit un fichier texte
        
        Args:
            file_path: Chemin vers le fichier TXT
            
        Returns:
            Contenu du fichier ou None si échec
        """
        path = Path(file_path)
        
        if not path.exists():
            self.logger.error(f"Fichier introuvable: {file_path}")
            return None
        
        try:
            # Essayer différents encodages courants
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    
                    self.logger.info(f"Fichier lu avec {encoding}: {len(text)} caractères")
                    return text
                    
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    self.logger.debug(f"Erreur avec encodage {encoding}: {e}")
                    continue
            
            # Si aucun encodage ne fonctionne, essayer en mode binaire et décoder avec erreurs
            self.logger.warning(f"Encodages standards échoués, tentative avec gestion d'erreurs")
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            return text
            
        except Exception as e:
            self.logger.error(f"Erreur lecture fichier {file_path}: {e}")
            return None
    
    def get_file_info(self, file_path: str) -> dict:
        """
        Récupère les informations sur le fichier
        
        Args:
            file_path: Chemin vers le fichier
            
        Returns:
            Dictionnaire avec les infos du fichier
        """
        path = Path(file_path)
        
        if not path.exists():
            return {
                'existe': False,
                'erreur': 'Fichier introuvable'
            }
        
        try:
            stat = path.stat()
            return {
                'nom': path.name,
                'taille': stat.st_size,
                'extension': path.suffix,
                'existe': True,
                'est_fichier': path.is_file(),
                'parent': str(path.parent)
            }
        except Exception as e:
            self.logger.error(f"Erreur récupération infos fichier: {e}")
            return {
                'existe': False,
                'erreur': str(e)
            }
    
    def list_files_in_directory(self, directory: str, extension: str = '.txt') -> list:
        """
        Liste les fichiers dans un répertoire
        
        Args:
            directory: Chemin du répertoire
            extension: Extension des fichiers à lister
            
        Returns:
            Liste des chemins de fichiers
        """
        path = Path(directory)
        
        if not path.exists() or not path.is_dir():
            self.logger.error(f"Répertoire introuvable: {directory}")
            return []
        
        try:
            files = list(path.glob(f'*{extension}'))
            self.logger.info(f"{len(files)} fichiers {extension} trouvés dans {directory}")
            return [str(f) for f in files]
        except Exception as e:
            self.logger.error(f"Erreur listage fichiers: {e}")
            return []