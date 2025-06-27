import numpy as np
import random
from collections import defaultdict, deque
import pickle
import os
from game_logic import SokobanGame

class SokobanEnv:
    """
    Wrapper pour l'environnement Sokoban afin de l'adapter aux algorithmes de RL.
    """
    def __init__(self, game_instance: SokobanGame):
        self.game = game_instance
        self.action_space = ["UP", "DOWN", "LEFT", "RIGHT"]
        self.current_level_data = None
        self.initial_state = None

    def reset(self, level_index=0):
        """
        Réinitialise l'environnement au début d'un niveau.
        Retourne l'état initial.
        """
        self.game.start_level(level_index)
        self.current_level_data = [row[:] for row in self.game.levels[level_index]]
        self.initial_state = self._get_state()
        return self.initial_state

    def step(self, action: str):
        """
        Exécute une action dans l'environnement.
        Retourne (nouvel_état, récompense, terminé, info).
        """
        initial_grid = [row[:] for row in self.game.board.get_display_grid()]
        initial_box_positions = self.game.board.box_positions[:]
        initial_player_pos = self.game.board.player_pos
        initial_moves = self.game.moves_count

        result = self.game.move_player(action)
        new_state = self._get_state()
        done = self.game.board.is_level_complete()

        # Système de récompenses amélioré
        reward = self._calculate_reward(initial_grid, initial_box_positions, initial_player_pos, result, done)

        info = {"moves": self.game.moves_count, "score": self.game.score, "valid_move": result}
        return new_state, reward, done, info

    def _calculate_reward(self, initial_grid, initial_box_positions, initial_player_pos, move_result, done):
        """
        Calcule la récompense basée sur l'action effectuée.
        """
        reward = 0
        
        # Pénalité de base pour chaque mouvement
        reward -= 1
        
        # Pénalité pour mouvement invalide
        if not move_result:
            return -10
        
        # Récompense massive pour terminer le niveau
        if done:
            return 1000
        
        # Récompenses pour placer des caisses sur des cibles
        current_box_positions = self.game.board.box_positions
        boxes_on_targets = 0
        for box_pos in current_box_positions:
            if self.game.board.is_target(box_pos[0], box_pos[1]):
                boxes_on_targets += 1
        
        # Récompense progressive pour les caisses sur cibles
        reward += boxes_on_targets * 50
        
        # Bonus pour nouvelle caisse sur cible
        initial_boxes_on_targets = 0
        for box_pos in initial_box_positions:
            if self.game.board.is_target(box_pos[0], box_pos[1]):
                initial_boxes_on_targets += 1
        
        if boxes_on_targets > initial_boxes_on_targets:
            reward += 200  # Bonus pour nouvelle caisse placée
        elif boxes_on_targets < initial_boxes_on_targets:
            reward -= 100  # Pénalité pour retirer une caisse d'une cible
        
        # Récompense pour se rapprocher des caisses non placées
        reward += self._proximity_reward()
        
        # Pénalité pour les caisses dans les coins (deadlock)
        reward -= self._deadlock_penalty() * 50
        
        return reward

    def _proximity_reward(self):
        """
        Récompense basée sur la proximité du joueur aux caisses non placées.
        """
        player_pos = self.game.board.player_pos
        if not player_pos:
            return 0
        
        unplaced_boxes = []
        for box_pos in self.game.board.box_positions:
            if not self.game.board.is_target(box_pos[0], box_pos[1]):
                unplaced_boxes.append(box_pos)
        
        if not unplaced_boxes:
            return 0
        
        # Distance Manhattan minimale aux caisses non placées
        min_distance = min(abs(player_pos[0] - box[0]) + abs(player_pos[1] - box[1]) 
                          for box in unplaced_boxes)
        
        # Récompense inversement proportionnelle à la distance
        return max(0, 10 - min_distance)

    def _deadlock_penalty(self):
        """
        Détecte les situations de deadlock (caisses coincées).
        """
        penalty = 0
        for box_pos in self.game.board.box_positions:
            if self.game.board.is_target(box_pos[0], box_pos[1]):
                continue  # Ignore les caisses déjà placées
            
            row, col = box_pos
            # Vérifier si la caisse est dans un coin
            adjacent_walls = 0
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if (self.game.board.is_wall(new_row, new_col) or 
                    not self.game.board.is_valid_position(new_row, new_col)):
                    adjacent_walls += 1
            
            if adjacent_walls >= 2:
                penalty += 1
        
        return penalty

    def _get_state(self):
        """
        Retourne une représentation de l'état actuel du jeu.
        """
        grid = self.game.board.get_display_grid()
        # Convertir la grille en un tuple pour qu'elle soit hashable
        flat_grid = tuple(tuple(row) for row in grid)
        player_pos = self.game.board.player_pos
        box_positions = tuple(sorted(self.game.board.box_positions))
        return (flat_grid, player_pos, box_positions)

    def get_possible_actions(self):
        """
        Retourne la liste des actions possibles depuis l'état actuel.
        """
        possible_actions = []
        current_row, current_col = self.game.board.player_pos

        for action_name, (dr, dc) in self.game.directions.items():
            next_row, next_col = current_row + dr, current_col + dc
            if self.game.board.is_valid_position(next_row, next_col):
                if not self.game.board.is_wall(next_row, next_col):
                    if self.game.board.is_box(next_row, next_col):
                        # Si c'est une caisse, vérifier si elle peut être poussée
                        if self.game.board.can_push_box(next_row, next_col, (dr, dc)):
                            possible_actions.append(action_name)
                    else:
                        # Si c'est un espace vide ou une cible, le joueur peut s'y déplacer
                        possible_actions.append(action_name)
        return possible_actions


