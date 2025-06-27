#!/usr/bin/env python3
"""
Lanceur principal pour le jeu Sokoban
Lance directement la version graphique complète
"""

import subprocess
import sys

def install_pygame():
    """
    Installe Pygame si ce n'est pas déjà fait.
    """
    try:
        import pygame
    except ImportError:
        print("Pygame n'est pas installé. Installation en cours...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pygame"])
            print("Pygame a été installé avec succès.")
        except Exception as e:
            print(f"Erreur lors de l'installation de Pygame: {e}")
            sys.exit(1)

def main():
    """
    Lance directement la version graphique complète
    """
    install_pygame()
    print("\n🚀 Lancement de la version graphique complète...")
    try:
        from sokoban_complete import SokobanCompleteGame
        game = SokobanCompleteGame()
        game.run()
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")

if __name__ == "__main__":
    main()


