import pygame
import sys
import time
import os
from game_logic import SokobanGame
from game_features import SokobanDatabase, SokobanAudio, SokobanLevels
from sokoban_bot import SokobanBot # Import du bot ML

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
SUCCESS_COLOR = (0, 150, 0)
ERROR_COLOR = (200, 0, 0)


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
        
        # Charger les niveaux étendus
        extended_levels = SokobanLevels.get_extended_levels()
        self.game = SokobanGame()
        self.game.levels = extended_levels
        self.level_info = SokobanLevels.get_level_info()
        
        # Interface graphique
        self.window_width = 1000
        self.window_height = 750
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Sokoban - Jeu Complet avec Bot ML")
        
        # Polices
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 20)
        self.large_font = pygame.font.Font(None, 48)
        
        # État du jeu
        self.state = "MENU"  # MENU, GAME, SCORES, SETTINGS, BOT_GAME
        self.player_name = "Joueur"
        self.start_time = None
        self.clock = pygame.time.Clock()
        
        # Zone de jeu
        self.game_area_x = 50
        self.game_area_y = 120
        
        # Bot ML
        self.bot = SokobanBot(self.game)
        self.bot_playing = False
        self.bot_actions = []
        self.current_bot_action_index = 0
        self.bot_level_to_play = 0
        self.bot_training = False
        self.bot_training_progress = 0
        self.bot_status = "Prêt"
        self.bot_last_action_time = 0
        self.bot_action_delay = 300  # millisecondes entre les actions du bot

        # Boutons
        self.create_buttons()
        
        # Mapping des touches
        self.key_mapping = {
            pygame.K_UP: 'UP',
            pygame.K_DOWN: 'DOWN',
            pygame.K_LEFT: 'LEFT',
            pygame.K_RIGHT: 'RIGHT'
        }

        # Charger les assets
        self.assets = {}
        self.load_assets()

    
    def create_buttons(self):
        """Crée les boutons de l'interface"""
        # Boutons du menu principal
        self.menu_buttons = [
            Button(400, 200, 200, 50, "Nouveau Jeu", self.font),
            Button(400, 270, 200, 50, "Scores", self.font),
            Button(400, 340, 200, 50, "Paramètres", self.font),
            Button(400, 410, 200, 50, "Bot ML", self.font),
            Button(400, 480, 200, 50, "Quitter", self.font)
        ]
        
        # Boutons en jeu
        self.game_buttons = [
            Button(700, 150, 150, 40, "Annuler (U)", self.small_font),
            Button(700, 200, 150, 40, "Recommencer (R)", self.small_font),
            Button(700, 250, 150, 40, "Menu (M)", self.small_font),
            Button(700, 300, 150, 40, "Scores", self.small_font),
            Button(700, 350, 150, 40, "Niveau suivant", self.small_font)
        ]
        
        # Boutons des scores
        self.score_buttons = [
            Button(400, 650, 200, 50, "Retour", self.font)
        ]
        
        # Boutons des paramètres
        self.settings_buttons = [
            Button(300, 200, 200, 40, "Sons: ON", self.font),
            Button(300, 250, 200, 40, "Musique: ON", self.font),
            Button(300, 300, 200, 40, "Volume: 70%", self.font),
            Button(400, 650, 200, 50, "Retour", self.font)
        ]

        # Boutons pour le bot ML
        self.bot_buttons = []
        for i in range(len(self.game.levels)):
            self.bot_buttons.append(Button(200, 200 + i * 70, 200, 50, f"Entraîner Niveau {i + 1}", self.font))
            self.bot_buttons.append(Button(450, 200 + i * 70, 200, 50, f"Jouer Niveau {i + 1}", self.font))
        self.bot_buttons.append(Button(700, 200, 150, 50, "Arrêter Bot", self.font))
        self.bot_buttons.append(Button(400, 650, 200, 50, "Retour au Menu", self.font))

    
    def draw_cell(self, x, y, cell_value):
        """Dessine une cellule de la grille"""
        rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
        
        # Dessiner le fond de la cellule
        if cell_value in self.assets:
            self.screen.blit(self.assets[cell_value], rect)
        else:
            # Fallback avec des couleurs simples
            colors = {
                -1: (100, 100, 100),  # Mur - gris foncé
                0: (240, 240, 240),   # Sol - gris clair
                1: (255, 255, 0),     # Cible - jaune
                2: (139, 69, 19),     # Caisse - marron
                3: (0, 0, 255),       # Joueur - bleu
                4: (255, 165, 0),     # Caisse sur cible - orange
                5: (0, 255, 0)        # Joueur sur cible - vert
            }
            color = colors.get(cell_value, (255, 255, 255))
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)
    
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
        
        # Titre principal
        title_text = self.large_font.render("SOKOBAN", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(self.window_width//2, 80))
        self.screen.blit(title_text, title_rect)
        
        # Sous-titre
        subtitle_text = self.font.render("Jeu de puzzle classique avec Bot ML", True, TEXT_COLOR)
        subtitle_rect = subtitle_text.get_rect(center=(self.window_width//2, 130))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Instructions
        instructions = [
            "Poussez toutes les caisses (■) sur les cibles (○)",
            "Utilisez les flèches pour vous déplacer",
            "Le bot ML peut apprendre à résoudre les niveaux automatiquement"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(self.window_width//2, 560 + i * 25))
            self.screen.blit(text, text_rect)
        
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
        level_name = level_info.get("name", f'Niveau {game_state["level"]}')
        difficulty = level_info.get("difficulty", 'Inconnu')
        
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
            "Contrôles:",
            "↑↓←→ : Déplacer",
            "U : Annuler",
            "R : Recommencer",
            "M : Menu",
            "",
            "Légende:",
            "■ : Caisse",
            "○ : Cible",
            "● : Caisse placée",
            "☺ : Joueur"
        ]
        
        for i, instruction in enumerate(instructions):
            color = TEXT_COLOR if instruction else BACKGROUND_COLOR
            text = self.small_font.render(instruction, True, color)
            self.screen.blit(text, (700, 400 + i * 20))
        
        # Message de victoire
        if game_state['is_complete']:
            victory_text = self.title_font.render("NIVEAU TERMINÉ!", True, SUCCESS_COLOR)
            text_rect = victory_text.get_rect(center=(self.window_width//2, self.window_height - 150))
            self.screen.blit(victory_text, text_rect)
            
            continue_text = self.font.render("Appuyez sur ESPACE pour continuer", True, TEXT_COLOR)
            continue_rect = continue_text.get_rect(center=(self.window_width//2, self.window_height - 120))
            self.screen.blit(continue_text, continue_rect)

    def draw_bot_game(self):
        """Dessine l'écran du bot ML"""
        self.screen.fill(BACKGROUND_COLOR)

        # Titre
        title_text = self.title_font.render("BOT ML SOKOBAN", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(self.window_width//2, 50))
        self.screen.blit(title_text, title_rect)

        # Statut du bot
        status_color = SUCCESS_COLOR if self.bot_status == "Terminé" else TEXT_COLOR
        if self.bot_training:
            status_color = ERROR_COLOR
        
        status_text = self.font.render(f"Statut: {self.bot_status}", True, status_color)
        status_rect = status_text.get_rect(center=(self.window_width//2, 100))
        self.screen.blit(status_text, status_rect)

        # Boutons
        for button in self.bot_buttons:
            button.draw(self.screen)

        # Affichage du jeu du bot
        if self.bot_playing:
            level_text = self.font.render(f"Le bot joue le niveau {self.bot_level_to_play + 1}", True, TEXT_COLOR)
            level_rect = level_text.get_rect(center=(self.window_width//2, 350))
            self.screen.blit(level_text, level_rect)

            # Afficher la grille du bot en temps réel
            game_state = self.game.get_game_state()
            if game_state:
                # Centrer la grille
                grid_width = len(game_state['grid'][0]) * CELL_SIZE if game_state['grid'] else 0
                grid_height = len(game_state['grid']) * CELL_SIZE if game_state['grid'] else 0
                self.game_area_x = (self.window_width - grid_width) // 2
                self.game_area_y = 380
                
                self.draw_grid(game_state['grid'])
                
                moves_text = self.font.render(f"Mouvements du bot: {game_state['moves']}", True, TEXT_COLOR)
                moves_rect = moves_text.get_rect(center=(self.window_width//2, 380 + grid_height + 30))
                self.screen.blit(moves_text, moves_rect)

        # Instructions
        instructions = [
            "Le bot utilise l'apprentissage par renforcement (Q-Learning)",
            "Entraînez d'abord le bot sur un niveau, puis regardez-le jouer",
            "Plus l'entraînement est long, meilleure sera la performance"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(self.window_width//2, 150 + i * 25))
            self.screen.blit(text, text_rect)
    
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
        header_positions = [100, 200, 300, 400, 500, 600]
        
        for i, header in enumerate(headers):
            text = self.font.render(header, True, TEXT_COLOR)
            self.screen.blit(text, (header_positions[i], header_y))
        
        # Ligne de séparation
        pygame.draw.line(self.screen, TEXT_COLOR, (100, header_y + 30), (700, header_y + 30), 2)
        
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
        
        # Boutons
        for button in self.settings_buttons:
            button.draw(self.screen)
        
        # Instructions
        instructions = [
            "Cliquez sur les boutons pour modifier les paramètres",
            "Les paramètres sont sauvegardés automatiquement",
            "Note: Audio désactivé pour éviter les erreurs système"
        ]
        
        for i, instruction in enumerate(instructions):
            text = self.small_font.render(instruction, True, TEXT_COLOR)
            text_rect = text.get_rect(center=(self.window_width//2, 400 + i * 30))
            self.screen.blit(text, text_rect)
    
    def handle_menu_events(self, event):
        """Gère les événements du menu"""
        for i, button in enumerate(self.menu_buttons):
            if button.handle_event(event):
                if i == 0:  # Nouveau Jeu
                    self.state = "GAME"
                    self.game.start_level(0)
                    self.start_time = time.time()
                elif i == 1:  # Scores
                    self.state = "SCORES"
                elif i == 2:  # Paramètres
                    self.state = "SETTINGS"
                elif i == 3:  # Bot ML
                    self.state = "BOT_GAME"
                elif i == 4:  # Quitter
                    return False
        return True
    
    def handle_game_events(self, event):
        """Gère les événements du jeu"""
        if event.type == pygame.KEYDOWN:
            if event.key in self.key_mapping:
                direction = self.key_mapping[event.key]
                result = self.game.move_player(direction)
                
                if result == 'LEVEL_COMPLETE':
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
            
            elif event.key == pygame.K_u:
                self.game.undo_move()
            
            elif event.key == pygame.K_r:
                self.game.reset_level()
                self.start_time = time.time()
            
            elif event.key == pygame.K_m:
                self.state = "MENU"
            
            elif event.key == pygame.K_SPACE:
                game_state = self.game.get_game_state()
                if game_state and game_state['is_complete']:
                    if self.game.has_next_level():
                        self.game.next_level()
                        self.start_time = time.time()
                    else:
                        self.state = "MENU"
        
        # Boutons
        for i, button in enumerate(self.game_buttons):
            if button.handle_event(event):
                if i == 0:  # Annuler
                    self.game.undo_move()
                elif i == 1:  # Recommencer
                    self.game.reset_level()
                    self.start_time = time.time()
                elif i == 2:  # Menu
                    self.state = "MENU"
                elif i == 3:  # Scores
                    self.state = "SCORES"
                elif i == 4:  # Niveau suivant
                    if self.game.has_next_level():
                        self.game.next_level()
                        self.start_time = time.time()
        
        return True
    
    def handle_scores_events(self, event):
        """Gère les événements de l'écran des scores"""
        for button in self.score_buttons:
            if button.handle_event(event):
                self.state = "MENU"
        return True
    
    def handle_settings_events(self, event):
        """Gère les événements de l'écran des paramètres"""
        for i, button in enumerate(self.settings_buttons):
            if button.handle_event(event):
                if i == 3:  # Retour
                    self.state = "MENU"
        return True

    def handle_bot_game_events(self, event):
        """Gère les événements de l'écran du bot ML"""
        for i, button in enumerate(self.bot_buttons):
            if button.handle_event(event):
                if i < len(self.game.levels) * 2: # Boutons d'entraînement et de jeu
                    level_index = (i // 2)
                    if i % 2 == 0: # Entraîner
                        if not self.bot_training and not self.bot_playing:
                            self.start_bot_training(level_index)
                    else: # Jouer
                        if not self.bot_training and not self.bot_playing:
                            self.start_bot_playing(level_index)
                elif i == len(self.game.levels) * 2:  # Arrêter Bot
                    self.stop_bot()
                elif i == len(self.game.levels) * 2 + 1:  # Retour au Menu
                    self.stop_bot()
                    self.state = "MENU"
        return True

    def start_bot_training(self, level_index):
        """Démarre l'entraînement du bot"""
        self.bot_level_to_play = level_index
        self.bot_training = True
        self.bot_status = f"Entraînement niveau {level_index + 1}..."
        
    def start_bot_playing(self, level_index):
        """Démarre le jeu du bot"""
        self.bot_level_to_play = level_index
        self.bot_status = f"Résolution niveau {level_index + 1}..."
        solved, moves, actions = self.bot.play_level(level_index=level_index)
        if solved:
            self.bot_actions = actions
            self.current_bot_action_index = 0
            self.game.start_level(level_index)
            self.bot_playing = True
            self.bot_last_action_time = pygame.time.get_ticks()
            self.bot_status = f"Bot joue niveau {level_index + 1}"
        else:
            self.bot_status = f"Échec niveau {level_index + 1} - Entraînez d'abord!"
    
    def stop_bot(self):
        """Arrête le bot"""
        self.bot_playing = False
        self.bot_training = False
        self.bot_status = "Arrêté"

    def load_assets(self):
        """Charge les images des éléments du jeu"""
        try:
            # Vérifier si le fichier d'assets existe
            assets_path = os.path.join(os.path.dirname(__file__), 'assets', 'sokoban_assets.png')
            if os.path.exists(assets_path):
                # Charger l'image complète des assets
                sokoban_assets_img = pygame.image.load(assets_path).convert_alpha()

                # Définir les coordonnées de chaque asset dans l'image complète
                asset_coords = {
                    -1: (0, 0),   # Mur
                    0: (40, 0),   # Sol
                    1: (80, 0),   # Cible
                    2: (120, 0),  # Caisse
                    3: (160, 0),  # Joueur (face)
                    4: (200, 0),  # Caisse sur cible
                    5: (240, 0)   # Joueur sur cible
                }

                for key, coords in asset_coords.items():
                    x, y = coords
                    # Extraire la sous-surface pour chaque asset
                    self.assets[key] = pygame.transform.scale(sokoban_assets_img.subsurface(pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)), (CELL_SIZE, CELL_SIZE))
                
                print("Assets chargés avec succès depuis l'image.")
            else:
                print("Fichier d'assets non trouvé, utilisation des couleurs par défaut.")

        except pygame.error as e:
            print(f"Erreur de chargement des assets: {e}")
            print("Utilisation des couleurs par défaut.")

    def update_bot(self):
        """Met à jour la logique du bot"""
        current_time = pygame.time.get_ticks()
        
        # Entraînement du bot (non-bloquant)
        if self.bot_training:
            # Entraîner par petits blocs pour ne pas bloquer l'interface
            # Augmenter le nombre d'épisodes par bloc pour un entraînement plus rapide
            self.bot.train(num_episodes=50, level_index=self.bot_level_to_play)
            self.bot_training = False # Entraînement terminé pour ce bloc
            self.bot_status = f"Entraînement terminé niveau {self.bot_level_to_play + 1}"
        
        # Jeu du bot
        if self.bot_playing and current_time - self.bot_last_action_time > self.bot_action_delay:
            if self.current_bot_action_index < len(self.bot_actions):
                action = self.bot_actions[self.current_bot_action_index]
                result = self.game.move_player(action)
                self.current_bot_action_index += 1
                self.bot_last_action_time = current_time
                
                if self.game.board.is_level_complete():
                    self.bot_playing = False
                    self.bot_status = f"Niveau {self.bot_level_to_play + 1} terminé!"
            else:
                self.bot_playing = False
                self.bot_status = f"Niveau {self.bot_level_to_play + 1} - Actions épuisées"

    def run(self):
        """Boucle principale du jeu"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.state == "MENU":
                    running = self.handle_menu_events(event)
                elif self.state == "GAME":
                    running = self.handle_game_events(event)
                elif self.state == "SCORES":
                    running = self.handle_scores_events(event)
                elif self.state == "SETTINGS":
                    running = self.handle_settings_events(event)
                elif self.state == "BOT_GAME":
                    running = self.handle_bot_game_events(event)

            # Mise à jour de la logique du bot
            self.update_bot()

            # Logique de mise à jour et de dessin
            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "GAME":
                self.draw_game()
            elif self.state == "SCORES":
                self.draw_scores()
            elif self.state == "SETTINGS":
                self.draw_settings()
            elif self.state == "BOT_GAME":
                self.draw_bot_game()

            pygame.display.flip()
            self.clock.tick(60) # Limite le jeu à 60 FPS

        pygame.quit()
        sys.exit()