class AdvancedQLearningAgent:
    """
    Agent Q-learning amélioré avec exploration adaptative et mémoire d'expérience.
    """
    def __init__(self, action_space, alpha=0.1, gamma=0.95, epsilon=1.0, 
                 epsilon_decay=0.995, epsilon_min=0.01, memory_size=10000):
        self.q_table = defaultdict(lambda: np.zeros(len(action_space)))
        self.action_space = action_space
        self.alpha = alpha  # Taux d'apprentissage
        self.gamma = gamma  # Facteur de réduction
        self.epsilon = epsilon  # Taux d'exploration
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        
        # Mémoire d'expérience pour replay
        self.memory = deque(maxlen=memory_size)
        self.replay_batch_size = 32
        
        # Statistiques d'apprentissage
        self.episode_rewards = []
        self.episode_lengths = []

    def remember(self, state, action, reward, next_state, done):
        """
        Stocke une expérience dans la mémoire.
        """
        self.memory.append((state, action, reward, next_state, done))

    def choose_action(self, state, possible_actions):
        """
        Choisit une action en utilisant la stratégie epsilon-greedy améliorée.
        """
        if not possible_actions:
            return random.choice(self.action_space)
        
        if random.uniform(0, 1) < self.epsilon:
            # Exploration: choisir une action aléatoire parmi les possibles
            return random.choice(possible_actions)
        else:
            # Exploitation: choisir l'action avec la plus haute valeur Q
            q_values = self.q_table[state]
            # Filtrer les Q-values pour les actions possibles
            action_q_values = [(action, q_values[self.action_space.index(action)]) 
                              for action in possible_actions]
            best_action = max(action_q_values, key=lambda x: x[1])[0]
            return best_action

    def learn(self, state, action, reward, next_state, done):
        """
        Met à jour la table Q après une étape.
        """
        action_index = self.action_space.index(action)
        
        # Valeur Q actuelle
        current_q = self.q_table[state][action_index]
        
        # Maximum de la valeur Q pour le prochain état
        max_next_q = np.max(self.q_table[next_state]) if not done else 0
        
        # Nouvelle valeur Q (équation de Bellman)
        target_q = reward + self.gamma * max_next_q
        new_q = current_q + self.alpha * (target_q - current_q)
        self.q_table[state][action_index] = new_q

        # Stocker l'expérience
        self.remember(state, action, reward, next_state, done)

    def replay_experience(self):
        """
        Rejoue des expériences aléatoires de la mémoire pour améliorer l'apprentissage.
        """
        if len(self.memory) < self.replay_batch_size:
            return
        
        batch = random.sample(self.memory, self.replay_batch_size)
        for state, action, reward, next_state, done in batch:
            self.learn(state, action, reward, next_state, done)

    def decay_epsilon(self):
        """
        Réduit le taux d'exploration.
        """
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save_model(self, filepath):
        """
        Sauvegarde le modèle.
        """
        model_data = {
            'q_table': dict(self.q_table),
            'epsilon': self.epsilon,
            'episode_rewards': self.episode_rewards,
            'episode_lengths': self.episode_lengths
        }
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)

    def load_model(self, filepath):
        """
        Charge un modèle sauvegardé.
        """
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            self.q_table = defaultdict(lambda: np.zeros(len(self.action_space)), model_data['q_table'])
            self.epsilon = model_data.get('epsilon', self.epsilon)
            self.episode_rewards = model_data.get('episode_rewards', [])
            self.episode_lengths = model_data.get('episode_lengths', [])
            return True
        return False


