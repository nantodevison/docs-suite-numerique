# Écoute client

**État : en préparation** — les fiches sont rédigées dans Docs ;
le rapatriement dans Grist viendra ensuite.

Projet suivi dans l'espace Grist [gestion de projets](../../espaces/gestion-projets/)
(ligne de `Projets2`, colonnes `ect_client_*` et table `Rex_ecoute_client`).

Document de contexte (accès restreint) :
[Écoute client — contexte](https://docs.numerique.gouv.fr/docs/cc780879-7cf5-436b-a679-4bd87a0ee19b/)

## La fiche type

Modèle Docs public : [[Date]__[Affaire]__Écoute Client](https://docs.numerique.gouv.fr/docs/d9b4210e-ae68-4ca0-9667-a4624894c334/)

Sections : participants (Cerema, client) · synthèse du besoin (150 caractères) ·
le besoin (règle des 3 « Pourquoi ? ») · l'état actuel · le délai · les attentes ·
1ère réponse (On y va / On y va pas / On y va mais on va faire différemment) ·
adaptations proposées · retour client à chaud.

## Correspondance fiche → Grist (à confirmer)

| Fiche | Grist |
|---|---|
| Synthèse du besoin | `Projets2.ect_client_probleme` |
| 1ère réponse | `Projets2.ect_client_1ere_reponse` |
| Participants clients | `Projets2.ect_client_contacts` |
| Lien vers la fiche | `Projets2.ect_client_fiche` |

## Autres éléments Grist liés à l'écoute client

Ils ne proviennent pas de la fiche :

| Grist | Rôle |
|---|---|
| `Projets2.ect_client_format_demande` | comment le client a pris contact (mail, téléphone…) |
| `Projets2.ect_client_reponse_finale` | décision finale de donner suite ou non à la demande du client (en modifiant ou non les objectifs) |
| table `Rex_ecoute_client` | retour d'expérience **méthodologique** sur l'écoute : ce qui a marché, ce qui a raté, pour améliorer les écoutes suivantes |

## Points d'attention

- Les fiches remplies contiennent des données personnelles (participants) :
  elles ne doivent jamais être copiées dans ce dépôt public.
- Pour une future synchronisation, voir [`../../python/`](../../python/) :
  la lecture de Docs se réutilise, l'extraction par section est à écrire.
