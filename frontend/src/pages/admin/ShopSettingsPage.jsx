import { useEffect, useRef, useState } from "react";
import { Layout } from "../../components/layout/Layout";
import { api, UPLOADS_BASE, formatApiError } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../../components/ui/select";
import { Plus, Upload, Pencil } from "lucide-react";
import { toast } from "sonner";

export default function ShopSettingsPage() {
  const [shops, setShops] = useState([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ nom: "", type: "boutique", adresse: "", telephone: "" });
  const logoRefs = useRef({});

  const load = async () => {
    const { data } = await api.get("/shops");
    setShops(data);
  };
  useEffect(() => { load(); }, []);

  const openCreate = () => { setEditing(null); setForm({ nom: "", type: "boutique", adresse: "", telephone: "" }); setOpen(true); };
  const openEdit = (s) => { setEditing(s); setForm({ nom: s.nom, type: s.type, adresse: s.adresse, telephone: s.telephone }); setOpen(true); };

  const save = async () => {
    try {
      if (editing) await api.patch(`/shops/${editing.id}`, form);
      else await api.post("/shops", form);
      toast.success("Boutique enregistrée");
      setOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const uploadLogo = async (shopId, file) => {
    const fd = new FormData();
    fd.append("file", file);
    await api.post(`/shops/${shopId}/logo`, fd, { headers: { "Content-Type": "multipart/form-data" } });
    toast.success("Logo mis à jour");
    load();
  };

  return (
    <Layout title="Boutiques &amp; Dépôts">
      <div className="flex justify-end mb-5">
        <Button data-testid="shop-add-button" onClick={openCreate} className="gap-2"><Plus size={16} />Nouvelle boutique/dépôt</Button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="shop-list">
        {shops.map((s) => (
          <div key={s.id} className="rounded-xl border border-border bg-card p-5" data-testid={`shop-card-${s.id}`}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                {s.logo_url ? <img src={`${UPLOADS_BASE}${s.logo_url}`} className="w-12 h-12 object-contain rounded-md bg-secondary" /> : <div className="w-12 h-12 rounded-md bg-secondary" />}
                <div>
                  <p className="font-heading font-semibold">{s.nom}</p>
                  <p className="text-xs text-muted-foreground uppercase">{s.type}</p>
                </div>
              </div>
              <button data-testid={`shop-edit-${s.id}`} onClick={() => openEdit(s)}><Pencil size={15} /></button>
            </div>
            <p className="text-sm text-muted-foreground">{s.adresse}</p>
            <p className="text-sm text-muted-foreground mb-3">Tél: {s.telephone}</p>
            <input type="file" accept="image/*" className="hidden" ref={(el) => (logoRefs.current[s.id] = el)} onChange={(e) => e.target.files[0] && uploadLogo(s.id, e.target.files[0])} data-testid={`shop-logo-input-${s.id}`} />
            <Button size="sm" variant="outline" className="gap-2" onClick={() => logoRefs.current[s.id].click()} data-testid={`shop-logo-button-${s.id}`}><Upload size={14} />Changer le logo</Button>
          </div>
        ))}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent data-testid="shop-form-dialog">
          <DialogHeader><DialogTitle>{editing ? "Modifier" : "Nouvelle boutique/dépôt"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <Input data-testid="shop-form-nom" placeholder="Nom" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} />
            <Select value={form.type} onValueChange={(v) => setForm({ ...form, type: v })} disabled={!!editing}>
              <SelectTrigger data-testid="shop-form-type-select"><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="boutique">Boutique</SelectItem><SelectItem value="depot">Dépôt</SelectItem></SelectContent>
            </Select>
            <Input data-testid="shop-form-adresse" placeholder="Adresse" value={form.adresse} onChange={(e) => setForm({ ...form, adresse: e.target.value })} />
            <Input data-testid="shop-form-telephone" placeholder="Téléphone" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} />
          </div>
          <DialogFooter><Button data-testid="shop-form-save" onClick={save}>Enregistrer</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
