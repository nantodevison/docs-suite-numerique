// ══════════════════════════════════════════════════════
//  BREVO
// ══════════════════════════════════════════════════════
var BREVO_API_KEY = BREVO_KEY ;
var BREVO_SENDER_EMAIL = EMAIL ;
var BREVO_SENDER_NAME = 'Plateforme Questions GT "Harmonisation CBS" -- DGPR';

// ══════════════════════════════════════════════════════
//  STATE
// ══════════════════════════════════════════════════════
var users = [];
var usersMap = {};
var allQuestions = [];
var allThemes = [];
var questionThemeLinks = [];
var selectedThemes = [];
var currentUserId = null;

grist.ready({ requiredAccess: 'full' });
init();
setupImagePaste();

// ══════════════════════════════════════════════════════
//  DÉTECTION AUTOMATIQUE DE L'UTILISATEUR
// ══════════════════════════════════════════════════════
async function getCurrentUserEmail() {
  try {
    var res = await grist.docApi.applyUserActions([
      ['AddRecord', 'Widget_Session', null, {}]
    ]);
    var newId = res.retValues[0];
    var t = await grist.docApi.fetchTable('Widget_Session');
    var idx = t.id.indexOf(newId);
    var email = idx >= 0 && t.email ? t.email[idx] : null;
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
//  INIT
// ══════════════════════════════════════════════════════
async function init() {
  try {
    var u = await grist.docApi.fetchTable('Users');
    var sel = document.getElementById('selUser');
    sel.innerHTML = '<option value="">— Votre nom —</option>';
    for (var i = 0; i < u.id.length; i++) {
      var displayName = (u.display && u.display[i]) ? u.display[i] : u.nom[i];
      users.push({ id: u.id[i], nom: u.nom[i], role: u.role[i], email: u.email ? u.email[i] : null, display: displayName });
      usersMap[u.id[i]] = { nom: u.nom[i], role: u.role[i], email: u.email ? u.email[i] : null, display: displayName };
      sel.innerHTML += '<option value="'+u.id[i]+'">'+esc(displayName)+'</option>';
    }
    var fAuteur = document.getElementById('fAuteur');
    users.forEach(function(u) {
      fAuteur.innerHTML += '<option value="'+u.id+'">'+esc(u.display||u.nom)+'</option>';
    });

    // Détection automatique de l'utilisateur connecté
    var gristEmail = await getCurrentUserEmail();
    if (gristEmail) {
      var matched = users.find(function(u){ return u.email && u.email.toLowerCase() === gristEmail; });
      if (matched) {
        currentUserId = matched.id;
        sel.value = String(matched.id);
        console.log('🎯 Utilisateur détecté :', matched.display || matched.nom);
      } else {
        console.warn('❌ Aucun utilisateur correspondant à :', gristEmail);
      }
    }
  } catch(e) { console.warn('Users:', e); }

  await loadThemes();
  await loadQuestions();
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
    refreshThemeDatalist();
    var fTheme = document.getElementById('fTheme');
    fTheme.innerHTML = '<option value="">— Tous —</option>';
    allThemes.forEach(function(t) {
      fTheme.innerHTML += '<option value="'+t.id+'">'+esc(t.libelle)+'</option>';
    });
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
    .filter(function(l) { return l.question === qId; })
    .map(function(l) {
      var t = allThemes.find(function(x) { return x.id === l.theme; });
      return t || null;
    })
    .filter(Boolean);
}

function refreshThemeDatalist() {
  var dl = document.getElementById('themeDatalist');
  dl.innerHTML = allThemes.map(function(t) {
    return '<option value="'+esc(t.libelle)+'">';
  }).join('');
}

// ══════════════════════════════════════════════════════
//  LOAD QUESTIONS
// ══════════════════════════════════════════════════════
async function loadQuestions() {
  try {
    var q = await grist.docApi.fetchTable('Questions');
    allQuestions = [];
    for (var i = 0; i < q.id.length; i++) {
      allQuestions.push({
        id: q.id[i],
        contenu: q.contenu[i],
        statut: q.statut[i],
        auteur: q.auteur[i],
        date: q.date_creation[i]
      });
    }
    allQuestions.sort(function(a,b){ return (b.date||0)-(a.date||0); });
    renderSearch();
  } catch(e) {
    document.getElementById('searchResults').innerHTML =
      '<div class="empty-search">❌ Erreur de chargement</div>';
  }
}

// ══════════════════════════════════════════════════════
//  SEARCH & FILTERS
// ══════════════════════════════════════════════════════
function getFiltered() {
  var txt = document.getElementById('searchInput').value.trim().toLowerCase();
  var fThemeId = +document.getElementById('fTheme').value || null;
  var fStatut = document.getElementById('fStatut').value;
  var fAuteurId = +document.getElementById('fAuteur').value || null;

  return allQuestions.filter(function(q) {
    if (txt && !(q.contenu||'').toLowerCase().includes(txt)) return false;
    if (fStatut==='nouvelle') {
      if (q.statut!=='nouvelle') return false;
    } else if (fStatut==='en_cours') {
      if (['qualifiee','en_escalade_expert'].indexOf(q.statut)<0) return false;
    } else if (fStatut==='validee') {
      if (q.statut!=='validee') return false;
    } else if (fStatut==='close') {
      if (q.statut!=='close') return false;
    }
    if (fAuteurId && q.auteur !== fAuteurId) return false;
    if (fThemeId) {
      var links = questionThemeLinks.filter(function(l) {
        return l.question === q.id && l.theme === fThemeId;
      });
      if (!links.length) return false;
    }
    return true;
  });
}

function renderSearch() {
  var filtered = getFiltered();
  var countEl = document.getElementById('searchCount');
  var resEl = document.getElementById('searchResults');

  countEl.textContent = filtered.length + ' question' + (filtered.length > 1 ? 's' : '') +
    ' sur ' + allQuestions.length;

  if (!filtered.length) {
    resEl.innerHTML = '<div class="empty-search">✅ Aucune question correspondante — la vôtre est peut-être nouvelle !</div>';
    return;
  }

  resEl.innerHTML = filtered.map(function(q) {
    var st = q.statut || 'nouvelle';
    var dt = q.date ? new Date(q.date*1000).toLocaleDateString('fr-FR') : '';
    var auteurNom = usersMap[q.auteur] ? esc(usersMap[q.auteur].display || usersMap[q.auteur].nom) : '';
    var themes = getThemesForQuestion(q.id);
    var themesHtml = themes.map(function(t) {
      return '<span class="ri-theme">'+esc(t.libelle)+'</span>';
    }).join('');

    return '<div class="ri">' +
      '<div class="ri-top">' +
        '<span class="ri-ref">Q-'+String(q.id).padStart(4,'0')+'</span>' +
        '<span class="st st-'+st+'">'+st+'</span>' +
        themesHtml +
      '</div>' +
      '<div class="ri-contenu">'+esc((q.contenu||'').substring(0,120))+(q.contenu&&q.contenu.length>120?'…':'')+'</div>' +
      '<div class="ri-bottom">' +
        (auteurNom ? '<span class="ri-date">👤 '+auteurNom+'</span>' : '') +
        '<span class="ri-date">📅 '+dt+'</span>' +
      '</div>' +
    '</div>';
  }).join('');
}

function clearFilters() {
  document.getElementById('searchInput').value = '';
  document.getElementById('fTheme').value = '';
  document.getElementById('fStatut').value = '';
  document.getElementById('fAuteur').value = '';
  renderSearch();
}

// ══════════════════════════════════════════════════════
//  THEME INPUT (pour la soumission)
// ══════════════════════════════════════════════════════
function addTheme() {
  var input = document.getElementById('themeInput');
  var val = input.value.trim();
  if (!val) return;
  if (selectedThemes.indexOf(val) >= 0) { input.value = ''; return; }
  selectedThemes.push(val);
  input.value = '';
  renderThemeTags();
}

function removeTheme(idx) {
  selectedThemes.splice(idx, 1);
  renderThemeTags();
}

function renderThemeTags() {
  document.getElementById('themeTags').innerHTML = selectedThemes.map(function(t, i) {
    return '<span class="theme-tag">'+esc(t)+
      '<span class="remove" onclick="removeTheme('+i+')">×</span></span>';
  }).join('');
}

document.getElementById('themeInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') { e.preventDefault(); addTheme(); }
});

