import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { api, formatApiError } from "../../lib/api";
import { useAuth, hasPerm } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Plus, Lock, FileDown, Trash2, Search } from "lucide-react";
import { toast } from "sonner";

export default function RepriseListPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [search, setSearch] = useState("");

  const load = () => api.get("/reprises").then((r) => setItems(r.data));
  useEffect(() => { load(); }, []);

  const filtered = items.filter((it) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (it.numero || "").toLowerCase().includes(q) || (it.client_nom || "").toLowerCase().includes(q) || (it.modele || "").toLowerCase().includes(q);
  });

  const remove = async (id) => {
    try {
      await api.delete(`/reprises/${id}`);
      toast.success("Reprise supprimée");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <Layout title="Reprises téléphone">
      <div className="flex justify-between items-center gap-3 mb-5">
        <div className="relative w-full max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input data-testid="reprise-search-input" placeholder="Rechercher par n°, client, modèle..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        {hasPerm(user, "reprise", "create") && (
          <Link to="/reprises/new">
            <Button data-testid="reprise-add-button" className="gap-2 shrink-0"><Plus size={16} /> Nouvelle reprise</Button>
          </Link>
        )}
      </div>
      <div className="rounded-xl border border-border bg-card overflow-hidden" data-testid="reprise-list">
        <table className="w-full text-sm">
          <thead className="bg-secondary text-left">
            <tr><th className="p-3">N°</th><th className="p-3">Date</th><th className="p-3">Client</th><th className="p-3">Modèle</th><th className="p-3"></th></tr>
          </thead>
          <tbody>
            {filtered.map((it) => (
              <tr key={it.id} className="border-t border-border" data-testid={`reprise-row-${it.id}`}>
                <td className="p-3">{it.numero}</td>
                <td className="p-3">{it.date}</td>
                <td className="p-3">{it.client_nom}</td>
                <td className="p-3">{it.modele}</td>
                <td className="p-3 text-right">
                  {it.can_open ? (
                    <div className="flex justify-end items-center gap-3">
                      <Link to={`/reprises/${it.id}`} data-testid={`reprise-open-${it.id}`} className="text-primary text-sm">
                        {hasPerm(user, "reprise", "edit") ? "Modifier" : "Voir"}
                      </Link>
                      <a href={`${api.defaults.baseURL}/reprises/${it.id}/pdf`} target="_blank" rel="noreferrer" data-testid={`reprise-pdf-${it.id}`} title="PDF"><FileDown size={15} /></a>
                      {hasPerm(user, "reprise", "delete") && (
                        <button data-testid={`reprise-delete-${it.id}`} onClick={() => remove(it.id)} title="Supprimer" className="text-destructive"><Trash2 size={15} /></button>
                      )}
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
