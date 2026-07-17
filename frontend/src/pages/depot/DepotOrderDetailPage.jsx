import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { api } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Plus, Minus, RotateCcw, FileText, Tag } from "lucide-react";

export default function DepotOrderDetailPage() {
  const { id } = useParams();
  const [order, setOrder] = useState(null);

  const load = async () => {
    const { data } = await api.get(`/depot/orders/${id}`);
    setOrder(data);
  };
  useEffect(() => { load(); }, [id]);

  const inc = async (lineId, delta) => {
    await api.post(`/depot/orders/${id}/lines/${lineId}/increment`, { delta });
    load();
  };
  const reset = async (lineId) => {
    await api.post(`/depot/orders/${id}/lines/${lineId}/increment`, { reset: true });
    load();
  };

  if (!order) return null;

  return (
    <Layout title={`Commande ${order.numero}`}>
      <div className="flex gap-3 mb-6 no-print">
        <a href={`${process.env.REACT_APP_BACKEND_URL}${order.delivery_pdf_url}`} target="_blank" rel="noreferrer">
          <Button variant="outline" className="gap-2" data-testid="depot-view-delivery"><FileText size={16} />Bon de livraison</Button>
        </a>
        {order.label_pdf_url && (
          <a href={`${process.env.REACT_APP_BACKEND_URL}${order.label_pdf_url}`} target="_blank" rel="noreferrer">
            <Button variant="outline" className="gap-2" data-testid="depot-view-label"><Tag size={16} />Étiquette</Button>
          </a>
        )}
      </div>

      <div className="space-y-3" data-testid="depot-line-list">
        {(order.lines || []).length === 0 && <p className="text-muted-foreground">Aucune ligne détectée automatiquement. Vérifiez le bon de livraison.</p>}
        {(order.lines || []).map((line) => {
          const done = line.quantite_picked >= line.quantite_attendue;
          return (
            <div key={line.id} className={`rounded-xl border p-4 flex items-center justify-between min-h-[64px] ${done ? "border-emerald-500/50 bg-emerald-500/10" : "border-border bg-card"}`} data-testid={`depot-line-${line.id}`}>
              <div>
                <p className="font-medium">{line.description}</p>
                <p className="text-sm text-muted-foreground">{line.quantite_picked} / {line.quantite_attendue}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button size="icon" variant="outline" className="min-h-[48px] min-w-[48px]" data-testid={`depot-line-minus-${line.id}`} onClick={() => inc(line.id, -1)}><Minus /></Button>
                <Button size="icon" variant="outline" className="min-h-[48px] min-w-[48px]" data-testid={`depot-line-reset-${line.id}`} onClick={() => reset(line.id)}><RotateCcw size={16} /></Button>
                <Button size="icon" className="min-h-[48px] min-w-[48px]" data-testid={`depot-line-plus-${line.id}`} onClick={() => inc(line.id, 1)}><Plus /></Button>
              </div>
            </div>
          );
        })}
      </div>
    </Layout>
  );
}
