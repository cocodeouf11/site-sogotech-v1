import { useEffect, useState } from "react";
import { Layout } from "../../components/layout/Layout";
import { api, UPLOADS_BASE, formatApiError } from "../../lib/api";
import { useAuth, hasPerm } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import { Plus, Pencil, Trash2, Package, Search } from "lucide-react";
import { toast } from "sonner";

export default function StockPage() {
  const { user } = useAuth();
  const [articles, setArticles] = useState([]);
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ nom: "", quantite: 0, categorie: "", prix: 0, code: "" });
  const [photoFile, setPhotoFile] = useState(null);

  const load = async () => {
    const { data } = await api.get("/stock");
    setArticles(data);
  };
  useEffect(() => { load(); }, []);

  const filtered = articles.filter((a) => {
    const q = search.trim().toLowerCase();
    if (!q) return true;
    return (a.nom || "").toLowerCase().includes(q) || (a.categorie || "").toLowerCase().includes(q) || (a.code || "").toLowerCase().includes(q);
  });

  const openCreate = () => {
    setEditing(null);
    setForm({ nom: "", quantite: 0, categorie: "", prix: 0, code: "" });
    setPhotoFile(null);
    setOpen(true);
  };
  const openEdit = (a) => {
    setEditing(a);
    setForm({ nom: a.nom, quantite: a.quantite, categorie: a.categorie || "", prix: a.prix || 0, code: a.code || "" });
    setPhotoFile(null);
    setOpen(true);
  };

  const save = async () => {
    try {
      let article;
      if (editing) {
        const { data } = await api.patch(`/stock/${editing.id}`, form);
        article = data;
      } else {
        const { data } = await api.post("/stock", form);
        article = data;
      }
      if (photoFile) {
        const fd = new FormData();
        fd.append("file", photoFile);
        await api.post(`/stock/${article.id}/photo`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      }
      toast.success("Article enregistré");
      setOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const remove = async (id) => {
    try {
      await api.delete(`/stock/${id}`);
      toast.success("Article supprimé");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <Layout title="Stock">
      <div className="flex justify-between items-center gap-3 mb-5">
        <div className="relative w-full max-w-sm">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <Input data-testid="stock-search-input" placeholder="Rechercher un article, une catégorie, un ID..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9" />
        </div>
        {hasPerm(user, "stock", "add") && (
          <Button data-testid="stock-add-button" onClick={openCreate} className="gap-2 shrink-0">
            <Plus size={16} /> Ajouter un article
          </Button>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4" data-testid="stock-grid">
        {filtered.map((a) => (
          <div key={a.id} className="aspect-square rounded-xl border border-border bg-card p-3 flex flex-col group relative" data-testid={`stock-card-${a.id}`}>
            <div className="flex-1 rounded-lg bg-secondary overflow-hidden flex items-center justify-center mb-2">
              {a.photo_url ? (
                <img src={`${UPLOADS_BASE}${a.photo_url}`} alt={a.nom} className="w-full h-full object-cover" />
              ) : (
                <Package className="text-muted-foreground" size={32} />
              )}
            </div>
            <p className="text-sm font-medium truncate" data-testid={`stock-card-name-${a.id}`}>{a.nom}</p>
            <p className="text-xs text-muted-foreground">ID: {a.code || a.id.slice(-6)}</p>
            <p className="text-xs font-semibold" data-testid={`stock-card-qty-${a.id}`}>Qté: {a.quantite}</p>
            {hasPerm(user, "stock", "edit") && (
              <div className="absolute top-2 right-2 hidden group-hover:flex gap-1">
                <button data-testid={`stock-edit-${a.id}`} onClick={() => openEdit(a)} className="p-1.5 rounded-md bg-background/90 border border-border">
                  <Pencil size={13} />
                </button>
                {hasPerm(user, "stock", "delete") && (
                  <button data-testid={`stock-delete-${a.id}`} onClick={() => remove(a.id)} className="p-1.5 rounded-md bg-background/90 border border-border text-destructive">
                    <Trash2 size={13} />
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent data-testid="stock-form-dialog">
          <DialogHeader><DialogTitle>{editing ? "Modifier l'article" : "Nouvel article"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <Input data-testid="stock-form-nom" placeholder="Nom" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} />
            <Input data-testid="stock-form-code" placeholder="ID article (laisser vide pour génération automatique)" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} />
            <Input data-testid="stock-form-quantite" type="number" placeholder="Quantité" value={form.quantite} onChange={(e) => setForm({ ...form, quantite: Number(e.target.value) })} />
            <Input data-testid="stock-form-categorie" placeholder="Catégorie" value={form.categorie} onChange={(e) => setForm({ ...form, categorie: e.target.value })} />
            <Input data-testid="stock-form-prix" type="number" placeholder="Prix (€)" value={form.prix} onChange={(e) => setForm({ ...form, prix: Number(e.target.value) })} />
            <Input data-testid="stock-form-photo" type="file" accept="image/*" onChange={(e) => setPhotoFile(e.target.files[0])} />
          </div>
          <DialogFooter>
            <Button data-testid="stock-form-save" onClick={save}>Enregistrer</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
