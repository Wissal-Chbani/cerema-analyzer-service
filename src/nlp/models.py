"""
Modèles de données pour les aides à la navigation
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from bson import ObjectId
from pydantic import BaseModel, Field, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue


class PyObjectId(ObjectId):
    """ObjectId personnalisé pour Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """Pydantic v2 schema"""
        from pydantic_core import core_schema
        
        # Accepter à la fois str ET ObjectId
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.no_info_after_validator_function(
                cls.validate,
                core_schema.str_schema(),
            )
        ])
    
    @classmethod
    def validate(cls, v):
        """Valide et convertit en ObjectId"""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if not ObjectId.is_valid(v):
                raise ValueError(f"Invalid ObjectId: {v}")
            return ObjectId(v)
        raise ValueError(f"Invalid type for ObjectId: {type(v)}")
    
    @classmethod
    def __get_pydantic_json_schema__(cls, core_schema, handler: GetJsonSchemaHandler) -> JsonSchemaValue:
        """Schema JSON pour la documentation"""
        return {"type": "string", "format": "objectid"}


class FeuModel(BaseModel):
    """Modèle pour les caractéristiques d'un feu"""
    couleur: Optional[str] = None
    rythme: Optional[str] = None
    portee_nominale: Optional[int] = None
    secteurs: Optional[str] = None
    type_signal: Optional[str] = None
    rythme_detaille: Optional[str] = None

    model_config = {"json_encoders": {ObjectId: str}}


class AideSonoreModel(BaseModel):
    """Modèle pour une aide sonore"""
    type: Optional[str] = None
    rythme: Optional[str] = None

    model_config = {"json_encoders": {ObjectId: str}}


class BaliseRaconModel(BaseModel):
    """Modèle pour une balise Racon"""
    present: bool = False
    lettre_morse: Optional[str] = None

    model_config = {"json_encoders": {ObjectId: str}}


class BoueeExempleModel(BaseModel):
    """Modèle pour un exemple de bouée dans un tableau"""
    nom: Optional[str] = None
    position: Optional[str] = None
    marque: Optional[str] = None
    numero: Optional[str] = None

    model_config = {"json_encoders": {ObjectId: str}}


class AideNavigationModel(BaseModel):
    """Modèle complet d'une aide à la navigation"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    nom_fichier: str
    chemin_local: str
    cree_le: datetime
    mime_type: str
    taille: int

    # META-DONNÉES D'EXTRACTION
    extraction_status: str = "pending"  # success | partial | failed | skipped
    extraction_confidence: float = 0.0
    extraction_method: Optional[str] = None
    extraction_warnings: List[str] = []
    extraction_date: Optional[datetime] = None

    # TYPE DE DOCUMENT
    type_document: Optional[str] = None
    nombre_aides: int = 1
    voir_document_original: bool = False
    raison_reference_originale: Optional[str] = None

    # Identification
    n_sysi: Optional[str] = None
    nom_patrimoine: Optional[str] = None
    nom_bapteme: Optional[str] = None

    # Localisation
    position: Optional[str] = None
    systeme_geodesique: Optional[str] = None
    zone: Optional[str] = None

    # Support physique
    nature_support: Optional[str] = None
    hauteur_support: Optional[float] = None
    altitude_base: Optional[float] = None

    # Signalisation
    marque: Optional[str] = None
    caractere: Optional[str] = None  # Alias pour marque
    fonction: Optional[str] = None
    classement: Optional[str] = None
    validite: Optional[str] = None
    marque_jour: Optional[str] = None
    voyant: Optional[bool] = None
    bande_retro_reflechissante: Optional[bool] = None
    reflecteur_radar: Optional[bool] = None

    # Feu
    feu: Optional[FeuModel] = None

    # Sonore / Électronique
    aide_sonore: Optional[AideSonoreModel] = None
    ais_aton: Optional[bool] = None
    balise_racon: Optional[BaliseRaconModel] = None

    # Métier
    date_decision: Optional[datetime] = None
    date_arrete: Optional[datetime] = None
    reference_arrete: Optional[str] = None

    # Mode d'accès
    mode_acces: Optional[str] = None

    # Pour les tableaux complexes
    exemples_bouees: Optional[List[BoueeExempleModel]] = None

    # Métadonnées d'extraction
    extraction_metadata: Optional[Dict[str, Any]] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }


class DocumentSourceModel(BaseModel):
    """Modèle du document source MongoDB"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    chemin_local: str
    cree_le: datetime
    mime_type: str
    modifie_le: datetime
    nom_fichier: str
    taille: int
    ajoute_le: Optional[datetime] = None
    texte_ocr: Optional[str] = None  # Si le texte OCR est stocké

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
        "json_encoders": {ObjectId: str},
    }
