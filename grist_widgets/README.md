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

## Développement local avec VS Code

Le dossier `.vscode/` à la racine du dépôt fournit une configuration
optionnelle pour travailler confortablement depuis VS Code (extensions
recommandées, tâches, configurations de lancement). Ces fichiers sont
**non-obligatoires** et peuvent être ignorés si vous utilisez un autre éditeur.

### Extensions recommandées

À l'ouverture du dépôt, VS Code propose automatiquement d'installer :

| Extension | Rôle |
|-----------|------|
| **Live Server** (`ritwickdey.LiveServer`) | Serveur local avec rechargement automatique |
| **Prettier** (`esbenp.prettier-vscode`) | Formateur HTML / CSS / JS |
| **Python** (`ms-python.python`) | Support Python pour `sync.py` et notebooks |
| **DotENV** (`mikestead.dotenv`) | Colorisation des fichiers `.env` |

### Option A – Serveur local avec Python (aucune dépendance)

C'est l'approche recommandée pour les widgets HTML/JS purs de ce dépôt :
aucun outil supplémentaire requis, Python est déjà disponible dans l'environnement.

**Via les tâches VS Code** (`Ctrl+Shift+P` → *Exécuter la tâche*) :

| Tâche | Commande équivalente | URL locale |
|-------|----------------------|------------|
| `Grist: serveur – echanges (port 8081)` | `python -m http.server 8081` dans `grist_widgets/echanges/` | http://localhost:8081/ |
| `Grist: serveur – questions (port 8082)` | `python -m http.server 8082` dans `grist_widgets/questions/` | http://localhost:8082/ |
| `Grist: serveur – parcours-doc (port 8083)` | `python -m http.server 8083` dans `grist_widgets/parcours-doc/` | http://localhost:8083/ |

Ou avec la tâche générique qui demande quel widget et quel port utiliser :
`Grist: démarrer le serveur local (Python)`.

**En ligne de commande** (alternative directe) :

```bash
# Depuis la racine du dépôt
cd grist_widgets/echanges
python -m http.server 8081
# Widget accessible sur http://localhost:8081/index.html
```

### Option B – Live Server (rechargement automatique)

1. Installez l'extension **Live Server** (`ritwickdey.LiveServer`).
2. Ouvrez `grist_widgets/<widget>/index.html` dans VS Code.
3. Cliquez sur **Go Live** dans la barre d'état (en bas à droite).
4. Le navigateur s'ouvre automatiquement avec rechargement à chaque sauvegarde.

> **Note :** Live Server sert depuis la racine du dépôt par défaut ;
> l'URL sera donc `http://localhost:5500/grist_widgets/<widget>/index.html`.

### Utiliser le widget en développement dans Grist

Une fois le serveur local démarré, pointez le Custom Widget Grist sur l'URL locale :

1. Dans Grist, ajoutez ou modifiez un **Custom Widget**.
2. Saisissez l'URL : `http://localhost:8081/` (ou le port correspondant au widget).
3. Sauvegardez. Grist charge le widget depuis votre machine.
4. Chaque modification du code est prise en compte après rafraîchissement du widget (F5 dans le panneau Grist).

> ⚠️ L'instance Grist doit être accessible depuis la même machine que le serveur local
> (ex. Grist Desktop ou un Grist auto-hébergé en local). Les instances ministérielles
> isolées n'acceptent pas les URLs `localhost` externes.

---

### Option C – Template `custom-widget-builder` (widgets avancés)

Le [`custom-widget-builder`](https://github.com/gristlabs/custom-widget-builder)
est un template officiel Grist Labs basé sur **Vite** pour créer des widgets
avec un vrai outillage frontend (React, TypeScript, etc.).

> Les widgets actuels de ce dépôt sont des **HTML/JS purs** et n'utilisent pas
> ce template. Reportez-vous à cette section uniquement si vous créez un nouveau
> widget avec des dépendances npm.

#### Initialiser un widget avec le template

```bash
# Depuis grist_widgets/
npm create grist-widget@latest mon-nouveau-widget
cd mon-nouveau-widget
npm install
```

#### Développement avec rechargement automatique

Via la tâche VS Code `Grist: npm run dev (custom-widget-builder)`, ou :

```bash
cd grist_widgets/mon-nouveau-widget
npm run dev
# Serveur Vite démarre sur http://localhost:5173/ par défaut (port configurable dans vite.config.ts)
```

Pointez ensuite l'URL `http://localhost:5173/` (ou le port affiché dans le terminal) dans Grist (Custom Widget).

#### Construire les artefacts (build)

Via la tâche VS Code `Grist: npm run build (custom-widget-builder)`, ou :

```bash
cd grist_widgets/mon-nouveau-widget
npm run build
# Les fichiers compilés se trouvent dans dist/
```

#### Copier les artefacts dans Grist

Après le build, le dossier `dist/` contient un fichier `index.html` autonome
(avec tout le JS/CSS inliné ou bundlé). Deux options :

**Sur une instance avec accès internet** : hébergez `dist/` sur un serveur
statique (GitHub Pages, etc.) et pointez l'URL dans Grist.

**Sur l'instance ministérielle (sans internet)** :

1. Ouvrez `dist/index.html` dans un éditeur de texte.
2. Dans Grist, ajoutez un **Custom Widget** → choisissez *"Coller du code HTML"*.
3. Collez l'intégralité du contenu de `dist/index.html`.
4. Enregistrez.

> Si le build génère des fichiers JS/CSS séparés (chunks), vérifiez que
> `vite.config.ts` est configuré avec `build.rollupOptions.output.inlineDynamicImports: true`
> pour produire un seul fichier autonome.

---

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
