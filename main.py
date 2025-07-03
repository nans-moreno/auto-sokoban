#!/usr/bin/env python3
"""
Lanceur principal pour le jeu Sokoban
Lance directement la version graphique complète
"""

def main():
    """Lance directement la version graphique complète"""
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

if __name__ == "__main__":
    main()

