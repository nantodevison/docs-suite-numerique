// ══════════════════════════════════════════════════════
//  CONFIG BREVO
// ══════════════════════════════════════════════════════
var BREVO_API_KEY = BREVO_KEY ;
var BREVO_SENDER_EMAIL = EMAIL ;
var BREVO_SENDER_NAME = 'Plateforme Questions GT "Harmonisation CBS" -- DGPR';

// ══════════════════════════════════════════════════════
//  STATE
// ══════════════════════════════════════════════════════
var allQuestions = [];
var allReponses = [];
var usersMap = {};
var chapitres = [];
var allVotes = [];
var allThemes = [];
var questionThemeLinks = [];
var openCardId = null;
var currentUserId = null;

var COV_LABELS = {
  couverte:'🟢 Couvert', partielle:'🟡 Partiel',
  non_couverte:'🔴 Non couvert', hors_perimetre:'⚪ Hors périmètre',
  a_evaluer:'🔵 À évaluer'
};

// ══════════════════════════════════════════════════════
//  GRIST INIT
// ══════════════════════════════════════════════════════
grist.ready({ requiredAccess: 'full' });
loadAll();
setupImagePaste();

async function loadAll() {
  await loadRef();
  await loadThemes();
  await loadVotes();
  await loadReponses();
  await loadQuestions();
}

async function getCurrentUserEmail() {
  try {
    // 1. Crée un enregistrement → Grist y injecte automatiquement user.Email
    var res = await grist.docApi.applyUserActions([
      ['AddRecord', 'Widget_Session', null, {}]
    ]);
    var newId = res.retValues[0];

    // 2. Relit la table pour récupérer l'email injecté
    var t = await grist.docApi.fetchTable('Widget_Session');
    var idx = t.id.indexOf(newId);
    var email = idx >= 0 && t.email ? t.email[idx] : null;

    // 3. Supprime l'enregistrement — on ne laisse pas de trace
    await grist.docApi.applyUserActions([
      ['RemoveRecord', 'Widget_Session', newId]
    ]);

    return email ? email.toLowerCase() : null;

  } catch(e) {
    console.warn('getCurrentUserEmail:', e);
    return null;
  }
}

// ══════════════════════════════════════════════════════
//  LOAD REFERENCE DATA
// ══════════════════════════════════════════════════════
async function loadRef() {
  // 1. Charger Users
  try {
    var u = await grist.docApi.fetchTable('Users');
    for (var i = 0; i < u.id.length; i++) {
      usersMap[u.id[i]] = {
        id: u.id[i], nom: u.nom[i], role: u.role[i],
        email: u.email ? u.email[i] : null,
        display: u.display ? u.display[i] : u.nom[i]
      };
    }
  } catch(e) { console.warn('Users:', e); }

  // 2. ← ICI : remplace tout l'ancien bloc getUser() par ça
  try {
    var gristEmail = await getCurrentUserEmail();
    console.log('✅ Email détecté:', gristEmail);

    if (gristEmail) {
      var matched = Object.values(usersMap).find(function(u){
        return u.email && u.email.toLowerCase() === gristEmail;
      });
      if (matched) {
        currentUserId = matched.id;
        console.log('🎯 Identifié comme:', matched.nom);
      } else {
        console.warn('❌ Aucun match pour:', gristEmail);
        var admins = Object.values(usersMap).filter(function(u){ return u.role==='admin'; });
        if (admins.length) currentUserId = admins[0].id;
      }
    } else {
      var admins = Object.values(usersMap).filter(function(u){ return u.role==='admin'; });
      if (admins.length) currentUserId = admins[0].id;
    }
  } catch(e) {
    console.warn('Identification:', e);
    var admins = Object.values(usersMap).filter(function(u){ return u.role==='admin'; });
    if (admins.length) currentUserId = admins[0].id;
  }

  // 3. Charger les chapitres
  try {
    var c = await grist.docApi.fetchTable('Chapitres');
    chapitres = c.id.map(function(_, i){
      return {id:c.id[i], numero:c.numero[i], titre:c.titre[i],
              contenu:c.contenu[i], niveau:c.niveau[i]};
    });
    chapitres.sort(function(a,b){
      return (a.numero||'').localeCompare(b.numero||'',undefined,{numeric:true});
    });
  } catch(e) { console.warn('Chapitres:', e); }
}

// ══════════════════════════════════════════════════════
//  LOAD THEMES
// ══════════════════════════════════════════════════════
async function loadThemes() {
  try {
    var t = await grist.docApi.fetchTable('Enum_Themes');
    allThemes = [];
    for (var i = 0; i < t.id.length; i++) {
      allThemes.push({ id: t.id[i], libelle: t.libelle[i] });
    }
    allThemes.sort(function(a,b){ return a.libelle.localeCompare(b.libelle); });
    
    // Peuple le filtre thème
    var fTheme = document.getElementById('filterTheme');
    if (fTheme) {
      fTheme.innerHTML = '<option value="">— Tous —</option>' +
        allThemes.map(function(t){
          return '<option value="'+t.id+'">'+esc(t.libelle)+'</option>';
        }).join('');
    }
  } catch(e) { console.warn('Themes:', e); }

  try {
    var l = await grist.docApi.fetchTable('Question_Theme_Link');
    questionThemeLinks = [];
    for (var i = 0; i < l.id.length; i++) {
      questionThemeLinks.push({ id: l.id[i], question: l.question[i], theme: l.theme[i] });
    }
  } catch(e) { console.warn('Links:', e); }
}

function getThemesForQuestion(qId) {
  return questionThemeLinks
    .filter(function(l){ return l.question === qId; })
    .map(function(l){
      var t = allThemes.find(function(x){ return x.id === l.theme; });
      return t ? t.libelle : '?';
    });
}

// ══════════════════════════════════════════════════════
//  LOAD VOTES
// ══════════════════════════════════════════════════════
async function loadVotes() {
  try {
    var v = await grist.docApi.fetchTable('Votes');
    allVotes = [];
    for (var i = 0; i < v.id.length; i++) {
      allVotes.push({
        id: v.id[i], utilisateur: v.utilisateur[i],
        type_cible: v.type_cible[i], question: v.question[i],
        reponse: v.reponse[i], valeur: v.valeur[i]
      });
    }
  } catch(e) { console.warn('Votes:', e); }
}

// ══════════════════════════════════════════════════════
//  LOAD REPONSES (pour le filtre texte)
// ═════════════════════════════════════════════════════
async function loadReponses() {
  try {
    var r = await grist.docApi.fetchTable('Reponses');
    allReponses = [];
    for (var i = 0; i < r.id.length; i++) {
      allReponses.push({
        id: r.id[i],
        question: r.question[i],
        contenu: r.contenu[i]
      });
    }
  } catch(e) { console.warn('Reponses (filtre):', e); }
}

