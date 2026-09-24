# Observatoire des trafics routiers de Nouvelle-Aquitaine

**État : Kanban intégré au dépôt (version d'origine), test par URL à faire.**

Projet suivi dans l'espace Grist [gestion de projets](../../espaces/gestion-projets/)
(ligne de `Projets2`).

## Kanban

Un Kanban de suivi des tâches a été développé par Rémi (CDD) pour ce projet,
d'abord par copier-coller dans le Custom Widget Builder de Grist. Il est intégré
à ce dépôt dans [`widgets/kanban/`](../../widgets/kanban/) (version d'origine),
et sera généralisé pour servir à d'autres projets de l'espace.

Particularités propres à l'Observatoire, à conserver sous forme de réglage
lors de la généralisation :
- onglets **Tâches / Standardiser / Linéariser**, fondés sur deux EPICs
  (« Standardiser les données gestionnaires », « Linéariser les départements ») ;
- statuts spécifiques (`📧Demande envoyée`, `💾Data non transmises`,
  `💽Data transmises`, `🔎Data vérifées`, `🆙Disponible`) ;
- champ **Millésime**.
