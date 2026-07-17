export const BOUTIQUE_GRADES = [
  "Gestionnaire toutes boutiques",
  "Gestionnaire de boutique",
  "Responsable de boutique",
  "Technicien",
  "Vendeur",
];

export const DEPOT_GRADES = ["Chef de dépôt", "Magasinier"];

export const ALL_GRADES = [...BOUTIQUE_GRADES, ...DEPOT_GRADES];

export const URGENCE_COLORS = {
  basse: "bg-emerald-500/15 text-emerald-600 border-emerald-500/30",
  moyenne: "bg-amber-500/15 text-amber-600 border-amber-500/30",
  haute: "bg-orange-500/15 text-orange-600 border-orange-500/30",
  critique: "bg-red-500/15 text-red-600 border-red-500/30",
};
