# -*- coding: utf-8 -*-
"""
core/utils.py
--------------
Outils utilitaires pour le moteur d'analyse.

Ce module contient des fonctions génériques de nettoyage et de normalisation du texte
extrait via OCR, indépendantes du contexte métier.

Fonctions principales :
- nettoyer_texte : supprime les caractères spéciaux, accents et espaces multiples
- normaliser_texte : met le texte en minuscules, enlève les accents, etc.

Ce fichier constitue la première étape du pipeline d'analyse NLP/ML.

Auteur : Wissal Chbani
Date : Octobre 2025
"""

import re
import unicodedata