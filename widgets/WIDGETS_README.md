# Widgets Grist — Documentation

Ce dossier contient deux widgets Grist autonomes (HTML/CSS/JS) :

| Fichier | Widget | Description |
|---|---|---|
| `widget2-echanges/index.html` | Widget 2 – Échanges | Chat expert, fil de discussion par question |
| `widget3-questions/index.html` | Widget 3 – Questions | Liste et gestion des questions |

---

## Prérequis Grist

### Tables requises

#### `Questions`

| Colonne | Type Grist | Description |
|---|---|---|
| `titre` | Texte | Intitulé court de la question |
| `contenu` | Texte | Description détaillée (optionnel, Markdown) |
| `auteur_id` | Référence → Users | Auteur de la question |
| `date_creation` | DateTime | Date de création (Unix secondes) |
| `est_doublon` | Booléen | `true` si la question est un doublon |
| `question_canonique` | Référence → Questions | Question originale (si doublon) |

#### `Reponses` *(Widget 2 uniquement)*

| Colonne | Type Grist | Description |
|---|---|---|
| `question_id` | Référence → Questions | Question associée |
| `auteur_id` | Référence → Users | Auteur de la réponse |
| `contenu` | Texte | Corps du message (Markdown, peut contenir des images base64) |
| `date_creation` | DateTime | Date d'envoi |
| `date_modification` | DateTime | Date de la dernière modification (optionnel) |

#### `Users`

