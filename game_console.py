"""
Version console du jeu Sokoban pour tester la logique sans interface graphique
"""

from game_logic import SokobanGame

class SokobanConsole:
    """Version console du jeu Sokoban"""
    
    def __init__(self):
        self.game = SokobanGame()
        
        # Symboles pour l'affichage console
        self.symbols = {
            -1: '█',  # Mur
            0: ' ',   # Espace vide
            1: '.',   # Cible
            2: '$',   # Caisse
            3: '@',   # Joueur
            4: '*',   # Caisse sur cible
            5: '+'    # Joueur sur cible
        }
        
        # Mapping des commandes
        self.commands = {
            'z': 'UP',
            'q': 'LEFT',
            's': 'DOWN',
            'd': 'RIGHT',
            'u': 'UNDO',
            'r': 'RESET',
            'n': 'NEXT',
            'h': 'HELP',
            'x': 'QUIT'
        }
    
    def display_grid(self, grid):
        """Affiche la grille dans la console"""
        print("\n" + "="*30)
        for row in grid:
            line = ""
            for cell in row:
                line += self.symbols.get(cell, '?')
            print(line)
        print("="*30)
    
    def display_status(self, game_state):
        """Affiche les informations de statut"""
        if game_state:
            print(f"Niveau: {game_state['level']} | Mouvements: {game_state['moves']} | Score: {game_state['score']}")
            if game_state['is_complete']:
                print("🎉 NIVEAU TERMINÉ! 🎉")
    
    def display_help(self):
        """Affiche l'aide"""
        print("\n--- AIDE ---")
        print("z/q/s/d : Déplacer (haut/gauche/bas/droite)")
        print("u : Annuler le dernier mouvement")
        print("r : Recommencer le niveau")
        print("n : Niveau suivant (si terminé)")
        print("h : Afficher cette aide")
        print("x : Quitter")
        print("-----------\n")
    
    def run(self):
        """Boucle principale du jeu console"""
        print("🎮 SOKOBAN - Version Console 🎮")
        print("Tapez 'h' pour l'aide")
        
        # Démarrer le premier niveau
        self.game.start_level(0)
        
        while True:
            # Afficher l'état actuel
            game_state = self.game.get_game_state()
            if game_state:
                self.display_grid(game_state['grid'])
                self.display_status(game_state)
            
            # Demander une commande
            try:
                command = input("\nCommande: ").lower().strip()
                
                if command == 'x':
                    print("Au revoir!")
                    break
                
                elif command == 'h':
                    self.display_help()
                
                elif command in ['z', 'q', 's', 'd']:
                    direction = self.commands[command]
                    result = self.game.move_player(direction)
                    
                    if result == 'LEVEL_COMPLETE':
                        print("🎉 Niveau terminé! Tapez 'n' pour le niveau suivant.")
                    elif not result:
                        print("❌ Mouvement impossible!")
                
                elif command == 'u':
                    if self.game.undo_move():
                        print("↶ Mouvement annulé")
                    else:
                        print("❌ Aucun mouvement à annuler")
                
                elif command == 'r':
                    self.game.reset_level()
                    print("🔄 Niveau recommencé")
                
                elif command == 'n':
                    game_state = self.game.get_game_state()
                    if game_state and game_state['is_complete']:
                        if self.game.next_level():
                            print(f"➡️ Niveau {self.game.current_level + 1} démarré!")
                        else:
                            print("🏆 Tous les niveaux terminés! Félicitations!")
                    else:
                        print("❌ Terminez d'abord le niveau actuel!")
                
                else:
                    print("❓ Commande inconnue. Tapez 'h' pour l'aide.")
            
            except KeyboardInterrupt:
                print("\n\nJeu interrompu. Au revoir!")
                break
            except EOFError:
                print("\n\nJeu terminé. Au revoir!")
                break


if __name__ == "__main__":
    console_game = SokobanConsole()
    console_game.run()