// ══════════════════════════════════════════════════════
//  VOTE HELPERS
// ══════════════════════════════════════════════════════
function getVoteScore(typeCible, targetId) {
  return allVotes
    .filter(function(v){ return v.type_cible===typeCible && v[typeCible]===targetId; })
    .reduce(function(sum,v){ return sum+v.valeur; }, 0);
}
function getMyVote(typeCible, targetId) {
  return allVotes.find(function(v){
    return v.type_cible===typeCible && v[typeCible]===targetId && v.utilisateur===currentUserId;
  }) || null;
}
function renderVoteBox(typeCible, targetId) {
  var score = getVoteScore(typeCible, targetId);
  var myVote = getMyVote(typeCible, targetId);
  var myVal = myVote ? myVote.valeur : 0;
  var scoreClass = score>0?'positive':(score<0?'negative':'neutral');
  var upClass = myVal===1?' voted-up':'';
  var downClass = myVal===-1?' voted-down':'';
  return '<span class="vote-box">' +
    '<span class="vote-btn'+upClass+'" onclick="event.stopPropagation();doVote(\''+typeCible+'\','+targetId+',1)">👍</span>' +
    '<span class="vote-score '+scoreClass+'">'+score+'</span>' +
    '<span class="vote-btn'+downClass+'" onclick="event.stopPropagation();doVote(\''+typeCible+'\','+targetId+',-1)">👎</span>' +
  '</span>';
}
async function doVote(typeCible, targetId, valeur) {
  var existing = getMyVote(typeCible, targetId);
  if (existing) {
    if (existing.valeur===valeur) {
      await grist.docApi.applyUserActions([['RemoveRecord','Votes',existing.id]]);
      toast('🗑️ Vote retiré');
    } else {
      await grist.docApi.applyUserActions([['UpdateRecord','Votes',existing.id,{
        valeur:valeur, date_vote:Date.now()/1000
      }]]);
      toast(valeur===1?'👍 Vote modifié':'👎 Vote modifié');
    }
  } else {
    var record = {utilisateur:currentUserId,type_cible:typeCible,
                  valeur:valeur,date_vote:Date.now()/1000};
    record[typeCible] = targetId;
    await grist.docApi.applyUserActions([['AddRecord','Votes',null,record]]);
    toast(valeur===1?'👍 Voté !':'👎 Voté !');
  }
  await loadVotes();
  renderQList();
  if (openCardId) loadMsgs(openCardId);
}

// ══════════════════════════════════════════════════════
//  LOAD QUESTIONS
// ══════════════════════════════════════════════════════
async function loadQuestions() {
  try {
    var qt = await grist.docApi.fetchTable('Questions');
    allQuestions = [];
    for (var i = 0; i < qt.id.length; i++) {
      allQuestions.push({
        id: qt.id[i], contenu: qt.contenu[i], auteur: qt.auteur[i],
        date_creation: qt.date_creation[i],
        statut: qt.statut[i], couverture_doc: qt.couverture_doc[i],
        est_doublon: qt.est_doublon[i], conversation: qt.conversation[i],
        validee_par_utilisateur: qt.validee_par_utilisateur[i],
        reponse_validee: qt.reponse_validee ? qt.reponse_validee[i] : null,
        doublon_de: qt.doublon_de ? qt.doublon_de[i] : null,
      });
    }
    allQuestions.sort(function(a,b){ return (b.date_creation||0)-(a.date_creation||0); });
    populateAuthorFilter();
    renderQList();
  } catch(e) {
    document.getElementById('qList').innerHTML =
      '<div class="empty"><div class="icon">❌</div>'+esc(e.message)+'</div>';
  }
}

// ══════════════════════════════════════════════════════
//  POPULATE AUTHOR FILTER
// ══════════════════════════════════════════════════════
function populateAuthorFilter() {
  var select = document.getElementById('filterAuteur');
  if (!select) return;
  var authorIds = new Set();
  allQuestions.forEach(function(q){ if (q.auteur) authorIds.add(q.auteur); });
  var options = '<option value="all">👥 Tous</option>';
  options += '<option value="mes_questions">👤 Mes questions</option>';
  options += '<option disabled>──────────</option>';
  authorIds.forEach(function(id){
    var user = usersMap[id];
    if (user) options += '<option value="'+id+'">'+esc(user.display||user.nom)+'</option>';
  });
  select.innerHTML = options;
}

// ══════════════════════════════════════════════════════
//  FILTER
// ══════════════════════════════════════════════════════
function getFiltered() {
  var fSearch = document.getElementById('filterSearch').value.trim().toLowerCase();
  var fThemeId = +document.getElementById('filterTheme').value || null;
  var fStatut = document.getElementById('filterStatut').value;
  var fAuteur = document.getElementById('filterAuteur').value;
  
  var filtered = allQuestions;
  
  // Filtre recherche texte
  if (fSearch) {
    filtered = filtered.filter(function(q){
      // Cherche dans le contenu de la question
      if ((q.contenu||'').toLowerCase().includes(fSearch)) return true;
      // Cherche dans le contenu des réponses liées
      return allReponses.some(function(r){
        return r.question === q.id && (r.contenu||'').toLowerCase().includes(fSearch);
      });
    });
  }
  
  // Filtre thème
  if (fThemeId) {
    filtered = filtered.filter(function(q){
      var links = questionThemeLinks.filter(function(l){
        return l.question === q.id && l.theme === fThemeId;
      });
      return links.length > 0;
    });
  }
  
  // Filtre statut
  if (fStatut==='nouvelle') {
    filtered = filtered.filter(function(q){ return q.statut==='nouvelle'; });
  } else if (fStatut==='en_cours') {
    filtered = filtered.filter(function(q){
      return ['qualifiee','en_escalade_expert'].indexOf(q.statut)>=0;
    });
  } else if (fStatut==='validee') {
    filtered = filtered.filter(function(q){ return q.statut==='validee'; });
  } else if (fStatut==='close') {
    filtered = filtered.filter(function(q){ return q.statut==='close'; });
  }
  
  // Filtre auteur
  if (fAuteur==='mes_questions') {
    filtered = filtered.filter(function(q){ return q.auteur===currentUserId; });
  } else if (fAuteur!=='all') {
    var authorId = parseInt(fAuteur);
    filtered = filtered.filter(function(q){ return q.auteur===authorId; });
  }
  
  return filtered;
}

