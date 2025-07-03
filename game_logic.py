"""
Module de logique du jeu Sokoban
Contient les classes principales pour gérer l'état du jeu et les règles
Inclut la détection des caisses bloquées dans les coins
"""

class GameBoard:
    """
    Représente la grille de jeu Sokoban
    Utilise une matrice pour représenter les différents éléments :
    - -1 : Obstacle/Mur
    - 0 : Espace vide
    - 1 : Emplacement cible (où les caisses doivent être placées)
    - 2 : Caisse
    - 3 : Joueur
    - 4 : Caisse sur emplacement cible
    - 5 : Joueur sur emplacement cible
    """
    
    def __init__(self, level_data):
        """
        Initialise la grille de jeu à partir des données de niveau
        
        Args:
            level_data: Liste de listes représentant la grille initiale
        """
        self.grid = [row[:] for row in level_data]  # Copie profonde
        self.rows = len(self.grid)
        self.cols = len(self.grid[0]) if self.rows > 0 else 0
        self.player_pos = self._find_player_position()
        self.target_positions = self._find_target_positions()
        self.box_positions = self._find_box_positions()
        self.moves_history = []  # Pour l'annulation des mouvements
        
    def _find_player_position(self):
        """Trouve la position initiale du joueur"""
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == 3 or self.grid[row][col] == 5:
                    return (row, col)
        return None
    
    def _find_target_positions(self):
        """Trouve toutes les positions des emplacements cibles"""
        targets = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == 1 or self.grid[row][col] == 4 or self.grid[row][col] == 5:
                    targets.append((row, col))
        return targets
    
    def _find_box_positions(self):
        """Trouve toutes les positions des caisses"""
        boxes = []
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] == 2 or self.grid[row][col] == 4:
                    boxes.append((row, col))
        return boxes
    
    def is_valid_position(self, row, col):
        """Vérifie si une position est valide (dans les limites de la grille)"""
        return 0 <= row < self.rows and 0 <= col < self.cols
    
    def is_wall(self, row, col):
        """Vérifie si une position contient un mur"""
        if not self.is_valid_position(row, col):
            return True
        return self.grid[row][col] == -1
    
    def is_box(self, row, col):
        """Vérifie si une position contient une caisse"""
        if not self.is_valid_position(row, col):
            return False
        return self.grid[row][col] == 2 or self.grid[row][col] == 4
    
    def is_target(self, row, col):
        """Vérifie si une position est un emplacement cible"""
        return (row, col) in self.target_positions
    
    def can_move_to(self, row, col):
        """Vérifie si le joueur peut se déplacer vers une position"""
        if not self.is_valid_position(row, col) or self.is_wall(row, col):
            return False
        return not self.is_box(row, col)
    
    def can_push_box(self, box_row, box_col, direction):
        """
        Vérifie si une caisse peut être poussée dans une direction
        
        Args:
            box_row, box_col: Position de la caisse
            direction: Tuple (delta_row, delta_col) représentant la direction
        
        Returns:
            bool: True si la caisse peut être poussée
        """
        new_row = box_row + direction[0]
        new_col = box_col + direction[1]
        
        if not self.is_valid_position(new_row, new_col):
            return False
        
        if self.is_wall(new_row, new_col) or self.is_box(new_row, new_col):
            return False
        
        return True
    
    def is_box_in_corner(self, box_row, box_col):
        """
        Vérifie si une caisse est bloquée dans un coin (situation irréversible)
        
        Args:
            box_row, box_col: Position de la caisse
            
        Returns:
            bool: True si la caisse est dans un coin et ne peut plus bouger
        """
        # Si la caisse est sur une cible, elle n'est pas bloquée
        if self.is_target(box_row, box_col):
            return False
        
        # Vérifier les 4 coins possibles
        # Coin haut-gauche
        if self.is_wall(box_row - 1, box_col) and self.is_wall(box_row, box_col - 1):
            return True
        
        # Coin haut-droite
        if self.is_wall(box_row - 1, box_col) and self.is_wall(box_row, box_col + 1):
            return True
        
        # Coin bas-gauche
        if self.is_wall(box_row + 1, box_col) and self.is_wall(box_row, box_col - 1):
            return True
        
        # Coin bas-droite
        if self.is_wall(box_row + 1, box_col) and self.is_wall(box_row, box_col + 1):
            return True
        
        return False
    
    def is_box_stuck_on_wall(self, box_row, box_col):
        """
        Vérifie si une caisse est bloquée contre un mur sans cibles accessibles
        
        Args:
            box_row, box_col: Position de la caisse
            
        Returns:
            bool: True si la caisse est définitivement bloquée
        """
        # Si la caisse est sur une cible, elle n'est pas bloquée
        if self.is_target(box_row, box_col):
            return False
        
        # Vérifier si la caisse est contre un mur horizontal (haut ou bas)
        if self.is_wall(box_row - 1, box_col):
            # Mur en haut, vérifier s'il y a des cibles sur cette ligne
            targets_on_row = [t for t in self.target_positions if t[0] == box_row]
            if not targets_on_row:
                # Pas de cibles sur cette ligne, vérifier si bloquée des deux côtés
                if self.is_wall(box_row, box_col - 1) or self.is_wall(box_row, box_col + 1):
                    return True
                
        if self.is_wall(box_row + 1, box_col):
            # Mur en bas, vérifier s'il y a des cibles sur cette ligne
            targets_on_row = [t for t in self.target_positions if t[0] == box_row]
            if not targets_on_row:
                # Pas de cibles sur cette ligne, vérifier si bloquée des deux côtés
                if self.is_wall(box_row, box_col - 1) or self.is_wall(box_row, box_col + 1):
                    return True
        
        # Vérifier si la caisse est contre un mur vertical (gauche ou droite)
        if self.is_wall(box_row, box_col - 1):
            # Mur à gauche, vérifier s'il y a des cibles sur cette colonne
            targets_on_col = [t for t in self.target_positions if t[1] == box_col]
            if not targets_on_col:
                # Pas de cibles sur cette colonne, vérifier si bloquée des deux côtés
                if self.is_wall(box_row - 1, box_col) or self.is_wall(box_row + 1, box_col):
                    return True
                
        if self.is_wall(box_row, box_col + 1):
            # Mur à droite, vérifier s'il y a des cibles sur cette colonne
            targets_on_col = [t for t in self.target_positions if t[1] == box_col]
            if not targets_on_col:
                # Pas de cibles sur cette colonne, vérifier si bloquée des deux côtés
                if self.is_wall(box_row - 1, box_col) or self.is_wall(box_row + 1, box_col):
                    return True
        
        return False
    
    def check_for_stuck_boxes(self):
        """
        Vérifie si des caisses sont définitivement bloquées
        
        Returns:
            list: Liste des positions des caisses bloquées
        """
        stuck_boxes = []
        
        for box_pos in self.box_positions:
            box_row, box_col = box_pos
            
            # Vérifier si la caisse est dans un coin
            if self.is_box_in_corner(box_row, box_col):
                stuck_boxes.append(box_pos)
            # Ou si elle est bloquée contre un mur
            elif self.is_box_stuck_on_wall(box_row, box_col):
                stuck_boxes.append(box_pos)
        
        return stuck_boxes
    
    def move_player(self, direction):
        """
        Déplace le joueur dans une direction donnée
        
        Args:
            direction: Tuple (delta_row, delta_col) représentant la direction
        
        Returns:
            str ou bool: 'BOX_STUCK' si une caisse est bloquée, True si succès, False sinon
        """
        if not self.player_pos:
            return False
        
        current_row, current_col = self.player_pos
        new_row = current_row + direction[0]
        new_col = current_col + direction[1]
        
        # Sauvegarder l'état actuel pour l'annulation
        self._save_state()
        
        # Vérifier si la nouvelle position est valide
        if not self.is_valid_position(new_row, new_col) or self.is_wall(new_row, new_col):
            self.moves_history.pop()  # Retirer la sauvegarde inutile
            return False
        
        box_pushed = False
        box_new_position = None
        
        # Vérifier s'il y a une caisse à pousser
        if self.is_box(new_row, new_col):
            if not self.can_push_box(new_row, new_col, direction):
                self.moves_history.pop()  # Retirer la sauvegarde inutile
                return False
            
            # Déplacer la caisse
            box_new_row = new_row + direction[0]
            box_new_col = new_col + direction[1]
            box_new_position = (box_new_row, box_new_col)
            box_pushed = True
            
            # Retirer la caisse de sa position actuelle
            if self.is_target(new_row, new_col):
                self.grid[new_row][new_col] = 1  # Emplacement cible vide
            else:
                self.grid[new_row][new_col] = 0  # Espace vide
            
            # Placer la caisse à sa nouvelle position
            if self.is_target(box_new_row, box_new_col):
                self.grid[box_new_row][box_new_col] = 4  # Caisse sur cible
            else:
                self.grid[box_new_row][box_new_col] = 2  # Caisse normale
            
            # Mettre à jour la liste des positions des caisses
            self.box_positions = [pos for pos in self.box_positions if pos != (new_row, new_col)]
            self.box_positions.append((box_new_row, box_new_col))
        
        # Déplacer le joueur
        # Restaurer l'ancienne position du joueur
        if self.is_target(current_row, current_col):
            self.grid[current_row][current_col] = 1  # Emplacement cible vide
        else:
            self.grid[current_row][current_col] = 0  # Espace vide
        
        # Placer le joueur à sa nouvelle position
        if self.is_target(new_row, new_col):
            self.grid[new_row][new_col] = 5  # Joueur sur cible
        else:
            self.grid[new_row][new_col] = 3  # Joueur normal
        
        # Mettre à jour la position du joueur
        self.player_pos = (new_row, new_col)
        
        # Vérifier si une caisse vient d'être poussée dans un coin
        if box_pushed and box_new_position:
            if self.is_box_in_corner(box_new_position[0], box_new_position[1]):
                return 'BOX_STUCK'
        
        return True
    
    def _save_state(self):
        """Sauvegarde l'état actuel du jeu pour l'annulation"""
        state = {
            'grid': [row[:] for row in self.grid],
            'player_pos': self.player_pos,
            'box_positions': self.box_positions[:]
        }
        self.moves_history.append(state)
        
        # Limiter l'historique pour éviter une consommation excessive de mémoire
        if len(self.moves_history) > 100:
            self.moves_history = self.moves_history[-100:]
    
    def undo_move(self):
        """Annule le dernier mouvement"""
        if not self.moves_history:
            return False
        
        last_state = self.moves_history.pop()
        self.grid = last_state['grid']
        self.player_pos = last_state['player_pos']
        self.box_positions = last_state['box_positions']
        
        return True
    
    def is_level_complete(self):
        """Vérifie si le niveau est terminé (toutes les caisses sur les cibles)"""
        for target_pos in self.target_positions:
            row, col = target_pos
            if self.grid[row][col] != 4:  # Seule une caisse sur cible compte
                return False
        return True
    
    def reset_level(self, original_level_data):
        """Remet le niveau à son état initial"""
        self.__init__(original_level_data)
    
    def get_display_grid(self):
        """Retourne une copie de la grille pour l'affichage"""
        return [row[:] for row in self.grid]
    
    def get_stats(self):
        """Retourne des statistiques sur l'état actuel du niveau"""
        total_boxes = len(self.box_positions)
        boxes_on_targets = sum(1 for box in self.box_positions if box in self.target_positions)
        stuck_boxes = len(self.check_for_stuck_boxes())
        
        return {
            'total_boxes': total_boxes,
            'boxes_on_targets': boxes_on_targets,
            'stuck_boxes': stuck_boxes,
            'progress_percentage': (boxes_on_targets / total_boxes * 100) if total_boxes > 0 else 0
        }


