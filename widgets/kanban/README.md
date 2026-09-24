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

Relevées à la lecture du code, puis en partie vérifiées lors du test par URL
du 2026-09-24 (sur une copie du document de gestion de projets).

**Valeurs propres à l'Observatoire, codées en dur :**
- le projet des nouvelles cartes est la **6ᵉ ligne** de `Projets2`
  (`tablePrj.id[5]`) : fragile si des lignes sont supprimées ou réordonnées ;
- les personnes assignables sont limitées aux contacts n° 20, 21, 23 et 360 ;
- les onglets Standardiser et Linéariser reposent sur les noms exacts de deux
  EPICs, et sur des listes de statuts propres au projet ;
- les tables `Projets2`, `Contacts` et `EPICs` sont lues par leur nom.

**Bug confirmé en test :**
- les champs de type référence (EPIC, Assigné à) sont enregistrés comme du
  **texte** : la cellule devient invalide dans Grist, et le badge affiche
  `#Invalid Ref` (EPIC) ou `#Invalid RefList` (`qui_`). Modifier l'EPIC d'une
  carte depuis le panneau ✏️ ne change rien à l'affichage. **En attendant le
  correctif, ne pas modifier ces deux champs depuis le panneau** ; les cellules
  abîmées se réparent dans Grist en resélectionnant la valeur.

**Autres défauts relevés à la lecture du code :**
- `grist.ready()` est appelé deux fois, et un `fetchTable('EPICs')` est placé
  hors du bloc de gestion d'erreur ;
- le préréglage cherche une colonne `Millésime`, alors qu'elle s'appelle
  `Millesime` ;
- si la table est vide, le panneau ⚙ ne propose aucune colonne.