// ══════════════════════════════════════════════════════
//  RENDER QUESTION LIST
// ══════════════════════════════════════════════════════
function renderQList() {
  var filtered = getFiltered();
  document.getElementById('qCount').textContent = filtered.length+' / '+allQuestions.length;

  if (!filtered.length) {
    document.getElementById('qList').innerHTML =
      '<div class="empty"><div class="icon">✅</div>Aucune question</div>';
    return;
  }

  document.getElementById('qList').innerHTML = filtered.map(function(q) {
    var st = q.statut||'nouvelle';
    var cov = q.couverture_doc||'a_evaluer';
    var isOpen = openCardId===q.id;
    var au = usersMap[q.auteur];
    var themes = getThemesForQuestion(q.id);
    var isClosed = st==='close';
    var isValidated = st==='validee';

    var themeDatalistHtml = '<datalist id="qThemeDL_'+q.id+'">'+
      allThemes.map(function(t){ return '<option value="'+esc(t.libelle)+'">'; }).join('')+
      '</datalist>';

    // Options couverture
    var covOptions = Object.keys(COV_LABELS).map(function(k){
      return '<option value="'+k+'"'+(cov===k?' selected':'')+'>'+COV_LABELS[k]+'</option>';
    }).join('');

    // Options sollicitation
    var sollicOptions = '<option value="">— Choisir un utilisateur —</option>' +
      Object.values(usersMap).map(function(u){
        return '<option value="'+u.id+'">'+esc(u.display||u.nom)+'</option>';
      }).join('');

    // Options doublon (toujours calculées, utilisées dans le form btn-row)
    var dupOptions = '<option value="">— Question source —</option>' +
      allQuestions.filter(function(x){ return x.id !== q.id; }).map(function(x){
        return '<option value="'+x.id+'">Q-'+String(x.id).padStart(4,'0')+' – '+esc((x.contenu||'').substring(0,50))+'</option>';
      }).join('');

    // Badge doublon (info-panel COL 1 : lecture seule)
    var doublonBadge = (q.est_doublon && q.doublon_de)
      ? '<div style="margin-top:6px"><span style="background:#fef3c7;color:#92400e;padding:2px 6px;border-radius:6px;font-size:11px;font-weight:600">🔁 Doublon de Q-'+String(q.doublon_de).padStart(4,'0')+'</span></div>'
      : '';

    return '<div class="qcard'+(isOpen?' open selected':'')+'" data-id="'+q.id+'">' +

      // HEAD
      '<div class="qcard-head" onclick="toggleCard('+q.id+')">' +
        '<div style="display:flex;flex-direction:column;align-items:center;gap:3px;flex-shrink:0;min-width:80px">' +
          '<span class="qcard-ref">Q-'+String(q.id).padStart(4,'0')+'</span>' +
          renderVoteBox('question', q.id) +
          '<span class="badge s-'+st+'">'+esc(st)+'</span>' +
        '</div>' +
        '<span class="qcard-txt" id="qtxt_'+q.id+'">'+renderMarkdownInline(q.contenu||'')+'</span>' +
        '<button class="btn-expand-txt" id="btnexp_'+q.id+'" ' +
          'onclick="event.stopPropagation();toggleTxt('+q.id+')" ' +
          'title="Voir plus">▼</button>' +
      '</div>' +

      // BODY
      '<div class="qcard-body">' +

        // INFO PANEL : 4 colonnes
      '<div class="info-panel">' +

        // COL 1 : Auteur + Date + Doublon
        '<div class="info-col">' +
          '<div class="info-col-title">ℹ️ Infos</div>' +
          '<dl class="info-grid">' +
            '<dt>Auteur</dt><dd>'+esc(au?(au.display||au.nom):'?')+'</dd>' +
            '<dt>Date</dt><dd>'+(q.date_creation?new Date(q.date_creation*1000).toLocaleDateString('fr-FR'):'—')+'</dd>' +
          '</dl>' +
          doublonBadge +
        '</div>' +

        // COL 2 : Thèmes
        '<div class="info-col">' +
          '<div class="info-col-title">🏷️ Thèmes</div>' +
          '<div style="display:flex;gap:4px;margin-top:6px">' +
            '<input type="text" id="qThemeInput_'+q.id+'" list="qThemeDL_'+q.id+'" placeholder="Ajouter…" ' +
              'style="flex:1;padding:3px 6px;border:1px solid var(--border);border-radius:6px;font-size:10px" ' +
              'onkeydown="if(event.key===\'Enter\'){event.preventDefault();addQTheme('+q.id+')}">' +
            themeDatalistHtml +
            '<button onclick="addQTheme('+q.id+')" ' +
              'style="padding:3px 8px;border:1px solid var(--accent);background:white;color:var(--accent);' +
              'border-radius:6px;font-size:10px;cursor:pointer;font-weight:600;flex-shrink:0">+</button>' +
          '</div>' +
          '<div class="theme-tags" id="qThemeTags_'+q.id+'">' +
            themes.map(function(t){
              return '<span class="theme-tag">'+esc(t)+
                '<span class="remove" onclick="event.stopPropagation();removeQTheme('+q.id+',\''+esc(t).replace(/'/g,"\\'")+'\')">×</span></span>';
            }).join('') +
          '</div>' +
        '</div>' +

        // COL 3 : Couverture doc
        '<div class="info-col">' +
          '<div class="info-col-title">📄 Couverture doc</div>' +
          '<select class="cov-select" id="selCov_'+q.id+'" onchange="saveCov('+q.id+')">' +
            Object.keys(COV_LABELS).map(function(k){
              return '<option value="'+k+'"'+(cov===k?' selected':'')+'>'+COV_LABELS[k]+'</option>';
            }).join('') +
          '</select>' +
        '</div>' +

        // COL 4 : Sollicitation
        '<div class="info-col">' +
          '<div class="info-col-title">✉️ Solliciter un utilisateur</div>' +
          '<div style="display:flex;gap:6px;align-items:center;flex-wrap:nowrap">' +
            '<select class="sollic-select" id="selSollic_'+q.id+'" style="flex:0 0 180px">'+sollicOptions+'</select>' +
            '<textarea class="sollic-textarea" id="txtSollic_'+q.id+'" maxlength="500" ' +
              'placeholder="Message optionnel (500 car. max)…" ' +
              'style="flex:1;height:32px;min-height:32px;resize:none;padding:5px 8px"></textarea>' +
            '<button class="btn-sollic" id="btnSollic_'+q.id+'" onclick="sendSollicitation('+q.id+')" style="height:32px;align-self:auto">✉️ Envoyer</button>' +
          '</div>' +
        '</div>' +

      '</div>' +

        // MESSAGES
        '<div class="msg-zone" id="msgs_'+q.id+'"><div class="msg-empty">Chargement…</div></div>' +

        // INPUT / BANNERS
        (isClosed ?
          '<div class="closed-banner">🔒 Question clôturée</div>' :
        isValidated ?
          '<div class="validated-banner">✅ Réponse validée par l\'auteur</div>' :
        '<div class="inp-zone" id="inp_'+q.id+'">' +
          '<div class="inp-selectors">' +
            '<div class="inp-selector"><label>Qui</label>' +
              '<select id="selUser_'+q.id+'">'+userOptions()+'</select></div>' +
            '<div class="inp-selector"><label>Source</label>' +
              '<select id="selSrc_'+q.id+'">' +
                '<option value="doc_reference">📖 Doc référence</option>' +
                '<option value="admin">🛡️ Admin</option>' +
                '<option value="autre_question">🔄 Autre question</option>' +
                '<option value="autre">💡 Autre</option>' +
              '</select></div>' +
            '<div class="inp-selector"><label>Chapitre</label>' +
              '<select id="selCh_'+q.id+'"><option value="">— Aucun —</option>'+chapOptions()+'</select></div>' +
          '</div>' +
          '<div class="inp-msg">' +
            '<div class="md-toolbar" style="background:#f1f3f5;border:1px solid var(--border);border-bottom:none;border-radius:8px 8px 0 0;padding:4px 6px;display:flex;gap:2px;flex-wrap:wrap">' +
              '<button type="button" class="md-btn" onclick="mdWrapTA(\'txtMsg_'+q.id+'\',\'**\',\'**\')" title="Gras"><strong>B</strong></button>' +
              '<button type="button" class="md-btn" onclick="mdWrapTA(\'txtMsg_'+q.id+'\',\'*\',\'*\')" title="Italique"><em>I</em></button>' +
              '<button type="button" class="md-btn" onclick="mdWrapTA(\'txtMsg_'+q.id+'\',\'`\',\'`\')" title="Code">⌥</button>' +
              '<button type="button" class="md-btn" onclick="mdWrapTA(\'txtMsg_'+q.id+'\',\'```\\n\',\'\\n```\')" title="Bloc code">{ }</button>' +
              '<span style="width:1px;height:16px;background:var(--border);margin:0 2px;align-self:center"></span>' +
              '<button type="button" class="md-btn" onclick="mdLineTA(\'txtMsg_'+q.id+'\',\'## \')" title="Titre">H</button>' +
              '<button type="button" class="md-btn" onclick="mdLineTA(\'txtMsg_'+q.id+'\',\'- \')" title="Liste">≡</button>' +
              '<button type="button" class="md-btn" onclick="mdLineTA(\'txtMsg_'+q.id+'\',\'1. \')" title="Liste numérotée">1.</button>' +
              '<span style="width:1px;height:16px;background:var(--border);margin:0 2px;align-self:center"></span>' +
              '<button type="button" class="md-btn" onclick="mdWrapTA(\'txtMsg_'+q.id+'\',\'[\',\'](url)\')" title="Lien">🔗</button>' +
              '<button type="button" class="md-btn" onclick="mdLineTA(\'txtMsg_'+q.id+'\',\'> \')" title="Citation">❝</button>' +
            '</div>' +
            '<textarea id="txtMsg_'+q.id+'" rows="4" placeholder="Votre message / réponse…" ' +
              'style="border-radius:0 0 12px 12px;border-top:none" ' +
              'onkeydown="if(event.key===\'Enter\'&&!event.shiftKey){event.preventDefault();sendResp('+q.id+')}"></textarea>' +
          '</div>' +
          '<div class="btn-row">' +
            '<button class="btn btn-send" onclick="sendResp('+q.id+')">💬 Envoyer</button>' +
            '<button class="btn btn-close" onclick="closeQuestion('+q.id+')">🔒 Clôturer</button>' +
            (q.est_doublon && q.doublon_de
              ? '<button class="btn btn-doublon-off" onclick="unmarkDuplicate('+q.id+')">✖ Retirer doublon</button>'
              : '<button class="btn btn-doublon" id="btnDuplon_'+q.id+'" onclick="showDuplicateForm('+q.id+')">🔁 Doublon</button>') +
            '<button class="btn btn-notify" id="btnNotify_'+q.id+'" onclick="notifyAuthor('+q.id+')" style="display:none">✉️ Notifier auteur</button>' +
          '</div>' +
          '<div id="dupForm_'+q.id+'" style="display:none;padding:6px 0 2px">' +
            '<div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap">' +
              '<select id="dupSel_'+q.id+'" style="flex:1;min-width:150px;max-width:320px;padding:4px 8px;border:1px solid var(--border);border-radius:6px;font-size:12px">'+dupOptions+'</select>' +
              '<button onclick="event.stopPropagation();saveDuplicate('+q.id+')" style="padding:4px 12px;background:#f59e0b;color:white;border:none;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;flex-shrink:0">✔ Valider</button>' +
              '<button onclick="event.stopPropagation();hideDuplicateForm('+q.id+')" style="padding:4px 10px;background:var(--grey);color:white;border:none;border-radius:6px;font-size:12px;cursor:pointer;flex-shrink:0">✖</button>' +
            '</div>' +
          '</div>' +
        '</div>'
        ) +

      '</div>' +
    '</div>';
  }).join('');
}

function userOptions() {
  return Object.values(usersMap).map(function(u){
    var sel = u.id===currentUserId?' selected':'';
    return '<option value="'+u.id+'"'+sel+'>'+esc(u.display||u.nom)+'</option>';
  }).join('');
}
function chapOptions() {
  return chapitres.map(function(c){
    return '<option value="'+c.id+'">§'+c.numero+' '+esc(c.titre)+'</option>';
  }).join('');
}

// ══════════════════════════════════════════════════════
//  SAVE COUVERTURE DOC
// ══════════════════════════════════════════════════════
async function saveCov(qId) {
  var val = document.getElementById('selCov_'+qId).value;
  await grist.docApi.applyUserActions([['UpdateRecord','Questions',qId,{
    couverture_doc: val
  }]]);
  // Met à jour localement
  var q = allQuestions.find(function(x){ return x.id===qId; });
  if (q) q.couverture_doc = val;
  toast('💾 Couverture enregistrée');
}

// ══════════════════════════════════════════════════════
//  SEND SOLLICITATION (email via Brevo)
// ══════════════════════════════════════════════════════
async function sendSollicitation(qId) {
  var btn = document.getElementById('btnSollic_'+qId);
  var targetId = +document.getElementById('selSollic_'+qId).value;
  var msg = document.getElementById('txtSollic_'+qId).value.trim();

  if (!targetId) { alert('Sélectionnez un utilisateur à solliciter'); return; }

  var target = usersMap[targetId];
  if (!target || !target.email) {
    alert('Cet utilisateur n\'a pas d\'adresse email renseignée');
    return;
  }

  var q = allQuestions.find(function(x){ return x.id===qId; });
  if (!q) return;

  if (btn) btn.disabled = true;

  try {
    var subject = '💬 Sollicitation sur la question Q-'+String(qId).padStart(4,'0');
    var htmlContent =
      '<p>Bonjour '+esc(target.nom)+',</p>' +
      '<p>Vous êtes sollicité(e) pour apporter votre expertise sur la question suivante :</p>' +
      '<blockquote style="border-left:3px solid #4361ee;padding-left:12px;color:#555;margin:12px 0">' +
        esc(q.contenu.substring(0,300))+(q.contenu.length>300?'…':'') +
      '</blockquote>' +
      (msg ?
        '<p><strong>Message :</strong></p>' +
        '<blockquote style="border-left:3px solid #2d6a4f;padding-left:12px;margin:12px 0">'+esc(msg)+'</blockquote>'
      : '') +
      '<p style="margin-top:20px;font-size:12px;color:#555">Connectez-vous à la plateforme pour répondre.</p>' +
      '<hr style="margin:20px 0;border:none;border-top:1px solid #ddd">' +
      '<p style="font-size:11px;color:#999">Cet email est automatique, merci de ne pas y répondre.</p>';

    var resp = await fetch('https://api.brevo.com/v3/smtp/email', {
      method: 'POST',
      headers: {
        'accept': 'application/json',
        'api-key': BREVO_API_KEY,
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        sender: { name: BREVO_SENDER_NAME, email: BREVO_SENDER_EMAIL },
        to: [{ email: target.email, name: target.nom }],
        subject: subject,
        htmlContent: htmlContent
      })
    });

    if (!resp.ok) {
      var err = await resp.json();
      throw new Error('Brevo: '+(err.message||resp.statusText));
    }

    toast('✉️ Sollicitation envoyée à '+target.nom);
    document.getElementById('txtSollic_'+qId).value = '';
    document.getElementById('selSollic_'+qId).value = '';

  } catch(e) {
    alert('❌ Erreur d\'envoi : '+e.message);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ══════════════════════════════════════════════════════
//  THEME ADD / REMOVE
// ══════════════════════════════════════════════════════
async function addQTheme(qId) {
  var input = document.getElementById('qThemeInput_'+qId);
  if (!input) return;
  var val = input.value.trim();
  if (!val) return;

  var existing = allThemes.find(function(t){
    return t.libelle.toLowerCase()===val.toLowerCase();
  });
  var themeId;
  if (existing) {
    themeId = existing.id;
  } else {
    var tRes = await grist.docApi.applyUserActions([
      ['AddRecord','Enum_Themes',null,{libelle:val}]
    ]);
    themeId = tRes.retValues[0];
    allThemes.push({id:themeId,libelle:val});
  }

  var alreadyLinked = questionThemeLinks.find(function(l){
    return l.question===qId && l.theme===themeId;
  });
  if (alreadyLinked) { input.value=''; toast('⚠️ Thème déjà associé'); return; }

  await grist.docApi.applyUserActions([
    ['AddRecord','Question_Theme_Link',null,{question:qId,theme:themeId}]
  ]);
  input.value='';
  toast('🏷️ Thème ajouté');
  await loadThemes();
  var savedOpen = openCardId;
  await loadQuestions();
  openCardId = savedOpen;
  renderQList();
  if (openCardId) loadMsgs(openCardId);
}

async function removeQTheme(qId, libelle) {
  var theme = allThemes.find(function(t){
    return t.libelle.toLowerCase()===libelle.toLowerCase();
  });
  if (!theme) return;
  var link = questionThemeLinks.find(function(l){
    return l.question===qId && l.theme===theme.id;
  });
  if (!link) return;

  await grist.docApi.applyUserActions([['RemoveRecord','Question_Theme_Link',link.id]]);
  toast('🗑️ Thème retiré');
  await loadThemes();
  var savedOpen = openCardId;
  await loadQuestions();
  openCardId = savedOpen;
  renderQList();
  if (openCardId) loadMsgs(openCardId);
}

// ══════════════════════════════════════════════════════
//  TOGGLE CARD
// ══════════════════════════════════════════════════════
function toggleCard(id) {
  if (openCardId===id) { openCardId=null; renderQList(); return; }
  openCardId = id;
  renderQList();
  loadMsgs(id);
}

// ══════════════════════════════════════════════════════
//  LOAD MESSAGES
// ══════════════════════════════════════════════════════
async function loadMsgs(qId) {
  var el = document.getElementById('msgs_'+qId);
  if (!el) return;
  try {
    var r = await grist.docApi.fetchTable('Reponses');
    var msgs = [];
    var hasNotifiable = false;
    var q = allQuestions.find(function(x){ return x.id===qId; });
    var validatedRespId = q ? q.reponse_validee : null;

    for (var i = 0; i < r.id.length; i++) {
      if (r.question[i]===qId) {
        var notifEnvoyee = r.notification_envoyee ? r.notification_envoyee[i] : false;
        msgs.push({
          id: r.id[i], auteur: r.auteur[i], contenu: r.contenu[i],
          source: r.source_reponse[i], chapitre: r.chapitre_principal[i],
          statut: r.statut_reponse[i], date: r.date_creation[i],
          finale: r.est_reponse_finale[i], notification_envoyee: notifEnvoyee,
          is_validated: r.id[i]===validatedRespId
        });
        if (r.statut_reponse[i]==='validee' && !notifEnvoyee) hasNotifiable = true;
      }
    }
    msgs.sort(function(a,b){ return (a.date||0)-(b.date||0); });
    renderMsgs(qId, msgs, q);
    var btnNotify = document.getElementById('btnNotify_'+qId);
    if (btnNotify) btnNotify.style.display = hasNotifiable?'inline-block':'none';
  } catch(e) {
    el.innerHTML = '<div class="msg-empty">Erreur: '+esc(e.message)+'</div>';
  }
}

function renderMsgs(qId, msgs, question) {
  var el = document.getElementById('msgs_'+qId);
  if (!msgs.length) {
    el.innerHTML = '<div class="msg-empty">💬 Aucune réponse — démarrez la discussion !</div>';
    return;
  }
  var isClosed = question && question.statut==='close';
  var isValidated = question && question.statut==='validee';
  var isAuthor = question && question.auteur===currentUserId;
  var canValidate = !isClosed && !isValidated;

  el.innerHTML = msgs.map(function(m) {
    var u = usersMap[m.auteur];
    var nm = u?(u.display||u.nom):'User#'+m.auteur;
    var role = u?u.role:'user';
    var ic = role==='admin'
      ? '<span style="display:inline-block;padding:1px 5px;background:#dbeafe;color:#1e40af;border-radius:3px;font-size:10px;font-weight:700;line-height:16px;vertical-align:middle">ADM</span>'
      : '';
    var side = m.auteur===currentUserId?'right':'left';
    var tm = m.date?new Date(m.date*1000).toLocaleString('fr-FR'):'';

    var chapHtml='';
    if (m.chapitre) {
      var ch = chapitres.find(function(c){ return c.id===m.chapitre; });
      if (ch) chapHtml='<div class="msg-chapter">📖 <a>§'+ch.numero+' '+esc(ch.titre)+'</a></div>';
    }

    // Statut affiché
    var statusHtml='';
    if (m.statut==='validee') {
      statusHtml=' <span class="msg-status" style="background:#d1fae5;color:#065f46">✅ validée</span>';
    } else if (m.statut==='rejetee') {
      statusHtml=' <span class="msg-status" style="background:#fee2e2;color:#991b1b">❌ rejetée</span>';
    }

    // Boutons valider / retirer
    var validateHtml='';
    if (m.is_validated) {
      validateHtml='<span class="msg-validated">✅ Réponse retenue</span>';
      if (!isClosed) {
        validateHtml+=' <button onclick="invalidateResponse('+qId+','+m.id+')" '+
          'style="font-size:9px;padding:2px 8px;border:1px solid var(--red);'+
          'background:white;color:var(--red);border-radius:6px;cursor:pointer;'+
          'font-weight:600;margin-left:8px" '+
          'onmouseover="this.style.background=\'var(--red)\';this.style.color=\'white\'" '+
          'onmouseout="this.style.background=\'white\';this.style.color=\'var(--red)\'">✖ Retirer</button>';
      }
    } else if (m.statut==='envoyee' && canValidate) {
      validateHtml='<div class="msg-validate">'+
        '<button onclick="validateResponse('+qId+','+m.id+')">✅ C\'est la bonne réponse</button>'+
        '</div>';
    }

    var voteHtml='<div style="padding:2px 8px">'+renderVoteBox('reponse',m.id)+'</div>';

    // Bouton édition — uniquement pour l'auteur, si question non clôturée/validée
    var canEdit = m.auteur === currentUserId && !isClosed && !m.is_validated;
    var editBtn = canEdit
      ? '<button class="btn-edit-msg" onclick="startEditMsg('+m.id+','+qId+')" title="Modifier">✏️</button>'
      : '';

    return '<div class="msg '+side+'" id="msgrow_'+m.id+'">' +
      '<span class="msg-head">'+(ic ? ic+' ' : '')+esc(nm)+' - '+tm+statusHtml+' '+editBtn+'</span>' +
      '<div style="display:flex;align-items:flex-start;gap:6px">' +
        '<div class="msg-bubble" id="msgbubble_'+m.id+'">'+renderMarkdown(m.contenu||'')+'</div>' +
        '<div style="display:flex;flex-direction:column;gap:4px;flex-shrink:0;padding-top:4px">' +
          chapHtml +
          voteHtml +
          validateHtml +
        '</div>' +
      '</div>' +
    '</div>';
  }).join('');
  el.scrollTop = el.scrollHeight;
}

// ══════════════════════════════════════════════════════
//  EDIT MESSAGE
// ══════════════════════════════════════════════════════
function startEditMsg(msgId, qId) {
  var bubble = document.getElementById('msgbubble_'+msgId);
  if (!bubble) return;

  // Retrouve le contenu brut (markdown) depuis allReponses
  var rep = allReponses.find(function(r){ return r.id === msgId; });
  var rawContent = rep ? (rep.contenu || '') : '';

  // Remplace la bulle par une zone d'édition
  bubble.outerHTML =
    '<div class="msg-edit-zone" id="msgedit_'+msgId+'">' +
      '<textarea id="msgeditTA_'+msgId+'">'+esc(rawContent)+'</textarea>' +
      '<div class="msg-edit-actions">' +
        '<button class="btn-edit-save" onclick="saveEditMsg('+msgId+','+qId+')">💾 Enregistrer</button>' +
        '<button class="btn-edit-cancel" onclick="cancelEditMsg('+msgId+','+qId+')">✖ Annuler</button>' +
      '</div>' +
    '</div>';

  // Focus + curseur en fin de texte
  var ta = document.getElementById('msgeditTA_'+msgId);
  if (ta) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); }
}

