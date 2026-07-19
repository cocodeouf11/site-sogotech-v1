import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { api } from "../../lib/api";
import { useAuth, hasPerm } from "../../context/AuthContext";
import { Truck, Bell } from "lucide-react";

const STATUS_STYLE = {
  envoyee: "bg-amber-500/15 text-amber-600 border-amber-500/30",
  conforme: "bg-emerald-500/15 text-emerald-600 border-emerald-500/30",
  non_conforme: "bg-red-500/15 text-red-600 border-red-500/30",
};

const STATUS_LABEL = {
  envoyee: "En attente de validation",
  conforme: "Conforme",
  non_conforme: "Non conforme",
};

export default function CommandeListPage() {
  const { user } = useAuth();
  const [commandes, setCommandes] = useState([]);
  const isDepot = hasPerm(user, "depot");

  useEffect(() => { api.get("/commandes").then((r) => setCommandes(r.data)); }, []);

  const notifications = commandes.filter((c) => c.notification_message);

  return (
    <Layout title="Commande">
      {isDepot && notifications.length > 0 && (
        <div className="space-y-2 mb-6" data-testid="commande-notifications">
          {notifications.map((c) => (
            <div key={c.id} className="flex items-start gap-2 rounded-lg border border-primary/30 bg-primary/5 p-3 text-sm" data-testid={`commande-notification-${c.id}`}>
              <Bell size={15} className="text-primary shrink-0 mt-0.5" />
              <span>{c.notification_message}</span>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="commande-list">
        {commandes.length === 0 && <p className="text-muted-foreground">Aucune commande pour le moment.</p>}
        {commandes.map((c) => (
          <Link key={c.id} to={`/commandes/${c.id}`} data-testid={`commande-card-${c.id}`} className="rounded-xl border border-border bg-card p-5 hover:border-primary transition-colors duration-200">
            <div className="flex items-center justify-between mb-2">
              <p className="font-heading font-semibold flex items-center gap-2"><Truck size={18} />CMD {c.numero}</p>
              <span className={`text-xs px-2 py-1 rounded-md border ${STATUS_STYLE[c.status]}`}>{STATUS_LABEL[c.status]}</span>
            </div>
            <p className="text-sm text-muted-foreground">Boutique : {c.shop_nom}</p>
            <p className="text-xs text-muted-foreground mt-1">{(c.lines || []).length} ligne(s)</p>
          </Link>
        ))}
      </div>
    </Layout>
  );
}
