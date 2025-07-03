"""
Module de gestion de la base de données pour le jeu Sokoban
Gère les scores, les classements et les statistiques des joueurs
"""

import sqlite3
import os
from datetime import datetime

class SokobanDatabase:
    """
    Classe pour gérer la persistance des données du jeu Sokoban
    """
    
    def __init__(self, db_path="sokoban_scores.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialise la base de données avec les tables nécessaires"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table des scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                level INTEGER NOT NULL,
                moves INTEGER NOT NULL,
                time_seconds INTEGER NOT NULL,
                score INTEGER NOT NULL,
                date_completed TEXT NOT NULL
            )
        ''')
        
        # Table des statistiques globales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT UNIQUE NOT NULL,
                total_levels_completed INTEGER DEFAULT 0,
                total_moves INTEGER DEFAULT 0,
                total_time_seconds INTEGER DEFAULT 0,
                best_score INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                last_played TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_score(self, player_name, level, moves, time_seconds, score):
        """
        Sauvegarde un score dans la base de données
        
        Args:
            player_name: Nom du joueur
            level: Numéro du niveau
            moves: Nombre de mouvements
            time_seconds: Temps en secondes
            score: Score obtenu
        
        Returns:
            bool: True si la sauvegarde a réussi
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insérer le score
            cursor.execute('''
                INSERT INTO scores (player_name, level, moves, time_seconds, score, date_completed)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (player_name, level, moves, time_seconds, score, datetime.now().isoformat()))
            
            # Mettre à jour les statistiques du joueur
            self._update_player_stats(cursor, player_name, level, moves, time_seconds, score)
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la sauvegarde du score: {e}")
            return False
    
    def _update_player_stats(self, cursor, player_name, level, moves, time_seconds, score):
        """Met à jour les statistiques du joueur"""
        # Vérifier si le joueur existe
        cursor.execute('SELECT * FROM player_stats WHERE player_name = ?', (player_name,))
        player = cursor.fetchone()
        
        if player:
            # Mettre à jour les statistiques existantes
            cursor.execute('''
                UPDATE player_stats 
                SET total_levels_completed = total_levels_completed + 1,
                    total_moves = total_moves + ?,
                    total_time_seconds = total_time_seconds + ?,
                    best_score = MAX(best_score, ?),
                    games_played = games_played + 1,
                    last_played = ?
                WHERE player_name = ?
            ''', (moves, time_seconds, score, datetime.now().isoformat(), player_name))
        else:
            # Créer un nouveau joueur
            cursor.execute('''
                INSERT INTO player_stats 
                (player_name, total_levels_completed, total_moves, total_time_seconds, 
                 best_score, games_played, last_played)
                VALUES (?, 1, ?, ?, ?, 1, ?)
            ''', (player_name, moves, time_seconds, score, datetime.now().isoformat()))
    
    def get_best_scores(self, level=None, limit=10):
        """
        Récupère les meilleurs scores
        
        Args:
            level: Niveau spécifique (None pour tous les niveaux)
            limit: Nombre maximum de scores à retourner
        
        Returns:
            list: Liste des meilleurs scores
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if level is not None:
                cursor.execute('''
                    SELECT player_name, level, moves, time_seconds, score, date_completed
                    FROM scores 
                    WHERE level = ?
                    ORDER BY score DESC, moves ASC, time_seconds ASC
                    LIMIT ?
                ''', (level, limit))
            else:
                cursor.execute('''
                    SELECT player_name, level, moves, time_seconds, score, date_completed
                    FROM scores 
                    ORDER BY score DESC, moves ASC, time_seconds ASC
                    LIMIT ?
                ''', (limit,))
            
            scores = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'player_name': row[0],
                    'level': row[1],
                    'moves': row[2],
                    'time_seconds': row[3],
                    'score': row[4],
                    'date_completed': row[5]
                }
                for row in scores
            ]
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des scores: {e}")
            return []
    
    def get_player_stats(self, player_name):
        """
        Récupère les statistiques d'un joueur
        
        Args:
            player_name: Nom du joueur
        
        Returns:
            dict: Statistiques du joueur ou None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM player_stats WHERE player_name = ?', (player_name,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'player_name': row[1],
                    'total_levels_completed': row[2],
                    'total_moves': row[3],
                    'total_time_seconds': row[4],
                    'best_score': row[5],
                    'games_played': row[6],
                    'last_played': row[7]
                }
            return None
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des statistiques: {e}")
            return None
    
    def get_all_players(self):
        """
        Récupère la liste de tous les joueurs
        
        Returns:
            list: Liste des noms de joueurs
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT player_name FROM player_stats ORDER BY best_score DESC')
            players = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return players
            
        except sqlite3.Error as e:
            print(f"Erreur lors de la récupération des joueurs: {e}")
            return []


# Module d'effets sonores
class SokobanAudio:
    """
    Classe pour gérer les effets sonores du jeu Sokoban
    Utilise pygame.mixer pour jouer les fichiers audio
    """
    
    def __init__(self):
        self.sounds_enabled = True
        self.music_enabled = True
        self.volume = 0.7
        
        # Initialiser pygame mixer
        try:
            import pygame
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            self.pygame_available = True
            
            # Charger les effets sonores
            self.sound_files = {
                'move': 'sounds/move.wav',
                'push_box': 'sounds/push_box.wav',
                'box_on_target': 'sounds/box_on_target.wav',
                'level_complete': 'sounds/level_complete.wav',
                'undo': 'sounds/undo.wav',
                'reset': 'sounds/reset.wav',
                'menu_click': 'sounds/menu_click.wav'
            }
            
            # Précharger les sons
            self.sounds = {}
            for name, file_path in self.sound_files.items():
                try:
                    self.sounds[name] = pygame.mixer.Sound(file_path)
                    self.sounds[name].set_volume(self.volume)
                except:
                    print(f"⚠️ Impossible de charger le son: {file_path}")
                    self.sounds[name] = None
            
        except Exception as e:
            print(f"⚠️ Audio non disponible ({e}), mode silencieux")
            self.pygame_available = False
            self.sounds = {}
    
    def play_sound(self, sound_name):
        """
        Joue un effet sonore
        
        Args:
            sound_name: Nom de l'effet sonore
        """
        if not self.sounds_enabled or not self.pygame_available:
            return
        
        if sound_name in self.sounds and self.sounds[sound_name]:
            try:
                self.sounds[sound_name].play()
            except:
                print(f"⚠️ Erreur lors de la lecture du son: {sound_name}")
    
    def play_music(self, music_name="background"):
        """
        Joue une musique de fond
        
        Args:
            music_name: Nom de la musique
        """
        if self.music_enabled:
            print(f"🎵 Musique de fond: {music_name}")
    
    def stop_music(self):
        """Arrête la musique de fond"""
        if self.music_enabled and self.pygame_available:
            try:
                import pygame
                pygame.mixer.music.stop()
            except:
                pass
        print("🔇 Musique arrêtée")
    
    def set_volume(self, volume):
        """
        Définit le volume
        
        Args:
            volume: Volume entre 0.0 et 1.0
        """
        self.volume = max(0.0, min(1.0, volume))
        
        # Mettre à jour le volume de tous les sons
        if self.pygame_available:
            for sound in self.sounds.values():
                if sound:
                    sound.set_volume(self.volume)
        
        print(f"🔊 Volume: {int(self.volume * 100)}%")
    
    def toggle_sounds(self):
        """Active/désactive les effets sonores"""
        self.sounds_enabled = not self.sounds_enabled
        status = "activés" if self.sounds_enabled else "désactivés"
        print(f"🔊 Effets sonores {status}")
    
    def toggle_music(self):
        """Active/désactive la musique"""
        self.music_enabled = not self.music_enabled
        status = "activée" if self.music_enabled else "désactivée"
        print(f"🎵 Musique {status}")


# Module de niveaux étendus
class SokobanLevels:
    """
    Classe pour gérer une collection étendue de niveaux Sokoban
    """
    
    @staticmethod
    def get_extended_levels():
        """
        Retourne une collection de niveaux de difficulté croissante
        
        Returns:
            list: Liste des niveaux
        """
        levels = []
        
        # Niveau 1 - Très facile (tutoriel)
        levels.append([
            [-1, -1, -1, -1, -1],
            [-1,  0,  1,  0, -1],
            [-1,  0,  2,  0, -1],
            [-1,  0,  3,  0, -1],
            [-1, -1, -1, -1, -1]
        ])
        
        # Niveau 2 - Facile
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
        
        # Niveau 3 - Moyen
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
        
        # Niveau 4 - Difficile
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
        
        # Niveau 5 - Très difficile (corrigé)
        levels.append([
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
            [-1,  0,  0,  0,  0,  0,  0,  0,  0,  0, -1],
            [-1,  0,  2,  0, -1, -1, -1,  0,  2,  0, -1],
            [-1,  0,  0,  0,  0,  1,  0,  0,  0,  0, -1],
            [-1, -1, -1,  2,  0,  1,  0,  2, -1, -1, -1],
            [-1,  1,  0,  0,  0,  3,  0,  0,  0,  1, -1],
            [-1, -1, -1,  2,  0,  1,  0,  2, -1, -1, -1],
            [-1,  0,  0,  0,  0,  1,  0,  0,  0,  0, -1],
            [-1,  0,  0,  0, -1, -1, -1,  0,  0,  0, -1],
            [-1,  0,  0,  0,  0,  0,  0,  0,  0,  0, -1],
            [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
        ])
        
        return levels
    
    @staticmethod
    def get_level_info():
        """
        Retourne les informations sur chaque niveau
        
        Returns:
            list: Liste des informations de niveau
        """
        return [
            {"name": "Tutoriel", "difficulty": "Très facile", "boxes": 1},
            {"name": "Premiers pas", "difficulty": "Facile", "boxes": 2},
            {"name": "Obstacles", "difficulty": "Moyen", "boxes": 4},
            {"name": "Défi", "difficulty": "Difficile", "boxes": 3},
            {"name": "Maître", "difficulty": "Très difficile", "boxes": 4}
        ]


# Test des nouvelles fonctionnalités
if __name__ == "__main__":
    # Test de la base de données
    print("=== Test de la base de données ===")
    db = SokobanDatabase()
    
    # Sauvegarder quelques scores de test
    db.save_score("Alice", 1, 15, 120, 850)
    db.save_score("Bob", 1, 20, 180, 750)
    db.save_score("Alice", 2, 25, 200, 700)
    
    # Récupérer les meilleurs scores
    best_scores = db.get_best_scores(level=1, limit=5)
    print("Meilleurs scores niveau 1:")
    for score in best_scores:
        print(f"  {score['player_name']}: {score['score']} points ({score['moves']} mouvements)")
    
    # Test des effets sonores
    print("\n=== Test des effets sonores ===")
    audio = SokobanAudio()
    audio.play_sound('move')
    audio.play_sound('push_box')
    audio.play_sound('level_complete')
    
    # Test des niveaux étendus
    print("\n=== Test des niveaux étendus ===")
    levels = SokobanLevels.get_extended_levels()
    level_info = SokobanLevels.get_level_info()
    
    for i, info in enumerate(level_info):
        print(f"Niveau {i+1}: {info['name']} - {info['difficulty']} ({info['boxes']} caisses)")
    
    print(f"\nTotal de {len(levels)} niveaux disponibles")

