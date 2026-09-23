# pmd-suite-numerique

Boîte à outils du groupe **PMD** (Politique de Mobilité Durable, Cerema Sud-Ouest)
pour utiliser les outils de la **Suite Numérique** (Docs, Grist, Fichiers) :
widgets Grist réutilisables, synchronisation Docs → Grist, modèles de documents.

L'objectif est de capitaliser des fonctionnalités (Kanban, fiches, parcours
documentaires…) pour les diffuser auprès des collègues, sans repartir de zéro
à chaque projet.

## Organisation du dépôt

| Dossier | Répond à la question | Contenu |
|---|---|---|
| [`widgets/`](widgets/) | Où est le code d'un widget, et à quelle URL ? | Tous les widgets Grist, à plat, et leur **catalogue** |
| [`python/`](python/) | Comment synchroniser Docs et Grist ? | Clients API Docs et Grist, script de synchronisation |
| [`espaces/`](espaces/) | À quoi ressemble tel document Grist ? | Schéma (structure des tables, jamais de données) de chaque document Grist |
| [`projets/`](projets/) | Qu'est-ce qui concerne tel projet ? | Un dossier par projet : besoin, widgets utilisés, modèles Docs… |
| `images/` | — | Images publiées automatiquement par la synchronisation (GT CBS) |

## Utiliser un widget

Les widgets sont servis par GitHub Pages et se branchent dans Grist par URL :

```
https://nantodevison.github.io/pmd-suite-numerique/widgets/<nom-du-widget>/
```

La liste des widgets disponibles et la marche à suivre sont dans
[`widgets/README.md`](widgets/README.md).

## Projets

| Projet | État | Dossier |
|---|---|---|
| GT Harmonisation des méthodes de production des CBS (cartographie du bruit) | terminé, sert de référence | [`projets/gt-cbs-bruit/`](projets/gt-cbs-bruit/) |
| Observatoire des trafics routiers de Nouvelle-Aquitaine | Kanban en cours d'intégration | [`projets/observatoire-trafics/`](projets/observatoire-trafics/) |
| Écoute client | en préparation (fiches dans Docs, puis rapatriement dans Grist) | [`projets/ecoute-client/`](projets/ecoute-client/) |

> ⚠️ Ce dépôt est **public** : il ne doit contenir ni données (contacts, retours,
> écoutes client…), ni secrets (clés d'API, jetons, cookies). Ces derniers vont
> dans le fichier `.env`, qui n'est pas versionné.
