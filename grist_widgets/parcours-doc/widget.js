// ══════════════════════════════════════════════════════
//  STATE
// ══════════════════════════════════════════════════════
var chapitres = [];
var selectedChId = null;

// ══════════════════════════════════════════════════════
//  GRIST INIT
// ══════════════════════════════════════════════════════
grist.ready({ requiredAccess: 'full' });
loadChapitres();

// ══════════════════════════════════════════════════════
//  LOAD CHAPITRES
// ══════════════════════════════════════════════════════
async function loadChapitres() {
  try {
    var c = await grist.docApi.fetchTable('Chapitres');
    chapitres = c.id.map(function(_, i){
      return {
        id: c.id[i],
        numero: c.numero[i],
        titre: c.titre[i],
        contenu: c.contenu[i],
        niveau: c.niveau[i],
        document: c.document[i],
        url: c.url[i]
      };
    });
    
    // Sort by numero (natural sort for "1.2.3" style)
    chapitres.sort(function(a, b){
      return (a.numero||'').localeCompare(b.numero||'', undefined, {numeric: true});
    });
    
    renderCh(chapitres);
  } catch(e) {
    document.getElementById('chList').innerHTML =
      '<div class="empty">❌ Erreur: '+esc(e.message)+'</div>';
  }
}

// ══════════════════════════════════════════════════════
//  RENDER CHAPITRES
// ══════════════════════════════════════════════════════
function renderCh(list) {
  var el = document.getElementById('chList');
  
  if (!list.length) {
    el.innerHTML = '<div class="empty">✅ Aucun chapitre trouvé</div>';
    return;
  }
  
  el.innerHTML = list.map(function(c) {
    // Indent based on level (1=10px, 2=24px, 3=38px, etc.)
    var pad = 10 + Math.min((c.niveau||1)-1, 3) * 14;
    var isSelected = selectedChId === c.id ? ' selected' : '';
    
    var urlLink = c.url
      ? '<a href="'+c.url+'" target="_blank" rel="noopener noreferrer" '+
        'onclick="event.stopPropagation()" '+
        'style="font-size:10px;color:var(--accent);white-space:nowrap;flex-shrink:0">↗ source</a>'
      : '';
    return '<div class="ch-item'+isSelected+'" style="padding-left:'+pad+'px" '+
      'onclick="selectCh('+c.id+')" data-id="'+c.id+'">'+
      '<span class="ch-num">§'+(c.numero||'')+'</span>'+
      '<span class="ch-title">'+esc(c.titre||'Sans titre')+'</span>'+
      urlLink+'</div>';
  }).join('');
}

// ══════════════════════════════════════════════════════
//  FILTER CHAPITRES
// ══════════════════════════════════════════════════════
function filterCh(query) {
  var q = query.toLowerCase().trim();
  
  if (!q) {
    renderCh(chapitres);
    return;
  }
  
  var filtered = chapitres.filter(function(c){
    var searchable = (c.numero||'') + ' ' + (c.titre||'') + ' ' + (c.contenu||'');
    return searchable.toLowerCase().includes(q);
  });
  
  renderCh(filtered);
}

// ══════════════════════════════════════════════════════
//  SELECT CHAPITRE
// ══════════════════════════════════════════════════════
function selectCh(id) {
  selectedChId = id;
  var ch = chapitres.find(function(c){ return c.id === id; });
  if (!ch) return;

  // Marquer l'item sélectionné dans la liste
  document.querySelectorAll('.ch-item').forEach(function(el){
    el.classList.toggle('selected', +el.dataset.id === id);
  });

  // Remplir le header de la modale
  var sourceLink = ch.url
    ? ' <a href="'+ch.url+'" target="_blank" rel="noopener noreferrer" '+
      'style="font-size:11px;color:var(--accent);font-weight:400">(Lien vers la source)</a>'
    : '';
  document.getElementById('chModalTitle').innerHTML =
    '<span style="font-weight:700;color:var(--text2);font-size:12px">§'+esc(ch.numero||'')+'</span>'+
    ' <span style="font-weight:700;color:var(--text);font-size:14px">'+esc(ch.titre||'Sans titre')+'</span>'+
    sourceLink;

  // Remplir le corps en Markdown
  var preview = document.getElementById('chPrev');
  preview.innerHTML = marked.parse(ch.contenu || 'Aucun contenu disponible');
  preview.scrollTop = 0;

  // Ouvrir le backdrop + modale
  document.getElementById('ch-backdrop').style.display = 'block';
  document.getElementById('chModal').classList.add('visible');
}

function resetSelection() {
  selectedChId = null;

  // Fermer backdrop + modale
  document.getElementById('ch-backdrop').style.display = 'none';
  document.getElementById('chModal').classList.remove('visible');

  // Désélectionner les items
  document.querySelectorAll('.ch-item').forEach(function(el){
    el.classList.remove('selected');
  });
}

// ══════════════════════════════════════════════════════
//  HELPERS
// ══════════════════════════════════════════════════════
function esc(t) {
  var d = document.createElement('div');
  d.textContent = t||'';
  return d.innerHTML;
}