"""
Module d'interface graphique pour le jeu Sokoban
Utilise Pygame pour l'affichage et la gestion des événements
"""

import pygame
import sys
from game_logic import SokobanGame

# Initialisation de Pygame
pygame.init()

# Constantes pour l'affichage
CELL_SIZE = 30
GRID_COLOR = (200, 200, 200)
BACKGROUND_COLOR = (240, 240, 240)

# Couleurs pour les différents éléments
COLORS = {
    -1: (100, 100, 100),    # Mur - Gris foncé
    0: (255, 255, 255),     # Espace vide - Blanc
    1: (255, 255, 0),       # Cible - Jaune
    2: (139, 69, 19),       # Caisse - Marron
    3: (0, 0, 255),         # Joueur - Bleu
    4: (255, 165, 0),       # Caisse sur cible - Orange
    5: (0, 255, 0)          # Joueur sur cible - Vert
}

# Caractères pour l'affichage textuel (debug)
SYMBOLS = {
    -1: '█',  # Mur
    0: ' ',   # Espace vide
    1: '.',   # Cible
    2: '$',   # Caisse
    3: '@',   # Joueur
    4: '*',   # Caisse sur cible
    5: '+'    # Joueur sur cible
}

class SokobanRenderer:
    """
    Classe responsable du rendu graphique du jeu Sokoban
    """
    
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 20)
        self.title_font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 16)
        
        # Charger et redimensionner l'image du mur
        self.wall_image = pygame.image.load("assets/wall.png")
        self.wall_image = pygame.transform.scale(self.wall_image, (CELL_SIZE, CELL_SIZE))
        
        # Calculer la taille
        title_text = self.title_font.render("Sokoban", True, (0, 0, 0))
        title_rect = title_text.get_rect(center=(self.window_width // 2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Afficher les instructions
        start_y = self.window_height - 150
        for i, instruction in enumerate(instructions):
            text_rect = text.get_rect(center=(self.window_width // 2, start_y + i * 30))
            self.screen.blit(text, text_rect)
        
        # Définir les dimensions du panneau AI
        self.ai_panel_x = self.window_width - 42  # Position à gauche de la bordure droite
        self.ai_panel_width = 400  # Largeur ajustée pour rester visible
        self.ai_panel_height = self.window_height - 40  # Hauteur adaptée

