import grist
from functions import *       # global uppercase functions
import datetime, math, re     # modules commonly needed in formulas


@grist.UserTable
class Alertes:
  question = grist.Reference('Questions')
  expert = grist.Reference('Users')
  type_alerte = grist.Choice()
  message = grist.Text()

  def _default_date_envoi(rec, table, value, user):
    return NOW()
  date_envoi = grist.DateTime('Europe/Paris')
  statut_alerte = grist.Choice()
  declenchee_par = grist.Reference('Users')

  @grist.formulaType(grist.DateTime('Europe/Paris'))
  def date_traitement(rec, table):
    return None


@grist.UserTable
class Chapitres:
  document = grist.Reference('Documents')
  parent_chapitre = grist.Reference('Chapitres')
  numero = grist.Text()
  titre = grist.Text()
  contenu = grist.Text()
  niveau = grist.Int()
  ordre = grist.Int()
  mots_cles = grist.ChoiceList()
  themes = grist.ChoiceList()
  url = grist.Text()

  @grist.formulaType(grist.Numeric())
  def nb_questions(rec, table):
    liens = Reponse_Chapitre_Link.lookupRecords(chapitre=rec.id)
    question_ids = set()
    for l in liens:
      rep = Reponses.lookupRecords(id=l.reponse)
      if rep:
        question_ids.add(rep[0].question)
    return len(question_ids)

  @grist.formulaType(grist.Text())
  def reference(rec, table):
    doc = Documents.lookupRecords(id=rec.document)
    d = "{} v{}".format(doc[0].titre, doc[0].version) if doc else "?"
    return u"{} — §{} {}".format(d, rec.numero, rec.titre)


@grist.UserTable
class Conversations:
  question = grist.Reference('Questions')
  statut = grist.Choice()
  ouverte_par = grist.Reference('Users')

  def _default_date_ouverture(rec, table, value, user):
    return NOW()
  date_ouverture = grist.DateTime('Europe/Paris')
  date_cloture = grist.DateTime('Europe/Paris')

  def titre(rec, table):
    q = Questions.lookupRecords(conversation=rec.id)
    if q:
      return u"Discussion — {}...".format(q[0].contenu[:60])
    return "Conversation #{}".format(rec.id)

  @grist.formulaType(grist.Reference('Users'))
  def cloturee_par(rec, table):
    return 0


@grist.UserTable
class Documents:
  titre = grist.Text()
  version = grist.Text()
  date_publication = grist.Date()
  statut_doc = grist.Choice()
  description = grist.Text()
  url_source = grist.Text()
  document = grist.Attachments()

  def nb_chapitres2(rec, table):
    return len(Chapitres.lookupRecords(document=rec.id))

  def score_maturite2(rec, table):
    lacs = Lacunes_Doc.lookupRecords(document=rec.id)
    if not lacs:
      return 100
    poids = {'critique':10, 'haute':5, 'normale':2, 'basse':1}
    ouvertes = [l for l in lacs if l.statut_lacune not in ('resolue','integree_doc','rejetee')]
    total = sum(poids.get(l.priorite, 1) for l in ouvertes)
    return max(0, 100 - total)

  def taux_couverture2(rec, table):
    questions = Questions.lookupRecords()
    pertinentes = [q for q in questions if q.couverture_doc and q.couverture_doc != 'hors_perimetre']
    if not pertinentes:
      return None
    couvertes = sum(1 for q in pertinentes if q.couverture_doc in ('couverte', 'partielle'))
    return round(100 * couvertes / len(pertinentes))


@grist.UserTable
class Enum_Themes:
  libelle = grist.Text()


@grist.UserTable
class Lacunes_Doc:
  titre = grist.Text()
  description = grist.Text()
  document = grist.Reference('Documents')
  chapitre_suggere = grist.Reference('Chapitres')
  statut_lacune = grist.Choice()
  priorite = grist.Choice()
  signale_par = grist.Reference('Users')
  date_signalement = grist.DateTime('Europe/Paris')
  question_origine = grist.Reference('Questions')

  @grist.formulaType(grist.Text())
  def numero_chapitre_propose(rec, table):
    return ''

  @grist.formulaType(grist.Int())
  def nb_occurrences(rec, table):
    return 0