async function saveEditMsg(msgId, qId) {
  var ta = document.getElementById('msgeditTA_'+msgId);
  if (!ta) return;
  var newContent = ta.value.trim();
  if (!newContent) { alert('Le message ne peut pas être vide'); return; }

  try {
    await grist.docApi.applyUserActions([['UpdateRecord', 'Reponses', msgId, {
      contenu: newContent
    }]]);

    // Mise à jour locale dans allReponses
    var rep = allReponses.find(function(r){ return r.id === msgId; });
    if (rep) rep.contenu = newContent;

    toast('✏️ Message modifié');
    await loadMsgs(qId);
  } catch(e) {
    alert('❌ Erreur : ' + e.message);
  }
}

function cancelEditMsg(msgId, qId) {
  // Recharge simplement les messages pour restaurer l'affichage
  loadMsgs(qId);
}

// ══════════════════════════════════════════════════════
//  SEND RESPONSE
// ══════════════════════════════════════════════════════
async function sendResp(qId) {
  var txt = document.getElementById('txtMsg_'+qId).value.trim();
  if (!txt) { alert('Rédigez un message'); return; }
  var uid = +document.getElementById('selUser_'+qId).value;
  var src = document.getElementById('selSrc_'+qId).value;
  var chapId = +document.getElementById('selCh_'+qId).value||0;

  var res = await grist.docApi.applyUserActions([['AddRecord','Reponses',null,{
    question:qId, contenu:txt, auteur:uid||0, source_reponse:src,
    chapitre_principal:chapId, date_creation:Date.now()/1000,
    statut_reponse:'envoyee', est_reponse_finale:false,
    notification_envoyee:false
  }]]);

  var newId = res.retValues[0];
  if (chapId && newId) {
    await grist.docApi.applyUserActions([['AddRecord','Reponse_Chapitre_Link',null,{
      reponse:newId, chapitre:chapId, pertinence:'directe'
    }]]);
  }

  var q = allQuestions.find(function(x){ return x.id===qId; });

  // ── MISE À JOUR STATUT QUESTION ──
  var q = allQuestions.find(function(x){ return x.id===qId; });
  if (q && q.statut === 'nouvelle') {
    await grist.docApi.applyUserActions([['UpdateRecord','Questions',qId,{
      statut: 'qualifiee'
    }]]);
    q.statut = 'qualifiee'; // mise à jour locale
  }

  if (q && !q.conversation) {
    var convRes = await grist.docApi.applyUserActions([['AddRecord','Conversations',null,{
      question:qId, statut:'ouverte', date_ouverture:Date.now()/1000, ouverte_par:uid||0
    }]]);
    await grist.docApi.applyUserActions([['UpdateRecord','Questions',qId,{
      conversation:convRes.retValues[0]
    }]]);
  }

  document.getElementById('txtMsg_'+qId).value='';
  toast('💬 Envoyé');
  await loadMsgs(qId);
  await loadReponses();

  // ── ENVOI MAIL ──
  await notifyOnNewResponse(qId, uid, txt);
}

