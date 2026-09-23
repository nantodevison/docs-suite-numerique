# widgets/

Tous les **widgets Grist** (HTML/CSS/JS) du dépôt, rangés **à plat** : un dossier
par widget, quel que soit le projet qui l'utilise.

Chaque widget est publié par GitHub Pages à l'adresse :

```
https://nantodevison.github.io/pmd-suite-numerique/widgets/<nom-du-dossier>/
```

> ⚠️ **Le nom du dossier fait partie de l'URL.** Déplacer ou renommer le dossier
> d'un widget publié casse tous les documents Grist qui l'utilisent. Le classement
> (générique ou spécifique, projets concernés…) se fait dans le catalogue
> ci-dessous, jamais par l'arborescence.

## Catalogue

### Format

| Champ | Contenu | Valeurs autorisées |
|---|---|---|
| **Widget** | nom du dossier, avec lien | — |
| **Rôle** | ce que fait le widget, en une phrase | texte libre |
| **Portée** | peut-il servir ailleurs tel quel ? | `générique` · `spécifique` |
| **Projet(s)** | projets qui l'utilisent | noms de dossiers de [`../projets/`](../projets/), ou `—` |
| **Données** | générique : colonnes à associer ; spécifique : tables lues ou écrites | texte court |
| **Accès** | niveau demandé à Grist | `read table` · `full` |
| **Statut** | où en est-il ? | `en développement` · `en service` · `archivé` |

### Widgets

| Widget | Rôle | Portée | Projet(s) | Données | Accès | Statut |
|---|---|---|---|---|---|---|
| [parcours-doc](parcours-doc/) | Parcourir les chapitres d'un document Docs synchronisé | spécifique | gt-cbs-bruit | lit `Chapitres` | `full` | archivé |
| [questions](questions/) | Poser des questions sur le document et les classer par thème | spécifique | gt-cbs-bruit | lit et écrit `Questions`, `Question_Theme_Link`, `Enum_Themes`, `Widget_Session` ; lit `Users` | `full` | archivé |
| [echanges](echanges/) | Répondre aux questions, voter, lier les réponses aux chapitres ; notifications email (désactivées) | spécifique | gt-cbs-bruit | lit et écrit `Questions`, `Reponses`, `Votes`, `Reponse_Chapitre_Link`, `Conversations`… ; lit `Chapitres`, `Users` | `full` | archivé |

## Conventions

- Chaque widget est composé d'un `index.html` et d'un fichier JavaScript ; `index.html` charge ce dernier par `<script src="…">` (indispensable en mode URL).
- Pas de dépendances npm : seules des CDN publics sont utilisés (chargés via `<script src="...">`).
- La bibliothèque `grist-plugin-api.js` est toujours chargée depuis `https://docs.getgrist.com/grist-plugin-api.js`.
- Toujours appeler `grist.ready()` **avant** tout appel à l'API Grist (évite l'erreur `RPC_UNKNOWN_FORWARD_DEST`).
- Les dossiers dont le nom commence par `_` (futurs `_gabarit/`, `_lib/`) ne sont pas des widgets : ce sont des ressources partagées. Ils sont publiés grâce au fichier `.nojekyll` à la racine du dépôt.

## Workflow : modifier un widget

1. **Modifier** le fichier dans ce dépôt (ex. `widgets/echanges/widget.js`).
2. **Committer** et **pousser**, puis fusionner sur `master` (la branche publiée par GitHub Pages).
3. Mettre à jour Grist, selon le mode de déploiement du widget :
   - **par URL (GitHub Pages)** : rien à faire, la nouvelle version est publiée automatiquement 1 à 2 minutes après la fusion sur `master` ; il suffit de recharger la page Grist ;
   - **par copier-coller** : dans Grist, ouvrir le widget → *Modifier* → coller `index.html` dans l'onglet HTML et le fichier JavaScript dans l'onglet JavaScript.

## Brancher un widget par URL (GitHub Pages)

1. Dans Grist : *Ajouter une vue* → *Personnalisée* → **URL personnalisée**, puis coller :
   ```
   https://nantodevison.github.io/pmd-suite-numerique/widgets/<widget>/
   ```
2. Grist affiche l'avertissement « Attention aux vues personnalisées de source inconnue ». Il est normal : cocher la case et confirmer.
3. Dans le panneau de droite, **Niveau d'accès** → **Accès complet au document**. Sinon, le widget affiche « Access not granted ».

Le code servi est public (dépôt GitHub public). Chaque widget charge aussi
`grist-plugin-api.js` (getgrist.com) et, pour `parcours-doc`, `marked` (jsDelivr).

## Notes de sécurité

- **Pas de secrets dans le JS** : ne jamais inclure de clé API ou de token dans les widgets frontend.
- **Niveau d'accès** : demander le niveau minimal ; `full` seulement si le widget écrit dans le document ou lit d'autres tables que celle de la vue.
- **Images** : voir [`../python/README.md`](../python/README.md#gestion-des-images-internes).