// ══════════════════════════════════════════════════════
//  SUBMIT
// ══════════════════════════════════════════════════════
async function submitQ() {
  var uid = +document.getElementById('selUser').value;
  var txt = document.getElementById('inQ').value.trim();
  if (!uid) { alert('Sélectionnez votre nom'); return; }
  if (!txt) { alert('Rédigez votre question'); return; }

  document.getElementById('btnSub').disabled = true;

  try {
    var res = await grist.docApi.applyUserActions([
      ['AddRecord', 'Questions', null, {
        contenu: txt,
        auteur: uid,
        date_creation: Date.now() / 1000,
        statut: 'nouvelle',
        couverture_doc: 'a_evaluer',
        est_doublon: false,
        escaladee: false,
        validee_par_utilisateur: false
      }]
    ]);

    var newId = res.retValues[0];
    var ref = 'Q-' + String(newId).padStart(4, '0');

    for (var i = 0; i < selectedThemes.length; i++) {
      var libelle = selectedThemes[i];
      var existing = allThemes.find(function(t) {
        return t.libelle.toLowerCase() === libelle.toLowerCase();
      });
      var themeId;
      if (existing) {
        themeId = existing.id;
      } else {
        var tRes = await grist.docApi.applyUserActions([
          ['AddRecord', 'Enum_Themes', null, { libelle: libelle }]
        ]);
        themeId = tRes.retValues[0];
        allThemes.push({ id: themeId, libelle: libelle });
      }
      await grist.docApi.applyUserActions([
        ['AddRecord', 'Question_Theme_Link', null, { question: newId, theme: themeId }]
      ]);
    }

    selectedThemes = [];
    renderThemeTags();
    refreshThemeDatalist();
    document.getElementById('inQ').value = '';
    document.getElementById('modalRef').textContent = ref;
    document.getElementById('modal').style.display = 'flex';

    await loadThemes();
    await loadQuestions();

    await notifyAdminsNewQuestion(newId, ref, uid, txt);

  } catch(e) {
    alert('❌ Erreur: ' + e.message);
  }

  document.getElementById('btnSub').disabled = false;
}

