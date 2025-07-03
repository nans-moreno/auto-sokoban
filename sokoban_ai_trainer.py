"""
Interface graphique complète pour entraîner et visualiser l'IA Sokoban
Version avec fenêtre agrandie et interface réorganisée
Inclut toutes les fonctionnalités : apprentissage par observation, détection des coins, etc.
"""

import pygame
import sys
import os
import json
import time
import threading
import pickle
import random
import numpy as np
from collections import defaultdict, deque
import hashlib
from sokoban_complete import SokobanCompleteGame, Button
from game_logic import SokobanGame, GameBoard

# Constantes d'affichage
BACKGROUND_COLOR = (240, 240, 240)
TEXT_COLOR = (0, 0, 0)
BUTTON_COLOR = (180, 180, 180)
BUTTON_HOVER_COLOR = (160, 160, 160)
PANEL_COLOR = (230, 230, 230)
PANEL_BORDER_COLOR = (200, 200, 200)

# ==================== CLASSES DE L'IA ====================

class TabuList:
    """Liste tabou pour éviter de revisiter les états récents"""
    def __init__(self, max_size=100):
        self.tabu_states = deque(maxlen=max_size)
        self.tabu_dict = {}
        
    def add(self, state_hash):
        if state_hash not in self.tabu_dict:
            self.tabu_states.append(state_hash)
            self.tabu_dict[state_hash] = time.time()
            if len(self.tabu_states) == self.tabu_states.maxlen:
                oldest = self.tabu_states[0]
                if oldest in self.tabu_dict:
                    del self.tabu_dict[oldest]
    
    def is_tabu(self, state_hash, threshold_seconds=10):
        if state_hash in self.tabu_dict:
            elapsed = time.time() - self.tabu_dict[state_hash]
            if elapsed < threshold_seconds:
                return True
            else:
                del self.tabu_dict[state_hash]
        return False
    
    def clear(self):
        self.tabu_states.clear()
        self.tabu_dict.clear()


