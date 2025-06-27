# 🎮 Sokoban avec Bot ML - Version Complète

Un jeu Sokoban classique entièrement fonctionnel avec un bot d'intelligence artificielle utilisant l'apprentissage par renforcement.

## 🌟 Fonctionnalités

### 🎯 Jeu Sokoban Classique
- **5 niveaux** de difficulté progressive
- **Interface graphique** moderne avec Pygame
- **Système de scores** et classements
- **Sauvegarde automatique** des progrès
- **Contrôles intuitifs** (clavier et souris)

### 🤖 Bot d'Intelligence Artificielle
- **Apprentissage par renforcement** (Q-Learning avancé)
- **Entraînement adaptatif** avec mémoire d'expérience
- **Sauvegarde des modèles** entraînés
- **Visualisation en temps réel** des stratégies
- **Statistiques détaillées** d'apprentissage

### 🎨 Interface Utilisateur
- **Menu principal** avec navigation intuitive
- **Écran de jeu** avec informations en temps réel
- **Interface Bot ML** dédiée à l'IA
- **Système de scores** avec historique
- **Paramètres** configurables

## 🚀 Installation et Lancement

### Prérequis
- Python 3.7+
- Pygame (installé automatiquement)

### Lancement Rapide
```bash
# Cloner ou télécharger le projet
cd auto-sokoban

# Lancer le jeu (installation automatique des dépendances)
python3 main.py
```

Le jeu installera automatiquement Pygame si nécessaire.

## 🎮 Comment Jouer

### Contrôles de Base
- **↑↓←→** : Déplacer le joueur
- **U** : Annuler le dernier mouvement
- **R** : Recommencer le niveau
- **M** : Retour au menu principal
- **Espace** : Niveau suivant (si terminé)

### Objectif
Poussez toutes les caisses (■) sur les emplacements cibles (○) pour terminer le niveau.

### Légende
- **☺** : Joueur
- **■** : Caisse
- **○** : Emplacement cible
- **●** : Caisse correctement placée
- **▓** : Mur

## 🤖 Utilisation du Bot ML

### 1. Accéder au Bot
Menu Principal → "Bot ML"

### 2. Entraîner le Bot
- Cliquez sur "Entraîner Niveau X"
- L'entraînement prend quelques secondes à quelques minutes
- Le modèle est sauvegardé automatiquement

### 3. Regarder le Bot Jouer
- Cliquez sur "Jouer Niveau X" après l'entraînement
- Observez le bot résoudre le puzzle en temps réel
- Les statistiques s'affichent pendant le jeu

### 4. Paramètres Recommandés
- **Entraînement initial** : 500+ épisodes pour de bons résultats
- **Niveaux faciles** : Commencez par le niveau 1
- **Patience** : L'apprentissage peut prendre du temps selon la complexité

## 📊 Fonctionnalités Avancées

### Système de Scores
- **Calcul automatique** basé sur les mouvements et le temps
- **Classement persistant** des meilleurs scores
- **Historique complet** des parties

### Bot ML Avancé
- **Q-Learning** avec exploration epsilon-greedy
- **Mémoire d'expérience** pour améliorer l'apprentissage
- **Détection de deadlocks** pour éviter les situations impossibles
- **Récompenses sophistiquées** pour guider l'apprentissage
- **Arrêt anticipé** si pas d'amélioration

### Sauvegarde et Persistance
- **Modèles ML** sauvegardés dans le dossier `models/`
- **Base de données** SQLite pour les scores
- **Configuration** automatiquement préservée

## 🧪 Tests et Validation

### Tests Automatisés
```bash
python3 test_game.py
```

Les tests vérifient :
- ✅ Imports et dépendances
- ✅ Logique de base du jeu
- ✅ Fonctionnement de la base de données
- ✅ Chargement des niveaux
- ✅ Entraînement et performance du bot

### Résultats Attendus
- **5/5 tests réussis**
- **Temps d'exécution** : < 1 seconde
- **Aucune erreur critique**

## 📁 Structure du Projet

```
auto-sokoban/
├── main.py                 # 🚀 Point d'entrée principal
├── sokoban_complete.py     # 🎮 Interface graphique complète
├── game_logic.py          # ⚙️ Logique de base du jeu
├── game_features.py       # 🗄️ Base de données et niveaux
├── sokoban_bot.py         # 🤖 Bot ML avancé
├── test_game.py           # 🧪 Tests automatisés
├── AMELIORATIONS.md       # 📋 Documentation des améliorations
├── models/                # 💾 Modèles ML sauvegardés
├── assets/                # 🎨 Images du jeu
└── sounds/                # 🔊 Effets sonores
```

## 🔧 Technologies Utilisées

- **Python 3.11** : Langage principal
- **Pygame** : Interface graphique et gestion des événements
- **NumPy** : Calculs numériques pour le machine learning
- **SQLite** : Base de données légère pour les scores
- **Pickle** : Sérialisation des modèles d'IA

## 📈 Performances du Bot

### Métriques Typiques
- **États explorés** : 6,000+ configurations uniques
- **Temps d'entraînement** : 30 secondes à 5 minutes selon le niveau
- **Taux de réussite** : Variable selon la complexité du niveau
- **Stratégies émergentes** : Le bot développe ses propres techniques

### Conseils d'Optimisation
1. **Entraînement long** : Plus d'épisodes = meilleures performances
2. **Niveaux progressifs** : Commencez par les niveaux faciles
3. **Patience** : L'apprentissage par renforcement prend du temps
4. **Réentraînement** : N'hésitez pas à relancer l'entraînement

## 🎯 Objectifs du Projet

Ce projet démontre :
- ✅ **Intégration réussie** de l'IA dans un jeu classique
- ✅ **Interface utilisateur** moderne et intuitive
- ✅ **Code robuste** avec gestion d'erreurs
- ✅ **Tests automatisés** pour la fiabilité
- ✅ **Documentation complète** pour la maintenance

## 🤝 Contribution

Le code est structuré de manière modulaire pour faciliter les améliorations :
- **Nouveaux algorithmes ML** : Modifier `sokoban_bot.py`
- **Nouveaux niveaux** : Ajouter dans `game_features.py`
- **Interface** : Personnaliser `sokoban_complete.py`
- **Tests** : Étendre `test_game.py`

## 📝 Licence

Ce projet est fourni à des fins éducatives et de démonstration.

---

**🎉 Amusez-vous bien avec Sokoban et son bot IA !**

*Pour plus de détails techniques, consultez `AMELIORATIONS.md`*

