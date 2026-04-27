/* widget.js – Widget Échanges (Widget 2)
 *
 * Affiche la liste des échanges liés au chapitre sélectionné dans Grist.
 * Chaque échange est cliquable pour positionner le curseur Grist sur la ligne.
 *
 * Table attendue : voir README.md
 */

(function () {
  "use strict";

  /* ── Éléments DOM ───────────────────────────────────────────────── */
  const listEl    = document.getElementById("list");
  const searchEl  = document.getElementById("search-bar");
  const filterEl  = document.getElementById("filter-statut");
  const emptyEl   = document.getElementById("empty");
  const errorEl   = document.getElementById("error");

  /* ── État local ─────────────────────────────────────────────────── */
  let allRecords = [];
  let selectedId = null;

  /* ── Affichage d'erreur ─────────────────────────────────────────── */
  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.style.display = "block";
  }

  function hideError() {
    errorEl.style.display = "none";
  }

  /* ── Utilitaires ────────────────────────────────────────────────── */
  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatDate(val) {
    if (!val) return "";
    // Grist stocke les dates en secondes Unix pour les colonnes Date
    const ts = typeof val === "number" ? val * 1000 : Date.parse(val);
    if (isNaN(ts)) return String(val);
    return new Date(ts).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  function normalizeStatut(val) {
    return String(val || "")
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")  // retire les accents
      .trim();
  }

  function statutCssClass(statut) {
    const s = normalizeStatut(statut);
    if (s.includes("ferm") || s === "closed" || s === "resolu") return "statut-ferme";
    if (s.includes("attente") || s === "waiting" || s === "pending") return "statut-attente";
    return "statut-ouvert";
  }

  /* ── Rendu de la liste ──────────────────────────────────────────── */
  function render(records) {
    listEl.innerHTML = "";

    const query  = (searchEl.value || "").toLowerCase().trim();
    const filtre = (filterEl.value || "").toLowerCase().trim();

    let filtered = records;

    if (query) {
      filtered = filtered.filter(
        (r) =>
          (r.titre   || "").toLowerCase().includes(query) ||
          (r.contenu || "").toLowerCase().includes(query) ||
          (r.auteur  || "").toLowerCase().includes(query)
      );
    }

    if (filtre) {
      filtered = filtered.filter((r) =>
        normalizeStatut(r.statut).includes(filtre)
      );
    }

    if (filtered.length === 0) {
      emptyEl.style.display = "block";
      return;
    }
    emptyEl.style.display = "none";

    filtered.forEach((record) => {
      const rowId   = record.id;
      const titre   = record.titre   || "(sans titre)";
      const auteur  = record.auteur  || "";
      const date    = formatDate(record.date);
      const contenu = record.contenu || "";
      const statut  = record.statut  || "ouvert";

      const div = document.createElement("div");
      div.className = `echange${rowId === selectedId ? " active" : ""}`;
      div.dataset.rowId = rowId;

      div.innerHTML = `
        <div class="echange-header">
          <span class="echange-titre">${escapeHtml(titre)}</span>
          <span class="echange-date">${escapeHtml(date)}</span>
        </div>
        ${auteur ? `<div class="echange-auteur">${escapeHtml(auteur)}</div>` : ""}
        <div class="echange-contenu">${escapeHtml(contenu)}</div>
        <span class="tag ${statutCssClass(statut)}">${escapeHtml(statut)}</span>
      `;

      div.addEventListener("click", () => selectRecord(rowId));
      listEl.appendChild(div);
    });
  }

  /* ── Sélection d'un enregistrement ─────────────────────────────── */
  function selectRecord(rowId) {
    selectedId = rowId;
    document.querySelectorAll(".echange").forEach((el) => {
      el.classList.toggle("active", Number(el.dataset.rowId) === rowId);
    });
    grist.setCursorPos({ rowId }).catch(() => {});
  }

  /* ── Initialisation Grist ───────────────────────────────────────── */

  // IMPORTANT : appeler grist.ready() EN PREMIER, avant tout autre appel API.
  // Sans cela, Grist retourne l'erreur RPC_UNKNOWN_FORWARD_DEST.
  grist.ready({
    requiredAccess: "read table",
    columns: [
      { name: "titre",   title: "Titre de l'échange", type: "Text" },
      { name: "auteur",  title: "Auteur",             type: "Text",    optional: true },
      { name: "date",    title: "Date",               type: "Date",    optional: true },
      { name: "statut",  title: "Statut",             type: "Choice",  optional: true },
      { name: "contenu", title: "Contenu / message",  type: "Text",    optional: true },
      { name: "chapitre_ref", title: "Chapitre lié",  type: "Integer", optional: true },
    ],
  });

  // Mise à jour lors d'un changement de données dans la vue
  grist.onRecords(function (records) {
    hideError();
    // Tri par date décroissante (les plus récents en premier)
    allRecords = (records || []).slice().sort((a, b) => {
      const dA = Number(a.date) || 0;
      const dB = Number(b.date) || 0;
      return dB - dA;
    });
    render(allRecords);
  });

  // Synchronisation avec la sélection Grist
  grist.onRecord(function (record) {
    if (!record) return;
    selectedId = record.id;
    document.querySelectorAll(".echange").forEach((el) => {
      el.classList.toggle("active", Number(el.dataset.rowId) === selectedId);
    });
  });

  /* ── Filtres en temps réel ──────────────────────────────────────── */
  searchEl.addEventListener("input",  () => render(allRecords));
  filterEl.addEventListener("change", () => render(allRecords));
}());
