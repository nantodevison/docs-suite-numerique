# Espace « gestion de projets »

Document Grist unique du groupe PMD (instance Grist de la DINUM), qui regroupe
plusieurs modules autour de la table **`Projets2`**. Chaque projet suivi
(Valorisation, Écoute client, Observatoire des trafics…) est une **ligne** de
`Projets2`.

[`grist_schema.py`](grist_schema.py) est l'export du code Grist (*Outils → Vue du
code*) : il décrit la structure des tables, sans aucune donnée. C'est la
référence pour les noms de tables et de colonnes utilisés par les widgets.

## Modules

| Module | Tables ou colonnes |
|---|---|
| Gestion de projet | `Projets2` → `Objectifs_resultats_cles` → `EPICs` → `Taches` |
| CRM | `Contacts`, `Structures`, `Interactions` |
| Retours utilisateurs | `Retour_U` et ses tables `Enum_…` (`Enum_Type_retourU`, `Enum_Tags_retourU`, `Enum_Opportunite_retourU`) |
| Valorisation | colonnes de `Projets2` : `Plus_value_Cerema`, `Exemple_de_resultat`, `Duplicable`, `image`, `Latitude`/`Longitude`… ; table `Info_valorisation_projet` |
| Écoute client | colonnes `ect_client_*` de `Projets2` ; table `Rex_ecoute_client` |

## Points d'attention

- **`Taches.couleur_statut`** ne connaît que 5 statuts (`🖐️ À faire`, `♻️ En cours`,
  `✅ Fait`, `🗃️ Archivé`, `❌ Annulé`) et lève une erreur pour les autres, alors
  que `EPICs.Avancement` et le Kanban de l'Observatoire en utilisent d'autres
  (`📧Demande envoyée`, `💾Data non transmises`, `🆙Disponible`…). Un widget ne
  doit pas dépendre de cette colonne.
- **`Taches.qui_`** est une liste de références (`ReferenceList`) vers `Contacts`,
  pas une référence simple.

## À nettoyer un jour

- Deux tables proches : `Departement` et `Departements`.
- Plusieurs liens entre `Projets2` et les contacts ou structures : `Contacts`,
  `Contacts_Projets`, `ect_client_contacts`, `Structures`, `Client`, `Partenaire`.
- `from urllib import quote` (formules `Envoi_mail` et `Mail_groupe`) est une
  syntaxe Python 2, alors que `EPICs.Avancement` utilise une f-string (Python 3) :
  le document tourne donc probablement en Python 3, et `Mail_groupe` est
  probablement en erreur (`from urllib.parse import quote` en Python 3).