async function notifyOnNewResponse(qId, responderId, responseText) {
  var q = allQuestions.find(function(x){ return x.id===qId; });
  if (!q) return;

  var responder = usersMap[responderId];
  var responderName = responder ? responder.nom : 'Un utilisateur';
  var questionRef = 'Q-'+String(qId).padStart(4,'0');

  // Collecte les destinataires : auteur de la question + tous les répondants précédents (dédoublonnés)
  var recipientIds = new Set();
  if (q.auteur) recipientIds.add(q.auteur);

  try {
    var r = await grist.docApi.fetchTable('Reponses');
    for (var i = 0; i < r.id.length; i++) {
      if (r.question[i]===qId && r.auteur[i]) {
        recipientIds.add(r.auteur[i]);
      }
    }
  } catch(e) { console.warn('Fetch reponses for mail:', e); }

  // Exclure l'auteur de la réponse courante (il sait ce qu'il a écrit)
  recipientIds.delete(responderId);

  if (!recipientIds.size) return;

  // Filtre ceux qui ont un email
  var recipients = [];
  recipientIds.forEach(function(id) {
    var u = usersMap[id];
    if (u && u.email) recipients.push({ email: u.email, name: u.nom });
  });

  if (!recipients.length) return;

  var subject = '[GT Harmonisation CBS] Une réponse à votre question '+questionRef;

  var htmlContent =
    '<p>Bonjour,</p>' +
    '<p>Une réponse a été apportée par <strong>'+esc(responderName)+'</strong> à la question ' +
      '<em>'+esc((q.contenu||'').substring(0,300))+(q.contenu&&q.contenu.length>300?'…':'')+'</em> :</p>' +
    '<blockquote style="border-left:3px solid #4361ee;padding:8px 12px;margin:12px 0;color:#1e293b;background:#f8f9fa;border-radius:4px">' +
      esc(responseText) +
    '</blockquote>' +
    '<p>Merci d\'effectuer l\'une des actions suivantes sur ' +
      '<a href="https://grist.numerique.gouv.fr/o/docs/hS3dtdZqcve2/DGPR/p/14" style="color:#4361ee;font-weight:600">la plateforme</a> :</p>' +
    '<ul style="padding-left:20px;margin:8px 0">' +
      '<li>valider la réponse</li>' +
      '<li>répondre à nouveau car la réponse n\'est pas satisfaisante</li>' +
    '</ul>' +
    '<p style="margin-top:20px">Très Cordialement<br>' +
      '<strong>L\'équipe du GT Harmonisation</strong></p>' +
    '<hr style="margin:20px 0;border:none;border-top:1px solid #ddd">' +
    '<p style="font-size:11px;color:#999">Cet email est automatique, merci de ne pas y répondre.</p>';

  // Envoi un mail par destinataire (Brevo ne supporte pas le même "to" pour des gens différents avec personnalisation)
  for (var j = 0; j < recipients.length; j++) {
    try {
      var resp = await fetch('https://api.brevo.com/v3/smtp/email', {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'api-key': BREVO_API_KEY,
          'content-type': 'application/json'
        },
        body: JSON.stringify({
          sender: { name: BREVO_SENDER_NAME, email: BREVO_SENDER_EMAIL },
          to: [{ email: recipients[j].email, name: recipients[j].name }],
          subject: subject,
          htmlContent: htmlContent
        })
      });
      if (!resp.ok) {
        var err = await resp.json();
        console.warn('Brevo error for '+recipients[j].email+':', err.message||resp.statusText);
      }
    } catch(e) {
      console.warn('Mail error for '+recipients[j].email+':', e);
    }
  }

  toast('✉️ Notification envoyée à '+recipients.length+' personne'+(recipients.length>1?'s':''));
}

