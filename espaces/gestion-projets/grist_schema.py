import grist
from functions import *       # global uppercase functions
import datetime, math, re     # modules commonly needed in formulas


@grist.UserTable
class Contacts:
  Nom = grist.Text()
  Prenom = grist.Text()
  Email = grist.Text()
  Telephone = grist.Text()
  Structure = grist.Reference('Structures')
  Note = grist.Text()

  def _default_Doublon_Email(rec, table, value, user):
    return len(Contacts.lookupRecords(Email=rec.Email)) > 1 and rec.Email != ''
  Doublon_Email = grist.Bool()
  Service = grist.Choice()
  Projets = grist.ReferenceList('Projets2', reverse_of='Contacts_Projets')

  @grist.formulaType(grist.Text())
  def Envoi_mail(rec, table):
    from urllib import quote
    return " mailto:%s" % rec.Email

  @grist.formulaType(grist.Text())
  def Nom_complet(rec, table):
    if rec.Prenom and rec.Nom:
      return rec.Prenom + " " + rec.Nom
    elif rec.Prenom and not rec.Nom:
      return rec.Prenom
    elif not rec.Prenom and rec.Nom:
      return rec.Nom
    else:
      return None

  @grist.formulaType(grist.Bool())
  def Test_doublon_Nom(rec, table):
    return len(Contacts.lookupRecords(Nom_complet=rec.Nom_complet)) > 1

  def Nombre_d_interactions(rec, table):
    return len(Interactions.lookupRecords(Contacts=CONTAINS(rec.id)))

  class _Summary:

    @grist.formulaType(grist.ReferenceList('Contacts'))
    def group(rec, table):
      return table.getSummarySourceGroup(rec)

    @grist.formulaType(grist.Int())
    def count(rec, table):
      return len(rec.group)

    def gristHelper_Display(rec, table):
      return rec.Structure.Nom


@grist.UserTable
class Departement:
  NumeroDept = grist.Numeric()
  NomDept = grist.Text()

  @grist.formulaType(grist.Text())
  def GestionComplet(rec, table):
    return ", ".join(
        [
            r.Nom
            for r in Structures.all
            if rec.id in [x.id for x in r.Departements]
        ]
    )

  @grist.formulaType(grist.Numeric())
  def Nb_gestionnaire_fait(rec, table):
    return len([
        r for r in Taches.all
        if r.Fait
        and r.Nom in rec.GestionComplet
    ])

  @grist.formulaType(grist.Numeric())
  def Nb_gestionnaire(rec, table):
    return len(rec.GestionComplet.split(","))

  @grist.formulaType(grist.Numeric())
  def Avance(rec, table):
    if rec.Nb_gestionnaire == 0:
        return 0
    else:
        return round(
            rec.Nb_gestionnaire_fait / rec.Nb_gestionnaire,
            1
        )


@grist.UserTable
class Departements:
  NumeroDept = grist.Numeric()
  NomDept = grist.Text()
  GestionComplet = grist.ReferenceList('Structures', reverse_of='Departements')

  def Departements(rec, table):
    return None


@grist.UserTable
class EPICs:
  Projet = grist.Reference('Projets2', reverse_of='EPICs')
  Titre = grist.Text()
  Taches = grist.ReferenceList('Taches', reverse_of='EPIC')
  Notes = grist.Text()
  Retour_U = grist.ReferenceList('Retour_U', reverse_of='EPIC')
  objectifs_resultats_cle = grist.Reference('Objectifs_resultats_cles', reverse_of='EPICs')
  Priorite = grist.Choice()

  def Avancement(rec, table):
    cnt=0
    cnt_tot = len([t for t in rec.Taches.statut
      if t in('🖐️ À faire', '♻️ En cours',
      '✅ Fait', '📧Demande envoyée', '💾Data non transmises',
      '💽Data transmises', '🔎Data vérifées')])

    for t in rec.Taches.statut :
      if t == '✅ Fait':
        cnt += 1

    if all([t in ('🗃️ Archivé', '❌ Annulé', '✅ Fait') for t in rec.Taches.statut ]):
      if cnt_tot == 0:
        cnt_tot = 1
      cnt = cnt_tot

    return f"{round((cnt/cnt_tot)*100)} %"


