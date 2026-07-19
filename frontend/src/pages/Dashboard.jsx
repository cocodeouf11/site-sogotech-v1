import { useEffect, useState } from "react";
import { Package, ShoppingCart, Wrench, FileText, RefreshCcw, Warehouse } from "lucide-react";
import { Layout } from "../components/layout/Layout";
import { api } from "../lib/api";
import { useAuth, hasPerm } from "../context/AuthContext";

function StatCard({ icon: Icon, label, value, testId }) {
  return (
    <div className="rounded-xl border border-border bg-card p-6 h-full transition-transform duration-200 hover:-translate-y-0.5" data-testid={testId}>
      <div className="flex items-center justify-between mb-3">
        <Icon className="text-primary" size={22} />
        <span className="text-3xl font-heading font-bold">{value}</span>
      </div>
      <p className="text-sm text-muted-foreground">{label}</p>
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState({ articles: 0, tickets: 0, interventions: 0, devis: 0, reprises: 0, depot: 0 });

  useEffect(() => {
    if (!user) return;
    (async () => {
      const calls = [
        api.get("/stock"),
        api.get("/caisse"),
        api.get("/interventions"),
        api.get("/devis"),
        api.get("/reprises"),
        hasPerm(user, "depot") ? api.get("/depot/orders") : Promise.resolve({ data: [] }),
      ];
      const results = await Promise.allSettled(calls);
      const val = (r) => (r.status === "fulfilled" ? r.value.data.length : 0);
      setStats({
        articles: val(results[0]),
        tickets: val(results[1]),
        interventions: val(results[2]),
        devis: val(results[3]),
        reprises: val(results[4]),
        depot: val(results[5]),
      });
    })();
  }, [user]);

  return (
    <Layout title={`Bonjour, ${user?.prenom || ""}`}>
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        <StatCard icon={Package} label="Articles en stock" value={stats.articles} testId="stat-articles" />
        <StatCard icon={ShoppingCart} label="Tickets / Factures" value={stats.tickets} testId="stat-tickets" />
        <StatCard icon={Wrench} label="Interventions" value={stats.interventions} testId="stat-interventions" />
        <StatCard icon={FileText} label="Devis" value={stats.devis} testId="stat-devis" />
        <StatCard icon={RefreshCcw} label="Reprises" value={stats.reprises} testId="stat-reprises" />
        <StatCard icon={Warehouse} label="Commandes dépôt" value={stats.depot} testId="stat-depot" />
      </div>
    </Layout>
  );
}