// ══════════════════════════════════════════════════════
//  VALIDATE / INVALIDATE RESPONSE
// ══════════════════════════════════════════════════════
async function validateResponse(qId, respId) {
  if (!confirm('Valider cette réponse comme la bonne ?')) return;
  await grist.docApi.applyUserActions([['UpdateRecord','Reponses',respId,{
    est_reponse_finale:true, statut_reponse:'validee'
  }]]);
  await grist.docApi.applyUserActions([['UpdateRecord','Questions',qId,{
    statut:'validee', validee_par_utilisateur:true,
    reponse_validee:respId, date_validation:Date.now()/1000,
    validee_par:currentUserId
  }]]);
  var q = allQuestions.find(function(x){ return x.id===qId; });
  if (q && q.conversation) {
    await grist.docApi.applyUserActions([['UpdateRecord','Conversations',q.conversation,{
      statut:'close', date_cloture:Date.now()/1000
    }]]);
  }
  toast('✅ Réponse validée !');
  var savedOpen = openCardId;
  await loadQuestions();
  openCardId = savedOpen;
  renderQList();
  if (openCardId) loadMsgs(openCardId);
}

async function invalidateResponse(qId, respId) {
  if (!confirm('Retirer la validation ?')) return;
  await grist.docApi.applyUserActions([['UpdateRecord','Reponses',respId,{
    est_reponse_finale:false, statut_reponse:'envoyee'
  }]]);
  await grist.docApi.applyUserActions([['UpdateRecord','Questions',qId,{
    statut:'qualifiee', validee_par_utilisateur:false,
    reponse_validee:0, date_validation:0,
    validee_par:0, invalidee_par:currentUserId
  }]]);
  var q = allQuestions.find(function(x){ return x.id===qId; });
  if (q && q.conversation) {
    await grist.docApi.applyUserActions([['UpdateRecord','Conversations',q.conversation,{statut:'ouverte'}]]);
  }
  toast('🔄 Validation retirée');
  var savedOpen = openCardId;
  await loadQuestions();
  openCardId = savedOpen;
  renderQList();
  if (openCardId) loadMsgs(openCardId);
}