@grist.UserTable
class Enum_Competences_specifiques:

  def _default_competences(rec, table, value, user):
    if len(value) > 30:
      return ValueError("Competences ne doit pas dépasser 30 caractères")
    else:
      return value
  competences = grist.Text()


@grist.UserTable
class Enum_Donnees:

  def _default_donnees(rec, table, value, user):
    if len(value) > 40:
      return ValueError("Données ne doit pas dépasser 40 caractères")
    else:
      return value
  donnees = grist.Text()


@grist.UserTable
class Enum_Opportunite_retourU:
  Besoin_Opportunite = grist.Text()

  def counting(rec, table):
    return len(Retour_U.lookupRecords(Opportunites=rec.id))


@grist.UserTable
class Enum_Tags_retourU:
  Tags = grist.Text()

  def counting(rec, table):
    return len(Retour_U.lookupRecords(Tags=CONTAINS(rec.id)))


@grist.UserTable
class Enum_Territoire:
  Nom = grist.Text()


@grist.UserTable
class Enum_Themes:

  def _default_enum_theme(rec, table, value, user):
    if len(value) > 40:
      return ValueError("Theme ne doit pas dépasser 40 caractères")
    else:
      return value
  enum_theme = grist.Text()


@grist.UserTable
class Enum_Type_retourU:
  Type = grist.Text()


@grist.UserTable
class Info_Template:
  Info_Template = grist.Text()


@grist.UserTable
class Info_valorisation_projet:
  Info_valorisation_projet = grist.Text()


@grist.UserTable
class Interactions:
  Contacts = grist.ReferenceList('Contacts')

  def _default_Date(rec, table, value, user):
    return NOW()
  Date = grist.DateTime('Europe/Paris')
  Type = grist.Choice()
  Description = grist.Text()
  Projets = grist.ReferenceList('Projets2')

  class _Summary:

    @grist.formulaType(grist.ReferenceList('Interactions'))
    def group(rec, table):
      return table.getSummarySourceGroup(rec)

    @grist.formulaType(grist.Int())
    def count(rec, table):
      return len(rec.group)


@grist.UserTable
class OTV:
  otv = grist.Text()


@grist.UserTable
class Objectifs_resultats_cles:
  Projet = grist.Reference('Projets2', reverse_of='Objectifs_resultats_cles')
  Objectifs = grist.Text()
  resultats_cle = grist.Text()
  delai = grist.Date()
  EPICs = grist.ReferenceList('EPICs', reverse_of='objectifs_resultats_cle')


@grist.UserTable
class Projets2:

  def _default_Titre(rec, table, value, user):
    if len(value) > 30:
      return "Titre ne doit pas dépasser 30 caractères"
    else:
      return value
  Titre = grist.Text()

  def _default_Sous_Titre(rec, table, value, user):
    if len(value) > 50:
      return "Sous titre ne doit pas dépasser 50 caractères"
    else:
      return value
  Sous_Titre = grist.Text()
  Territoire = grist.ReferenceList('Enum_Territoire')
  Client = grist.ReferenceList('Structures')
  Partenaire = grist.ReferenceList('Structures')

  def _default_Description(rec, table, value, user):
    if len(value) > 250:
      return ValueError("La description ne doit pas dépasser 250 caractères")
    else:
      return value
  Description = grist.Text()

  def _default_Exemple_de_resultat(rec, table, value, user):
    if len(value) > 250:
      return ValueError("L'exemple de résultat ne doit pas dépasser 250 caractères")
    else:
      return value
  Exemple_de_resultat = grist.Text()
  Donnees = grist.ReferenceList('Enum_Donnees')
  Competences_specifiques = grist.ReferenceList('Enum_Competences_specifiques')
  Contacts = grist.ReferenceList('Contacts')
  Reference = grist.Text()
  Latitude = grist.Numeric()
  Longitude = grist.Numeric()
  Theme = grist.ReferenceList('Enum_Themes')
  image = grist.Any()
  Annee = grist.Int()
  EPICs = grist.ReferenceList('EPICs', reverse_of='Projet')

  def _default_Plus_value_Cerema(rec, table, value, user):
    if len(value) > 150:
      return ValueError("La plus-value ne doit pas dépasser 150 caractères")
    else:
      return value
  Plus_value_Cerema = grist.Text()
  ect_client_fiche = grist.Text()
  ect_client_format_demande = grist.ChoiceList()
  ect_client_contacts = grist.ReferenceList('Contacts')

  def _default_ect_client_probleme(rec, table, value, user):
    if len(value) > 150:
      return ValueError("Le problème ne doit pas dépasser 150 caractères")
    else:
      return value
  ect_client_probleme = grist.Text()
  ect_client_1ere_reponse = grist.Choice()
  ect_client_reponse_finale = grist.Choice()
  Duplicable = grist.Bool()
  Objectifs_resultats_cles = grist.ReferenceList('Objectifs_resultats_cles', reverse_of='Projet')
  Contacts_Projets = grist.ReferenceList('Contacts', reverse_of='Projets')
  Structures = grist.ReferenceList('Structures', reverse_of='Projets')

  def Contacts_Email(rec, table):
    return rec.Contacts.Email


