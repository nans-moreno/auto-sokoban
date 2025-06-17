#!/usr/bin/env python3
"""
Lanceur principal pour le jeu Sokoban
Permet de choisir entre la version console et la version graphique
"""

import sys
import os

def show_menu():
    """Affiche le menu de sélection"""
    print("🎮 SOKOBAN - Sélection de version 🎮")
    print("=" * 40)
    print("1. Version graphique complète (Pygame)")
    print("2. Version console (texte)")
    print("3. Test de la logique de base")
    print("4. Quitter")
    print("=" * 40)

def main():
    """Fonction principale"""
    while True:
        show_menu()
        
        try:
            choice = input("\nVotre choix (1-4): ").strip()
            
            if choice == '1':
                print("\n🚀 Lancement de la version graphique complète...")
                try:
                    from sokoban_complete import SokobanCompleteGame
                    game = SokobanCompleteGame()
                    game.run()
                except ImportError as e:
                    print(f"❌ Erreur d'importation: {e}")
                    print("Assurez-vous que Pygame est installé: pip install pygame")
                except Exception as e:
                    print(f"❌ Erreur lors du lancement: {e}")
                break
            
            elif choice == '2':
                print("\n🚀 Lancement de la version console...")
                try:
                    from game_console import SokobanConsole
                    console_game = SokobanConsole()
                    console_game.run()
                except Exception as e:
                    print(f"❌ Erreur lors du lancement: {e}")
                break
            
            elif choice == '3':
                print("\n🔧 Test de la logique de base...")
                try:
                    from game_logic import SokobanGame
                    
                    # Test simple
                    game = SokobanGame()
                    game.start_level(0)
                    
                    print("✅ Test réussi!")
                    print("État initial du jeu:")
                    state = game.get_game_state()
                    
                    # Affichage simple de la grille
                    symbols = {-1: '█', 0: ' ', 1: '.', 2: '$', 3: '@', 4: '*', 5: '+'}
                    for row in state['grid']:
                        line = ""
                        for cell in row:
                            line += symbols.get(cell, '?')
                        print(line)
                    
                    print(f"Position du joueur: {state['player_pos']}")
                    print(f"Niveau: {state['level']}")
                    print(f"Mouvements: {state['moves']}")
                    
                except Exception as e:
                    print(f"❌ Erreur lors du test: {e}")
                
                input("\nAppuyez sur Entrée pour continuer...")
            
            elif choice == '4':
                print("\n👋 Au revoir!")
                break
            
            else:
                print("\n❌ Choix invalide. Veuillez entrer un nombre entre 1 et 4.")
                input("Appuyez sur Entrée pour continuer...")
        
        except KeyboardInterrupt:
            print("\n\n👋 Au revoir!")
            break
        except EOFError:
            print("\n\n👋 Au revoir!")
            break

if __name__ == "__main__":
    main()

