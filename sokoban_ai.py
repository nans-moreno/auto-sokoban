"""
Module d'Intelligence Artificielle pour le jeu Sokoban
Utilise le Q-learning (apprentissage par renforcement) pour apprendre à jouer
"""

import numpy as np
import pickle
import random
from collections import defaultdict
import time
from game_logic import SokobanGame, GameBoard

class SokobanAI:
    """
    IA pour le jeu Sokoban utilisant le Q-learning
    """
    
    def __init__(self, learning_rate=0.1, discount_factor=0.95, epsilon=0.1):
        """
        Initialise l'IA avec les paramètres d'apprentissage
        
        Args:
            learning_rate: Taux d'apprentissage (alpha)
            discount_factor: Facteur d'actualisation (gamma)
            epsilon: Probabilité d'exploration
        """
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        self.q_table = defaultdict(lambda: defaultdict(float))
        self.training_episodes = 0
        
        # Actions possibles
        self.actions = ['UP', 'DOWN', 'LEFT', 'RIGHT']
        
        # Statistiques
        self.stats = {
            'wins': 0,
            'total_moves': 0,
            'episodes': 0,
            'best_solution': {}  # Meilleure solution par niveau
        }
    
    def get_state_representation(self, board):
        """
        Convertit l'état du jeu en une représentation pour la Q-table
        
        Args:
            board: Instance de GameBoard
            
        Returns:
            tuple: Représentation de l'état
        """
        player_pos = board.player_pos
        if not player_pos:
            return None
        
        # Positions relatives des caisses
        box_positions = []
        for box in sorted(board.box_positions):
            rel_pos = (box[0] - player_pos[0], box[1] - player_pos[1])
            box_positions.append(rel_pos)
        
        # Positions relatives des cibles non occupées
        free_targets = []
        for target in sorted(board.target_positions):
            if board.grid[target[0]][target[1]] != 4:  # Pas de caisse sur la cible
                rel_pos = (target[0] - player_pos[0], target[1] - player_pos[1])
                free_targets.append(rel_pos)
        
        # État : tuple des positions relatives
        state = (tuple(box_positions), tuple(free_targets))
        return state
    
    def choose_action(self, board, training=True):
        """
        Choisit une action selon la politique epsilon-greedy
        
        Args:
            board: Instance de GameBoard
            training: Si True, utilise l'exploration epsilon-greedy
            
        Returns:
            str: Action choisie
        """
        state = self.get_state_representation(board)
        if state is None:
            return random.choice(self.actions)
        
        # Exploration vs Exploitation
        if training and random.random() < self.epsilon:
            return random.choice(self.actions)
        
        # Exploitation : choisir la meilleure action selon la Q-table
        q_values = self.q_table[state]
        if not q_values:
            return random.choice(self.actions)
        
        # Trouver les actions avec la valeur Q maximale
        max_q = max(q_values.values())
        best_actions = [action for action, q in q_values.items() if q == max_q]
        
        return random.choice(best_actions)
    
    def calculate_reward(self, board, old_board, action_success):
        """
        Calcule la récompense pour une action
        
        Args:
            board: État actuel du plateau
            old_board: État précédent du plateau
            action_success: Si l'action a réussi
            
        Returns:
            float: Récompense
        """
        if not action_success:
            return -0.1  # Pénalité pour action invalide
        
        # Récompense massive pour avoir terminé le niveau
        if board.is_level_complete():
            return 100.0
        
        reward = 0.0
        
        # Récompense pour mettre une caisse sur une cible
        old_boxes_on_targets = sum(1 for box in old_board.box_positions 
                                  if box in old_board.target_positions)
        new_boxes_on_targets = sum(1 for box in board.box_positions 
                                  if box in board.target_positions)
        
        if new_boxes_on_targets > old_boxes_on_targets:
            reward += 10.0
        elif new_boxes_on_targets < old_boxes_on_targets:
            reward -= 5.0  # Pénalité pour retirer une caisse d'une cible
        
        # Pénalité pour les mouvements (encourage les solutions courtes)
        reward -= 0.01
        
        # Pénalité pour les caisses bloquées dans les coins
        for box in board.box_positions:
            if self._is_box_stuck(board, box[0], box[1]):
                reward -= 1.0
        
        return reward
    
    def _is_box_stuck(self, board, box_row, box_col):
        """
        Vérifie si une caisse est bloquée définitivement
        """
        # Si la caisse est sur une cible, elle n'est pas bloquée
        if (box_row, box_col) in board.target_positions:
            return False
        
        # Vérifier si la caisse est dans un coin
        walls_around = 0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        for dr, dc in directions:
            new_row, new_col = box_row + dr, box_col + dc
            if board.is_wall(new_row, new_col):
                walls_around += 1
        
        # Si la caisse est entourée de 2 murs adjacents (coin), elle est bloquée
        if walls_around >= 2:
            # Vérifier les coins
            if (board.is_wall(box_row - 1, box_col) and board.is_wall(box_row, box_col - 1)) or \
               (board.is_wall(box_row - 1, box_col) and board.is_wall(box_row, box_col + 1)) or \
               (board.is_wall(box_row + 1, box_col) and board.is_wall(box_row, box_col - 1)) or \
               (board.is_wall(box_row + 1, box_col) and board.is_wall(box_row, box_col + 1)):
                return True
        
        return False
    
    def update_q_table(self, state, action, reward, next_state):
        """
        Met à jour la Q-table selon l'équation de Bellman
        """
        if state is None:
            return
        
        current_q = self.q_table[state][action]
        
        # Valeur Q maximale pour le prochain état
        if next_state is not None and self.q_table[next_state]:
            max_next_q = max(self.q_table[next_state].values())
        else:
            max_next_q = 0.0
        
        # Équation de mise à jour Q-learning
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_table[state][action] = new_q
    
    def train_episode(self, game, level_index, max_steps=500):
        """
        Entraîne l'IA sur un épisode (une partie)
        
        Args:
            game: Instance de SokobanGame
            level_index: Index du niveau
            max_steps: Nombre maximum de pas par épisode
            
        Returns:
            dict: Statistiques de l'épisode
        """
        game.start_level(level_index)
        
        steps = 0
        total_reward = 0
        moves_sequence = []
        
        while steps < max_steps and not game.board.is_level_complete():
            # État actuel
            state = self.get_state_representation(game.board)
            
            # Copie de l'état actuel pour calculer la récompense
            old_board = GameBoard(game.board.get_display_grid())
            
            # Choisir une action
            action = self.choose_action(game.board, training=True)
            
            # Exécuter l'action
            direction = game.directions[action]
            success = game.board.move_player(direction)
            
            # Calculer la récompense
            reward = self.calculate_reward(game.board, old_board, success)
            total_reward += reward
            
            # Nouvel état
            next_state = self.get_state_representation(game.board)
            
            # Mettre à jour la Q-table
            self.update_q_table(state, action, reward, next_state)
            
            if success:
                moves_sequence.append(action)
                game.moves_count += 1
            
            steps += 1
        
        # Statistiques
        episode_stats = {
            'completed': game.board.is_level_complete(),
            'steps': steps,
            'moves': len(moves_sequence),
            'total_reward': total_reward,
            'moves_sequence': moves_sequence
        }
        
        # Mettre à jour les statistiques globales
        self.stats['episodes'] += 1
        if episode_stats['completed']:
            self.stats['wins'] += 1
            # Sauvegarder la meilleure solution
            if level_index not in self.stats['best_solution'] or \
               len(moves_sequence) < len(self.stats['best_solution'][level_index]):
                self.stats['best_solution'][level_index] = moves_sequence
        
        return episode_stats
    
    def train(self, game, num_episodes=1000, levels=None, verbose=True):
        """
        Entraîne l'IA sur plusieurs épisodes
        
        Args:
            game: Instance de SokobanGame
            num_episodes: Nombre d'épisodes d'entraînement
            levels: Liste des indices de niveaux (None = tous)
            verbose: Afficher la progression
        """
        if levels is None:
            levels = list(range(len(game.levels)))
        
        self.training_episodes = num_episodes
        
        # Diminuer progressivement epsilon (exploration)
        initial_epsilon = self.epsilon
        epsilon_decay = 0.995
        min_epsilon = 0.01
        
        for episode in range(num_episodes):
            # Choisir un niveau aléatoire
            level_index = random.choice(levels)
            
            # Entraîner sur un épisode
            stats = self.train_episode(game, level_index)
            
            # Diminuer epsilon
            self.epsilon = max(min_epsilon, self.epsilon * epsilon_decay)
            
            # Afficher la progression
            if verbose and (episode + 1) % 100 == 0:
                win_rate = self.stats['wins'] / self.stats['episodes'] * 100
                print(f"Épisode {episode + 1}/{num_episodes} - "
                      f"Taux de victoire: {win_rate:.1f}% - "
                      f"Epsilon: {self.epsilon:.3f}")
        
        # Restaurer epsilon
        self.epsilon = initial_epsilon
        
        if verbose:
            print(f"\nEntraînement terminé!")
            print(f"Victoires totales: {self.stats['wins']}/{self.stats['episodes']}")
            print(f"Taille de la Q-table: {len(self.q_table)} états")
    
    def play(self, game, level_index, max_steps=200, delay=0.5):
        """
        Fait jouer l'IA sur un niveau
        
        Args:
            game: Instance de SokobanGame
            level_index: Index du niveau
            max_steps: Nombre maximum de pas
            delay: Délai entre les mouvements (en secondes)
            
        Returns:
            bool: True si le niveau a été complété
        """
        game.start_level(level_index)
        
        print(f"\n🤖 L'IA joue le niveau {level_index + 1}...")
        
        steps = 0
        moves = []
        
        while steps < max_steps and not game.board.is_level_complete():
            # Choisir la meilleure action (sans exploration)
            old_epsilon = self.epsilon
            self.epsilon = 0  # Pas d'exploration pendant le jeu
            action = self.choose_action(game.board, training=False)
            self.epsilon = old_epsilon
            
            # Exécuter l'action
            direction = game.directions[action]
            success = game.board.move_player(direction)
            
            if success:
                moves.append(action)
                print(f"Mouvement {len(moves)}: {action}")
                
                # Afficher la grille (optionnel)
                if delay > 0:
                    time.sleep(delay)
            
            steps += 1
        
        if game.board.is_level_complete():
            print(f"✅ Niveau complété en {len(moves)} mouvements!")
            return True
        else:
            print(f"❌ Échec après {steps} tentatives")
            return False
    
    def save_model(self, filename="sokoban_ai_model.pkl"):
        """Sauvegarde le modèle entraîné"""
        model_data = {
            'q_table': dict(self.q_table),
            'stats': self.stats,
            'training_episodes': self.training_episodes,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"📁 Modèle sauvegardé dans {filename}")
    
    def load_model(self, filename="sokoban_ai_model.pkl"):
        """Charge un modèle entraîné"""
        try:
            with open(filename, 'rb') as f:
                model_data = pickle.load(f)
            
            self.q_table = defaultdict(lambda: defaultdict(float), model_data['q_table'])
            self.stats = model_data['stats']
            self.training_episodes = model_data['training_episodes']
            self.learning_rate = model_data.get('learning_rate', 0.1)
            self.discount_factor = model_data.get('discount_factor', 0.95)
            
            print(f"📁 Modèle chargé depuis {filename}")
            print(f"   - États dans la Q-table: {len(self.q_table)}")
            print(f"   - Épisodes d'entraînement: {self.training_episodes}")
            return True
        except FileNotFoundError:
            print(f"❌ Fichier {filename} non trouvé")
            return False