@grist.UserTable
class Retour_U:
  Utilisateur = grist.Reference('Contacts')
  Nature = grist.ChoiceList()
  Observation = grist.Text()
  Commentaire = grist.Any()
  Screenshot = grist.Any()
  Type = grist.Reference('Enum_Type_retourU')
  Tags = grist.ReferenceList('Enum_Tags_retourU')
  Sentiment = grist.Choice()
  Opportunites = grist.Reference('Enum_Opportunite_retourU')
  Source = grist.Choice()
  ID_de_la_ligne = grist.Numeric()

  def _default_Date(rec, table, value, user):
    return NOW()
  Date = grist.Date()
  Projet = grist.Reference('Projets2')
  EPIC = grist.Reference('EPICs', reverse_of='Retour_U')
  Type_retour = grist.ChoiceList()
  Resolu = grist.Bool()


@grist.UserTable
class Rex_ecoute_client:
  Projet = grist.Reference('Projets2')
  proposition = grist.Text()
  rex = grist.Choice()


@grist.UserTable
class Structures:
  Nom = grist.Text()
  Nature_juridique = grist.Choice()
  Projets = grist.ReferenceList('Projets2', reverse_of='Structures')
  Departements = grist.ReferenceList('Departements', reverse_of='GestionComplet')

  @grist.formulaType(grist.Text())
  def Mail_groupe(rec, table):
    from urllib import quote
    people = Contacts.lookupRecords(Structure=rec.id)
    return "Courriel groupé (%s) mailto:%s" % (len(people), quote(", ".join(people.Email)))

  class _Summary:

    @grist.formulaType(grist.ReferenceList('Structures'))
    def group(rec, table):
      return table.getSummarySourceGroup(rec)

    @grist.formulaType(grist.Int())
    def count(rec, table):
      return len(rec.group)


@grist.UserTable
class Taches:
  Projet = grist.Reference('Projets2')
  Nom = grist.Text()
  statut = grist.Choice()
  date_cible = grist.Date()
  qui_ = grist.ReferenceList('Contacts')
  Description = grist.Text()
  Priorite = grist.Choice()
  EPIC = grist.Reference('EPICs', reverse_of='Taches')
  Bloque = grist.ReferenceList('Taches', reverse_of='Bloquee_par')
  Bloquee_par = grist.ReferenceList('Taches', reverse_of='Bloque')
  Millesime = grist.Text()
  Commentaire = grist.Text()

  @grist.formulaType(grist.Text())
  def couleur_statut(rec, table):
    if rec.statut == '✅ Fait':
        return '#E7FCDE'
    elif rec.statut == '🗃️ Archivé':
        return '#F0F0F0'
    elif rec.statut == '❌ Annulé':
        return '#DFD7D7'
    elif rec.statut == '🖐️ À faire':
        return '#FFE3E3'
    elif rec.statut == '♻️ En cours':
        return '#E3FFFF'
    else:
        raise ValueError("Le statut n'est pas pris en compte")

  @grist.formulaType(grist.Reference('Objectifs_resultats_cles'))
  def EPIC_objectifs_resultats_cle(rec, table):
    return rec.EPIC.objectifs_resultats_cle

  @grist.formulaType(grist.Bool())
  def Fait(rec, table):
    if rec.statut == "✅ Fait":
        return True
    elif rec.statut == "🗃️ Archivé":
        return True
    else:
        return False
