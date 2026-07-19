import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { DocumentHeader } from "../../components/DocumentHeader";
import { SignaturePad } from "../../components/SignaturePad";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Button } from "../../components/ui/button";
import { api, formatApiError } from "../../lib/api";
import { useAuth, hasPerm } from "../../context/AuthContext";
import { toast } from "sonner";
import { Plus, Trash2, Printer, Save } from "lucide-react";

const DEFAULT_MENTIONS = "Devis valable 30 jours à compter de sa date d'émission. Ce devis ne constitue pas une facture. Tout travail supplémentaire non prévu fera l'objet d'un devis complémentaire.";

export default function DevisFormPage() {
  const { id } = useParams();
  const isNew = id === "new";
  const navigate = useNavigate();
  const { user } = useAuth();
  const sigRef = useRef(null);
  const [shop, setShop] = useState(null);
  const [interventions, setInterventions] = useState([]);
  const [data, setData] = useState({
    numero: "", client_nom: "", client_tel: "", client_email: "",
    items: [], intervention_ids: [], mentions_legales: DEFAULT_MENTIONS,
  });

  useEffect(() => {
    (async () => {
      const [shopsRes, intRes] = await Promise.all([api.get("/shops"), api.get("/interventions")]);
      const myShop = shopsRes.data.find((s) => s.id === user.effective_shop_id);
      if (!myShop && isNew) {
        toast.error("Aucune boutique n'est assignée à votre compte. Contactez un administrateur.");
      }
      setShop(myShop || shopsRes.data[0]);
      setInterventions(intRes.data.filter((i) => i.can_open));
      if (!isNew) {
        const { data: item } = await api.get(`/devis/${id}`);
        setData(item);
      }
    })();
  }, [id]);

  const today = new Date().toLocaleDateString("fr-FR");
  const total = data.items.reduce((s, i) => s + i.prix_unitaire * i.quantite, 0);

  const addItem = () => setData({ ...data, items: [...data.items, { nom: "", prix_unitaire: 0, quantite: 1 }] });
  const updateItem = (idx, field, val) => {
    const items = [...data.items];
    items[idx] = { ...items[idx], [field]: val };
    setData({ ...data, items });
  };
  const removeItem = (idx) => setData({ ...data, items: data.items.filter((_, i) => i !== idx) });

  const toggleIntervention = (intId) => {
    const ids = data.intervention_ids.includes(intId)
      ? data.intervention_ids.filter((i) => i !== intId)
      : [...data.intervention_ids, intId];
    setData({ ...data, intervention_ids: ids });
  };

  const canEdit = data.is_shared_to_me
    ? data.share_mode === "write"
    : (isNew ? hasPerm(user, "devis", "create") : hasPerm(user, "devis", "edit"));

  const save = async () => {
    const signature_data = sigRef.current?.toDataURL() || data.signature_data || "";
    if (isNew && !shop) {
      toast.error("Impossible de créer : aucune boutique assignée à votre compte.");
      return;
    }
    try {
      if (isNew) {
        const { data: created } = await api.post("/devis", { ...data, shop_id: shop.id, signature_data });
        toast.success(`Devis ${created.numero} créé`);
        navigate(`/devis/${created.id}`);
      } else {
        await api.patch(`/devis/${id}`, { ...data, signature_data });
        toast.success("Devis mis à jour");
      }
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <Layout title="Devis">
      <div className="a4-sheet max-w-4xl mx-auto p-4 sm:p-8 md:p-12 rounded-md">
        <DocumentHeader shop={shop} numero={data.numero || "(auto)"} />
        {data.is_shared_to_me && (
          <p className="text-xs text-center text-muted-foreground mb-4" data-testid="devis-shared-banner">
            Document partagé par {data.shared_by_label} — {data.share_mode === "write" ? "lecture / écriture" : "lecture seule"}
          </p>
        )}
        <h2 className="font-heading text-xl font-bold text-center mb-6">DEVIS</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6 text-sm">
          <div><span className="font-semibold">Vendeur:</span> {data.vendeur_nom || `${user.prenom} ${user.nom}`}</div>
          <div><span className="font-semibold">Date:</span> {data.date || today}</div>
          <Input data-testid="devis-client-nom" disabled={!canEdit} placeholder="Nom client" value={data.client_nom} onChange={(e) => setData({ ...data, client_nom: e.target.value })} />
          <Input data-testid="devis-client-tel" disabled={!canEdit} placeholder="Téléphone" value={data.client_tel} onChange={(e) => setData({ ...data, client_tel: e.target.value })} />
        </div>

        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <p className="font-semibold text-sm">Lignes du devis</p>
            {canEdit && <Button size="sm" variant="outline" data-testid="devis-add-item" onClick={addItem} className="gap-1"><Plus size={14} />Ligne</Button>}
          </div>
          {data.items.map((item, idx) => (
            <div key={idx} className="grid grid-cols-2 sm:grid-cols-12 gap-2 mb-2 items-center">
              <Input disabled={!canEdit} data-testid={`devis-item-nom-${idx}`} className="col-span-2 sm:col-span-6" placeholder="Désignation" value={item.nom} onChange={(e) => updateItem(idx, "nom", e.target.value)} />
              <Input disabled={!canEdit} data-testid={`devis-item-qte-${idx}`} type="number" className="col-span-1 sm:col-span-2" value={item.quantite} onChange={(e) => updateItem(idx, "quantite", Number(e.target.value))} />
              <Input disabled={!canEdit} data-testid={`devis-item-prix-${idx}`} type="number" className="col-span-1 sm:col-span-3" value={item.prix_unitaire} onChange={(e) => updateItem(idx, "prix_unitaire", Number(e.target.value))} />
              {canEdit && <button data-testid={`devis-item-remove-${idx}`} onClick={() => removeItem(idx)} className="text-destructive justify-self-end sm:justify-self-auto"><Trash2 size={16} /></button>}
            </div>
          ))}
          <p className="text-right font-bold mt-2">Total: {total.toFixed(2)} €</p>
        </div>

        {interventions.length > 0 && (
          <div className="mb-6">
            <p className="font-semibold text-sm mb-2">Rattacher des fiches d'intervention</p>
            <div className="flex flex-wrap gap-2">
              {interventions.map((it) => (
                <button
                  key={it.id}
                  data-testid={`devis-toggle-intervention-${it.id}`}
                  onClick={() => canEdit && toggleIntervention(it.id)}
                  className={`text-xs px-2 py-1 rounded-md border ${data.intervention_ids.includes(it.id) ? "bg-primary text-primary-foreground" : "border-border"}`}
                >
                  {it.numero}
                </button>
              ))}
            </div>
          </div>
        )}

        <label className="text-sm font-semibold">Mentions légales</label>
        <Textarea data-testid="devis-mentions" disabled={!canEdit} className="mb-6 h-20" value={data.mentions_legales} onChange={(e) => setData({ ...data, mentions_legales: e.target.value })} />

        <label className="text-sm font-semibold block mb-2">Signature (bon pour accord)</label>
        <SignaturePad ref={sigRef} testId="devis-signature-pad" />

        <div className="flex gap-3 mt-6 no-print">
          {canEdit && <Button data-testid="devis-save-button" onClick={save} className="gap-2"><Save size={16} />Enregistrer</Button>}
          {!isNew && (
            <a href={`${api.defaults.baseURL}/devis/${id}/pdf`} target="_blank" rel="noreferrer">
              <Button variant="outline" data-testid="devis-pdf-button" className="gap-2"><Printer size={16} />PDF</Button>
            </a>
          )}
        </div>
      </div>
    </Layout>
  );
}