class SokobanBot:
    """
    Classe principale pour le bot Sokoban amélioré.
    """
    def __init__(self, game_instance: SokobanGame):
        self.env = SokobanEnv(game_instance)
        self.agent = AdvancedQLearningAgent(action_space=self.env.action_space)
        self.models_dir = "models"
        
        # Créer le dossier des modèles s'il n'existe pas
        if not os.path.exists(self.models_dir):
            os.makedirs(self.models_dir)

    def train(self, num_episodes=1000, level_index=0, save_model=True):
        """
        Entraîne le bot sur un niveau spécifique avec des améliorations.
        """
        print(f"\nDébut de l'entraînement pour le niveau {level_index + 1}...")
        
        # Charger un modèle existant si disponible
        model_path = os.path.join(self.models_dir, f"sokoban_level_{level_index}.pkl")
        if self.agent.load_model(model_path):
            print(f"Modèle existant chargé pour le niveau {level_index + 1}")
        
        best_reward = float('-inf')
        best_episode = 0
        no_improvement_count = 0
        
        for episode in range(num_episodes):
            state = self.env.reset(level_index)
            done = False
            total_reward = 0
            moves_in_episode = 0
            episode_start_time = 0

            while not done and moves_in_episode < 500:  # Limite de mouvements
                possible_actions = self.env.get_possible_actions()
                action = self.agent.choose_action(state, possible_actions)
                
                next_state, reward, done, info = self.env.step(action)
                self.agent.learn(state, action, reward, next_state, done)
                
                state = next_state
                total_reward += reward
                moves_in_episode = info["moves"]

            # Replay d'expérience
            if episode % 10 == 0:
                self.agent.replay_experience()

            # Réduction de l'exploration
            self.agent.decay_epsilon()
            
            # Statistiques
            self.agent.episode_rewards.append(total_reward)
            self.agent.episode_lengths.append(moves_in_episode)
            
            # Suivi des améliorations
            if total_reward > best_reward:
                best_reward = total_reward
                best_episode = episode
                no_improvement_count = 0
            else:
                no_improvement_count += 1
            
            # Affichage périodique
            if episode % 100 == 0 or episode == num_episodes - 1:
                avg_reward = np.mean(self.agent.episode_rewards[-100:]) if self.agent.episode_rewards else 0
                print(f"Épisode {episode + 1}/{num_episodes} - "
                      f"Récompense moyenne: {avg_reward:.2f}, "
                      f"Meilleure: {best_reward:.2f} (épisode {best_episode + 1}), "
                      f"Epsilon: {self.agent.epsilon:.3f}")
            
            # Arrêt anticipé si pas d'amélioration
            if no_improvement_count > 200 and episode > 500:
                print(f"Arrêt anticipé à l'épisode {episode + 1} (pas d'amélioration)")
                break

        # Sauvegarder le modèle
        if save_model:
            self.agent.save_model(model_path)
            print(f"Modèle sauvegardé: {model_path}")
        
        print("Entraînement terminé.")
        return self.agent.episode_rewards, self.agent.episode_lengths

    def play_level(self, level_index=0, max_moves=500, verbose=False):
        """
        Fait jouer le bot sur un niveau après l'entraînement.
        """
        if verbose:
            print(f"\nLe bot joue le niveau {level_index + 1}...")
        
        state = self.env.reset(level_index)
        done = False
        moves = 0
        actions_taken = []
        total_reward = 0

        # Mode exploitation pure
        original_epsilon = self.agent.epsilon
        self.agent.epsilon = 0.0

        while not done and moves < max_moves:
            possible_actions = self.env.get_possible_actions()
            if not possible_actions:
                if verbose:
                    print("Aucune action possible, le bot est bloqué.")
                break
            
            action = self.agent.choose_action(state, possible_actions)
            next_state, reward, done, info = self.env.step(action)
            
            state = next_state
            moves = info["moves"]
            actions_taken.append(action)
            total_reward += reward
            
            if verbose and moves % 10 == 0:
                print(f"Mouvement {moves}, Action: {action}, Récompense totale: {total_reward}")

        # Restaurer l'epsilon
        self.agent.epsilon = original_epsilon

        if verbose:
            if done:
                print(f"Niveau {level_index + 1} terminé en {moves} mouvements!")
            else:
                print(f"Niveau {level_index + 1} non terminé après {moves} mouvements.")
        
        return done, moves, actions_taken

    def get_training_stats(self):
        """
        Retourne les statistiques d'entraînement.
        """
        if not self.agent.episode_rewards:
            return None
        
        return {
            'total_episodes': len(self.agent.episode_rewards),
            'average_reward': np.mean(self.agent.episode_rewards),
            'best_reward': np.max(self.agent.episode_rewards),
            'average_length': np.mean(self.agent.episode_lengths),
            'current_epsilon': self.agent.epsilon,
            'q_table_size': len(self.agent.q_table)
        }


if __name__ == "__main__":
    # Exemple d'utilisation avec tests
    game = SokobanGame()
    bot = SokobanBot(game)

    # Test d'entraînement et de jeu
    for level in range(min(2, len(game.levels))):
        print(f"\n{'='*50}")
        print(f"TEST NIVEAU {level + 1}")
        print(f"{'='*50}")
        
        # Entraînement
        rewards, lengths = bot.train(num_episodes=200, level_index=level)
        
        # Statistiques
        stats = bot.get_training_stats()
        if stats:
            print(f"\nStatistiques d'entraînement:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        
        # Test de jeu
        print(f"\nTest de performance:")
        for i in range(3):
            solved, moves, actions = bot.play_level(level_index=level, verbose=False)
            print(f"  Tentative {i+1}: {'Réussi' if solved else 'Échec'} en {moves} mouvements")

