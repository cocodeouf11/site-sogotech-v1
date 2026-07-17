import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { api } from "../../lib/api";
import { useAuth, hasPerm } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { Plus, Lock, FileDown } from "lucide-react";

export default function InterventionListPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);

  useEffect(() => {
    api.get("/interventions").then((r) => setItems(r.data));
  }, []);

  return (
    <Layout title="Interventions">
      <div className="flex justify-end mb-5">
        {hasPerm(user, "intervention", "create") && (
          <Link to="/interventions/new">
            <Button data-testid="intervention-add-button" className="gap-2"><Plus size={16} /> Nouvelle intervention</Button>
          </Link>
        )}
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden" data-testid="intervention-list">
        <table className="w-full text-sm">
          <thead className="bg-secondary text-left">
            <tr>
              <th className="p-3">N°</th><th className="p-3">Date</th><th className="p-3">Client</th><th className="p-3">Vendeur</th><th className="p-3"></th>
            </tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id} className="border-t border-border" data-testid={`intervention-row-${it.id}`}>
                <td className="p-3">{it.numero}</td>
                <td className="p-3">{it.date}</td>
                <td className="p-3">{it.client_nom}</td>
                <td className="p-3">{it.vendeur_nom}</td>
                <td className="p-3 text-right">
                  {it.can_open ? (
                    <div className="flex justify-end gap-3">
                      <Link to={`/interventions/${it.id}`} data-testid={`intervention-open-${it.id}`} className="text-primary text-sm">Ouvrir</Link>
                      <a href={`${api.defaults.baseURL}/interventions/${it.id}/pdf`} target="_blank" rel="noreferrer" data-testid={`intervention-pdf-${it.id}`}><FileDown size={15} /></a>
                    </div>
                  ) : (
                    <Lock size={14} className="text-muted-foreground inline" data-testid={`intervention-locked-${it.id}`} />
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  );
}
