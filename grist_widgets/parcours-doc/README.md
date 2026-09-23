# Widget 1 – Parcours documentaire (`parcours-doc`)

Affiche l'arborescence des chapitres d'un document Docs synchronisé dans Grist.
Permet de naviguer dans la hiérarchie et de sélectionner un chapitre pour que
les autres widgets (ex. contenu, échanges) réagissent en conséquence.

## Fichiers

| Fichier      | Rôle                                               |
|-------------|-----------------------------------------------------|
| `index.html` | Structure HTML et styles du widget                 |
| `widget.js`  | Logique Grist (prêt, réception des enregistrements, navigation) |

## Table Grist attendue

Nom de table par défaut : **`Chapitres`**

| Colonne       | Type    | Obligatoire | Description                                    |
|---------------|---------|-------------|------------------------------------------------|
| `titre`       | Text    | ✅           | Titre complet du chapitre (peut inclure un emoji) |
| `titre_propre`| Text    | ☐           | Titre sans emoji (généré par `sync.py`)        |
| `numero`      | Text    | ☐           | Numérotation hiérarchique (ex. `1.2.3`)        |
| `niveau`      | Numeric | ✅           | Profondeur dans l'arbre (0 = racine)           |
| `ordre`       | Numeric | ☐           | Ordre d'affichage                              |
| `url`         | Text    | ☐           | URL du chapitre dans Docs                      |
| `contenu`     | Text    | ☐           | Contenu Markdown du chapitre                   |

> Ces colonnes sont produites automatiquement par `src/sync.py`.

## Options du widget

Aucune option personnalisée n'est nécessaire. Le widget demande le niveau
d'accès complet (`full`).

## Déploiement dans Grist

### Option A – Copier-coller (onglets HTML + JavaScript)

1. Dans Grist, ajouter un widget de type **Custom Widget** et choisir de coller du code.
2. Coller le contenu de `index.html` dans l'onglet **HTML** et celui de `widget.js`
   dans l'onglet **JavaScript**.
3. Enregistrer. Le widget affiche immédiatement les chapitres de la vue active.

### Option B – URL (GitHub Pages)

```
https://nantodevison.github.io/docs-suite-numerique/grist_widgets/parcours-doc/
```

Voir [../README.md](../README.md#brancher-un-widget-par-url-github-pages) pour l'avertissement et le niveau d'accès.

## Notes de sécurité

- Le widget demande l'accès complet (`full`), bien qu'il ne fasse que lire la table `Chapitres`.
- Aucune clé API ni donnée sensible n'est incluse dans le code frontend.
- Les images présentes dans les contenus sont hébergées sur GitHub ou embarquées
  en base64, selon la configuration de la synchronisation.

## Résolution de problèmes courants

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| `RPC_UNKNOWN_FORWARD_DEST` dans la console | `grist.ready()` non appelé en premier | Vérifier que `widget.js` appelle `grist.ready()` avant tout autre appel Grist |
| Widget vide | Vue Grist sans données ou colonnes mal mappées | Vérifier le mapping des colonnes dans les options du widget |
| Sélection non synchronisée | `grist.setCursorPos` non supporté dans cette version | Mettre à jour l'instance Grist ou utiliser `grist.setSelectedRows` |
