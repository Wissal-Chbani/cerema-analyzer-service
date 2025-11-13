"""
Modèles de données pour les aides à la navigation - Pydantic v2
"""
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    """ObjectId personnalisé pour Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        """Pydantic v2 core schema"""
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
    def __get_pydantic_json_schema__(cls, core_schema, handler):
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

    model_config = ConfigDict(json_encoders={ObjectId: str})


class AideSonoreModel(BaseModel):
    """Modèle pour une aide sonore"""
    type: Optional[str] = None
    rythme: Optional[str] = None

    model_config = ConfigDict(json_encoders={ObjectId: str})


class BaliseRaconModel(BaseModel):
    """Modèle pour une balise Racon"""
    present: bool = False
    lettre_morse: Optional[str] = None

    model_config = ConfigDict(json_encoders={ObjectId: str})


class BoueeExempleModel(BaseModel):
    """Modèle pour un exemple de bouée dans un tableau"""
    nom: Optional[str] = None
    position: Optional[str] = None
    marque: Optional[str] = None
    numero: Optional[str] = None

    model_config = ConfigDict(json_encoders={ObjectId: str})


class DocumentSourceModel(BaseModel):
    """Modèle du document source MongoDB"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    chemin_local: str
    cree_le: Union[datetime, Dict[str, str]]
    mime_type: str
    modifie_le: Union[datetime, Dict[str, str]]
    nom_fichier: str
    taille: int
    ajoute_le: Optional[Union[datetime, Dict[str, str]]] = None
    texte_ocr: Optional[str] = None

    @field_validator('cree_le', 'modifie_le', 'ajoute_le', mode='before')
    @classmethod
    def parse_date(cls, v):
        """Convertit les dates MongoDB en datetime Python"""
        if v is None:
            return None
        
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, dict) and '$date' in v:
            date_str = v['$date']
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        
        return v

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )


class AideNavigationModel(BaseModel):
    """Modèle complet d'une aide à la navigation"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    nom_fichier: str
    chemin_local: str
    cree_le: datetime
    mime_type: str
    taille: int

    # META-DONNÉES D'EXTRACTION
    extraction_status: str = "pending"
    extraction_confidence: float = 0.0
    extraction_method: Optional[str] = None
    extraction_warnings: List[str] = []
    extraction_date: Optional[datetime] = None
    type_document: Optional[str] = None
    nombre_aides: int = 1
    voir_document_original: bool = False
    raison_reference_originale: Optional[str] = None

    # --- IDENTIFICATION ---
    n_sysi: Optional[str] = None
    nom_patrimoine: Optional[str] = None
    nom_bapteme: Optional[str] = None

    # --- LOCALISATION ---
    position: Optional[str] = None

    # --- SUPPORT PHYSIQUE ---
    nature_support: Optional[str] = None

    # --- SIGNALISATION ---
    marque: Optional[str] = None
    marque_jour: Optional[str] = None
    voyant: Optional[bool] = None
    bande_retro_reflechissante: Optional[bool] = None
    reflecteur_radar: Optional[bool] = None

    # --- FEU ---
    feu: Optional[FeuModel] = None

    # --- SONORE / ELECTRONIQUE ---
    aide_sonore: Optional[AideSonoreModel] = None
    ais_aton: Optional[bool] = None
    balise_racon: Optional[BaliseRaconModel] = None

    # --- METIER ---
    date_decision: Optional[datetime] = None

    # Métadonnées d'extraction
    extraction_metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )