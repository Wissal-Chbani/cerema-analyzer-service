"""
Adaptateur pour extraire le texte des PDFs
"""
import logging
from pathlib import Path
from typing import Optional
import PyPDF2
import pdfplumber

logger = logging.getLogger(__name__)


class OCRAdapter:
    """Adapte différentes méthodes d'extraction de texte depuis PDF"""
    
    def __init__(self):
        self.logger = logger
    
    def extract_text_from_pdf(self, file_path: str) -> Optional[str]:
        """
        Extrait le texte d'un PDF en utilisant plusieurs méthodes
        
        Args:
            file_path: Chemin vers le fichier PDF
            
        Returns:
            Texte extrait ou None si échec
        """
        path = Path(file_path)
        
        if not path.exists():
            self.logger.error(f"Fichier introuvable: {file_path}")
            return None
        
        if not path.suffix.lower() == '.pdf':
            self.logger.warning(f"Le fichier n'est pas un PDF: {file_path}")
            return None
        
        # Essayer d'abord pdfplumber (meilleure extraction)
        text = self._extract_with_pdfplumber(file_path)
        
        # Si échec, essayer PyPDF2
        if not text or len(text.strip()) < 50:
            self.logger.info("pdfplumber a échoué, tentative avec PyPDF2")
            text = self._extract_with_pypdf2(file_path)
        
        if text:
            self.logger.info(f"Texte extrait: {len(text)} caractères")
            return text
        else:
            self.logger.error(f"Échec de l'extraction pour: {file_path}")
            return None
    
    def _extract_with_pdfplumber(self, file_path: str) -> Optional[str]:
        """Extrait le texte avec pdfplumber"""
        try:
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                return '\n\n'.join(text_parts)
        except Exception as e:
            self.logger.error(f"Erreur pdfplumber: {e}")
            return None
    
    def _extract_with_pypdf2(self, file_path: str) -> Optional[str]:
        """Extrait le texte avec PyPDF2"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                return '\n\n'.join(text_parts)
        except Exception as e:
            self.logger.error(f"Erreur PyPDF2: {e}")
            return None
    
    def extract_metadata(self, file_path: str) -> dict:
        """Extrait les métadonnées d'un PDF"""
        metadata = {}
        
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                if pdf_reader.metadata:
                    metadata = {
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'creator': pdf_reader.metadata.get('/Creator', ''),
                        'producer': pdf_reader.metadata.get('/Producer', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'num_pages': len(pdf_reader.pages)
                    }
        except Exception as e:
            self.logger.error(f"Erreur extraction métadonnées: {e}")
        
        return metadata
    
    def is_pdf_scanned(self, file_path: str) -> bool:
        """
        Détermine si un PDF est scanné (image) ou natif (texte)
        
        Returns:
            True si le PDF est probablement scanné
        """
        try:
            text = self._extract_with_pypdf2(file_path)
            
            # Si très peu de texte extrait, c'est probablement un scan
            if not text or len(text.strip()) < 100:
                return True
            
            # Vérifier le ratio texte/pages
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                num_pages = len(pdf_reader.pages)
                
                # Moins de 50 caractères par page = probablement scanné
                chars_per_page = len(text) / num_pages if num_pages > 0 else 0
                return chars_per_page < 50
        
        except Exception as e:
            self.logger.error(f"Erreur détection scan: {e}")
            return False