// ══════════════════════════════════════════════════════
//  NOTIFY ADMINS
// ══════════════════════════════════════════════════════
async function notifyAdminsNewQuestion(qId, ref, authorId, contenu) {
  var author = usersMap[authorId];
  var authorName = author ? author.nom : 'Un utilisateur';
  var now = new Date().toLocaleString('fr-FR');

  var recipients = [];
  users.forEach(function(u) {
    if (u.role === 'admin' && u.id !== authorId && u.email) {
      recipients.push({ email: u.email, name: u.nom });
    }
  });

  if (!recipients.length) {
    console.warn('Aucun admin destinataire trouvé');
    return;
  }

  var subject = '[GT Harmonisation CBS] Nouvelle question ' + ref + ' posée';

  var htmlContent =
    '<p>Bonjour,</p>' +
    '<p>La question <strong>' + esc(ref) + '</strong> a été posée par <strong>' + esc(authorName) + '</strong> le ' + esc(now) + '.</p>' +
    '<p>La question est :</p>' +
    '<blockquote style="border-left:3px solid #4361ee;padding:8px 12px;margin:12px 0;color:#1e293b;background:#f8f9fa;border-radius:4px">' +
      esc(contenu) +
    '</blockquote>' +
    '<p style="margin-top:20px">Cordialement<br>' +
      '<strong>L\'équipe GT Harmonisation</strong></p>' +
    '<hr style="margin:20px 0;border:none;border-top:1px solid #ddd">' +
    '<p style="font-size:11px;color:#999">Cet email est automatique, merci de ne pas y répondre.</p>';

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
        console.warn('Brevo error:', err.message || resp.statusText);
      }
    } catch(e) {
      console.warn('Mail error:', e);
    }
  }
}

// ══════════════════════════════════════════════════════
//  HELPERS
// ═════════════════════════════════════════════════���════
function esc(t) {
  var d = document.createElement('div');
  d.textContent = t || '';
  return d.innerHTML;
}

// ══════════════════════════════════════════════════════
//  MARKDOWN TOOLBAR
// ══════════════════════════════════════════════════════
function mdWrap(prefix, suffix) {
  var ta = document.getElementById('inQ');
  var start = ta.selectionStart, end = ta.selectionEnd;
  var sel = ta.value.substring(start, end);
  var replacement = prefix + (sel || 'texte') + suffix;
  ta.value = ta.value.substring(0, start) + replacement + ta.value.substring(end);
  ta.focus();
  ta.selectionStart = start + prefix.length;
  ta.selectionEnd = start + prefix.length + (sel || 'texte').length;
}

function mdLine(prefix) {
  var ta = document.getElementById('inQ');
  var start = ta.selectionStart;
  var lineStart = ta.value.lastIndexOf('\n', start - 1) + 1;
  ta.value = ta.value.substring(0, lineStart) + prefix + ta.value.substring(lineStart);
  ta.focus();
  ta.selectionStart = ta.selectionEnd = start + prefix.length;
}

function togglePreview() {
  var ta = document.getElementById('inQ');
  var prev = document.getElementById('mdPreview');
  var btn = document.getElementById('btnPreview');
  if (prev.style.display === 'none') {
    prev.innerHTML = renderMarkdown(ta.value);
    prev.style.display = 'block';
    ta.style.display = 'none';
    btn.textContent = '✏️ Éditer';
  } else {
    prev.style.display = 'none';
    ta.style.display = 'block';
    btn.textContent = '👁 Aperçu';
  }
}

function renderMarkdown(txt) {
  if (!txt) return '<em style="color:#999">Rien à afficher…</em>';
  var h = txt
    .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width:100%;border-radius:6px;margin:6px 0;display:block;box-shadow:0 2px 8px rgba(0,0,0,.12)">')
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

// ══════════════════════════════════════════════════════
//  IMAGE PASTE
// ══════════════════════════════════════════════════════
function setupImagePaste() {
  document.addEventListener('paste', function(e) {
    var active = document.activeElement;
    if (!active || active.tagName !== 'TEXTAREA') return;
    if (active.id !== 'inQ') return;

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
            // Mettre à jour l'aperçu si actif
            var prev = document.getElementById('mdPreview');
            if (prev && prev.style.display !== 'none') {
              prev.innerHTML = renderMarkdown(ta.value);
            }
          };
        })(active);
        reader.readAsDataURL(blob);
        return;
      }
    }
  });
}