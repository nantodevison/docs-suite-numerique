# grist_widgets/

Ce dossier centralise et versionne le code source des **widgets Grist** (HTML/CSS/JS)
utilisés dans le cadre du projet docs-suite-numerique.

## Organisation

```
grist_widgets/
├── README.md              ← ce fichier
├── parcours-doc/          ← Widget 1 : navigation par chapitres (parcours documentaire)
│   ├── index.html
│   ├── widget.js
│   └── README.md
├── echanges/              ← Widget 2 : affichage des échanges
│   ├── index.html
│   ├── widget.js
│   └── README.md
└── questions/             ← Widget 3 : affichage des questions/réponses
    ├── index.html
    ├── widget.js
    └── README.md
```

## Conventions

- Chaque widget est autonome (HTML + JS inline ou dans `widget.js`).
- Pas de dépendances npm : seules des CDN publics sont utilisés (chargés via `<script src="...">`).
- La bibliothèque `grist-plugin-api.js` est toujours chargée depuis `https://docs.getgrist.com/grist-plugin-api.js`.
- Toujours appeler `grist.ready()` **avant** tout appel à l'API Grist (évite l'erreur `RPC_UNKNOWN_FORWARD_DEST`).
- Les images internes Docs sont stockées en base64 dans Grist (voir `src/docs_client.py`).

## Workflow : modifier un widget

1. **Modifier** le fichier dans ce dépôt (ex. `grist_widgets/echanges/widget.js`).
2. **Committer** et **pousser** sur la branche `master` (ou ouvrir une PR).
3. Dans Grist, ouvrir le widget concerné → **Custom Widget** → coller le contenu d'`index.html` dans l'éditeur de code personnalisé,
   _ou_ pointer l'URL raw GitHub si l'instance Grist accepte les URLs externes :
   ```
   https://raw.githubusercontent.com/nantodevison/docs-suite-numerique/master/grist_widgets/<widget>/index.html
   ```
4. Enregistrer et rafraîchir le widget dans Grist.

> **Astuce :** Sur l'instance ministérielle isolée (sans accès internet), utiliser
> le **copier-coller** du code source complet dans l'éditeur de widget intégré de Grist.

## Notes de sécurité

- **Images en base64** : les images internes sont embarquées en base64 directement dans le contenu Grist. Cela évite toute dépendance à un serveur externe non accessible depuis l'instance ministérielle.
- **Pas de secrets dans le JS** : ne jamais inclure de clé API ou de token dans les widgets frontend.
- **Accès minimal** : chaque widget ne demande que le niveau d'accès nécessaire (`read table` ou `full` si écriture requise).