# Programme de test et d'entraînement
if __name__ == "__main__":
    print("🎮 Sokoban AI - Apprentissage par renforcement")
    print("=" * 50)
    
    # Créer le jeu et l'IA
    game = SokobanGame()
    ai = SokobanAI(learning_rate=0.1, discount_factor=0.95, epsilon=0.2)
    
    # Charger un modèle existant ou entraîner un nouveau
    choice = input("\n1. Entraîner une nouvelle IA\n2. Charger une IA existante\nChoix (1/2): ")
    
    if choice == "2":
        if not ai.load_model():
            print("Entraînement d'une nouvelle IA...")
            choice = "1"
    
    if choice == "1":
        # Entraîner l'IA
        print("\n🏋️ Début de l'entraînement...")
        print("Cela peut prendre quelques minutes...")
        
        # Entraîner sur les premiers niveaux
        ai.train(game, num_episodes=2000, levels=[0, 1], verbose=True)
        
        # Sauvegarder le modèle
        ai.save_model()
    
    # Tester l'IA
    print("\n🎯 Test de l'IA sur les niveaux...")
    
    for level in range(min(2, len(game.levels))):
        print(f"\n--- Niveau {level + 1} ---")
        success = ai.play(game, level, max_steps=100, delay=0.1)
        
        if level in ai.stats['best_solution']:
            print(f"Meilleure solution connue: {len(ai.stats['best_solution'][level])} mouvements")
    
    print("\n✨ Terminé!")
