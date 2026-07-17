import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { api } from "../../lib/api";
import { useAuth, hasPerm } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { Plus, Lock, FileDown } from "lucide-react";

export default function RepriseListPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);

  useEffect(() => {
    api.get("/reprises").then((r) => setItems(r.data));
  }, []);

  return (
    <Layout title="Reprises téléphone">
      <div className="flex justify-end mb-5">
        {hasPerm(user, "reprise", "create") && (
          <Link to="/reprises/new">
            <Button data-testid="reprise-add-button" className="gap-2"><Plus size={16} /> Nouvelle reprise</Button>
          </Link>
        )}
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden" data-testid="reprise-list">
        <table className="w-full text-sm">
          <thead className="bg-secondary text-left">
            <tr><th className="p-3">N°</th><th className="p-3">Date</th><th className="p-3">Client</th><th className="p-3">Modèle</th><th className="p-3"></th></tr>
          </thead>
          <tbody>
            {items.map((it) => (
              <tr key={it.id} className="border-t border-border" data-testid={`reprise-row-${it.id}`}>
                <td className="p-3">{it.numero}</td>
                <td className="p-3">{it.date}</td>
                <td className="p-3">{it.client_nom}</td>
                <td className="p-3">{it.modele}</td>
                <td className="p-3 text-right">
                  {it.can_open ? (
                    <div className="flex justify-end gap-3">
                      <Link to={`/reprises/${it.id}`} data-testid={`reprise-open-${it.id}`} className="text-primary text-sm">Ouvrir</Link>
                      <a href={`${api.defaults.baseURL}/reprises/${it.id}/pdf`} target="_blank" rel="noreferrer" data-testid={`reprise-pdf-${it.id}`}><FileDown size={15} /></a>
                    </div>
                  ) : (
                    <Lock size={14} className="text-muted-foreground inline" data-testid={`reprise-locked-${it.id}`} />
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