| Colonne | Type Grist | Description |
|---|---|---|
| `nom` | Texte | Nom affiché |
| `email` | Texte | Adresse e-mail (pour l'identification automatique) |
| `role` | Texte | Rôle utilisateur : `user` ou `admin` |

#### `Widget_Session` *(optionnel)*

Table utilisée comme mécanisme d'identification alternatif :

| Colonne | Type Grist | Description |
|---|---|---|
| `email` | Texte | E-mail de l'utilisateur |
| `user_id` | Référence → Users | Utilisateur correspondant |

---

## Identification automatique de l'utilisateur

Les widgets tentent d'identifier l'utilisateur connecté dans cet ordre :

1. **`grist.getUser()`** — API Grist native (disponible sur les instances récentes).  
   Retourne l'e-mail de l'utilisateur connecté ; cherché dans la table `Users` par correspondance d'e-mail.

2. **Table `Widget_Session`** — Mécanisme de secours.  
   Le widget lit la première ligne de `Widget_Session` et utilise le `user_id` associé.

3. **Options du widget persistées** — `grist.getOptions()`.  
   Si l'utilisateur a déjà sélectionné son profil manuellement, l'option `currentUserId` est restaurée.

4. **Sélection manuelle** — Si aucune méthode automatique n'aboutit,  
   un sélecteur demande à l'utilisateur de choisir son profil dans la liste des `Users`.

---

## Installation dans Grist

1. **Hébergez** les fichiers HTML (ex. : GitHub Pages, serveur interne, Netlify, etc.).
2. Dans Grist, ajoutez un **widget personnalisé** (onglet *Ajouter un widget → Personnalisé*).
3. Entrez l'URL complète du fichier (ex. : `https://raw.githubusercontent.com/…/widget2-echanges/index.html`).
4. Sélectionnez l'accès **Lecture/écriture complète** (`Full document access`).
5. **Widget 2** : liez le widget à la table `Questions` pour que `grist.onRecord()` reçoive la question sélectionnée.

> **Note :** Si le widget est servi depuis `raw.githubusercontent.com`, l'en-tête MIME peut être incorrect.  
> Préférez GitHub Pages (`https://<user>.github.io/<repo>/`) ou tout autre hébergeur qui sert correctement le type MIME `text/html`.

---

## Fonctionnalités Widget 2 – Échanges

### Interface de chat

- Fil de discussion par question sélectionnée dans le tableau `Questions`.
- Avatars colorés (initiales) pour chaque participant.
- Rendu Markdown complet : **gras**, *italique*, `code`, blocs de code, listes, citations, liens, images.

### Envoi de messages

- Zone de saisie avec support Markdown.
- **Ctrl+Entrée** pour envoyer.
- Le contenu est enregistré dans la table `Reponses`.

### Édition / suppression

- Chaque auteur peut modifier ou supprimer ses propres messages.
- Les utilisateurs avec `role = 'admin'` peuvent modifier/supprimer tous les messages.
- Un message modifié affiche la mention *(modifié)* avec la date de modification.

### Renommage du nom d'utilisateur

- Bouton **✏️ Modifier le nom** dans l'en-tête du widget.
- Mise à jour immédiate de `Users.nom` dans Grist.
- Le nouveau nom est visible par tous les participants.

### Marquage doublon

- Bouton **⚠️ Marquer doublon** dans l'en-tête de la question.
- Optionnel : sélection de la question canonique dans la liste.
- Met à jour `Questions.est_doublon = true` et `Questions.question_canonique`.
- Bouton **✅ Retirer doublon** pour annuler.

### Collage d'images depuis le presse-papiers

1. Copiez une image (Imprim Écran, copier depuis un outil).
2. Cliquez dans la zone de saisie et appuyez sur **Ctrl+V**.
3. Un aperçu s'affiche sous la zone de saisie.
4. Cliquez **Envoyer** pour inclure l'image dans le message.
5. L'image est convertie en Data URL (base64) et insérée comme balise `<img>` dans le contenu Markdown.
6. Les images sont rendues avec `max-width: 100%` dans les messages.

#### Limite de taille des images

- Par défaut : **500 Ko** (avant encodage base64).
- Configurable dans le code : constante `CFG.MAX_IMAGE_KB` en haut du fichier JS.
- Un message d'erreur s'affiche si l'image dépasse la limite.

> **⚠️ Attention :** Les images base64 sont stockées directement dans le champ `contenu` de `Reponses`.  
> Les images volumineuses peuvent alourdir le document Grist. Limitez la taille si de nombreux utilisateurs collent des images.

---

## Fonctionnalités Widget 3 – Questions

### Liste des questions

- Affichage de toutes les questions de la table `Questions`.
- Tri par date de création (plus récentes en premier).
- Badge **Actif** / **⚠️ Doublon** sur chaque carte.

### Recherche et filtres

| Filtre | Description |
|---|---|
| **Toutes** | Toutes les questions |
| **Actives** | Questions non marquées doublon |
| **Doublons** | Questions marquées doublon |
| **Mes questions** | Questions de l'utilisateur courant |

La recherche textuelle filtre simultanément le titre et le contenu.

### Détail et édition

- Cliquer sur une question ouvre un panneau de détail avec rendu Markdown.
- L'auteur (ou un admin) peut modifier le titre et le contenu.
- Le panneau peut être fermé avec le bouton **✕**.

### Marquage doublon (même fonctionnement que le Widget 2)

- Bouton **⚠️ Doublon** sur chaque carte et dans le panneau de détail.
- Sélection optionnelle de la question canonique.
- Bouton **✅ Retirer doublon** pour annuler.

### Actualisation

- Bouton **⟳ Actualiser** pour recharger les données depuis Grist.

---

## Adaptation des noms de colonnes

Les noms de colonnes Grist sont centralisés dans la constante `CFG` en haut du fichier JS de chaque widget.  
Si vos tables utilisent des noms différents, modifiez uniquement cette section :

```javascript
const CFG = {
  T_QUESTIONS: 'Questions',   // nom de la table Questions
  T_REPONSES:  'Reponses',    // nom de la table Reponses (widget 2)
  T_USERS:     'Users',       // nom de la table Users
  T_SESSION:   'Widget_Session',

  Q_TITRE:     'titre',       // colonne titre dans Questions
  Q_AUTEUR:    'auteur_id',   // colonne ref auteur dans Questions
  // … etc.
};
```

---

## Permissions et rôles

| Action | Conditions |
|---|---|
| Lire les messages / questions | Tous les utilisateurs |
| Envoyer une réponse | Utilisateurs identifiés |
| Modifier un message | Auteur du message **ou** `role = 'admin'` |
| Supprimer un message | Auteur du message **ou** `role = 'admin'` |
| Renommer son profil | Utilisateur connecté (modifie `Users.nom`) |
| Marquer doublon | Tous les utilisateurs identifiés |
| Modifier une question | Auteur de la question **ou** `role = 'admin'` |

> Les permissions Grist (règles d'accès sur les tables) s'appliquent en plus des vérifications côté widget.  
> Les vérifications côté widget sont une aide à l'interface ; les règles Grist sont la source de vérité pour la sécurité.

---

## Tests manuels recommandés

### Identification utilisateur

1. Ouvrir le widget dans un document Grist avec la table `Users` peuplée.
2. Vérifier que le nom en haut à gauche correspond à l'utilisateur connecté.
3. Si non reconnu, vérifier que le sélecteur manuel s'affiche et que la sélection est persistée.

### Renommage (Widget 2 & 3)

1. Cliquer **✏️ Modifier le nom**.
2. Saisir un nouveau nom et valider.
3. Vérifier dans Grist que `Users.nom` a été mis à jour.
4. Vérifier que le nom est mis à jour dans l'interface sans rechargement.

### Envoi de message (Widget 2)

1. Sélectionner une question dans le tableau lié.
2. Saisir un message et cliquer **Envoyer** (ou Ctrl+Entrée).
3. Vérifier l'apparition du message dans le fil.
4. Vérifier l'enregistrement dans la table `Reponses` dans Grist.

### Édition de message (Widget 2)

1. Survoler un message pour faire apparaître **✏️ Modifier**.
2. Modifier le texte et enregistrer (ou Ctrl+Entrée).
3. Vérifier la mention *(modifié)* et la mise à jour dans Grist.

### Collage d'image (Widget 2)

1. Copier une image (ex. : Imprim Écran).
2. Cliquer dans la zone de saisie, appuyer Ctrl+V.
3. Vérifier l'aperçu de l'image sous la zone de saisie.
4. Envoyer le message.
5. Vérifier que l'image s'affiche correctement dans le fil (avec `max-width:100%`).
6. Tester avec une image > 500 Ko : vérifier le message d'erreur.
7. Cliquer **✕** sur l'aperçu : vérifier la suppression de l'image en attente.

### Marquage doublon (Widget 2 & 3)

1. Cliquer **⚠️ Marquer doublon** sur une question.
2. Optionnellement sélectionner la question canonique.
3. Valider : vérifier le badge **Doublon** et la mise à jour dans Grist.
4. Cliquer **✅ Retirer doublon** : vérifier le retour au badge **Actif**.

### Filtres / recherche (Widget 3)

1. Saisir un mot dans la recherche : vérifier le filtrage en temps réel.
2. Changer le filtre (Actives / Doublons / Mes questions) : vérifier les résultats.
3. Cliquer **⟳ Actualiser** après une modification dans Grist : vérifier la mise à jour.

---

## Dépendances CDN

Les widgets chargent les bibliothèques suivantes depuis jsDelivr / Grist CDN :

| Bibliothèque | URL | Rôle |
|---|---|---|
| grist-plugin-api | `https://docs.getgrist.com/grist-plugin-api.js` | API Grist officielle |
| marked v9 | `https://cdn.jsdelivr.net/npm/marked@9/marked.min.js` | Rendu Markdown |
| DOMPurify v3 | `https://cdn.jsdelivr.net/npm/dompurify@3/dist/purify.min.js` | Sanitisation XSS |

> Si l'instance Grist est isolée (pas d'accès Internet), hébergez ces bibliothèques en local et ajustez les balises `<script src="…">`.

> **Note pour les instances gouv.fr :** L'URL `https://docs.getgrist.com/grist-plugin-api.js` peut être remplacée par l'URL de votre instance Grist (ex. : `https://grist.numerique.gouv.fr/grist-plugin-api.js`).
