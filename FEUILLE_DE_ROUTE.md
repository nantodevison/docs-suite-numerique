# Feuille de route — pmd-suite-numerique

<!--
Ce fichier liste ce qui reste à faire. Il est lu par la compétence
"etat-des-lieux" en début de séance et mis à jour en fin de séance.
Gardez-le court : quelques lignes par section suffisent.
-->

## En cours
- [ ] Fusionner la branche feat/restructuration (nouvelle structure widgets/ python/ espaces/ projets/)

## Prochaines étapes
- [ ] Kanban de Rémi : décider des crédits, puis ajouter la version d'origine dans `widgets/kanban/` (commit dédié)
- [ ] Tester le Kanban par URL dans Grist, puis le généraliser (association de colonnes, « Sélectionner par » pour le projet, onglets configurables, références EPIC / `qui_`)
- [ ] Commits non signés et « changes must be made through a pull request » : configurer la signature sur ce poste ou assouplir les règles du dépôt
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