// ══════════════════════════════════════════════════════
//  CLOSE QUESTION
// ══════════════════════════════════════════════════════
async function closeQuestion(qId) {
  if (!confirm('Clôturer cette question ?')) return;
  await grist.docApi.applyUserActions([['UpdateRecord','Questions',qId,{statut:'close'}]]);
  var q = allQuestions.find(function(x){ return x.id===qId; });
  if (q && q.conversation) {
    await grist.docApi.applyUserActions([['UpdateRecord','Conversations',q.conversation,{
      statut:'close', date_cloture:Date.now()/1000
    }]]);
  }
  toast('🔒 Clôturée');
  var savedOpen = openCardId;
  await loadQuestions();
  openCardId = savedOpen;
  renderQList();
  if (openCardId) loadMsgs(openCardId);
}

// ══════════════════════════════════════════════════════
//  NOTIFY AUTHOR (réponse proposée)
// ══════════════════════════════════════════════════════
async function notifyAuthor(qId) {
  var btn = document.getElementById('btnNotify_'+qId);
  if (btn) btn.disabled = true;
  try {
    var q = allQuestions.find(function(x){ return x.id===qId; });
    if (!q) throw new Error('Question introuvable');
    var author = usersMap[q.auteur];
    if (!author||!author.email) throw new Error('Email de l\'auteur introuvable');

    var r = await grist.docApi.fetchTable('Reponses');
    var responseToNotify = null;
    for (var i = 0; i < r.id.length; i++) {
      if (r.question[i]===qId && r.statut_reponse[i]==='proposee' &&
          (!r.notification_envoyee||!r.notification_envoyee[i])) {
        responseToNotify = {id:r.id[i],contenu:r.contenu[i],auteur:r.auteur[i]};
        break;
      }
    }
    if (!responseToNotify) throw new Error('Aucune réponse à notifier');

    var responder = usersMap[responseToNotify.auteur];
    var responderName = responder?responder.nom:'Un expert';
    var subject = '✅ Réponse à votre question Q-'+String(qId).padStart(4,'0');
    var htmlContent =
      '<p>Bonjour '+esc(author.nom)+',</p>' +
      '<p>Une réponse a été proposée pour votre question :</p>' +
      '<blockquote style="border-left:3px solid #4361ee;padding-left:12px;color:#555">'+
        esc(q.contenu.substring(0,200))+(q.contenu.length>200?'...':'')+
      '</blockquote>' +
      '<p><strong>Réponse de '+esc(responderName)+' :</strong></p>' +
      '<blockquote style="border-left:3px solid #2d6a4f;padding-left:12px">'+
        esc(responseToNotify.contenu)+
      '</blockquote>' +
      '<p style="font-size:12px;color:#555;margin-top:20px">Connectez-vous pour valider ou poursuivre.</p>' +
      '<hr style="margin:20px 0;border:none;border-top:1px solid #ddd">' +
      '<p style="font-size:11px;color:#999">Email automatique, merci de ne pas répondre.</p>';

    var resp = await fetch('https://api.brevo.com/v3/smtp/email', {
      method:'POST',
      headers:{'accept':'application/json','api-key':BREVO_API_KEY,'content-type':'application/json'},
      body: JSON.stringify({
        sender:{name:BREVO_SENDER_NAME,email:BREVO_SENDER_EMAIL},
        to:[{email:author.email,name:author.nom}],
        subject:subject, htmlContent:htmlContent
      })
    });
    if (!resp.ok) { var err=await resp.json(); throw new Error('Brevo: '+(err.message||resp.statusText)); }

    await grist.docApi.applyUserActions([['UpdateRecord','Reponses',responseToNotify.id,{
      notification_envoyee: true
    }]]);

    toast('✉️ Notification envoyée à '+author.nom);
    await loadMsgs(qId);

  } catch(e) {
    alert('❌ Erreur d\'envoi : '+e.message);
    console.error('Notification error:', e);
  } finally {
    if (btn) btn.disabled = false;
  }
}

