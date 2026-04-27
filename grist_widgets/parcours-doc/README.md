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

Aucune option personnalisée n'est nécessaire. Le widget utilise uniquement
le niveau d'accès `read table`.

## Déploiement dans Grist

### Option A – Copier-coller (instance ministérielle sans internet)

1. Dans Grist, ajouter un widget de type **Custom Widget**.
2. Choisir **"Saisir une URL ou coller du code"**.
3. Coller l'intégralité du contenu de `index.html` **dans lequel vous aurez
   inséré inline le contenu de `widget.js`** juste avant `</body>` :

   ```html
   <!-- Remplacer la ligne <script src="widget.js"></script> par : -->
   <script>
     /* contenu de widget.js ici */
   </script>
   ```

4. Enregistrer. Le widget affiche immédiatement les chapitres de la vue active.

### Option B – URL GitHub Raw (instance avec accès internet)

Pointer le widget sur :
```
https://raw.githubusercontent.com/nantodevison/docs-suite-numerique/master/grist_widgets/parcours-doc/index.html
```

> ⚠️ Dans ce cas, `index.html` charge `widget.js` via `<script src="widget.js">`.
> Grist doit autoriser les URLs raw GitHub dans sa configuration CSP.

## Notes de sécurité

- Le widget ne demande que l'accès `read table` (lecture seule).
- Aucune clé API ni donnée sensible n'est incluse dans le code frontend.
- Les images éventuellement présentes dans les contenus sont stockées en base64
  directement dans la colonne Grist (pas d'appel réseau externe).

## Résolution de problèmes courants

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| `RPC_UNKNOWN_FORWARD_DEST` dans la console | `grist.ready()` non appelé en premier | Vérifier que `widget.js` appelle `grist.ready()` avant tout autre appel Grist |
| Widget vide | Vue Grist sans données ou colonnes mal mappées | Vérifier le mapping des colonnes dans les options du widget |
| Sélection non synchronisée | `grist.setCursorPos` non supporté dans cette version | Mettre à jour l'instance Grist ou utiliser `grist.setSelectedRows` |
