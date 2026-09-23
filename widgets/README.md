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

- Chaque widget est composé d'un `index.html` et d'un `widget.js` ; `index.html` charge `widget.js` par `<script src="widget.js">` (indispensable en mode URL).
- Pas de dépendances npm : seules des CDN publics sont utilisés (chargés via `<script src="...">`).
- La bibliothèque `grist-plugin-api.js` est toujours chargée depuis `https://docs.getgrist.com/grist-plugin-api.js`.
- Toujours appeler `grist.ready()` **avant** tout appel à l'API Grist (évite l'erreur `RPC_UNKNOWN_FORWARD_DEST`).
- Les images internes Docs sont hébergées sur GitHub si `GITHUB_TOKEN` est défini, sinon embarquées en base64 (voir [le README principal](../README.md#gestion-des-images-internes)).

## Workflow : modifier un widget

1. **Modifier** le fichier dans ce dépôt (ex. `grist_widgets/echanges/widget.js`).
2. **Committer** et **pousser** sur la branche `master` (ou ouvrir une PR).
3. Mettre à jour Grist, selon le mode de déploiement du widget :
   - **par URL (GitHub Pages)** : rien à faire, la nouvelle version est publiée automatiquement 1 à 2 minutes après le push sur la branche publiée ; il suffit de recharger la page Grist ;
   - **par copier-coller** : dans Grist, ouvrir le widget → *Modifier* → coller `index.html` dans l'onglet HTML et `widget.js` dans l'onglet JavaScript.

## Brancher un widget par URL (GitHub Pages)

1. Dans Grist : *Ajouter une vue* → *Personnalisée* → **URL personnalisée**, puis coller :
   ```
   https://nantodevison.github.io/docs-suite-numerique/grist_widgets/<widget>/
   ```
2. Grist affiche l'avertissement « Attention aux vues personnalisées de source inconnue ». Il est normal : cocher la case et confirmer.
3. Dans le panneau de droite, **Niveau d'accès** → **Accès complet au document**. Sinon, le widget affiche « Access not granted ».

> ⚠️ L'arborescence du dépôt fait partie de l'URL : déplacer ou renommer un dossier de widget casse les widgets branchés dessus.

Le code servi est public (dépôt GitHub public). Chaque widget charge aussi
`grist-plugin-api.js` (getgrist.com) et, pour `parcours-doc`, `marked` (jsDelivr).

## Notes de sécurité

- **Images** : hébergées sur GitHub (dépôt public) si `GITHUB_TOKEN` est défini, sinon embarquées en base64 dans le contenu Grist.
- **Pas de secrets dans le JS** : ne jamais inclure de clé API ou de token dans les widgets frontend.
- **Niveau d'accès** : les trois widgets demandent actuellement l'accès complet (`full`) ; réduire à `read table` ceux qui n'écrivent pas serait une amélioration.
