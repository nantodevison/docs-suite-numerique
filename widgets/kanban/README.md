# Widget Kanban (`kanban`)

Suivi de tâches en colonnes, une colonne par statut : glisser-déposer des cartes
et des colonnes, création, modification et suppression de cartes, filtres par
EPIC et par personne, tri par priorité.

**Auteur : Rémi** ([@Rmemb](https://github.com/Rmemb)), développé pour le projet
[Observatoire des trafics](../../projets/observatoire-trafics/).

> **Version d'origine**, reprise telle quelle depuis le Custom Widget Builder de
> Grist. Elle est **spécifique** à l'Observatoire (voir « Limites connues ») ;
> sa généralisation à d'autres projets (Écoute client, Valorisation) est prévue.

## Fichiers

| Fichier | Rôle |
|---|---|
| `index.html` | Structure HTML et styles ; charge `kanban.js` |
| `kanban.js` | Logique Grist : réception des données, rendu, glisser-déposer, écriture |

## Déploiement

Par URL (GitHub Pages) :

```
https://nantodevison.github.io/pmd-suite-numerique/widgets/kanban/
```

Voir [../README.md](../README.md#brancher-un-widget-par-url-github-pages) pour
l'avertissement et le niveau d'accès (**accès complet** requis).

> ⚠️ Le widget **écrit** dans la table (création, déplacement, modification,
> suppression de cartes). Pour un premier test, utiliser une copie du document.

## Configuration

Le bouton ⚙ ouvre un panneau qui associe les colonnes de la table aux champs du
Kanban : Titre et Statut (obligatoires), Description, Priorité, Assigné à,
Date / Échéance, EPIC, Millésime, Projet. Ce réglage, l'ordre des colonnes et
l'onglet actif sont mémorisés dans les options du widget (`grist.setOption`).

Par défaut, l'association est préremplie pour la table `Taches` de l'espace
[gestion de projets](../../espaces/gestion-projets/).

## Limites connues (version d'origine)

Relevées à la lecture du code, non encore vérifiées en test.

**Valeurs propres à l'Observatoire, codées en dur :**
- le projet des nouvelles cartes est la **6ᵉ ligne** de `Projets2`
  (`tablePrj.id[5]`) : fragile si des lignes sont supprimées ou réordonnées ;
- les personnes assignables sont limitées aux contacts n° 20, 21, 23 et 360 ;
- les onglets Standardiser et Linéariser reposent sur les noms exacts de deux
  EPICs, et sur des listes de statuts propres au projet ;
- les tables `Projets2`, `Contacts` et `EPICs` sont lues par leur nom.

**Bugs probables :**
- dans le panneau d'édition, les champs de type référence (EPIC, Assigné à)
  proposent des numéros de ligne et les enregistrent comme du texte, ce qui
  risque de casser la référence ;
- `qui_` est une liste de références : le badge et le filtre « Personne »
  affichent probablement des numéros ;
- `grist.ready()` est appelé deux fois, et un `fetchTable('EPICs')` est placé
  hors du bloc de gestion d'erreur ;
- le préréglage cherche une colonne `Millésime`, alors qu'elle s'appelle
  `Millesime` ;
- si la table est vide, le panneau ⚙ ne propose aucune colonne.