@grist.UserTable
class Messages_Chat:
  conversation = grist.Reference('Conversations')
  auteur = grist.Reference('Users')
  contenu = grist.Text()

  def _default_horodatage(rec, table, value, user):
    return NOW()
  horodatage = grist.DateTime('Europe/Paris')

  @grist.formulaType(grist.Choice())
  def role(rec, table):
    if rec.auteur:
      return rec.auteur.role or 'utilisateur'
    return 'utilisateur'


@grist.UserTable
class Modeles_Reponse:

  @grist.formulaType(grist.Text())
  def nom(rec, table):
    return ''

  @grist.formulaType(grist.Text())
  def contenu_modele(rec, table):
    return ''

  @grist.formulaType(grist.Choice())
  def categorie(rec, table):
    return ''

  @grist.formulaType(grist.ChoiceList())
  def themes(rec, table):
    return None


@grist.UserTable
class Question_Theme_Link:
  question = grist.Reference('Questions')
  theme = grist.Reference('Enum_Themes')


@grist.UserTable
class Questions:
  contenu = grist.Text()
  auteur = grist.Reference('Users')

  def _default_date_creation(rec, table, value, user):
    return NOW()
  date_creation = grist.DateTime('Europe/Paris')
  statut = grist.Choice()
  qualifiee_par = grist.Reference('Users')
  date_qualification = grist.DateTime('Europe/Paris')
  est_doublon = grist.Bool()
  question_canonique = grist.Reference('Questions')
  couverture_doc = grist.Choice()
  recherche_doc_par = grist.Reference('Users')
  date_recherche_doc = grist.DateTime('Europe/Paris')
  reponse_validee = grist.Reference('Reponses')
  validee_par_utilisateur = grist.Bool()
  date_validation = grist.DateTime('Europe/Paris')
  satisfaction = grist.Choice()
  commentaire_validation = grist.Text()
  escaladee = grist.Bool()
  lacune = grist.Reference('Lacunes_Doc')
  conversation = grist.Reference('Conversations')
  validee_par = grist.Reference('Users')
  invalidee_par = grist.Reference('Users')

  @grist.formulaType(grist.Int())
  def nb_reponses(rec, table):
    return len(Reponses.lookupRecords(question=rec.id))

  @grist.formulaType(grist.Numeric())
  def temps_resolution(rec, table):
    if rec.date_validation and rec.date_creation:
      delta = rec.date_validation - rec.date_creation
      return round(delta.total_seconds() / 3600, 1)
    return None

  @grist.formulaType(grist.Text())
  def reference_formatee(rec, table):
    icons = {
      'nouvelle':u'\U0001F195', 'en_qualification':u'\U0001F4CB',
      'qualifiee':u'\u2705', 'doublon_detecte':u'\U0001F504',
      'recherche_doc_en_cours':u'\U0001F50D', 'reponse_proposee':u'\U0001F4AC',
      'en_escalade_expert':u'\U0001F6A8', 'reponse_expert_proposee':u'\U0001F468\u200D\U0001F52C',
      'en_attente_validation':u'\u23F3', 'validee':u'\u2705',
      'insatisfaction':u'\U0001F61E', 'close':u'\U0001F512'
    }
    icon = icons.get(rec.statut, '?')
    return "Q-{:04d} {} {}".format(rec.id, icon, rec.statut or '')

  def experts_recommandes(rec, table):
    if not rec.themes:
      return "Aucun theme defini"
    experts = Users.lookupRecords(actif=True, disponible=True)
    matches = []
    for e in experts:
      if e.est_expert and e.themes_expertise:
        q_themes = rec.themes if isinstance(rec.themes, list) else []
        e_themes = e.themes_expertise if isinstance(e.themes_expertise, list) else []
        common = set(q_themes) & set(e_themes)
        if common:
          matches.append("{} ({})".format(e.nom, ", ".join(common)))
    return ", ".join(matches) if matches else "Aucun expert disponible"

  def besoin_attention(rec, table):
    return rec.statut in ('nouvelle', 'qualifiee', 'insatisfaction')

  def score_votes(rec, table):
    votes = Votes.lookupRecords(type_cible='question', question=rec.id)
    return sum(v.valeur for v in votes)

  def nb_votes(rec, table):
    return len(Votes.lookupRecords(type_cible='question', question=rec.id))


