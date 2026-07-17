import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { api, formatApiError } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import { Upload, PackageSearch, Tag } from "lucide-react";
import { toast } from "sonner";

const STATUS_STYLE = {
  en_attente: "bg-slate-500/15 text-slate-500 border-slate-500/30",
  en_cours: "bg-amber-500/15 text-amber-600 border-amber-500/30",
  termine: "bg-emerald-500/15 text-emerald-600 border-emerald-500/30",
};

function totals(order) {
  const total = (order.lines || []).reduce((s, l) => s + l.quantite_attendue, 0);
  const picked = (order.lines || []).reduce((s, l) => s + l.quantite_picked, 0);
  const percent = total > 0 ? Math.round((picked / total) * 100) : 0;
  return { total, picked, percent };
}

export default function DepotOrdersPage() {
  const [orders, setOrders] = useState([]);
  const [open, setOpen] = useState(false);
  const deliveryRef = useRef(null);
  const labelRef = useRef(null);

  const load = async () => {
    const { data } = await api.get("/depot/orders");
    setOrders(data);
  };
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!deliveryRef.current.files[0]) {
      toast.error("Le bon de livraison PDF est requis");
      return;
    }
    const fd = new FormData();
    fd.append("delivery", deliveryRef.current.files[0]);
    if (labelRef.current.files[0]) fd.append("label", labelRef.current.files[0]);
    try {
      const { data } = await api.post(`/depot/orders`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success(`Commande ${data.numero} créée (${(data.lines || []).length} lignes)`);
      setOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <Layout title="Dépôt">
      <div className="flex gap-2 mb-5 no-print">
        <Button variant="outline" data-testid="depot-tab-orders" className="gap-2"><PackageSearch size={16} />Commandes</Button>
        <Link to="/depot/etiquette">
          <Button variant="outline" data-testid="depot-tab-etiquette" className="gap-2"><Tag size={16} />Étiquette</Button>
        </Link>
        <div className="flex-1" />
        <Button data-testid="depot-add-button" onClick={() => setOpen(true)} className="gap-2"><Upload size={16} />Importer un bon de livraison</Button>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="depot-order-list">
        {orders.map((o) => {
          const { total, picked, percent } = totals(o);
          return (
            <Link key={o.id} to={`/depot/${o.id}`} data-testid={`depot-order-${o.id}`} className="rounded-xl border border-border bg-card p-5 min-h-[64px] hover:border-primary transition-colors duration-200">
              <div className="flex items-center justify-between mb-2">
                <p className="font-heading font-semibold flex items-center gap-2"><PackageSearch size={18} />CMD {o.numero}</p>
                <span className={`text-xs px-2 py-1 rounded-md border ${STATUS_STYLE[o.status]}`}>{o.status}</span>
              </div>
              <p className="text-sm text-muted-foreground">{picked}/{total} · {percent}%</p>
              <div className="h-1.5 rounded-full bg-secondary mt-2 overflow-hidden">
                <div className="h-full bg-primary transition-all duration-300" style={{ width: `${percent}%` }} />
              </div>
            </Link>
          );
        })}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent data-testid="depot-order-dialog">
          <DialogHeader><DialogTitle>Nouvelle commande à picker</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div>
              <label className="text-sm text-muted-foreground">Bon de livraison (PDF) — le N° de commande et les lignes sont extraits automatiquement</label>
              <Input data-testid="depot-delivery-input" type="file" accept="application/pdf" ref={deliveryRef} />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Étiquette Chronopost (optionnel)</label>
              <Input data-testid="depot-label-input" type="file" accept="application/pdf" ref={labelRef} />
            </div>
          </div>
          <DialogFooter><Button data-testid="depot-order-create-button" onClick={create}>Créer</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
