# Feuille de route — docs-suite-numerique

<!--
Ce fichier liste ce qui reste à faire. Il est lu par la compétence
"etat-des-lieux" en début de séance et mis à jour en fin de séance.
Gardez-le court : quelques lignes par section suffisent.
-->

## En cours
- [x] Fusionner la branche chore/claude-md (CLAUDE.md + .gitignore) — PR #8, 2026-09-23
- [ ] Fusionner la branche test/github-pages (widgets servis par URL + doc de déploiement)

## Prochaines étapes
- [ ] Après fusion de test/github-pages, basculer la source de GitHub Pages sur master
- [ ] Préparer le terrain des futurs widgets : structure par projets, dossier `commun/`, gabarit de widget prêt pour GitHub Pages
- [ ] Commits non signés : configurer la signature sur ce poste ou assouplir la règle du dépôt
- [ ] Compléter cette feuille de route (point 2 de l'état des lieux)

## Plus tard / idées
(suggestions de Claude, à valider)
- Vérifier que la sync fonctionne encore (cookies Docs probablement expirés depuis avril)
- Réactiver les notifications Brevo (NOTIFICATIONS_ENABLED)
- Éviter les doublons dans Chapitres quand on relance la sync

## Décisions récentes
<!-- Une ligne par décision : date — décision — raison en quelques mots -->
- 2026-09-23 — .vscode/settings.json n'est plus suivi par Git (tasks, launch et extensions le restent) — réglages propres au poste
- 2026-09-23 — les widgets peuvent être servis par GitHub Pages — test concluant avec parcours-doc sur l'instance Grist
- 2026-09-23 — les widgets du GT cartes de bruit ne sont plus en service — on prépare les futurs widgets plutôt que de migrer l'existant
