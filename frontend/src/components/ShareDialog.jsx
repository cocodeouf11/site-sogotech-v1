import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "./ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "./ui/select";
import { Button } from "./ui/button";
import { api, formatApiError } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { toast } from "sonner";

export function ShareDialog({ open, onOpenChange, module, itemId, onShared }) {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [targetUserId, setTargetUserId] = useState("");
  const [mode, setMode] = useState("read");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    setTargetUserId("");
    setMode("read");
    api.get("/users").then((r) => setUsers(r.data.filter((u) => u.id !== user.id)));
  }, [open, user]);

  const submit = async () => {
    if (!targetUserId) {
      toast.error("Choisissez un utilisateur destinataire");
      return;
    }
    setSubmitting(true);
    try {
      await api.post(`/${module}/${itemId}/share`, { user_id: targetUserId, mode });
      toast.success("Document partagé");
      onOpenChange(false);
      onShared?.();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent data-testid="share-dialog">
        <DialogHeader><DialogTitle>Partager ce document</DialogTitle></DialogHeader>
        <div className="space-y-4">
          <div>
            <p className="text-sm text-muted-foreground mb-2">Destinataire</p>
            <Select value={targetUserId} onValueChange={setTargetUserId}>
              <SelectTrigger data-testid="share-user-select"><SelectValue placeholder="Choisir un utilisateur" /></SelectTrigger>
              <SelectContent>
                {users.map((u) => (
                  <SelectItem key={u.id} value={u.id}>{u.prenom} {u.nom} — {u.poste}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Droits accordés</p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant={mode === "read" ? "default" : "outline"}
                size="sm"
                data-testid="share-mode-read"
                onClick={() => setMode("read")}
              >
                Lecture seule
              </Button>
              <Button
                type="button"
                variant={mode === "write" ? "default" : "outline"}
                size="sm"
                data-testid="share-mode-write"
                onClick={() => setMode("write")}
              >
                Lecture / écriture
              </Button>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button data-testid="share-dialog-submit" onClick={submit} disabled={submitting}>
            {submitting ? "Partage..." : "Partager"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
