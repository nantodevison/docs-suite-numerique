# Widget 2 – Échanges (`echanges`)

Affiche la liste des échanges (messages, commentaires, retours) associés aux
chapitres synchronisés depuis Docs. Permet de filtrer par texte ou par statut,
et synchronise la sélection avec le curseur Grist.

## Fichiers

| Fichier      | Rôle                                                   |
|-------------|--------------------------------------------------------|
| `index.html` | Structure HTML, styles du widget                       |
| `widget.js`  | Logique Grist : réception des données, rendu, filtrage |

## Table Grist attendue

Nom de table suggéré : **`Echanges`**

| Colonne        | Type    | Obligatoire | Description                                               |
|----------------|---------|-------------|-----------------------------------------------------------|
| `titre`        | Text    | ✅           | Titre court de l'échange                                  |
| `auteur`       | Text    | ☐           | Nom ou identifiant de l'auteur                            |
| `date`         | Date    | ☐           | Date de l'échange (stockée en secondes Unix par Grist)    |
| `statut`       | Choice  | ☐           | Statut : `ouvert`, `en attente`, `fermé` (texte libre)    |
| `contenu`      | Text    | ☐           | Corps du message                                          |
| `chapitre_ref` | Integer | ☐           | Référence (rowId) vers la table `Chapitres`               |

### Valeurs de statut reconnues

Le widget reconnaît automatiquement les variantes suivantes :

| Statut affiché | Valeurs acceptées (insensibles à la casse et aux accents) |
|----------------|----------------------------------------------------------|
| 🟢 Fermé        | `fermé`, `ferme`, `closed`, `résolu`, `resolu`           |
| 🟡 En attente   | `en attente`, `attente`, `waiting`, `pending`            |
| 🔵 Ouvert       | toute autre valeur                                       |

## Options du widget

Le widget ne demande que l'accès `read table` (lecture seule). Aucune écriture
n'est effectuée dans Grist depuis ce widget.

## Déploiement dans Grist

### Option A – Copier-coller (instance ministérielle sans internet)

1. Fusionner `widget.js` dans `index.html` :
   remplacer `<script src="widget.js"></script>` par le contenu de `widget.js`
   dans une balise `<script>`.
2. Dans Grist, ajouter un **Custom Widget** et coller le HTML complet.
3. Dans les options du widget, mapper les colonnes de la table `Echanges`.

### Option B – URL GitHub Raw

```
https://raw.githubusercontent.com/nantodevison/docs-suite-numerique/master/grist_widgets/echanges/index.html
```

## Notes de sécurité

- Lecture seule (`read table`) : aucune modification de données n'est possible.
- Pas de secret ni de clé API dans le code frontend.
- Le contenu des messages est affiché en texte brut (échappement HTML systématique)
  pour éviter toute injection XSS.

## Résolution de problèmes courants

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| `RPC_UNKNOWN_FORWARD_DEST` | `grist.ready()` non appelé en premier | Vérifier l'ordre d'appel dans `widget.js` |
| Liste vide | Table `Echanges` vide ou vue filtrée | Vérifier les données et les filtres Grist |
| Dates affichées incorrectement | Colonne de type `Text` au lieu de `Date` | Changer le type de la colonne en `Date` dans Grist |