class SokobanGame:
    """
    Classe principale du jeu Sokoban
    Gère l'état global du jeu et coordonne les différents modules
    """
    
    def __init__(self):
        self.current_level = 0
        self.levels = self._load_levels()
        self.board = None
        self.original_level_data = None
        self.score = 0
        self.moves_count = 0
        self.best_scores = {}  # Meilleurs scores par niveau
        
        # Directions de mouvement
        self.directions = {
            'UP': (-1, 0),
            'DOWN': (1, 0),
            'LEFT': (0, -1),
            'RIGHT': (0, 1)
        }
    
    def _load_levels(self):
        """Charge les niveaux de jeu"""
        levels = []
        
        # Niveau 1 - Tutoriel simple
        levels.append([
            [-1, -1, -1, -1, -1, -1, -1, -1],
            [-1,  0,  0,  0,  0,  0,  0, -1],
            [-1,  0,  2,  0,  0,  1,  0, -1],
            [-1,  0,  0,  3,  0,  0,  0, -1],
            [-1,  0,  0,  0,  2,  0,  0, -1],
            [-1,  0,  1,  0,  0,  0,  0, -1],
            [-1,  0,  0,  0,  0,  0,  0, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1]
        ])
        
        # Niveau 2 - Introduction aux obstacles
        levels.append([
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1,  0,  0,  0,  0,  0,  0,  0,  0, -1],
            [-1,  0,  2,  0,  2,  0,  1,  1,  0, -1],
            [-1,  0,  0, -1,  0, -1,  0,  0,  0, -1],
            [-1,  0,  0,  3,  0,  0,  0,  0,  0, -1],
            [-1,  0,  2,  0,  2,  0,  1,  1,  0, -1],
            [-1,  0,  0,  0,  0,  0,  0,  0,  0, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
        ])
        
        # Niveau 3 - Difficulté moyenne
        levels.append([
            [-1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1,  0,  0,  0, -1,  1,  1,  1, -1],
            [-1,  0,  2,  0, -1,  0,  0,  0, -1],
            [-1,  0,  2,  0,  0,  2,  0,  0, -1],
            [-1,  0,  2,  0, -1,  0,  0,  0, -1],
            [-1,  0,  0,  3, -1,  0,  0,  0, -1],
            [-1,  0,  0,  0, -1,  0,  0,  0, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1]
        ])
        
        return levels
    
    def start_level(self, level_index=0):
        """Démarre un niveau spécifique"""
        if 0 <= level_index < len(self.levels):
            self.current_level = level_index
            self.original_level_data = [row[:] for row in self.levels[level_index]]
            self.board = GameBoard(self.original_level_data)
            self.moves_count = 0
            return True
        return False
    
    def move_player(self, direction_key):
        """
        Déplace le joueur selon la direction spécifiée
        
        Args:
            direction_key: Clé de direction ('UP', 'DOWN', 'LEFT', 'RIGHT')
        
        Returns:
            str ou bool: 'LEVEL_COMPLETE', 'BOX_STUCK', True ou False
        """
        if not self.board or direction_key not in self.directions:
            return False
        
        direction = self.directions[direction_key]
        result = self.board.move_player(direction)
        
        if result == 'BOX_STUCK':
            return 'BOX_STUCK'
        elif result:
            self.moves_count += 1
            
            # Vérifier si le niveau est terminé
            if self.board.is_level_complete():
                self.score += self._calculate_level_score()
                
                # Enregistrer le meilleur score
                if self.current_level not in self.best_scores or \
                   self.moves_count < self.best_scores[self.current_level]:
                    self.best_scores[self.current_level] = self.moves_count
                
                return 'LEVEL_COMPLETE'
        
        return result
    
    def _calculate_level_score(self):
        """Calcule le score pour le niveau actuel"""
        # Score basé sur le nombre de mouvements (moins de mouvements = meilleur score)
        base_score = 1000
        penalty = min(self.moves_count * 5, 800)  # Pénalité maximale de 800
        bonus = 0
        
        # Bonus pour résolution rapide
        if self.moves_count < 20:
            bonus = 200
        elif self.moves_count < 50:
            bonus = 100
        
        return max(base_score - penalty + bonus, 100)  # Score minimum de 100
    
    def undo_move(self):
        """Annule le dernier mouvement"""
        if self.board:
            success = self.board.undo_move()
            if success and self.moves_count > 0:
                self.moves_count -= 1
            return success
        return False
    
    def reset_level(self):
        """Remet le niveau actuel à zéro"""
        if self.board and self.original_level_data:
            self.board.reset_level(self.original_level_data)
            self.moves_count = 0
            return True
        return False
    
    def get_game_state(self):
        """Retourne l'état actuel du jeu"""
        if not self.board:
            return None
        
        stats = self.board.get_stats()
        
        return {
            'grid': self.board.get_display_grid(),
            'level': self.current_level + 1,
            'moves': self.moves_count,
            'score': self.score,
            'is_complete': self.board.is_level_complete(),
            'player_pos': self.board.player_pos,
            'stuck_boxes': self.board.check_for_stuck_boxes(),
            'stats': stats,
            'best_moves': self.best_scores.get(self.current_level, None)
        }
    
    def next_level(self):
        """Passe au niveau suivant"""
        if self.current_level + 1 < len(self.levels):
            return self.start_level(self.current_level + 1)
        return False
    
    def has_next_level(self):
        """Vérifie s'il y a un niveau suivant"""
        return self.current_level + 1 < len(self.levels)
    
    def get_level_count(self):
        """Retourne le nombre total de niveaux"""
        return len(self.levels)
    
    def get_current_level_info(self):
        """Retourne des informations sur le niveau actuel"""
        if not self.board:
            return None
        
        return {
            'level_number': self.current_level + 1,
            'total_levels': len(self.levels),
            'target_count': len(self.board.target_positions),
            'box_count': len(self.board.box_positions),
            'grid_size': (self.board.rows, self.board.cols)
        }


# Test de base de la logique
if __name__ == "__main__":
    # Test simple de la logique du jeu
    game = SokobanGame()
    game.start_level(0)
    
    print("État initial du jeu:")
    state = game.get_game_state()
    for row in state['grid']:
        print(row)
    
    print(f"\nPosition du joueur: {state['player_pos']}")
    print(f"Niveau: {state['level']}")
    print(f"Mouvements: {state['moves']}")
    print(f"Niveau terminé: {state['is_complete']}")
    print(f"Caisses bloquées: {state['stuck_boxes']}")
    print(f"Statistiques: {state['stats']}")
    
    # Test de détection de caisse bloquée
    print("\n--- Test de détection de caisse bloquée ---")
    # Simuler des mouvements qui bloqueraient une caisse
    moves = ['RIGHT', 'RIGHT', 'UP', 'LEFT', 'DOWN', 'LEFT', 'LEFT', 'UP']
    
    for move in moves:
        result = game.move_player(move)
        if result == 'BOX_STUCK':
            print(f"⚠️ Caisse bloquée détectée après le mouvement {move}!")
            break
        elif result:
            print(f"Mouvement {move} effectué")
        else:
            print(f"Mouvement {move} impossible")
