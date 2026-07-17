BOUTIQUE_GRADES = [
    "Gestionnaire toutes boutiques",
    "Gestionnaire de boutique",
    "Responsable de boutique",
    "Technicien",
    "Vendeur",
]

DEPOT_GRADES = [
    "Chef de dépôt",
    "Magasinier",
]

ALL_GRADES = BOUTIQUE_GRADES + DEPOT_GRADES

DEFAULT_PERMISSIONS = {
    "reprise": {"create": False, "edit": False, "view": True, "delete": False},
    "devis": {"create": False, "edit": False, "view": True, "delete": False},
    "caisse": {"delete_ticket": False},
    "intervention": {"create": False, "edit": False, "view": True, "delete": False},
    "stock": {"add": False, "edit": False, "edit_quantity": False, "delete": False},
    "communication": True,
}

GRADE_PERMISSION_TEMPLATES = {
    "Gestionnaire toutes boutiques": {
        "reprise": {"create": True, "edit": True, "view": True, "delete": True},
        "devis": {"create": True, "edit": True, "view": True, "delete": True},
        "caisse": {"delete_ticket": True},
        "intervention": {"create": True, "edit": True, "view": True, "delete": True},
        "stock": {"add": True, "edit": True, "edit_quantity": True, "delete": True},
        "communication": True,
    },
    "Gestionnaire de boutique": {
        "reprise": {"create": True, "edit": True, "view": True, "delete": True},
        "devis": {"create": True, "edit": True, "view": True, "delete": True},
        "caisse": {"delete_ticket": True},
        "intervention": {"create": True, "edit": True, "view": True, "delete": True},
        "stock": {"add": True, "edit": True, "edit_quantity": True, "delete": True},
        "communication": True,
    },
    "Responsable de boutique": {
        "reprise": {"create": True, "edit": True, "view": True, "delete": False},
        "devis": {"create": True, "edit": True, "view": True, "delete": False},
        "caisse": {"delete_ticket": True},
        "intervention": {"create": True, "edit": True, "view": True, "delete": False},
        "stock": {"add": True, "edit": True, "edit_quantity": True, "delete": False},
        "communication": True,
    },
    "Technicien": {
        "reprise": {"create": True, "edit": True, "view": True, "delete": False},
        "devis": {"create": True, "edit": False, "view": True, "delete": False},
        "caisse": {"delete_ticket": False},
        "intervention": {"create": True, "edit": True, "view": True, "delete": False},
        "stock": {"add": False, "edit": False, "edit_quantity": True, "delete": False},
        "communication": True,
    },
    "Vendeur": {
        "reprise": {"create": True, "edit": False, "view": True, "delete": False},
        "devis": {"create": True, "edit": False, "view": True, "delete": False},
        "caisse": {"delete_ticket": False},
        "intervention": {"create": True, "edit": False, "view": True, "delete": False},
        "stock": {"add": False, "edit": False, "edit_quantity": False, "delete": False},
        "communication": True,
    },
    "Chef de dépôt": {
        "reprise": {"create": False, "edit": False, "view": False, "delete": False},
        "devis": {"create": True, "edit": True, "view": True, "delete": True},
        "caisse": {"delete_ticket": False},
        "intervention": {"create": True, "edit": True, "view": True, "delete": True},
        "stock": {"add": True, "edit": True, "edit_quantity": True, "delete": True},
        "communication": True,
    },
    "Magasinier": {
        "reprise": {"create": False, "edit": False, "view": False, "delete": False},
        "devis": {"create": False, "edit": False, "view": True, "delete": False},
        "caisse": {"delete_ticket": False},
        "intervention": {"create": True, "edit": False, "view": True, "delete": False},
        "stock": {"add": False, "edit": False, "edit_quantity": True, "delete": False},
        "communication": True,
    },
}
