# Analyse du niveau 5 - Très difficile

## Configuration actuelle:
```
[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
[-1,  0,  0,  0,  0,  0,  0,  0,  0,  0, -1]
[-1,  0,  2,  0, -1, -1, -1,  0,  2,  0, -1]
[-1,  0,  0,  0,  0,  1,  0,  0,  0,  0, -1]
[-1, -1, -1,  2,  0,  1,  0,  2, -1, -1, -1]
[-1,  1,  0,  0,  0,  3,  0,  0,  0,  1, -1]
[-1, -1, -1,  2,  0,  1,  0,  2, -1, -1, -1]
[-1,  0,  0,  0,  0,  1,  0,  0,  0,  0, -1]
[-1,  0,  2,  0, -1, -1, -1,  0,  2,  0, -1]
[-1,  0,  0,  0,  0,  0,  0,  0,  0,  0, -1]
[-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1]
```

## Légende:
- -1: Mur
- 0: Espace vide
- 1: Cible
- 2: Caisse
- 3: Joueur

## Problèmes identifiés:
1. Il y a 6 caisses (2) mais seulement 5 cibles (1)
2. Certaines caisses sont dans des positions où elles peuvent être bloquées définitivement
3. La disposition symétrique peut créer des situations de blocage

## Solutions possibles:
1. Ajouter une cible supplémentaire
2. Repositionner certaines caisses
3. Modifier la disposition pour éviter les blocages

