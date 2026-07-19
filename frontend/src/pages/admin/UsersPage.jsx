import { useEffect, useState } from "react";
import { Layout } from "../../components/layout/Layout";
import { api, formatApiError } from "../../lib/api";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "../../components/ui/dialog";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "../../components/ui/select";
import { Checkbox } from "../../components/ui/checkbox";
import { ALL_GRADES } from "../../constants";
import { Plus, Pencil, Trash2, Shield } from "lucide-react";
import { toast } from "sonner";

const MODULES = ["reprise", "devis", "intervention", "stock"];
const ACTIONS = { reprise: ["create", "edit", "view", "delete"], devis: ["create", "edit", "view", "delete"], intervention: ["create", "edit", "view", "delete"], stock: ["add", "edit", "edit_quantity", "delete"] };

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [shops, setShops] = useState([]);
  const [open, setOpen] = useState(false);
  const [permOpen, setPermOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ nom: "", prenom: "", poste: "", grades: [], shop_id: "", telephone: "", pin: "" });
  const [permTarget, setPermTarget] = useState(null);

  const load = async () => {
    const [u, s] = await Promise.all([api.get("/users"), api.get("/shops")]);
    setUsers(u.data);
    setShops(s.data);
  };
  useEffect(() => { load(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({ nom: "", prenom: "", poste: "", grades: [], shop_id: shops[0]?.id || "", telephone: "", pin: "" });
    setOpen(true);
  };
  const openEdit = (u) => {
    setEditing(u);
    setForm({ nom: u.nom, prenom: u.prenom, poste: u.poste, grades: u.grades || [], shop_id: u.shop_id || "", telephone: u.telephone || "", pin: "" });
    setOpen(true);
  };

  const toggleGrade = (g) => {
    setForm((f) => ({ ...f, grades: f.grades.includes(g) ? f.grades.filter((x) => x !== g) : [...f.grades, g] }));
  };

  const save = async () => {
    if (!form.shop_id) {
      toast.error("Merci de sélectionner une boutique / dépôt d'affectation");
      return;
    }
    try {
      if (editing) {
        const payload = { ...form };
        if (!payload.pin) delete payload.pin;
        await api.patch(`/users/${editing.id}`, payload);
      } else {
        await api.post("/users", form);
      }
      toast.success("Utilisateur enregistré");
      setOpen(false);
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const remove = async (id) => {
    try {
      await api.delete(`/users/${id}`);
      toast.success("Utilisateur supprimé");
      load();
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const openPerms = (u) => { setPermTarget(u); setPermOpen(true); };

  const togglePerm = (module, action) => {
    setPermTarget((t) => {
      const perms = { ...t.permissions };
      if (typeof perms[module] === "boolean") {
        perms[module] = !perms[module];
      } else {
        perms[module] = { ...perms[module], [action]: !perms[module][action] };
      }
      return { ...t, permissions: perms };
    });
  };

  const savePerms = async () => {
    await api.patch(`/users/${permTarget.id}`, { permissions: permTarget.permissions });
    toast.success("Permissions mises à jour");
    setPermOpen(false);
    load();
  };

  return (
    <Layout title="Utilisateurs">
      <div className="flex justify-end mb-5">
        <Button data-testid="user-add-button" onClick={openCreate} className="gap-2"><Plus size={16} />Nouvel utilisateur</Button>
      </div>
      <div className="rounded-xl border border-border bg-card overflow-x-auto" data-testid="user-list">
        <table className="w-full text-sm min-w-[600px]">
          <thead className="bg-secondary text-left">
            <tr><th className="p-3">Nom</th><th className="p-3">Poste</th><th className="p-3">Grades</th><th className="p-3">Boutique</th><th className="p-3"></th></tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-border" data-testid={`user-row-${u.id}`}>
                <td className="p-3">{u.prenom} {u.nom}</td>
                <td className="p-3">{u.poste}</td>
                <td className="p-3">{(u.grades || []).join(", ")}</td>
                <td className="p-3">{shops.find((s) => s.id === u.shop_id)?.nom || "-"}</td>
                <td className="p-3 flex justify-end gap-2">
                  <button data-testid={`user-perms-${u.id}`} onClick={() => openPerms(u)} title="Permissions"><Shield size={15} /></button>
                  <button data-testid={`user-edit-${u.id}`} onClick={() => openEdit(u)}><Pencil size={15} /></button>
                  {!u.is_admin && <button data-testid={`user-delete-${u.id}`} onClick={() => remove(u.id)} className="text-destructive"><Trash2 size={15} /></button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent data-testid="user-form-dialog" className="max-w-lg">
          <DialogHeader><DialogTitle>{editing ? "Modifier l'utilisateur" : "Nouvel utilisateur"}</DialogTitle></DialogHeader>
          <div className="space-y-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input data-testid="user-form-nom" placeholder="Nom" value={form.nom} onChange={(e) => setForm({ ...form, nom: e.target.value })} />
              <Input data-testid="user-form-prenom" placeholder="Prénom" value={form.prenom} onChange={(e) => setForm({ ...form, prenom: e.target.value })} />
            </div>
            <Input data-testid="user-form-poste" placeholder="Poste" value={form.poste} onChange={(e) => setForm({ ...form, poste: e.target.value })} />
            <Select value={form.shop_id} onValueChange={(v) => setForm({ ...form, shop_id: v })}>
              <SelectTrigger data-testid="user-form-shop-select"><SelectValue placeholder="Boutique / Dépôt d'affectation" /></SelectTrigger>
              <SelectContent>{shops.map((s) => <SelectItem key={s.id} value={s.id}>{s.nom}</SelectItem>)}</SelectContent>
            </Select>
            <Input data-testid="user-form-telephone" placeholder="Téléphone (optionnel)" value={form.telephone} onChange={(e) => setForm({ ...form, telephone: e.target.value })} />
            <Input data-testid="user-form-pin" placeholder={editing ? "Nouveau code PIN (laisser vide pour ne pas changer)" : "Code PIN (6 chiffres)"} value={form.pin} onChange={(e) => setForm({ ...form, pin: e.target.value })} />
            <div>
              <p className="text-sm text-muted-foreground mb-2">Grades (multiple possible)</p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {ALL_GRADES.map((g) => (
                  <label key={g} className="flex items-center gap-2 text-sm">
                    <Checkbox data-testid={`user-form-grade-${g}`} checked={form.grades.includes(g)} onCheckedChange={() => toggleGrade(g)} />
                    {g}
                  </label>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter><Button data-testid="user-form-save" onClick={save}>Enregistrer</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={permOpen} onOpenChange={setPermOpen}>
        <DialogContent data-testid="user-perms-dialog" className="max-w-lg">
          <DialogHeader><DialogTitle>Permissions — {permTarget?.prenom} {permTarget?.nom}</DialogTitle></DialogHeader>
          {permTarget && (
            <div className="space-y-4">
              {MODULES.map((mod) => (
                <div key={mod}>
                  <p className="text-sm font-semibold capitalize mb-1">{mod}</p>
                  <div className="flex gap-3 flex-wrap">
                    {ACTIONS[mod].map((action) => (
                      <label key={action} className="flex items-center gap-1.5 text-xs">
                        <Checkbox data-testid={`perm-${mod}-${action}`} checked={!!(permTarget.permissions[mod] || {})[action]} onCheckedChange={() => togglePerm(mod, action)} />
                        {action}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
              <div>
                <p className="text-sm font-semibold mb-1">Caisse</p>
                <label className="flex items-center gap-1.5 text-xs">
                  <Checkbox data-testid="perm-caisse-delete_ticket" checked={!!permTarget.permissions.caisse.delete_ticket} onCheckedChange={() => togglePerm("caisse", "delete_ticket")} />
                  Supprimer ticket/facture
                </label>
              </div>
              <div>
                <p className="text-sm font-semibold mb-1">Communication</p>
                <label className="flex items-center gap-1.5 text-xs">
                  <Checkbox data-testid="perm-communication" checked={!!permTarget.permissions.communication} onCheckedChange={() => setPermTarget((t) => ({ ...t, permissions: { ...t.permissions, communication: !t.permissions.communication } }))} />
                  Autorisé
                </label>
              </div>
              <div>
                <p className="text-sm font-semibold mb-1">Dépôt</p>
                <label className="flex items-center gap-1.5 text-xs">
                  <Checkbox data-testid="perm-depot" checked={!!permTarget.permissions.depot} onCheckedChange={() => setPermTarget((t) => ({ ...t, permissions: { ...t.permissions, depot: !t.permissions.depot } }))} />
                  Accès à la fonction Dépôt (picking, étiquette, envoi des bons de commande)
                </label>
              </div>
            </div>
          )}
          <DialogFooter><Button data-testid="user-perms-save" onClick={savePerms}>Enregistrer</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