@grist.UserTable
class Questions_similaires:
  question_nouvelle = grist.Reference('Questions')
  question_existante = grist.Reference('Questions')
  degre_similarite = grist.Choice()
  detectee_par = grist.Reference('Users')

  def _default_date_detection(rec, table, value, user):
    return NOW()
  date_detection = grist.DateTime('Europe/Paris')


@grist.UserTable
class Reponse_Chapitre_Link:
  reponse = grist.Reference('Reponses')
  chapitre = grist.Reference('Chapitres')
  pertinence = grist.Choice()

  @grist.formulaType(grist.Text())
  def extrait(rec, table):
    return ''


@grist.UserTable
class Reponses:
  question = grist.Reference('Questions')
  contenu = grist.Text()
  source_reponse = grist.Choice()
  auteur = grist.Reference('Users')

  def _default_date_creation(rec, table, value, user):
    return NOW()
  date_creation = grist.DateTime('Europe/Paris')
  statut_reponse = grist.Choice()
  chapitre_principal = grist.Reference('Chapitres')
  extrait_doc = grist.Text()
  est_reponse_finale = grist.Bool()
  note_qualite = grist.Int()

  def _default_notification_envoyee(rec, table, value, user):
    return False
  notification_envoyee = grist.Bool()

  @grist.formulaType(grist.Text())
  def commentaire_rejet(rec, table):
    return ''

  def sources_doc(rec, table):
    liens = Reponse_Chapitre_Link.lookupRecords(reponse=rec.id)
    if not liens:
      return "Aucune source documentaire"
    refs = []
    for l in liens:
      ch = Chapitres.lookupRecords(id=l.chapitre)
      if ch:
        refs.append(u"§{} {} [{}]".format(ch[0].numero, ch[0].titre, l.pertinence))
    return " | ".join(refs)

  def score_votes(rec, table):
    votes = Votes.lookupRecords(type_cible='reponse', reponse=rec.id)
    return sum(v.valeur for v in votes)

  def nb_votes(rec, table):
    return len(Votes.lookupRecords(type_cible='reponse', reponse=rec.id))


@grist.UserTable
class Retour_U:
  user = grist.Reference('Users')
  contenu = grist.Text()
  priorite = grist.Choice()

  def _default_date_et_heure(rec, table, value, user):
    return NOW()
  date_et_heure = grist.DateTime('Europe/Paris')
  type = grist.ChoiceList()
  done = grist.Bool()
  echanges = grist.Text()


@grist.UserTable
class Users:
  nom = grist.Text()
  email = grist.Text()
  role = grist.Choice()
  themes_expertise = grist.ChoiceList()
  service = grist.Choice()

  def _default_date_creation(rec, table, value, user):
    return NOW()
  date_creation = grist.DateTime('Europe/Paris')

  @grist.formulaType(grist.Bool())
  def est_admin(rec, table):
    return rec.role in ('admin', 'admin_expert')

  def display(rec, table):
    icones = {'utilisateur': u'\U0001F464', 'admin': u'\U0001F6E1'}
    icon = icones.get(rec.role, '')
    serv = rec.service if rec.service else ''
    return u"{} {} ({})".format(icon, rec.nom, serv)

  def nb_questions_posees(rec, table):
    return len(Questions.lookupRecords(auteur=rec.id))

  def nb_reponses_fournies(rec, table):
    return len(Reponses.lookupRecords(auteur=rec.id))

  def note_moyenne(rec, table):
    reps = Reponses.lookupRecords(auteur=rec.id)
    notes = [r.note_qualite for r in reps if r.note_qualite]
    return round(sum(notes) / len(notes), 1) if notes else None

  def charge_en_cours(rec, table):
    alertes = Alertes.lookupRecords(expert=rec.id)
    return sum(1 for a in alertes if a.statut_alerte in ('envoyee', 'vue'))


@grist.UserTable
class Votes:
  utilisateur = grist.Reference('Users')
  type_cible = grist.Choice()
  question = grist.Reference('Questions')
  reponse = grist.Reference('Reponses')
  valeur = grist.Int()

  def _default_date_vote(rec, table, value, user):
    return NOW()
  date_vote = grist.DateTime('Europe/Paris')


@grist.UserTable
class Widget_Session:

  def _default_email(rec, table, value, user):
    return user.Email
  email = grist.Text()