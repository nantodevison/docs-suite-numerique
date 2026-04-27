/* widget.js – Widget Parcours documentaire (Widget 1)
 *
 * Affiche l'arborescence des chapitres issus de la table Grist (Chapitres).
 * Lorsqu'un chapitre est sélectionné dans le widget, la ligne correspondante
 * est sélectionnée dans Grist (curseur), permettant aux autres widgets de
 * réagir via onRecord.
 *
 * Table attendue : voir README.md
 */

(function () {
  "use strict";

  /* ── Éléments DOM ───────────────────────────────────────────────── */
  const treeEl   = document.getElementById("tree");
  const searchEl = document.getElementById("search-bar");
  const emptyEl  = document.getElementById("empty");
  const errorEl  = document.getElementById("error");

  /* ── État local ─────────────────────────────────────────────────── */
  let allRecords   = [];   // tous les enregistrements Grist
  let selectedId   = null; // rowId actuellement sélectionné

  /* ── Affichage d'erreur ─────────────────────────────────────────── */
  function showError(msg) {
    errorEl.textContent = msg;
    errorEl.style.display = "block";
  }

  function hideError() {
    errorEl.style.display = "none";
  }

  /* ── Rendu de l'arbre ───────────────────────────────────────────── */
  function render(records) {
    treeEl.innerHTML = "";
    const query = (searchEl.value || "").toLowerCase().trim();

    const filtered = query
      ? records.filter(
          (r) =>
            (r.titre || "").toLowerCase().includes(query) ||
            (r.numero || "").toLowerCase().includes(query)
        )
      : records;

    if (filtered.length === 0) {
      emptyEl.style.display = "block";
      return;
    }
    emptyEl.style.display = "none";

    filtered.forEach((record) => {
      const niveau  = Math.min(Number(record.niveau) || 0, 3);
      const numero  = record.numero  || "";
      const titre   = record.titre_propre || record.titre || "(sans titre)";
      const rowId   = record.id;

      const div = document.createElement("div");
      div.className = `chapter level-${niveau}${rowId === selectedId ? " active" : ""}`;
      div.dataset.rowId = rowId;

      div.innerHTML = `<span class="numero">${escapeHtml(numero)}</span>`
                    + `<span class="titre">${escapeHtml(titre)}</span>`;

      div.addEventListener("click", () => selectRecord(rowId));
      treeEl.appendChild(div);
    });
  }

  /* ── Sélection d'un enregistrement ─────────────────────────────── */
  function selectRecord(rowId) {
    selectedId = rowId;
    // Met à jour la sélection visuelle
    document.querySelectorAll(".chapter").forEach((el) => {
      el.classList.toggle("active", Number(el.dataset.rowId) === rowId);
    });
    // Synchronise le curseur Grist
    grist.setCursorPos({ rowId }).catch(() => {});
  }

  /* ── Utilitaire ─────────────────────────────────────────────────── */
  function escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  /* ── Initialisation Grist ───────────────────────────────────────── */

  // IMPORTANT : appeler grist.ready() EN PREMIER, avant tout autre appel API.
  // Sans cela, Grist retourne l'erreur RPC_UNKNOWN_FORWARD_DEST.
  grist.ready({
    requiredAccess: "read table",
    columns: [
      { name: "titre",        title: "Titre complet",   type: "Text" },
      { name: "titre_propre", title: "Titre (sans emoji)", type: "Text", optional: true },
      { name: "numero",       title: "Numéro",          type: "Text", optional: true },
      { name: "niveau",       title: "Niveau",          type: "Numeric" },
      { name: "ordre",        title: "Ordre",           type: "Numeric", optional: true },
      { name: "url",          title: "URL",             type: "Text", optional: true },
    ],
  });

  // Réception de tous les enregistrements de la vue courante
  grist.onRecords(function (records) {
    hideError();
    // Trier par ordre puis par niveau pour l'affichage hiérarchique
    allRecords = (records || []).slice().sort((a, b) => {
      const ordA = Number(a.ordre) || 0;
      const ordB = Number(b.ordre) || 0;
      return ordA - ordB;
    });
    render(allRecords);
  });

  // Réaction au changement de curseur (autre widget ou Grist lui-même)
  grist.onRecord(function (record) {
    if (!record) return;
    selectedId = record.id;
    document.querySelectorAll(".chapter").forEach((el) => {
      el.classList.toggle("active", Number(el.dataset.rowId) === selectedId);
    });
  });

  /* ── Recherche en temps réel ────────────────────────────────────── */
  searchEl.addEventListener("input", () => render(allRecords));
}());
