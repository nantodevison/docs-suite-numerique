# Feuille de route — pmd-suite-numerique

<!--
Ce fichier liste ce qui reste à faire. Il est lu par la compétence
"etat-des-lieux" en début de séance et mis à jour en fin de séance.
Gardez-le court : quelques lignes par section suffisent.
-->

## En cours
- [x] Fusionner la branche feat/restructuration (nouvelle structure widgets/ python/ espaces/ projets/) — PR #10, 2026-09-23

## Prochaines étapes
- [x] Publier le Kanban de Rémi (PR #11) et corriger l'écriture des références et du nom de table (PR #12), testé par URL le 2026-09-24
- [ ] **Étape suivante** — Généraliser le Kanban pour un usage hors Observatoire (Écoute client, Valorisation) : retirer les valeurs codées en dur (projet OTV, contacts autorisés, noms d'EPICs et de tables), s'appuyer sur « Sélectionner par » pour le projet, rendre les onglets configurables
- [ ] Basculer le Kanban de l'Observatoire du builder vers la version par URL (à voir avec Rémi)
- [ ] Réparer les cellules EPIC / `qui_` invalides du document réel (en cours, par Martin)
- [ ] Valider la fiche type d'écoute client (Docs) avec May-Jeanne
- [ ] Ajouter un fichier `.env.example` (cité dans `python/README.md`, mais absent du dépôt)

## Plus tard / idées
(suggestions de Claude, à valider)
- Écoute client : modèle Docs, puis synchronisation vers Grist (en base64 pour les images : dépôt public)
- Nettoyer le schéma de l'espace gestion de projets (voir `espaces/gestion-projets/README.md`)
- Vérifier que la sync fonctionne encore (cookies Docs probablement expirés depuis avril)
- Éviter les doublons dans Chapitres quand on relance la sync

## Décisions récentes
<!-- Une ligne par décision : date — décision — raison en quelques mots -->
- 2026-09-23 — .vscode/settings.json n'est plus suivi par Git (tasks, launch et extensions le restent) — réglages propres au poste
- 2026-09-23 — les widgets peuvent être servis par GitHub Pages — test concluant avec parcours-doc sur l'instance Grist de la DINUM
- 2026-09-23 — les widgets du GT cartes de bruit ne sont plus en service — on prépare les futurs widgets plutôt que de migrer l'existant
- 2026-09-23 — dépôt renommé pmd-suite-numerique, gardé sur le compte nantodevison — outils destinés au groupe PMD
- 2026-09-23 — structure widgets/ (à plat, URL fixes) · python/ · espaces/ · projets/, avec catalogue des widgets — le classement évolue, les URL ne doivent pas bouger
- 2026-09-23 — règles GitHub limitées à master (pas de suppression, pas de réécriture), ni signature des commits ni PR exigées — trop contraignant pour un dépôt maintenu à une ou deux personnes
- 2026-09-23 — GitHub CLI (gh) installé en version portable dans %LOCALAPPDATA%\Programs\gh — pour que Claude puisse créer les PR
- 2026-09-24 — Rémi crédité comme co-auteur du Kanban (adresse noreply GitHub) — reconnaissance de son travail sans publier d'adresse personnelle
