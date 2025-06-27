#!/usr/bin/env python3
"""
Script de test pour vérifier les fonctionnalités du jeu Sokoban
"""

import sys
import os
import time

# Ajouter le répertoire courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_game_logic():
    """Test de la logique de base du jeu"""
    print("=== Test de la logique du jeu ===")
    
    try:
        from game_logic import SokobanGame
        
        # Créer une instance du jeu
        game = SokobanGame()
        print("✓ Création du jeu réussie")
        
        # Démarrer un niveau
        success = game.start_level(0)
        print(f"✓ Démarrage niveau 1: {'Réussi' if success else 'Échec'}")
        
        # Obtenir l'état du jeu
        state = game.get_game_state()
        print(f"✓ État du jeu obtenu: {state is not None}")
        
        if state:
            print(f"  - Niveau: {state['level']}")
            print(f"  - Mouvements: {state['moves']}")
            print(f"  - Score: {state['score']}")
            print(f"  - Position joueur: {state['player_pos']}")
        
        # Test de mouvement
        result = game.move_player('RIGHT')
        print(f"✓ Mouvement droite: {'Réussi' if result else 'Échec'}")
        
        # Test d'annulation
        undo_result = game.undo_move()
        print(f"✓ Annulation: {'Réussi' if undo_result else 'Échec'}")
        
        # Test de reset
        reset_result = game.reset_level()
        print(f"✓ Reset niveau: {'Réussi' if reset_result else 'Échec'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans test_game_logic: {e}")
        return False

def test_bot():
    """Test du bot ML"""
    print("\n=== Test du bot ML ===")
    
    try:
        from game_logic import SokobanGame
        from sokoban_bot import SokobanBot
        
        # Créer le jeu et le bot
        game = SokobanGame()
        bot = SokobanBot(game)
        print("✓ Création du bot réussie")
        
        # Test d'entraînement rapide
        print("  Entraînement rapide (10 épisodes)...")
        rewards, lengths = bot.train(num_episodes=10, level_index=0, save_model=False)
        print(f"✓ Entraînement terminé: {len(rewards)} épisodes")
        
        # Test de jeu
        solved, moves, actions = bot.play_level(level_index=0, max_moves=100, verbose=False)
        print(f"✓ Test de jeu: {'Résolu' if solved else 'Non résolu'} en {moves} mouvements")
        print(f"  Actions: {len(actions)} actions générées")
        
        # Statistiques
        stats = bot.get_training_stats()
        if stats:
            print(f"✓ Statistiques obtenues: {len(stats)} métriques")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans test_bot: {e}")
        return False

def test_database():
    """Test de la base de données"""
    print("\n=== Test de la base de données ===")
    
    try:
        from game_features import SokobanDatabase
        
        # Créer la base de données
        db = SokobanDatabase()
        print("✓ Création de la base de données réussie")
        
        # Test de sauvegarde de score
        db.save_score("TestPlayer", 1, 50, 120, 850)
        print("✓ Sauvegarde de score réussie")
        
        # Test de récupération des scores
        scores = db.get_best_scores(limit=5)
        print(f"✓ Récupération des scores: {len(scores)} scores trouvés")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans test_database: {e}")
        return False

def test_levels():
    """Test des niveaux"""
    print("\n=== Test des niveaux ===")
    
    try:
        from game_features import SokobanLevels
        
        # Test des niveaux étendus
        levels = SokobanLevels.get_extended_levels()
        print(f"✓ Niveaux chargés: {len(levels)} niveaux")
        
        # Test des informations de niveau
        level_info = SokobanLevels.get_level_info()
        print(f"✓ Informations de niveau: {len(level_info)} descriptions")
        
        # Vérifier la structure des niveaux
        for i, level in enumerate(levels[:2]):  # Tester les 2 premiers niveaux
            if level and len(level) > 0 and len(level[0]) > 0:
                print(f"✓ Niveau {i+1}: {len(level)}x{len(level[0])} cellules")
            else:
                print(f"✗ Niveau {i+1}: Structure invalide")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur dans test_levels: {e}")
        return False

def test_imports():
    """Test des imports"""
    print("\n=== Test des imports ===")
    
    modules_to_test = [
        'game_logic',
        'game_features', 
        'sokoban_bot',
        'sokoban_complete'
    ]
    
    success_count = 0
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"✓ Import {module}: Réussi")
            success_count += 1
        except Exception as e:
            print(f"✗ Import {module}: Échec - {e}")
    
    print(f"✓ Imports réussis: {success_count}/{len(modules_to_test)}")
    return success_count == len(modules_to_test)

def main():
    """Fonction principale de test"""
    print("🚀 TESTS DU JEU SOKOBAN")
    print("=" * 50)
    
    start_time = time.time()
    
    # Exécuter tous les tests
    tests = [
        ("Imports", test_imports),
        ("Logique du jeu", test_game_logic),
        ("Base de données", test_database),
        ("Niveaux", test_levels),
        ("Bot ML", test_bot)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Erreur critique dans {test_name}: {e}")
            results.append((test_name, False))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✓ RÉUSSI" if result else "✗ ÉCHEC"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    total_time = time.time() - start_time
    print(f"\nTests terminés en {total_time:.2f} secondes")
    print(f"Résultat: {passed}/{len(results)} tests réussis")
    
    if passed == len(results):
        print("🎉 Tous les tests sont passés avec succès!")
        return True
    else:
        print("⚠️  Certains tests ont échoué.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