// ══════════════════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════════════════
function decodeCL(v) {
  if (!v) return [];
  if (Array.isArray(v)) return v[0]==='L' ? v.slice(1) : v;
  if (typeof v==='string') return v.split(',').map(function(s){return s.trim()}).filter(Boolean);
  return [];
}

function esc(t) {
  var d = document.createElement('div');
  d.textContent = t||'';
  return d.innerHTML;
}

function toast(m) {
  var n = document.createElement('div');
  n.className='toast'; n.textContent=m;
  document.body.appendChild(n);
  setTimeout(function(){n.remove()},2500);
}

function renderMarkdown(txt) {
  if (!txt) return '';
  var h = txt
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="msg-img">')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
    .replace(/\n{2,}/g, '</p><p>')
    .replace(/\n/g, '<br>');
  return '<p>' + h + '</p>';
}

function renderMarkdownInline(txt) {
  if (!txt) return '';
  return txt
    .replace(/\*\*\*(.+?)\*\*\*/g, '<strong><em>$1</em></strong>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

function mdWrapTA(taId, prefix, suffix) {
  var ta = document.getElementById(taId);
  if (!ta) return;
  var start = ta.selectionStart, end = ta.selectionEnd;
  var sel = ta.value.substring(start, end);
  var replacement = prefix + (sel || 'texte') + suffix;
  ta.value = ta.value.substring(0, start) + replacement + ta.value.substring(end);
  ta.focus();
  ta.selectionStart = start + prefix.length;
  ta.selectionEnd = start + prefix.length + (sel || 'texte').length;
}

function mdLineTA(taId, prefix) {
  var ta = document.getElementById(taId);
  if (!ta) return;
  var start = ta.selectionStart;
  var lineStart = ta.value.lastIndexOf('\n', start - 1) + 1;
  ta.value = ta.value.substring(0, lineStart) + prefix + ta.value.substring(lineStart);
  ta.focus();
  ta.selectionStart = ta.selectionEnd = start + prefix.length;
}

function toggleTxt(qId) {
  var txt = document.getElementById('qtxt_'+qId);
  var btn = document.getElementById('btnexp_'+qId);
  if (!txt) return;
  txt.classList.toggle('expanded');
  btn.classList.toggle('expanded');
}

// ══════════════════════════════════════════════════════
//  DUPLICATE MANAGEMENT
// ══════════════════════════════════════════════════════
function showDuplicateForm(qId) {
  var form = document.getElementById('dupForm_'+qId);
  if (form) form.style.display = 'block';
}

function hideDuplicateForm(qId) {
  var form = document.getElementById('dupForm_'+qId);
  if (form) form.style.display = 'none';
}

async function saveDuplicate(qId) {
  var sel = document.getElementById('dupSel_'+qId);
  if (!sel) return;
  var sourceId = +sel.value;
  if (!sourceId) { alert('Sélectionnez la question source'); return; }

  await grist.docApi.applyUserActions([['UpdateRecord','Questions',qId,{
    est_doublon: true,
    doublon_de: sourceId
  }]]);
  toast('🔁 Question marquée comme doublon de Q-'+String(sourceId).padStart(4,'0'));
  var savedOpen = openCardId;
  await loadQuestions();
  openCardId = savedOpen;
  renderQList();
  if (openCardId) loadMsgs(openCardId);
}

async function unmarkDuplicate(qId) {
  if (!confirm('Retirer le statut doublon de cette question ?')) return;
  await grist.docApi.applyUserActions([['UpdateRecord','Questions',qId,{
    est_doublon: false,
    doublon_de: 0
  }]]);
  toast('✅ Statut doublon retiré');
  var savedOpen = openCardId;
  await loadQuestions();
  openCardId = savedOpen;
  renderQList();
  if (openCardId) loadMsgs(openCardId);
}

// ══════════════════════════════════════════════════════
//  IMAGE PASTE
// ══════════════════════════════════════════════════════
function setupImagePaste() {
  document.addEventListener('paste', function(e) {
    var active = document.activeElement;
    if (!active || active.tagName !== 'TEXTAREA') return;
    var id = active.id;
    // Cibler les zones de saisie des réponses et d'édition
    if (!id.startsWith('txtMsg_') && !id.startsWith('msgeditTA_')) return;

    var items = e.clipboardData && e.clipboardData.items;
    if (!items) return;

    for (var i = 0; i < items.length; i++) {
      if (items[i].type.indexOf('image') !== -1) {
        e.preventDefault();
        var blob = items[i].getAsFile();
        if (!blob) return;

        var reader = new FileReader();
        reader.onload = (function(ta) {
          return function(ev) {
            var dataUrl = ev.target.result;
            var imgMd = '\n![image]('+dataUrl+')\n';
            var pos = ta.selectionStart;
            ta.value = ta.value.substring(0, pos) + imgMd + ta.value.substring(pos);
            ta.selectionStart = ta.selectionEnd = pos + imgMd.length;
            ta.dispatchEvent(new Event('input'));
            toast('🖼️ Image insérée');
          };
        })(active);
        reader.readAsDataURL(blob);
        return;
      }
    }
  });
}