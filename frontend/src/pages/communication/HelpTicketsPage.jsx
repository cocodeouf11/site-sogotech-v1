import { useEffect, useState } from "react";
import { Layout } from "../../components/layout/Layout";
import { api, formatApiError } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../../components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import { URGENCE_COLORS } from "../../constants";
import { Plus } from "lucide-react";
import { toast } from "sonner";

export default function HelpTicketsPage() {
  const [tickets, setTickets] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ subject: "", description: "", urgence: "moyenne" });
  const [comment, setComment] = useState({});

  const load = async () => {
    const { data } = await api.get("/communication/tickets");
    setTickets(data);
  };
  useEffect(() => { load(); }, []);

  const create = async () => {
    try {
      await api.post("/communication/tickets", form);
      toast.success("Ticket créé");
      setOpen(false);
      setForm({ subject: "", description: "", urgence: "moyenne" });
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const updateStatus = async (id, status) => {
    await api.patch(`/communication/tickets/${id}`, { status });
    load();
  };

  const addComment = async (id) => {
    if (!comment[id]) return;
    await api.post(`/communication/tickets/${id}/comments`, { content: comment[id] });
    setComment({ ...comment, [id]: "" });
    load();
  };

  return (
    <Layout title="Tickets d'aide">
      <div className="flex justify-end mb-5">
        <Button data-testid="help-ticket-add-button" onClick={() => setOpen(true)} className="gap-2"><Plus size={16} />Nouveau ticket</Button>
      </div>
      <div className="space-y-3" data-testid="help-ticket-list">
        {tickets.map((t) => (
          <div key={t.id} className="rounded-xl border border-border bg-card p-4" data-testid={`help-ticket-${t.id}`}>
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="font-semibold">{t.subject}</p>
                <p className="text-sm text-muted-foreground">{t.description}</p>
                <p className="text-xs text-muted-foreground mt-1">Par {t.created_by_nom}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded-md border ${URGENCE_COLORS[t.urgence]}`} data-testid={`help-ticket-urgence-${t.id}`}>{t.urgence}</span>
            </div>
            <div className="flex gap-2 mb-2">
              {["ouvert", "en_cours", "resolu"].map((s) => (
                <button
                  key={s}
                  data-testid={`help-ticket-status-${s}-${t.id}`}
                  onClick={() => updateStatus(t.id, s)}
                  className={`text-xs px-2 py-1 rounded-md border ${t.status === s ? "bg-primary text-primary-foreground" : "border-border"}`}
                >
                  {s}
                </button>
              ))}
            </div>
            <div className="space-y-1 mb-2">
              {(t.comments || []).map((c, idx) => (
                <p key={idx} className="text-xs text-muted-foreground"><b>{c.author}:</b> {c.content}</p>
              ))}
            </div>
            <div className="flex gap-2">
              <Input data-testid={`help-ticket-comment-input-${t.id}`} placeholder="Ajouter un commentaire" value={comment[t.id] || ""} onChange={(e) => setComment({ ...comment, [t.id]: e.target.value })} />
              <Button size="sm" data-testid={`help-ticket-comment-send-${t.id}`} onClick={() => addComment(t.id)}>Envoyer</Button>
            </div>
          </div>
        ))}
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent data-testid="help-ticket-dialog">
          <DialogHeader><DialogTitle>Nouveau ticket d'aide</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <Input data-testid="help-ticket-subject" placeholder="Sujet" value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} />
            <Textarea data-testid="help-ticket-description" placeholder="Description" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} />
            <Select value={form.urgence} onValueChange={(v) => setForm({ ...form, urgence: v })}>
              <SelectTrigger data-testid="help-ticket-urgence-select"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="basse">Basse</SelectItem>
                <SelectItem value="moyenne">Moyenne</SelectItem>
                <SelectItem value="haute">Haute</SelectItem>
                <SelectItem value="critique">Critique</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter><Button data-testid="help-ticket-create-button" onClick={create}>Créer</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
