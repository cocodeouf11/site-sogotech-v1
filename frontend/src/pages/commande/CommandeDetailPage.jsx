import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { api, formatApiError } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { Checkbox } from "../../components/ui/checkbox";
import { Textarea } from "../../components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import { ArrowLeft, FileText, CheckCircle2, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

export default function CommandeDetailPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [commande, setCommande] = useState(null);
  const [nonConformeOpen, setNonConformeOpen] = useState(false);
  const [selectedLines, setSelectedLines] = useState({});
  const [description, setDescription] = useState("");

  const load = async () => {
    const { data } = await api.get(`/commandes/${id}`);
    setCommande(data);
  };
  useEffect(() => { load(); }, [id]);

  if (!commande) return null;

  const canResolve = commande.status === "envoyee" && (user.is_admin || user.shop_id === commande.shop_id);

  const validateConforme = async () => {
    try {
      await api.post(`/commandes/${id}/resolve-conforme`);
      toast.success("Commande validée : articles ajoutés au stock");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const toggleLine = (lineId) => setSelectedLines((s) => ({ ...s, [lineId]: !s[lineId] }));

  const submitNonConforme = async () => {
    const items = commande.lines.filter((l) => selectedLines[l.id]).map((l) => ({ line_id: l.id, description: l.description }));
    if (items.length === 0) {
      toast.error("Sélectionnez au moins un article");
      return;
    }
    try {
      await api.post(`/commandes/${id}/resolve-non-conforme`, { items, description });
      toast.success("Non-conformité signalée");
      setNonConformeOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <Layout title="Commande">
      <div className="flex items-center gap-3 sm:gap-4 mb-6 no-print">
        <Link to="/commandes" data-testid="commande-back-button" className="p-2 rounded-lg border border-border hover:bg-accent transition-colors duration-200 shrink-0">
          <ArrowLeft size={18} />
        </Link>
        <div className="min-w-0">
          <p className="font-heading text-xl sm:text-2xl font-bold truncate" data-testid="commande-detail-title">CMD {commande.numero}</p>
          <p className="text-sm text-muted-foreground">Boutique : {commande.shop_nom}</p>
        </div>
      </div>

      <a href={`${process.env.REACT_APP_BACKEND_URL}${commande.delivery_pdf_url}`} target="_blank" rel="noreferrer" className="inline-flex mb-6 no-print">
        <Button variant="outline" className="gap-2" data-testid="commande-view-delivery"><FileText size={16} />Voir le bon de livraison</Button>
      </a>

      <div className="space-y-2 mb-6" data-testid="commande-line-list">
        {(commande.lines || []).map((line) => (
          <div key={line.id} className="rounded-lg border border-border bg-card p-3 flex items-center justify-between gap-3" data-testid={`commande-line-${line.id}`}>
            <div className="min-w-0">
              <p className="font-medium break-words">{line.description}</p>
              <p className="text-xs text-muted-foreground">Quantité : {line.quantite_attendue}</p>
            </div>
          </div>
        ))}
      </div>

      {commande.status !== "envoyee" && (
        <div className="rounded-lg border border-border bg-card p-4 mb-6" data-testid="commande-resolution-summary">
          <p className="font-semibold">{commande.status === "conforme" ? "✅ Commande conforme" : "⚠️ Commande non conforme"}</p>
          {commande.resolution_note && <p className="text-sm text-muted-foreground mt-1">{commande.resolution_note}</p>}
          <p className="text-xs text-muted-foreground mt-1">Traité par {commande.resolved_by_nom}</p>
        </div>
      )}

      {canResolve && (
        <div className="flex flex-wrap gap-3 no-print">
          <Button data-testid="commande-conforme-button" onClick={validateConforme} className="gap-2 bg-emerald-600 hover:bg-emerald-700">
            <CheckCircle2 size={16} /> Tout est conforme
          </Button>
          <Button data-testid="commande-non-conforme-button" variant="destructive" onClick={() => setNonConformeOpen(true)} className="gap-2">
            <AlertTriangle size={16} /> Non conforme
          </Button>
        </div>
      )}

      <Dialog open={nonConformeOpen} onOpenChange={setNonConformeOpen}>
        <DialogContent data-testid="commande-non-conforme-dialog">
          <DialogHeader><DialogTitle>Signaler une non-conformité</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">Sélectionnez le ou les articles posant problème :</p>
            <div className="space-y-1 max-h-48 overflow-y-auto">
              {(commande.lines || []).map((line) => (
                <label key={line.id} className="flex items-center gap-2 text-sm">
                  <Checkbox data-testid={`commande-nc-check-${line.id}`} checked={!!selectedLines[line.id]} onCheckedChange={() => toggleLine(line.id)} />
                  {line.description}
                </label>
              ))}
            </div>
            <Textarea data-testid="commande-nc-description" placeholder="Description du problème" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <DialogFooter><Button data-testid="commande-nc-submit" onClick={submitNonConforme}>Envoyer le signalement</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
