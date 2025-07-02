"""
Module d'interface graphique pour le jeu Sokoban
Utilise Pygame pour l'affichage et la gestion des événements
"""

import pygame
import sys
from game_logic import SokobanGame

# Initialisation de Pygame
pygame.init()
WALL_IMAGE = pygame.image.load("assets/wall.png")  # Mets le chemin correct
WALL_IMAGE = pygame.transform.scale(WALL_IMAGE, (CELL_SIZE, CELL_SIZE))

# Constantes pour l'affichage
CELL_SIZE = 40
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
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        
        # Calculer la taille de la fenêtre
        self.window_width = 800
        self.window_height = 600
        
        # Zone de jeu
        self.game_area_x = 50
        self.game_area_y = 80
        
        # Initialiser l'écran
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Sokoban Game")
        
        # Horloge pour contrôler le framerate
        self.clock = pygame.time.Clock()
    
    def draw_cell(self, x, y, cell_value):
        """
        Dessine une cellule de la grille
        
        Args:
            x, y: Position en pixels
            cell_value: Valeur de la cellule (-1 à 5)
        """
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        
        if cell_value == -1:
            # Utilise l'image du mur
            self.screen.blit(WALL_IMAGE, rect)
        else:
            # Dessiner le fond de la cellule
            if cell_value in COLORS:
                pygame.draw.rect(self.screen, COLORS[cell_value], rect)
            else:
                pygame.draw.rect(self.screen, COLORS[0], rect)  # Blanc par défaut
            
            # Dessiner la bordure
            pygame.draw.rect(self.screen, GRID_COLOR, rect, 1)
            
            # Dessiner des symboles pour une meilleure lisibilité
            if cell_value in SYMBOLS and cell_value != 0:
                symbol = SYMBOLS[cell_value]
                text_color = (255, 255, 255) if cell_value == -1 else (0, 0, 0)
                
                # Ajuster la taille de police pour les symboles
                symbol_font = pygame.font.Font(None, 32)
                text_surface = symbol_font.render(symbol, True, text_color)
                text_rect = text_surface.get_rect(center=(x + CELL_SIZE//2, y + CELL_SIZE//2))
                self.screen.blit(text_surface, text_rect)
    
    def draw_grid(self, grid):
        """
        Dessine la grille de jeu complète
        
        Args:
            grid: Matrice représentant l'état du jeu
        """
        if not grid:
            return
        
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        
        for row in range(rows):
            for col in range(cols):
                x = self.game_area_x + col * CELL_SIZE
                y = self.game_area_y + row * CELL_SIZE
                self.draw_cell(x, y, grid[row][col])
    
    def draw_ui(self, game_state):
        """
        Dessine l'interface utilisateur (score, niveau, etc.)
        
        Args:
            game_state: État actuel du jeu
        """
        if not game_state:
            return
        
        # Titre
        title_text = self.title_font.render("SOKOBAN", True, (0, 0, 0))
        self.screen.blit(title_text, (10, 10))
        
        # Informations du jeu
        level_text = self.font.render(f"Niveau: {game_state['level']}", True, (0, 0, 0))
        moves_text = self.font.render(f"Mouvements: {game_state['moves']}", True, (0, 0, 0))
        score_text = self.font.render(f"Score: {game_state['score']}", True, (0, 0, 0))
        
        self.screen.blit(level_text, (10, 50))
        self.screen.blit(moves_text, (150, 50))
        self.screen.blit(score_text, (300, 50))
        
        # Message de victoire
        if game_state['is_complete']:
            victory_text = self.title_font.render("NIVEAU TERMINÉ!", True, (0, 255, 0))
            text_rect = victory_text.get_rect(center=(self.window_width//2, self.window_height - 50))
            self.screen.blit(victory_text, text_rect)
            
            continue_text = self.font.render("Appuyez sur ESPACE pour continuer", True, (0, 0, 0))
            continue_rect = continue_text.get_rect(center=(self.window_width//2, self.window_height - 20))
            self.screen.blit(continue_text, continue_rect)
    
    def draw_instructions(self):
        """Dessine les instructions de jeu"""
        instructions = [
            "Instructions:",
            "Flèches: Déplacer",
            "U: Annuler",
            "R: Recommencer",
            "ESC: Quitter"
        ]
        
        start_y = 150
        for i, instruction in enumerate(instructions):
            color = (0, 0, 0) if i == 0 else (100, 100, 100)
            text = self.font.render(instruction, True, color)
            self.screen.blit(text, (self.window_width - 150, start_y + i * 25))
    
    def render(self, game_state):
        """
        Effectue le rendu complet de l'écran
        
        Args:
            game_state: État actuel du jeu
        """
        # Effacer l'écran
        self.screen.fill(BACKGROUND_COLOR)
        
        # Dessiner les éléments
        if game_state:
            self.draw_grid(game_state['grid'])
            self.draw_ui(game_state)
        
        self.draw_instructions()
        
        # Mettre à jour l'affichage
        pygame.display.flip()
        self.clock.tick(60)  # 60 FPS


class SokobanGameUI:
    """
    Classe principale pour l'interface utilisateur du jeu Sokoban
    Gère les événements et coordonne le rendu avec la logique du jeu
    """
    
    def __init__(self):
        self.game = SokobanGame()
        self.renderer = SokobanRenderer(self.game)
        self.running = True
        
        # Mapping des touches
        self.key_mapping = {
            pygame.K_UP: 'UP',
            pygame.K_DOWN: 'DOWN',
            pygame.K_LEFT: 'LEFT',
            pygame.K_RIGHT: 'RIGHT'
        }
    
    def handle_events(self):
        """Gère les événements Pygame"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                elif event.key in self.key_mapping:
                    # Mouvement du joueur
                    direction = self.key_mapping[event.key]
                    result = self.game.move_player(direction)
                    
                    if result == 'LEVEL_COMPLETE':
                        print(f"Niveau {self.game.current_level + 1} terminé!")
                
                elif event.key == pygame.K_u:
                    # Annuler le dernier mouvement
                    self.game.undo_move()
                
                elif event.key == pygame.K_r:
                    # Recommencer le niveau
                    self.game.reset_level()
                
                elif event.key == pygame.K_SPACE:
                    # Passer au niveau suivant (si le niveau actuel est terminé)
                    game_state = self.game.get_game_state()
                    if game_state and game_state['is_complete']:
                        if self.game.has_next_level():
                            self.game.next_level()
                        else:
                            print("Tous les niveaux terminés!")
    
    def run(self):
        """Boucle principale du jeu"""
        # Démarrer le premier niveau
        self.game.start_level(0)
        
        print("Jeu Sokoban démarré!")
        print("Utilisez les flèches pour vous déplacer")
        print("U: Annuler, R: Recommencer, ESC: Quitter")
        
        while self.running:
            self.handle_events()
            
            # Obtenir l'état actuel du jeu
            game_state = self.game.get_game_state()
            
            # Effectuer le rendu
            self.renderer.render(game_state)
        
        # Nettoyage
        pygame.quit()
        sys.exit()


# Point d'entrée principal
if __name__ == "__main__":
    try:
        game_ui = SokobanGameUI()
        game_ui.run()
    except KeyboardInterrupt:
        print("\nJeu interrompu par l'utilisateur")
        pygame.quit()
        sys.exit()
    except Exception as e:
        print(f"Erreur: {e}")
        pygame.quit()
        sys.exit()

