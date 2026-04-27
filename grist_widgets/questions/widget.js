/* widget.js – Widget Questions / Réponses (Widget 3)
 *
 * Affiche les questions et leurs réponses associées.
 * Supporte le filtrage (toutes / sans réponse / avec réponse) et la recherche.
 * La sélection d'une carte synchronise le curseur Grist.
 *
 * Table attendue : voir README.md
 */

(function () {
  "use strict";

  /* ── Éléments DOM ───────────────────────────────────────────────── */
  const listEl   = document.getElementById("list");
  const searchEl = document.getElementById("search-bar");
  const emptyEl  = document.getElementById("empty");
  const errorEl  = document.getElementById("error");
  const tabsEl   = document.getElementById("tabs");

  /* ── État local ─────────────────────────────────────────────────── */
  let allRecords   = [];
  let selectedId   = null;
  let activeFilter = "tous"; // "tous" | "sans-reponse" | "avec-reponse"

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
    const ts = typeof val === "number" ? val * 1000 : Date.parse(val);
    if (isNaN(ts)) return String(val);
    return new Date(ts).toLocaleDateString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  }

  function hasReponse(record) {
    return Boolean(record.reponse && String(record.reponse).trim().length > 0);
  }

  /* ── Rendu de la liste ──────────────────────────────────────────── */
  function render(records) {
    listEl.innerHTML = "";

    const query = (searchEl.value || "").toLowerCase().trim();

    let filtered = records;

    // Filtre onglet
    if (activeFilter === "sans-reponse") {
      filtered = filtered.filter((r) => !hasReponse(r));
    } else if (activeFilter === "avec-reponse") {
      filtered = filtered.filter((r) => hasReponse(r));
    }

    // Filtre texte
    if (query) {
      filtered = filtered.filter(
        (r) =>
          (r.question || "").toLowerCase().includes(query) ||
          (r.reponse  || "").toLowerCase().includes(query) ||
          (r.auteur   || "").toLowerCase().includes(query)
      );
    }

    if (filtered.length === 0) {
      emptyEl.style.display = "block";
      return;
    }
    emptyEl.style.display = "none";

    filtered.forEach((record) => {
      const rowId    = record.id;
      const question = record.question || "(question vide)";
      const reponse  = record.reponse  || "";
      const auteur   = record.auteur   || "";
      const dateQ    = formatDate(record.date_question);
      const dateR    = formatDate(record.date_reponse);
      const avecRep  = hasReponse(record);

      const card = document.createElement("div");
      card.className = `qa-card${avecRep ? "" : " sans-reponse"}${rowId === selectedId ? " active" : ""}`;
      card.dataset.rowId = rowId;

      card.innerHTML = `
        <div class="qa-question">
          <div class="qa-question-header">
            <span class="qa-label">Question</span>
            ${dateQ ? `<span class="qa-date">${escapeHtml(dateQ)}</span>` : ""}
          </div>
          ${auteur ? `<div class="qa-auteur">${escapeHtml(auteur)}</div>` : ""}
          <div class="qa-text">${escapeHtml(question)}</div>
          ${!avecRep ? '<span class="badge-sans-reponse">⏳ Sans réponse</span>' : ""}
        </div>
        <div class="qa-reponse">
          <div class="qa-question-header">
            <span class="qa-label reponse">Réponse</span>
            ${dateR ? `<span class="qa-date">${escapeHtml(dateR)}</span>` : ""}
          </div>
          <div class="qa-text">${escapeHtml(reponse)}</div>
        </div>
      `;

      card.addEventListener("click", () => selectRecord(rowId));
      listEl.appendChild(card);
    });
  }

  /* ── Sélection d'un enregistrement ─────────────────────────────── */
  function selectRecord(rowId) {
    selectedId = rowId;
    document.querySelectorAll(".qa-card").forEach((el) => {
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
      { name: "question",      title: "Question",             type: "Text" },
      { name: "reponse",       title: "Réponse",              type: "Text",    optional: true },
      { name: "auteur",        title: "Auteur de la question",type: "Text",    optional: true },
      { name: "date_question", title: "Date de la question",  type: "Date",    optional: true },
      { name: "date_reponse",  title: "Date de la réponse",   type: "Date",    optional: true },
      { name: "chapitre_ref",  title: "Chapitre lié",         type: "Integer", optional: true },
    ],
  });

  // Réception des données
  grist.onRecords(function (records) {
    hideError();
    // Tri : sans réponse en premier, puis par date de question décroissante
    allRecords = (records || []).slice().sort((a, b) => {
      const aRep = hasReponse(a) ? 1 : 0;
      const bRep = hasReponse(b) ? 1 : 0;
      if (aRep !== bRep) return aRep - bRep;
      const dA = Number(a.date_question) || 0;
      const dB = Number(b.date_question) || 0;
      return dB - dA;
    });
    render(allRecords);
  });

  // Synchronisation curseur Grist
  grist.onRecord(function (record) {
    if (!record) return;
    selectedId = record.id;
    document.querySelectorAll(".qa-card").forEach((el) => {
      el.classList.toggle("active", Number(el.dataset.rowId) === selectedId);
    });
  });

  /* ── Onglets ────────────────────────────────────────────────────── */
  tabsEl.addEventListener("click", (e) => {
    const tab = e.target.closest(".tab");
    if (!tab) return;
    tabsEl.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    activeFilter = tab.dataset.filter;
    render(allRecords);
  });

  /* ── Recherche en temps réel ────────────────────────────────────── */
  searchEl.addEventListener("input", () => render(allRecords));
}());
