"""
Version complète du jeu Sokoban avec toutes les fonctionnalités
Intègre la logique de base, l'interface graphique et les fonctionnalités avancées
"""

import pygame
import sys
import time
from game_logic import SokobanGame
from game_features import SokobanDatabase, SokobanAudio, SokobanLevels

# Initialisation de Pygame
pygame.init()

# Constantes pour l'affichage
CELL_SIZE = 40
GRID_COLOR = (200, 200, 200)
BACKGROUND_COLOR = (240, 240, 240)
MENU_COLOR = (220, 220, 220)
BUTTON_COLOR = (180, 180, 180)
BUTTON_HOVER_COLOR = (160, 160, 160)
TEXT_COLOR = (0, 0, 0)

# Couleurs pour les différents éléments


class Button:
    """Classe pour créer des boutons cliquables"""
    
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.hovered = False
    
    def draw(self, screen):
        """Dessine le bouton"""
        color = BUTTON_HOVER_COLOR if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, TEXT_COLOR, self.rect, 2)
        
        # Texte centré
        text_surface = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        """Gère les événements du bouton"""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class SokobanCompleteGame:
    """
    Version complète du jeu Sokoban avec toutes les fonctionnalités
    """
    
    def __init__(self):
        # Initialisation des composants
        self.database = SokobanDatabase()
        self.audio = SokobanAudio()
        
        # Charger les niveaux étendus
        extended_levels = SokobanLevels.get_extended_levels()
        self.game = SokobanGame()
        self.game.levels = extended_levels
        self.level_info = SokobanLevels.get_level_info()
        
        # Interface graphique
        self.window_width = 900
        self.window_height = 700
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Sokoban - Jeu Complet")
        
        # Polices
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 20)
        
        # État du jeu
        self.state = "MENU"  # MENU, GAME, SCORES, SETTINGS
        self.player_name = "Joueur"
        self.start_time = None
        self.clock = pygame.time.Clock()
        
        # Zone de jeu
        self.game_area_x = 50
        self.game_area_y = 120
        
        # Boutons
        self.create_buttons()
        
        # Mapping des touches
        self.key_mapping = {
            pygame.K_UP: 'UP',
            pygame.K_DOWN: 'DOWN',
            pygame.K_LEFT: 'LEFT',
            pygame.K_RIGHT: 'RIGHT'
        }
        
        # Démarrer la musique
        self.audio.play_music("menu")

        # Charger les assets
        self.assets = {}
        self.load_assets()
    
    def create_buttons(self):
        """Crée les boutons de l'interface"""
        # Boutons du menu principal
        self.menu_buttons = [
            Button(350, 200, 200, 50, "Nouveau Jeu", self.font),
            Button(350, 270, 200, 50, "Scores", self.font),
            Button(350, 340, 200, 50, "Paramètres", self.font),
            Button(350, 410, 200, 50, "Quitter", self.font)
        ]
        
        # Boutons en jeu
        self.game_buttons = [
            Button(650, 150, 120, 40, "Annuler (U)", self.small_font),
            Button(650, 200, 120, 40, "Recommencer (R)", self.small_font),
            Button(650, 250, 120, 40, "Menu (M)", self.small_font),
            Button(650, 300, 120, 40, "Scores", self.small_font)
        ]
        
        # Boutons des scores
        self.score_buttons = [
            Button(350, 600, 200, 50, "Retour", self.font)
        ]
        
        # Boutons des paramètres
        self.settings_buttons = [
            Button(250, 200, 200, 40, "Sons: ON", self.font),
            Button(250, 250, 200, 40, "Musique: ON", self.font),
            Button(250, 300, 200, 40, "Volume: 70%", self.font),
            Button(350, 600, 200, 50, "Retour", self.font)
        ]
    
    def draw_cell(self, x, y, cell_value):
        """Dessine une cellule de la grille"""
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        
        # Dessiner le fond de la cellule
        if cell_value in self.assets:
            self.screen.blit(self.assets[cell_value], rect)
        else:
            pygame.draw.rect(self.screen, BACKGROUND_COLOR, rect) # Fallback pour les valeurs inconnues
    
    def draw_grid(self, grid):
        """Dessine la grille de jeu complète"""
        if not grid:
            return
        
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        
        for row in range(rows):
            for col in range(cols):
                x = self.game_area_x + col * CELL_SIZE
                y = self.game_area_y + row * CELL_SIZE
                self.draw_cell(x, y, grid[row][col])
    
    def draw_menu(self):
        """Dessine le menu principal"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Titre
        title_text = self.title_font.render("SOKOBAN", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(self.window_width//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Sous-titre
        subtitle_text = self.font.render("Jeu de puzzle classique", True, TEXT_COLOR)
        subtitle_rect = subtitle_text.get_rect(center=(self.window_width//2, 140))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Boutons
        for button in self.menu_buttons:
            button.draw(self.screen)
    
    def draw_game(self):
        """Dessine l'écran de jeu"""
        self.screen.fill(BACKGROUND_COLOR)
        
        game_state = self.game.get_game_state()
        if not game_state:
            return
        
        # Titre
        title_text = self.title_font.render("SOKOBAN", True, TEXT_COLOR)
        self.screen.blit(title_text, (10, 10))
        
        # Informations du niveau
        level_info = self.level_info[self.game.current_level] if self.game.current_level < len(self.level_info) else {}
        level_name = level_info.get('name', f'Niveau {game_state["level"]}')
        difficulty = level_info.get('difficulty', 'Inconnu')
        
        level_text = self.font.render(f"{level_name} - {difficulty}", True, TEXT_COLOR)
        self.screen.blit(level_text, (10, 50))
        
        # Statistiques
        moves_text = self.font.render(f"Mouvements: {game_state['moves']}", True, TEXT_COLOR)
        score_text = self.font.render(f"Score: {game_state['score']}", True, TEXT_COLOR)
        
        # Temps écoulé
        elapsed_time = 0
        if self.start_time:
            elapsed_time = int(time.time() - self.start_time)
        time_text = self.font.render(f"Temps: {elapsed_time}s", True, TEXT_COLOR)
        
        self.screen.blit(moves_text, (200, 50))
        self.screen.blit(score_text, (350, 50))
        self.screen.blit(time_text, (500, 50))
        
        # Grille de jeu
        self.draw_grid(game_state['grid'])
        
        # Boutons
        for button in self.game_buttons:
            button.draw(self.screen)
        
        # Instructions
        instructions = [
            "Flèches: Déplacer",
            "But: Pousser toutes",
            "les caisses ($) sur",
            "les cibles (.)",
            "",
            "Caisse sur cible: *",
            "Joueur sur cible: +"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, TEXT_COLOR)
            self.screen.blit(text, (650, 350 + i * 20))
        
        # Message de victoire
        if game_state['is_complete']:
            victory_text = self.title_font.render("NIVEAU TERMINÉ!", True, (0, 255, 0))
            text_rect = victory_text.get_rect(center=(self.window_width//2, self.window_height - 100))
            self.screen.blit(victory_text, text_rect)
            
            continue_text = self.font.render("Appuyez sur ESPACE pour continuer", True, TEXT_COLOR)
            continue_rect = continue_text.get_rect(center=(self.window_width//2, self.window_height - 70))
            self.screen.blit(continue_text, continue_rect)
    
    def draw_scores(self):
        """Dessine l'écran des scores"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Titre
        title_text = self.title_font.render("MEILLEURS SCORES", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(self.window_width//2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Récupérer les scores
        best_scores = self.database.get_best_scores(limit=10)
        
        # En-têtes
        headers = ["Rang", "Joueur", "Niveau", "Score", "Mouvements", "Temps"]
        header_y = 120
        header_positions = [50, 150, 250, 350, 450, 550]
        
        for i, header in enumerate(headers):
            text = self.font.render(header, True, TEXT_COLOR)
            self.screen.blit(text, (header_positions[i], header_y))
        
        # Ligne de séparation
        pygame.draw.line(self.screen, TEXT_COLOR, (50, header_y + 30), (650, header_y + 30), 2)
        
        # Scores
        for i, score in enumerate(best_scores[:10]):
            y = header_y + 60 + i * 30
            
            rank_text = self.font.render(str(i + 1), True, TEXT_COLOR)
            player_text = self.font.render(score['player_name'][:10], True, TEXT_COLOR)
            level_text = self.font.render(str(score['level']), True, TEXT_COLOR)
            score_text = self.font.render(str(score['score']), True, TEXT_COLOR)
            moves_text = self.font.render(str(score['moves']), True, TEXT_COLOR)
            time_text = self.font.render(f"{score['time_seconds']}s", True, TEXT_COLOR)
            
            texts = [rank_text, player_text, level_text, score_text, moves_text, time_text]
            
            for j, text in enumerate(texts):
                self.screen.blit(text, (header_positions[j], y))
        
        # Bouton retour
        for button in self.score_buttons:
            button.draw(self.screen)
    
    def draw_settings(self):
        """Dessine l'écran des paramètres"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Titre
        title_text = self.title_font.render("PARAMÈTRES", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(self.window_width//2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Mettre à jour les textes des boutons
        self.settings_buttons[0].text = f"Sons: {'ON' if self.audio.sounds_enabled else 'OFF'}"
        self.settings_buttons[1].text = f"Musique: {'ON' if self.audio.music_enabled else 'OFF'}"
        self.settings_buttons[2].text = f"Volume: {int(self.audio.volume * 100)}%"
        
        # Boutons
        for button in self.settings_buttons:
            button.draw(self.screen)
        
        # Instructions
        instructions = [
            "Cliquez sur les boutons pour modifier les paramètres",
            "Les paramètres sont sauvegardés automatiquement"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(self.window_width//2, 400 + i * 30))
            self.screen.blit(text, text_rect)
    
    def handle_menu_events(self, event):
        """Gère les événements du menu"""
        for i, button in enumerate(self.menu_buttons):
            if button.handle_event(event):
                self.audio.play_sound('menu_click')
                
                if i == 0:  # Nouveau Jeu
                    self.state = "GAME"
                    self.game.start_level(0)
                    self.start_time = time.time()
                    self.audio.play_music("game")
                elif i == 1:  # Scores
                    self.state = "SCORES"
                elif i == 2:  # Paramètres
                    self.state = "SETTINGS"
                elif i == 3:  # Quitter
                    return False
        return True
    
    def handle_game_events(self, event):
        """Gère les événements du jeu"""
        if event.type == pygame.KEYDOWN:
            if event.key in self.key_mapping:
                direction = self.key_mapping[event.key]
                result = self.game.move_player(direction)
                
                if result == 'LEVEL_COMPLETE':
                    self.audio.play_sound('level_complete')
                    
                    # Sauvegarder le score
                    elapsed_time = int(time.time() - self.start_time) if self.start_time else 0
                    game_state = self.game.get_game_state()
                    self.database.save_score(
                        self.player_name,
                        game_state['level'],
                        game_state['moves'],
                        elapsed_time,
                        game_state['score']
                    )
                elif result:
                    self.audio.play_sound('move')
            
            elif event.key == pygame.K_u:
                if self.game.undo_move():
                    self.audio.play_sound('undo')
            
            elif event.key == pygame.K_r:
                self.game.reset_level()
                self.start_time = time.time()
                self.audio.play_sound('reset')
            
            elif event.key == pygame.K_m:
                self.state = "MENU"
                self.audio.play_music("menu")
            
            elif event.key == pygame.K_SPACE:
                game_state = self.game.get_game_state()
                if game_state and game_state['is_complete']:
                    pygame.time.wait(500)  # Petite pause pour voir la victoire
                    if self.game.has_next_level():
                        self.game.next_level()
                        self.start_time = time.time()
                    else:
                        self.state = "MENU"
                        self.audio.play_music("menu")
        
        # Boutons
        for i, button in enumerate(self.game_buttons):
            if button.handle_event(event):
                self.audio.play_sound('menu_click')
                
                if i == 0:  # Annuler
                    if self.game.undo_move():
                        self.audio.play_sound('undo')
                elif i == 1:  # Recommencer
                    self.game.reset_level()
                    self.start_time = time.time()
                    self.audio.play_sound('reset')
                elif i == 2:  # Menu
                    self.state = "MENU"
                    self.audio.play_music("menu")
                elif i == 3:  # Scores
                    self.state = "SCORES"
        
        return True
    
    def handle_scores_events(self, event):
        """Gère les événements de l'écran des scores"""
        for button in self.score_buttons:
            if button.handle_event(event):
                self.audio.play_sound('menu_click')
                self.state = "MENU"
        return True
    
    def handle_settings_events(self, event):
        """Gère les événements de l'écran des paramètres"""
        for i, button in enumerate(self.settings_buttons):
            if button.handle_event(event):
                self.audio.play_sound('menu_click')
                
                if i == 0:  # Sons
                    self.audio.toggle_sounds()
                elif i == 1:  # Musique
                    self.audio.toggle_music()
                elif i == 2:  # Volume
                    new_volume = (self.audio.volume + 0.1) % 1.1
                    if new_volume > 1.0:
                        new_volume = 0.1
                    self.audio.set_volume(new_volume)
                elif i == 3:  # Retour
                    self.state = "MENU"
        return True
    
    def run(self):
        """Boucle principale du jeu"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "GAME":
                            self.state = "MENU"
                            self.audio.play_music("menu")
                        else:
                            running = False
                
                # Gérer les événements selon l'état
                if self.state == "MENU":
                    running = self.handle_menu_events(event)
                elif self.state == "GAME":
                    running = self.handle_game_events(event)
                elif self.state == "SCORES":
                    running = self.handle_scores_events(event)
                elif self.state == "SETTINGS":
                    running = self.handle_settings_events(event)
            
            # Dessiner selon l'état
            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "GAME":
                self.draw_game()
            elif self.state == "SCORES":
                self.draw_scores()
            elif self.state == "SETTINGS":
                self.draw_settings()
            
            if self.state == "GAME":
                game_state = self.game.get_game_state()
                if game_state and game_state['is_complete']:
                    pygame.time.wait(500)
                    if self.game.has_next_level():
                        self.game.next_level()
                        self.start_time = time.time()
                    else:
                        self.state = "MENU"
                        self.audio.play_music("menu")
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # Nettoyage
        pygame.quit()
        sys.exit()

    def load_assets(self):
        """Charge les images nécessaires pour le jeu"""
        self.assets[-1] = pygame.image.load("assets/wall.png")
        self.assets[-1] = pygame.transform.scale(self.assets[-1], (CELL_SIZE, CELL_SIZE))
        self.assets[0] = pygame.image.load("assets/floor.png")
        self.assets[0] = pygame.transform.scale(self.assets[0], (CELL_SIZE, CELL_SIZE))
        self.assets[1] = pygame.image.load("assets/target.png")
        self.assets[1] = pygame.transform.scale(self.assets[1], (CELL_SIZE, CELL_SIZE))
        self.assets[2] = pygame.image.load("assets/box.png")
        self.assets[2] = pygame.transform.scale(self.assets[2], (CELL_SIZE, CELL_SIZE))
        self.assets[3] = pygame.image.load("assets/player_front.png")
        self.assets[3] = pygame.transform.scale(self.assets[3], (CELL_SIZE, CELL_SIZE))
        # Optionnel : ajoute les autres directions si tu veux
        self.assets[4] = pygame.image.load("assets/box.png")  # Ou une image spéciale "box on target"
        self.assets[4] = pygame.transform.scale(self.assets[4], (CELL_SIZE, CELL_SIZE))
        self.assets[5] = pygame.image.load("assets/player_on_target.png")  # Joueur sur cible
        self.assets[5] = pygame.transform.scale(self.assets[5], (CELL_SIZE, CELL_SIZE))

# Point d'entrée principal
if __name__ == "__main__":
    try:
        game = SokobanCompleteGame()
        game.run()
    except KeyboardInterrupt:
        print("\nJeu interrompu par l'utilisateur")
        pygame.quit()
        sys.exit()
    except Exception as e:
        print(f"Erreur: {e}")
        pygame.quit()
        sys.exit()