class SokobanAI:
    """IA améliorée pour Sokoban avec système anti-boucles et apprentissage par observation"""
    
    def __init__(self, learning_rate=0.1, discount_factor=0.95, epsilon=0.2):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.training_episodes = 0
        
        # Actions possibles
        self.actions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        
        # Système anti-boucles
        self.tabu_list = TabuList(max_size=50)
        self.state_visit_count = defaultdict(int)
        self.recent_states = deque(maxlen=20)
        self.recent_actions = deque(maxlen=30)
        self.loop_detection_window = 10
        
        # Compteurs et paramètres adaptatifs
        self.stuck_counter = 0
        self.loop_counter = 0
        self.forced_exploration_mode = False
        self.exploration_boost = 0.0
        
        # Directions de mouvement
        self.directions = {
            'UP': (-1, 0),
            'DOWN': (1, 0),
            'LEFT': (0, -1),
            'RIGHT': (0, 1)
        }
        
        # Statistiques
        self.stats = {
            'wins': 0,
            'total_moves': 0,
            'episodes': 0,
            'loops_detected': 0,
            'best_solution': {},
            'human_demos_learned': 0
        }
    
    def get_state_hash(self, board):
        """Crée un hash unique pour l'état du plateau"""
        player_pos = board.player_pos
        if not player_pos:
            return None
            
        state_str = f"{player_pos}|"
        state_str += "|".join(f"{box}" for box in sorted(board.box_positions))
        state_str += "|targets:" + "|".join(f"{t}" for t in sorted(board.target_positions))
        
        return hashlib.md5(state_str.encode()).hexdigest()
    
    def get_state_representation(self, board):
        """Représentation d'état enrichie pour la Q-table"""
        player_pos = board.player_pos
        if not player_pos:
            return None
        
        features = []
        
        # Position absolue du joueur
        features.extend([player_pos[0], player_pos[1]])
        
        # Configuration des caisses
        box_positions_sorted = sorted(board.box_positions)
        for i in range(min(6, len(box_positions_sorted))):
            if i < len(box_positions_sorted):
                features.extend([box_positions_sorted[i][0], box_positions_sorted[i][1]])
            else:
                features.extend([0, 0])
        
        # Distance minimale de chaque caisse à sa cible la plus proche
        box_target_distances = []
        for box in board.box_positions:
            min_dist = float('inf')
            for target in board.target_positions:
                dist = abs(box[0] - target[0]) + abs(box[1] - target[1])
                min_dist = min(min_dist, dist)
            box_target_distances.append(min_dist)
        
        box_target_distances.sort()
        features.extend(box_target_distances[:4])
        
        # Nombre de caisses sur les cibles
        boxes_on_targets = sum(1 for box in board.box_positions 
                              if box in board.target_positions)
        features.append(boxes_on_targets)
        
        return tuple(features)
    
    def detect_loop(self):
        """Détection avancée de boucles"""
        if len(self.recent_states) < self.loop_detection_window:
            return False
        
        recent_list = list(self.recent_states)[-self.loop_detection_window:]
        unique_states = set(recent_list)
        
        if len(unique_states) <= self.loop_detection_window // 3:
            return True
        
        # Vérifier les patterns d'actions
        if len(self.recent_actions) >= 8:
            recent_actions_list = list(self.recent_actions)[-8:]
            
            # Vérifier les patterns répétitifs
            if (recent_actions_list == ['UP', 'DOWN'] * 4 or 
                recent_actions_list == ['DOWN', 'UP'] * 4 or
                recent_actions_list == ['LEFT', 'RIGHT'] * 4 or
                recent_actions_list == ['RIGHT', 'LEFT'] * 4):
                return True
        
        return False
    
    def choose_action(self, board, training=True):
        """Choisit une action avec système anti-boucles"""
        state = self.get_state_representation(board)
        state_hash = self.get_state_hash(board)
        
        if state is None or state_hash is None:
            return random.choice(self.actions)
        
        # Enregistrer l'état
        self.recent_states.append(state_hash)
        self.state_visit_count[state_hash] += 1
        
        # Détecter les boucles
        if self.detect_loop():
            self.loop_counter += 1
            self.stuck_counter += 2
            self.stats['loops_detected'] += 1
        else:
            self.loop_counter = max(0, self.loop_counter - 1)
            self.stuck_counter = max(0, self.stuck_counter - 1)
        
        # Mode d'exploration forcée si trop de boucles
        if self.loop_counter > 3 or self.stuck_counter > 5:
            self.forced_exploration_mode = True
            self.exploration_boost = 0.8
        else:
            self.forced_exploration_mode = False
            self.exploration_boost = max(0, self.exploration_boost - 0.1)
        
        # Calculer epsilon effectif
        effective_epsilon = min(0.95, self.epsilon + self.exploration_boost)
        
        # Forcer l'exploration si l'état est tabou
        if self.tabu_list.is_tabu(state_hash):
            effective_epsilon = 0.9
        
        # Exploration vs Exploitation
        if training and (random.random() < effective_epsilon or self.forced_exploration_mode):
            # Exploration intelligente
            available_actions = list(self.actions)
            
            # Éviter les actions opposées immédiates
            if len(self.recent_actions) > 0:
                last_action = self.recent_actions[-1]
                opposite = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}
                if last_action in opposite and len(available_actions) > 1:
                    opp_action = opposite[last_action]
                    if opp_action in available_actions:
                        available_actions.remove(opp_action)
            
            action = random.choice(available_actions)
        else:
            # Exploitation
            q_values = self.q_table[state].copy()
            
            if not q_values:
                action = random.choice(self.actions)
            else:
                # Pénaliser les états fréquemment visités
                visit_penalty = self.state_visit_count[state_hash] * 0.5
                
                adjusted_q_values = {}
                for act, q_value in q_values.items():
                    adjusted_q = q_value - visit_penalty
                    
                    # Pénalité pour les actions récentes
                    if len(self.recent_actions) >= 3:
                        recent_count = self.recent_actions.count(act)
                        adjusted_q -= recent_count * 0.3
                    
                    adjusted_q += random.uniform(-0.01, 0.01)
                    adjusted_q_values[act] = adjusted_q
                
                action = max(adjusted_q_values.keys(), key=lambda k: adjusted_q_values[k])
        
        # Enregistrer l'action
        self.recent_actions.append(action)
        
        # Ajouter l'état à la liste tabou si visité trop souvent
        if self.state_visit_count[state_hash] > 3:
            self.tabu_list.add(state_hash)
        
        return action
    
    def calculate_reward(self, board, old_board, action_success, action):
        """Calcule la récompense avec pénalités pour les boucles"""
        if not action_success:
            return -1.0
        
        if board.is_level_complete():
            return 100.0
        
        reward = 0.0
        
        # Récompenses pour les progrès
        old_boxes_on_targets = sum(1 for box in old_board.box_positions 
                                  if box in old_board.target_positions)
        new_boxes_on_targets = sum(1 for box in board.box_positions 
                                  if box in board.target_positions)
        
        if new_boxes_on_targets > old_boxes_on_targets:
            reward += 25.0
        elif new_boxes_on_targets < old_boxes_on_targets:
            reward -= 15.0
        
        # Pénalité pour les états revisités
        state_hash = self.get_state_hash(board)
        if state_hash:
            visit_count = self.state_visit_count[state_hash]
            if visit_count > 1:
                reward -= visit_count * 0.5
        
        # Pénalité pour les boucles
        if self.loop_counter > 0:
            reward -= self.loop_counter * 2.0
        
        # Pénalité pour les caisses bloquées
        if hasattr(board, 'check_for_stuck_boxes'):
            stuck_boxes = board.check_for_stuck_boxes()
            reward -= len(stuck_boxes) * 10.0
        
        reward -= 0.02  # Petit coût par mouvement
        
        return reward
    
    def update_q_table(self, state, action, reward, next_state):
        """Met à jour la Q-table"""
        if state is None:
            return
        
        current_q = self.q_table[state][action]
        
        if next_state is not None and self.q_table[next_state]:
            max_next_q = max(self.q_table[next_state].values())
        else:
            max_next_q = 0.0
        
        learning_rate = self.learning_rate
        if self.loop_counter > 0:
            learning_rate *= 1.5
        
        new_q = current_q + learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state][action] = new_q
    
    def reset_antiloop_mechanisms(self):
        """Réinitialise tous les mécanismes anti-boucles"""
        self.recent_states.clear()
        self.recent_actions.clear()
        self.state_visit_count.clear()
        self.tabu_list.clear()
        self.stuck_counter = 0
        self.loop_counter = 0
        self.forced_exploration_mode = False
        self.exploration_boost = 0.0
    
    def train_episode(self, game, level_index, max_steps=1000):
        """Entraîne l'IA sur un épisode"""
        game.start_level(level_index)
        self.reset_antiloop_mechanisms()
        
        steps = 0
        total_reward = 0
        moves_sequence = []
        no_progress_counter = 0
        last_boxes_on_targets = 0
        
        while steps < max_steps and not game.board.is_level_complete():
            state = self.get_state_representation(game.board)
            old_board = GameBoard(game.board.get_display_grid())
            
            action = self.choose_action(game.board, training=True)
            direction = self.directions[action]
            success = game.board.move_player(direction)
            
            reward = self.calculate_reward(game.board, old_board, success, action)
            total_reward += reward
            
            next_state = self.get_state_representation(game.board)
            self.update_q_table(state, action, reward, next_state)
            
            if success:
                moves_sequence.append(action)
                game.moves_count += 1
            
            # Vérifier le progrès
            current_boxes_on_targets = sum(1 for box in game.board.box_positions 
                                         if box in game.board.target_positions)
            if current_boxes_on_targets == last_boxes_on_targets:
                no_progress_counter += 1
            else:
                no_progress_counter = 0
                last_boxes_on_targets = current_boxes_on_targets
            
            if no_progress_counter > 50 or self.loop_counter > 10:
                break
            
            steps += 1
        
        episode_stats = {
            'completed': game.board.is_level_complete(),
            'steps': steps,
            'moves': len(moves_sequence),
            'total_reward': total_reward,
            'moves_sequence': moves_sequence
        }
        
        self.stats['episodes'] += 1
        if episode_stats['completed']:
            self.stats['wins'] += 1
            if level_index not in self.stats['best_solution'] or \
               len(moves_sequence) < len(self.stats['best_solution'][level_index]):
                self.stats['best_solution'][level_index] = moves_sequence
        
        return episode_stats
    
    def learn_from_human_move(self, state, action, success):
        """Apprend d'un mouvement humain"""
        if state and success:
            current_q = self.q_table[state][action]
            immediate_reward = 2.0  # Récompense pour imiter l'humain
            new_q = current_q + self.learning_rate * immediate_reward
            self.q_table[state][action] = new_q
    
    def save_model(self, filename="sokoban_ai_model.pkl"):
        """Sauvegarde le modèle"""
        model_data = {
            'q_table': dict(self.q_table),
            'stats': self.stats,
            'training_episodes': self.training_episodes,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Modèle sauvegardé dans {filename}")
    
    def load_model(self, filename="sokoban_ai_model.pkl"):
        """Charge un modèle"""
        try:
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = defaultdict(lambda: defaultdict(float), model_data['q_table'])
            self.stats = model_data['stats']
            self.training_episodes = model_data['training_episodes']
            self.learning_rate = model_data.get('learning_rate', 0.1)
            self.discount_factor = model_data.get('discount_factor', 0.95)
            
            print(f"💾 Modèle chargé depuis {filename}")
            return True
        except FileNotFoundError:
            print(f"⚠ Fichier {filename} non trouvé")
            return False


# ==================== ENREGISTREUR DE PARTIES HUMAINES ====================

class HumanPlayRecorder:
    """Enregistre les parties jouées par les humains pour l'apprentissage de l'IA"""
    
    def __init__(self):
        self.recording = False
        self.current_recording = {
            'level': 0,
            'states': [],
            'actions': [],
            'success': False,
            'moves_count': 0,
            'timestamp': time.time()
        }
        self.recordings_file = "human_play_data.json"
        self.load_recordings()
    
    def load_recordings(self):
        """Charge les enregistrements existants"""
        if os.path.exists(self.recordings_file):
            try:
                with open(self.recordings_file, 'r') as f:
                    self.all_recordings = json.load(f)
            except:
                self.all_recordings = []
        else:
            self.all_recordings = []
    
    def save_recordings(self):
        """Sauvegarde tous les enregistrements"""
        with open(self.recordings_file, 'w') as f:
            json.dump(self.all_recordings, f)
    
    def start_recording(self, level):
        """Commence un nouvel enregistrement"""
        self.recording = True
        self.current_recording = {
            'level': level,
            'states': [],
            'actions': [],
            'success': False,
            'moves_count': 0,
            'timestamp': time.time()
        }
    
    def record_move(self, state, action):
        """Enregistre un mouvement"""
        if self.recording:
            # Convertir l'état en format sérialisable
            if isinstance(state, tuple):
                state = list(state)
            self.current_recording['states'].append(state)
            self.current_recording['actions'].append(action)
            self.current_recording['moves_count'] += 1
    
    def stop_recording(self, success=False):
        """Arrête l'enregistrement et le sauvegarde si réussi"""
        if self.recording:
            self.recording = False
            self.current_recording['success'] = success
            
            if success or self.current_recording['moves_count'] > 10:
                self.all_recordings.append(self.current_recording)
                self.save_recordings()
                return True
        return False
    
    def get_successful_recordings(self, level=None):
        """Récupère les enregistrements réussis"""
        if level is not None:
            return [r for r in self.all_recordings 
                   if r['success'] and r['level'] == level]
        return [r for r in self.all_recordings if r['success']]


# ==================== INTERFACE D'ENTRAÎNEMENT COMPLÈTE ====================

class SokobanAITrainer(SokobanCompleteGame):
    """Extension du jeu complet avec toutes les fonctionnalités IA"""
    
    def __init__(self):
        # Créer la fenêtre plus grande AVANT d'appeler super().__init__()
        pygame.init()
        
        # FENÊTRE AGRANDIE
        self.window_width = 1200  # Plus large pour avoir de l'espace pour les contrôles IA
        self.window_height = 800  # Plus haut pour mieux organiser l'interface
        
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Sokoban AI Trainer - Interface étendue")
        
        # Définir TOUS les attributs nécessaires AVANT super().__init__()
        # Zone pour les contrôles IA (panneau à droite)
        self.ai_panel_x = 750
        self.ai_panel_width = 400
        self.ai_panel_height = self.window_height - 40
        
        # Maintenant initialiser le parent
        super().__init__()
        
        # Redéfinir la position de la zone de jeu (à gauche)
        self.game_area_x = 50
        self.game_area_y = 120
        
        # Créer l'IA
        self.ai = SokobanAI(learning_rate=0.15, discount_factor=0.95, epsilon=0.3)
        
        # Enregistreur de parties humaines
        self.human_recorder = HumanPlayRecorder()
        
        # État de l'entraînement
        self.training_active = False
        self.continuous_training = False
        self.ai_playing = False
        self.training_thread = None
        self.observation_mode = False
        
        # Option pour la détection des coins
        self.auto_detect_stuck_boxes = True
        
        # État de l'interface
        self.previous_state = None
        
        # Statistiques d'affichage
        self.training_stats = {
            'current_episode': 0,
            'total_episodes': 0,
            'win_rate': 0,
            'current_level': 0,
            'loops_detected': 0,
            'level_stats': {},
            'human_demos': 0
        }
        
        # Recréer tous les boutons avec le nouveau layout
        self.create_buttons()
    
    def create_buttons(self):
        """Crée les boutons de l'interface avec le nouveau layout"""
        # Boutons du menu principal (centrés)
        center_x = self.window_width // 2
        self.menu_buttons = [
            Button(center_x - 100, 200, 200, 50, "Nouveau Jeu", self.font),
            Button(center_x - 100, 270, 200, 50, "Scores", self.font),
            Button(center_x - 100, 340, 200, 50, "Paramètres", self.font),
            Button(center_x - 100, 410, 200, 50, "Quitter", self.font)
        ]
        
        # Boutons en jeu - dans le panneau de droite
        self.game_buttons = [
            Button(self.ai_panel_x + 20, 150, 150, 35, "Annuler (U)", self.small_font),
            Button(self.ai_panel_x + 180, 150, 150, 35, "Recommencer (R)", self.small_font),
            Button(self.ai_panel_x + 20, 195, 150, 35, "Menu (M)", self.small_font),
            Button(self.ai_panel_x + 180, 195, 150, 35, "Scores", self.small_font)
        ]
        
        # Boutons principaux pour l'IA - organisés verticalement dans le panneau
        self.ai_buttons = [
            Button(self.ai_panel_x + 20, 280, 170, 40, "Entraîner 1x", self.font),
            Button(self.ai_panel_x + 200, 280, 170, 40, "Entraîner ∞", self.font),
            Button(self.ai_panel_x + 20, 330, 170, 40, "IA Joue", self.font),
            Button(self.ai_panel_x + 200, 330, 170, 40, "Sauver IA", self.font),
            Button(self.ai_panel_x + 20, 380, 170, 40, "Charger IA", self.font),
            Button(self.ai_panel_x + 200, 380, 170, 40, "Options IA", self.font)
        ]
        
        # Boutons du menu OPTIONS (centrés)
        self.options_buttons = [
            Button(center_x - 100, 200, 200, 40, "Observer: OFF", self.font),
            Button(center_x - 100, 250, 200, 40, "Détection coins: ON", self.font),
            Button(center_x - 100, 300, 200, 40, "Apprendre des humains", self.font),
            Button(center_x - 100, 350, 200, 40, "Réinitialiser IA", self.font),
            Button(center_x - 100, 450, 200, 40, "Retour", self.font)
        ]
        
        # Boutons des scores
        self.score_buttons = [
            Button(center_x - 100, 650, 200, 50, "Retour", self.font)
        ]
        
        # Boutons des paramètres
        self.settings_buttons = [
            Button(center_x - 100, 200, 200, 40, "Sons: ON", self.font),
            Button(center_x - 100, 250, 200, 40, "Musique: ON", self.font),
            Button(center_x - 100, 300, 200, 40, "Volume: 70%", self.font),
            Button(center_x - 100, 600, 200, 50, "Retour", self.font)
        ]
    
    def draw_ai_panel(self):
        """Dessine le panneau latéral pour les contrôles IA"""
        # Fond du panneau
        panel_rect = pygame.Rect(self.ai_panel_x - 10, 20, self.ai_panel_width, self.ai_panel_height)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect)
        pygame.draw.rect(self.screen, PANEL_BORDER_COLOR, panel_rect, 2)
        
        # Titre du panneau
        title_text = self.font.render("Contrôles IA", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(self.ai_panel_x + self.ai_panel_width//2 - 10, 50))
        self.screen.blit(title_text, title_rect)
        
        # Ligne de séparation après le titre
        pygame.draw.line(self.screen, PANEL_BORDER_COLOR, 
                        (self.ai_panel_x, 75), 
                        (self.ai_panel_x + self.ai_panel_width - 20, 75), 2)
        
        # Section contrôles de jeu
        controls_title = self.small_font.render("Contrôles de jeu", True, TEXT_COLOR)
        self.screen.blit(controls_title, (self.ai_panel_x + 20, 120))
        
        # Ligne de séparation
        pygame.draw.line(self.screen, PANEL_BORDER_COLOR, 
                        (self.ai_panel_x, 250), 
                        (self.ai_panel_x + self.ai_panel_width - 20, 250), 1)
        
        # Section IA
        ia_title = self.small_font.render("Intelligence Artificielle", True, TEXT_COLOR)
        self.screen.blit(ia_title, (self.ai_panel_x + 20, 255))
        
        # Dessiner les boutons
        for button in self.game_buttons:
            button.draw(self.screen)
        
        for button in self.ai_buttons:
            button.draw(self.screen)
        
        # Ligne de séparation avant les statistiques
        pygame.draw.line(self.screen, PANEL_BORDER_COLOR, 
                        (self.ai_panel_x, 440), 
                        (self.ai_panel_x + self.ai_panel_width - 20, 440), 1)
        
        # Section statistiques
        stats_title = self.small_font.render("Statistiques IA", True, TEXT_COLOR)
        self.screen.blit(stats_title, (self.ai_panel_x + 20, 455))
        
        # Zone pour les statistiques
        self.draw_ai_stats(self.ai_panel_x + 20, 480)
    
    def draw_ai_stats(self, x, y):
        """Dessine les statistiques de l'IA"""
        # État principal
        if self.continuous_training:
            status_text = f"Entraînement continu - Niveau {self.training_stats['current_level'] + 1}/{len(self.game.levels)}"
            status_color = (0, 150, 0)
        elif self.training_active:
            status_text = f"Entraînement: {self.training_stats['current_episode']}/{self.training_stats['total_episodes']}"
            status_color = (0, 150, 0)
        elif self.ai_playing:
            status_text = "L'IA joue..."
            status_color = (0, 0, 255)
        elif self.observation_mode:
            status_text = "👁️ L'IA vous observe jouer..."
            status_color = (255, 0, 255)
        else:
            status_text = "IA prête"
            status_color = (100, 100, 100)
        
        # État
        status_surface = self.font.render(status_text, True, status_color)
        self.screen.blit(status_surface, (x, y))
        
        # Statistiques détaillées
        y += 35
        
        # Ligne 1 : Victoires et taux
        stats1 = f"Victoires: {self.ai.stats['wins']} | Taux: {self.training_stats['win_rate']:.1f}%"
        stats1_surface = self.small_font.render(stats1, True, TEXT_COLOR)
        self.screen.blit(stats1_surface, (x, y))
        
        # Ligne 2 : Q-table
        y += 20
        stats2 = f"Q-table: {len(self.ai.q_table)} états"
        stats2_surface = self.small_font.render(stats2, True, TEXT_COLOR)
        self.screen.blit(stats2_surface, (x, y))
        
        # Ligne 3 : Démonstrations humaines
        y += 20
        human_recordings = len(self.human_recorder.get_successful_recordings())
        if human_recordings > 0 or self.ai.stats.get('human_demos_learned', 0) > 0:
            demos_text = f"Démos: {self.ai.stats.get('human_demos_learned', 0)} apprises / {human_recordings} disponibles"
            demos_surface = self.small_font.render(demos_text, True, (0, 150, 0))
            self.screen.blit(demos_surface, (x, y))
            y += 20
        
        # Statistiques par niveau si en entraînement
        if self.continuous_training and self.training_stats['level_stats']:
            y += 10
            level_title = self.small_font.render("Progression par niveau:", True, TEXT_COLOR)
            self.screen.blit(level_title, (x, y))
            y += 25
            
            for level_idx, level_stat in self.training_stats['level_stats'].items():
                if level_stat['attempts'] > 0:
                    level_text = f"Niv {level_idx + 1}: {level_stat['win_rate']:.0f}% ({level_stat['wins']}/{level_stat['attempts']})"
                    if 'best_moves' in level_stat and level_stat['best_moves'] != float('inf'):
                        level_text += f" - Record: {level_stat['best_moves']}"
                    
                    color = (0, 150, 0) if level_stat['win_rate'] > 50 else (150, 0, 0)
                    level_surface = self.small_font.render(level_text, True, color)
                    self.screen.blit(level_surface, (x, y))
                    y += 20
        
        # Messages d'avertissement
        if self.observation_mode:
            y = self.window_height - 80
            obs_text = "📹 Jouez normalement - L'IA apprend de vos mouvements!"
            obs_surface = self.font.render(obs_text, True, (255, 0, 255))
            obs_rect = obs_surface.get_rect(center=(self.ai_panel_x + self.ai_panel_width//2 - 10, y))
            self.screen.blit(obs_surface, obs_rect)
        
        # Avertissement caisses bloquées
        game_state = self.game.get_game_state()
        if game_state and hasattr(self.game.board, 'check_for_stuck_boxes'):
            stuck_boxes = self.game.board.check_for_stuck_boxes()
            if stuck_boxes:
                warning_y = self.window_height - 50
                warning_text = self.font.render(f"⚠️ {len(stuck_boxes)} caisse(s) bloquée(s)!", True, (255, 0, 0))
                warning_rect = warning_text.get_rect(center=(self.ai_panel_x + self.ai_panel_width//2 - 10, warning_y))
                self.screen.blit(warning_text, warning_rect)
    
    def draw_game(self):
        """Surcharge pour ajouter le panneau IA"""
        # Dessiner d'abord le jeu de base (partie gauche)
        super().draw_game()
        
        # Puis dessiner le panneau IA (partie droite)
        self.draw_ai_panel()
    
    def show_stuck_box_dialog(self):
        """Affiche un dialogue quand une caisse est bloquée"""
        if not self.auto_detect_stuck_boxes:
            return
            
        overlay = pygame.Surface((self.window_width, self.window_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        dialog_width = 400
        dialog_height = 220
        dialog_x = (self.window_width - dialog_width) // 2
        dialog_y = (self.window_height - dialog_height) // 2
        
        dialog_rect = pygame.Rect(dialog_x, dialog_y, dialog_width, dialog_height)
        pygame.draw.rect(self.screen, (255, 255, 255), dialog_rect)
        pygame.draw.rect(self.screen, (0, 0, 0), dialog_rect, 3)
        
        warning_text = self.title_font.render("⚠️ Caisse Bloquée!", True, (255, 0, 0))
        warning_rect = warning_text.get_rect(center=(self.window_width//2, dialog_y + 40))
        self.screen.blit(warning_text, warning_rect)
        
        message_lines = [
            "Une caisse est coincée dans un coin!",
            "Le niveau est maintenant impossible à terminer.",
            "",
            "Appuyez sur R pour recommencer",
            "ou U pour annuler le dernier mouvement",
            "ou ESPACE pour continuer quand même"
        ]
        
        for i, line in enumerate(message_lines):
            text = self.small_font.render(line, True, (0, 0, 0))
            text_rect = text.get_rect(center=(self.window_width//2, dialog_y + 80 + i * 20))
            self.screen.blit(text, text_rect)
        
        pygame.display.flip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game.reset_level()
                        self.start_time = time.time()
                        self.audio.play_sound('reset')
                        waiting = False
                    elif event.key == pygame.K_u:
                        if self.game.undo_move():
                            self.audio.play_sound('undo')
                        waiting = False
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_ESCAPE:
                        waiting = False
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
    
    def train_ai_continuous_background(self):
        """Entraîne l'IA en continu sur tous les niveaux"""
        self.continuous_training = True
        self.training_active = True
        
        # Initialiser les stats par niveau
        for i in range(len(self.game.levels)):
            self.training_stats['level_stats'][i] = {
                'attempts': 0,
                'wins': 0,
                'win_rate': 0,
                'best_moves': float('inf')
            }
        
        try:
            while self.continuous_training:
                for level_index in range(len(self.game.levels)):
                    if not self.continuous_training:
                        break
                    
                    self.training_stats['current_level'] = level_index
                    
                    # Entraîner sur ce niveau
                    stats = self.ai.train_episode(self.game, level_index, max_steps=1000)
                    
                    # Mettre à jour les statistiques
                    self.training_stats['total_episodes'] += 1
                    level_stats = self.training_stats['level_stats'][level_index]
                    level_stats['attempts'] += 1
                    
                    if stats['completed']:
                        level_stats['wins'] += 1
                        if stats['moves'] < level_stats['best_moves']:
                            level_stats['best_moves'] = stats['moves']
                        print(f"✔ Niveau {level_index + 1} complété en {stats['moves']} mouvements!")
                    else:
                        print(f"❌ Niveau {level_index + 1} - Échec après {stats['steps']} tentatives")
                    
                    level_stats['win_rate'] = (level_stats['wins'] / level_stats['attempts']) * 100
                    
                    if self.ai.stats['episodes'] > 0:
                        self.training_stats['win_rate'] = (self.ai.stats['wins'] / self.ai.stats['episodes']) * 100
                    
                    self.ai.epsilon = max(0.01, self.ai.epsilon * 0.999)
                
                # Résumé après chaque cycle
                print(f"\n🎯 Cycle terminé - Total épisodes: {self.training_stats['total_episodes']}")
                for idx, level_stat in self.training_stats['level_stats'].items():
                    print(f"   Niveau {idx + 1}: {level_stat['win_rate']:.1f}% ({level_stat['wins']}/{level_stat['attempts']})")
                
        except Exception as e:
            print(f"Erreur pendant l'entraînement: {e}")
        
        self.training_active = False
        self.continuous_training = False
    
    def train_from_human_demonstrations(self):
        """Entraîne l'IA à partir des démonstrations humaines"""
        print("\n📚 Apprentissage à partir des démonstrations humaines...")
        
        successful_recordings = self.human_recorder.get_successful_recordings()
        
        if not successful_recordings:
            print("❌ Aucune démonstration humaine trouvée!")
            print("   Jouez d'abord quelques niveaux avec 'Observer: ON'")
            return
        
        print(f"📖 {len(successful_recordings)} démonstrations trouvées")
        
        for i, recording in enumerate(successful_recordings):
            print(f"\n📑 Analyse de la démonstration {i+1}/{len(successful_recordings)}")
            print(f"   Niveau: {recording['level'] + 1}")
            print(f"   Mouvements: {recording['moves_count']}")
            
            self.game.start_level(recording['level'])
            
            for j, action in enumerate(recording['actions']):
                current_state = self.ai.get_state_representation(self.game.board)
                
                if current_state:
                    reward_boost = 10.0 * (1 - j / len(recording['actions']))
                    current_q = self.ai.q_table[current_state][action]
                    new_q = current_q + self.ai.learning_rate * reward_boost
                    self.ai.q_table[current_state][action] = new_q
                
                self.game.move_player(action)
            
            self.ai.stats['human_demos_learned'] += 1
            self.training_stats['human_demos'] += 1
        
        print(f"\n✔ L'IA a appris de {len(successful_recordings)} démonstrations")
    
    def ai_play_level(self):
        """Fait jouer l'IA sur le niveau actuel"""
        if self.ai_playing:
            return
        
        self.ai_playing = True
        
        def play():
            self.ai.reset_antiloop_mechanisms()
            old_epsilon = self.ai.epsilon
            self.ai.epsilon = 0
            
            max_steps = 200
            steps = 0
            
            while steps < max_steps and not self.game.board.is_level_complete() and self.ai_playing:
                action = self.ai.choose_action(self.game.board, training=False)
                result = self.game.move_player(action)
                
                if result == 'BOX_STUCK':
                    print("⚠️ L'IA a poussé une caisse dans un coin!")
                    if self.auto_detect_stuck_boxes:
                        self.game.reset_level()
                        self.start_time = time.time()
                        print("🔄 L'IA recommence le niveau...")
                        steps = 0
                        continue
                elif result:
                    self.audio.play_sound('move')
                    time.sleep(0.3)
                
                if self.ai.loop_counter > 5:
                    print("⚠️ L'IA est coincée dans une boucle")
                    break
                
                steps += 1
            
            self.ai.epsilon = old_epsilon
            self.ai_playing = False
            
            if self.game.board.is_level_complete():
                print("🎉 L'IA a complété le niveau!")
            else:
                print(f"❌ L'IA n'a pas pu terminer le niveau")
        
        threading.Thread(target=play, daemon=True).start()
    
    def handle_game_events(self, event):
        """Gère les événements du jeu avec enregistrement - VERSION CORRIGÉE"""
        if event.type == pygame.KEYDOWN:
            if event.key in self.key_mapping:
                direction = self.key_mapping[event.key]
                
                # Enregistrer pour l'observation
                if self.observation_mode:
                    current_state = self.ai.get_state_representation(self.game.board)
                    
                result = self.game.move_player(direction)
                
                if self.observation_mode and result and current_state:
                    self.human_recorder.record_move(current_state, direction)
                    self.ai.learn_from_human_move(current_state, direction, True)
                
                if result == 'LEVEL_COMPLETE':
                    self.audio.play_sound('level_complete')
                    
                    if self.observation_mode:
                        self.human_recorder.stop_recording(success=True)
                        print("📹 Démonstration enregistrée avec succès!")
                    
                    elapsed_time = int(time.time() - self.start_time) if self.start_time else 0
                    game_state = self.game.get_game_state()
                    self.database.save_score(
                        self.player_name,
                        game_state['level'],
                        game_state['moves'],
                        elapsed_time,
                        game_state['score']
                    )
                elif result == 'BOX_STUCK':
                    self.audio.play_sound('menu_click')
                    self.show_stuck_box_dialog()
                elif result:
                    self.audio.play_sound('move')
                    
                return True
            
            elif event.key == pygame.K_u:
                if self.game.undo_move():
                    self.audio.play_sound('undo')
                return True
                
            elif event.key == pygame.K_r:
                if self.observation_mode:
                    self.human_recorder.stop_recording(success=False)
                
                self.game.reset_level()
                self.start_time = time.time()
                self.audio.play_sound('reset')
                
                if self.observation_mode:
                    self.human_recorder.start_recording(self.game.current_level)
                return True
                
            elif event.key == pygame.K_m:
                self.state = "MENU"
                self.audio.play_music("menu")
                return True
                
            elif event.key == pygame.K_SPACE:
                game_state = self.game.get_game_state()
                if game_state and game_state['is_complete']:
                    pygame.time.wait(500)
                    if self.game.has_next_level():
                        self.game.next_level()
                        self.start_time = time.time()
                        if self.observation_mode:
                            self.human_recorder.start_recording(self.game.current_level)
                    else:
                        self.state = "MENU"
                        self.audio.play_music("menu")
                return True
        
        # Gérer les boutons du jeu
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
        
        # Gérer les boutons IA
        self.handle_ai_buttons(event)
        
        return True
    
    def handle_ai_buttons(self, event):
        """Gère les événements des boutons IA"""
        for i, button in enumerate(self.ai_buttons):
            if button.handle_event(event):
                self.audio.play_sound('menu_click')
                
                if i == 0:  # Entraîner 1x
                    if not self.training_active:
                        print("🔄 Entraînement unique...")
                        self.training_thread = threading.Thread(
                            target=lambda: self.ai_train_batch(1500),
                            daemon=True
                        )
                        self.training_thread.start()
                        button.text = "Arrêter"
                    else:
                        self.training_active = False
                        button.text = "Entraîner 1x"
                
                elif i == 1:  # Entraîner ∞
                    if not self.continuous_training:
                        print("\n🔄 ENTRAÎNEMENT CONTINU DÉMARRÉ")
                        self.training_thread = threading.Thread(
                            target=self.train_ai_continuous_background,
                            daemon=True
                        )
                        self.training_thread.start()
                        button.text = "Arrêter ∞"
                    else:
                        self.continuous_training = False
                        button.text = "Entraîner ∞"
                
                elif i == 2:  # IA Joue
                    if not self.training_active and not self.ai_playing:
                        print(f"\n🤖 L'IA joue le niveau {self.game.current_level + 1}...")
                        self.ai_play_level()
                
                elif i == 3:  # Sauver IA
                    self.ai.save_model("sokoban_ai_model.pkl")
                
                elif i == 4:  # Charger IA
                    self.ai.load_model("sokoban_ai_model.pkl")
                
                elif i == 5:  # Options IA
                    self.previous_state = self.state
                    self.state = "OPTIONS_IA"
    
    def handle_options_events(self, event):
        """Gère les événements du menu OPTIONS"""
        for i, button in enumerate(self.options_buttons):
            if button.handle_event(event):
                self.audio.play_sound('menu_click')
                
                if i == 0:  # Observer
                    self.observation_mode = not self.observation_mode
                    button.text = f"Observer: {'ON' if self.observation_mode else 'OFF'}"
                    
                    if self.observation_mode:
                        print("\n👁️ MODE OBSERVATION ACTIVÉ")
                        print("   L'IA apprend de vos mouvements!")
                        if self.state == "GAME":
                            self.human_recorder.start_recording(self.game.current_level)
                    else:
                        print("\n👁️ Mode observation désactivé")
                        self.human_recorder.stop_recording()
                
                elif i == 1:  # Détection coins
                    self.auto_detect_stuck_boxes = not self.auto_detect_stuck_boxes
                    button.text = f"Détection coins: {'ON' if self.auto_detect_stuck_boxes else 'OFF'}"
                    print(f"🔍 Détection des caisses bloquées: {'activée' if self.auto_detect_stuck_boxes else 'désactivée'}")
                
                elif i == 2:  # Apprendre des humains
                    threading.Thread(
                        target=self.train_from_human_demonstrations,
                        daemon=True
                    ).start()
                
                elif i == 3:  # Réinitialiser IA
                    self.ai = SokobanAI(learning_rate=0.15, discount_factor=0.95, epsilon=0.3)
                    print("🔄 IA réinitialisée")
                
                elif i == 4:  # Retour
                    self.state = self.previous_state if self.previous_state else "GAME"
        
        return True
    
    def draw_options(self):
        """Dessine l'écran des options IA"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # Titre
        title_text = self.title_font.render("OPTIONS DE L'IA", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(self.window_width//2, 50))
        self.screen.blit(title_text, title_rect)
        
        # Sous-titre
        subtitle_text = self.font.render("Configuration de l'Intelligence Artificielle", True, TEXT_COLOR)
        subtitle_rect = subtitle_text.get_rect(center=(self.window_width//2, 90))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Mettre à jour les textes des boutons
        self.options_buttons[0].text = f"Observer: {'ON' if self.observation_mode else 'OFF'}"
        self.options_buttons[1].text = f"Détection coins: {'ON' if self.auto_detect_stuck_boxes else 'OFF'}"
        
        # Dessiner les boutons
        for button in self.options_buttons:
            button.draw(self.screen)
        
        # Descriptions des options
        descriptions = [
            ("Observer", "L'IA apprend en vous regardant jouer"),
            ("Détection coins", "Avertit quand une caisse est bloquée"),
            ("Apprendre des humains", "Analyse vos parties réussies"),
            ("Réinitialiser IA", "Efface tout l'apprentissage de l'IA")
        ]
        
        desc_y = 500
        for desc_title, desc_text in descriptions:
            title_surface = self.font.render(desc_title + ":", True, TEXT_COLOR)
            text_surface = self.small_font.render(desc_text, True, (100, 100, 100))
            
            self.screen.blit(title_surface, (100, desc_y))
            self.screen.blit(text_surface, (100, desc_y + 25))
            desc_y += 60
    
    def ai_train_batch(self, num_episodes):
        """Entraîne l'IA pour un nombre fixe d'épisodes"""
        self.training_active = True
        self.training_stats['total_episodes'] = num_episodes
        
        for episode in range(num_episodes):
            if not self.training_active:
                break
            
            self.training_stats['current_episode'] = episode + 1
            level_index = episode % len(self.game.levels)
            self.training_stats['current_level'] = level_index
            
            self.ai.train_episode(self.game, level_index)
            
            if self.ai.stats['episodes'] > 0:
                self.training_stats['win_rate'] = (self.ai.stats['wins'] / self.ai.stats['episodes']) * 100
            
            self.ai.epsilon = max(0.01, self.ai.epsilon * 0.995)
        
        self.training_active = False
        print("✔ Entraînement terminé!")
    
    def run(self):
        """Boucle principale du jeu avec gestion du menu OPTIONS"""
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.state == "OPTIONS_IA":
                            self.state = self.previous_state if self.previous_state else "GAME"
                        elif self.state == "GAME":
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
                elif self.state == "OPTIONS_IA":
                    running = self.handle_options_events(event)
            
            # Dessiner selon l'état
            if self.state == "MENU":
                self.draw_menu()
            elif self.state == "GAME":
                self.draw_game()
            elif self.state == "SCORES":
                self.draw_scores()
            elif self.state == "SETTINGS":
                self.draw_settings()
            elif self.state == "OPTIONS_IA":
                self.draw_options()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        # Nettoyage
        pygame.quit()
        sys.exit()


# Programme principal
if __name__ == "__main__":
    try:
        print("🎮 Sokoban AI Trainer - Interface étendue")
        print("=" * 60)
        print("Fonctionnalités incluses:")
        print("✔ Fenêtre agrandie (1200x800) pour plus d'espace")
        print("✔ Panneau dédié pour les contrôles IA")
        print("✔ Interface mieux organisée sans superposition")
        print("✔ Entraînement par renforcement (Q-learning)")
        print("✔ Apprentissage par observation des humains")
        print("✔ Détection des caisses bloquées dans les coins")
        print("✔ Système anti-boucles avancé")
        print("✔ Entraînement continu sur tous les niveaux")
        print("✔ Sauvegarde et chargement des modèles")
        print("=" * 60)
        
        trainer = SokobanAITrainer()
        trainer.run()
        
    except Exception as e:
        print(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()
        sys.exit()
