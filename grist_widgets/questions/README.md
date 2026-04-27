# Widget 3 – Questions / Réponses (`questions`)

Affiche les questions posées sur les chapitres documentaires, avec leurs
réponses associées. Permet de filtrer par statut (sans réponse / avec réponse)
et de rechercher par texte libre.

## Fichiers

| Fichier      | Rôle                                                       |
|-------------|-------------------------------------------------------------|
| `index.html` | Structure HTML, styles, onglets de filtre                  |
| `widget.js`  | Logique Grist : réception des données, rendu, filtrage Q&R |

## Table Grist attendue

Nom de table suggéré : **`Questions`**

| Colonne        | Type    | Obligatoire | Description                                            |
|----------------|---------|-------------|--------------------------------------------------------|
| `question`     | Text    | ✅           | Texte de la question                                   |
| `reponse`      | Text    | ☐           | Réponse à la question (vide si non encore répondu)     |
| `auteur`       | Text    | ☐           | Auteur de la question                                  |
| `date_question`| Date    | ☐           | Date de soumission de la question                      |
| `date_reponse` | Date    | ☐           | Date de la réponse                                     |
| `chapitre_ref` | Integer | ☐           | Référence (rowId) vers la table `Chapitres`            |

## Fonctionnalités

| Fonctionnalité | Description |
|----------------|-------------|
| Onglet « Toutes » | Affiche toutes les questions |
| Onglet « Sans réponse » | Affiche uniquement les questions sans réponse, triées en premier |
| Onglet « Avec réponse » | Affiche uniquement les questions avec réponse |
| Recherche texte | Filtre sur question, réponse et auteur |
| Synchronisation curseur | Clic sur une carte → sélection dans Grist |

## Options du widget

Accès requis : `read table` (lecture seule).

## Déploiement dans Grist

### Option A – Copier-coller (instance ministérielle sans internet)

1. Fusionner `widget.js` dans `index.html` :
   remplacer `<script src="widget.js"></script>` par le contenu de `widget.js`
   dans une balise `<script>`.
2. Dans Grist, ajouter un **Custom Widget** et coller le HTML complet.
3. Dans les options du widget, mapper les colonnes de la table `Questions`.

### Option B – URL GitHub Raw

```
https://raw.githubusercontent.com/nantodevison/docs-suite-numerique/master/grist_widgets/questions/index.html
```

## Notes de sécurité

- Lecture seule (`read table`) : aucune modification n'est effectuée dans Grist.
- Tout le contenu affiché est échappé HTML pour prévenir les injections XSS.
- Pas de clé API ni de token dans le code frontend.
- Si les questions contiennent des images (issues de Docs), elles sont stockées
  en base64 dans Grist et s'affichent directement sans appel réseau externe.

## Résolution de problèmes courants

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| `RPC_UNKNOWN_FORWARD_DEST` | `grist.ready()` non appelé en premier | Vérifier l'ordre d'appel dans `widget.js` |
| Onglet « Sans réponse » vide | Colonne `reponse` absente ou mal mappée | Vérifier le mapping dans les options du widget |
| Dates non affichées | Colonne de type `Text` au lieu de `Date` | Changer le type de la colonne en `Date` dans Grist |
