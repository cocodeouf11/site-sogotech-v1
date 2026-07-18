import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { api, formatApiError } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "../../components/ui/dropdown-menu";
import { ArrowLeft, FileText, Tag, Trash2, MoreVertical } from "lucide-react";
import { toast } from "sonner";

function totals(order) {
  const total = (order.lines || []).reduce((s, l) => s + l.quantite_attendue, 0);
  const picked = (order.lines || []).reduce((s, l) => s + l.quantite_picked, 0);
  const percent = total > 0 ? Math.round((picked / total) * 100) : 0;
  return { total, picked, percent };
}

function LinePill({ line, onTap }) {
  const done = line.quantite_picked >= line.quantite_attendue;
  return (
    <button
      onClick={onTap}
      data-testid={`depot-line-pill-${line.id}`}
      className={`min-h-[56px] min-w-[64px] px-4 rounded-full font-heading text-lg font-bold border-2 transition-colors duration-150 active:scale-95 ${
        done ? "bg-emerald-500 border-emerald-500 text-white" : "bg-card border-foreground/20 text-foreground hover:border-primary"
      }`}
    >
      {line.quantite_picked}/{line.quantite_attendue}
    </button>
  );
}

export default function DepotOrderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);

  const load = async () => {
    const { data } = await api.get(`/depot/orders/${id}`);
    setOrder(data);
  };
  useEffect(() => { load(); }, [id]);

  const tap = async (lineId) => {
    await api.post(`/depot/orders/${id}/lines/${lineId}/tap`);
    load();
  };

  const removeOrder = async () => {
    try {
      await api.delete(`/depot/orders/${id}`);
      toast.success("Commande supprimée");
      navigate("/depot");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  if (!order) return null;
  const { total, picked, percent } = totals(order);

  return (
    <Layout title="Dépôt">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 no-print">
        <div className="flex items-center gap-3 sm:gap-4 min-w-0">
          <Link to="/depot" data-testid="depot-back-button" className="p-2 rounded-lg border border-border hover:bg-accent transition-colors duration-200 shrink-0">
            <ArrowLeft size={18} />
          </Link>
          <div className="min-w-0">
            <p className="font-heading text-xl sm:text-2xl font-bold truncate" data-testid="depot-order-title">CMD {order.numero}</p>
            <p className="text-sm text-muted-foreground" data-testid="depot-order-progress">{picked}/{total} · {percent}%</p>
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" data-testid="depot-actions-button" className="gap-2 shrink-0">ACTIONS <MoreVertical size={16} /></Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <a href={`${process.env.REACT_APP_BACKEND_URL}${order.delivery_pdf_url}`} target="_blank" rel="noreferrer" data-testid="depot-view-delivery" className="flex items-center gap-2 cursor-pointer">
                <FileText size={15} /> Bon de livraison
              </a>
            </DropdownMenuItem>
            {order.label_pdf_url && (
              <DropdownMenuItem asChild>
                <a href={`${process.env.REACT_APP_BACKEND_URL}${order.label_pdf_url}`} target="_blank" rel="noreferrer" data-testid="depot-view-label" className="flex items-center gap-2 cursor-pointer">
                  <Tag size={15} /> Étiquette
                </a>
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={removeOrder} data-testid="depot-delete-order" className="text-destructive gap-2">
              <Trash2 size={15} /> Supprimer la commande
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <div className="h-2 rounded-full bg-secondary mb-6 overflow-hidden no-print">
        <div className="h-full bg-primary transition-all duration-300" style={{ width: `${percent}%` }} />
      </div>

      <div className="space-y-3" data-testid="depot-line-list">
        {(order.lines || []).length === 0 && <p className="text-muted-foreground">Aucune ligne détectée automatiquement dans ce bon de livraison.</p>}
        {(order.lines || []).map((line) => {
          const done = line.quantite_picked >= line.quantite_attendue;
          return (
            <div
              key={line.id}
              className={`rounded-xl border-2 border-dashed p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 sm:gap-4 min-h-[64px] ${done ? "border-emerald-500/40 bg-emerald-500/5" : "border-border bg-card"}`}
              data-testid={`depot-line-${line.id}`}
            >
              <div className="min-w-0">
                <p className="font-medium break-words">{line.description}</p>
                <p className="text-xs text-muted-foreground mt-1 break-words">
                  {line.ugs && <>UGS : {line.ugs} </>}
                  Étagère : {line.etagere} | Colonne : {line.colonne} | Tiroir : {line.tiroir} | Bac : {line.bac}
                </p>
              </div>
              <LinePill line={line} onTap={() => tap(line.id)} />
            </div>
          );
        })}
      </div>
    </Layout>
  );
}
