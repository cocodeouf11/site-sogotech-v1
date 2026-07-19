import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Package, ShoppingCart, Wrench, FileText, RefreshCcw,
  MessageSquare, Warehouse, Users, Store, LogOut, X, Truck,
} from "lucide-react";
import { useAuth, hasPerm } from "../../context/AuthContext";

const linkClass = ({ isActive }) =>
  `flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors duration-200 ${
    isActive ? "bg-primary text-primary-foreground" : "text-foreground/70 hover:bg-accent hover:text-foreground"
  }`;

export function Sidebar({ open, onClose }) {
  const { user, logout } = useAuth();
  if (!user) return null;

  const items = [
    { to: "/", label: "Tableau de bord", icon: LayoutDashboard, show: true },
    { to: "/stock", label: "Stock", icon: Package, show: true },
    { to: "/caisse", label: "Caisse", icon: ShoppingCart, show: true },
    { to: "/interventions", label: "Interventions", icon: Wrench, show: hasPerm(user, "intervention", "view") },
    { to: "/devis", label: "Devis", icon: FileText, show: hasPerm(user, "devis", "view") },
    { to: "/reprises", label: "Reprises", icon: RefreshCcw, show: hasPerm(user, "reprise", "view") },
    { to: "/commandes", label: "Commande", icon: Truck, show: true },
    { to: "/depot", label: "Dépôt", icon: Warehouse, show: hasPerm(user, "depot") },
    { to: "/communication", label: "Messagerie", icon: MessageSquare, show: hasPerm(user, "communication") },
    { to: "/admin/users", label: "Utilisateurs", icon: Users, show: user.is_admin },
    { to: "/admin/shops", label: "Boutiques", icon: Store, show: user.is_admin },
  ];

  return (
    <>
      {open && (
        <div
          onClick={onClose}
          data-testid="sidebar-overlay"
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
        />
      )}
      <aside
        data-testid="sidebar"
        className={`fixed lg:sticky top-0 left-0 z-50 w-72 lg:w-64 shrink-0 border-r border-border bg-card flex flex-col h-screen transition-transform duration-300 ${
          open ? "translate-x-0" : "-translate-x-full"
        } lg:translate-x-0`}
      >
        <div className="px-5 py-6 flex items-center justify-between">
          <div>
            <p className="font-heading text-xl font-bold tracking-tight">SOGO Gestion</p>
            <p className="text-xs text-muted-foreground mt-0.5">Boutique &amp; Dépôt</p>
          </div>
          <button onClick={onClose} data-testid="sidebar-close-button" className="lg:hidden p-1.5 rounded-md hover:bg-accent">
            <X size={18} />
          </button>
        </div>
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
          {items.filter((i) => i.show).map((item) => (
            <NavLink key={item.to} to={item.to} onClick={onClose} className={linkClass} data-testid={`sidebar-link-${item.to.replace(/\//g, "-") || "home"}`}>
              <item.icon className="w-4.5 h-4.5" size={18} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-border">
          <div className="px-2 py-2 mb-1">
            <p className="text-sm font-medium" data-testid="sidebar-user-name">{user.prenom} {user.nom}</p>
            <p className="text-xs text-muted-foreground">{(user.grades || []).join(", ")}</p>
          </div>
          <button
            onClick={logout}
            data-testid="logout-button"
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-destructive hover:bg-destructive/10 transition-colors duration-200"
          >
            <LogOut size={16} /> Déconnexion
          </button>
        </div>
      </aside>
    </>
  );
}
