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
import { Printer, Save } from "lucide-react";

export default function InterventionFormPage() {
  const { id } = useParams();
  const isNew = id === "new";
  const navigate = useNavigate();
  const { user } = useAuth();
  const sigRef = useRef(null);
  const [shop, setShop] = useState(null);
  const [data, setData] = useState({
    numero: "",
    client_nom: "", client_tel: "", client_email: "", client_adresse: "",
    materiel: "", imei: "", motif: "", intervention_effectuee: "",
  });

  useEffect(() => {
    (async () => {
      const shopsRes = await api.get("/shops");
      const myShop = shopsRes.data.find((s) => s.id === user.shop_id);
      if (!myShop && isNew) {
        toast.error("Aucune boutique n'est assignée à votre compte. Contactez un administrateur.");
      }
      setShop(myShop || shopsRes.data[0]);
      if (!isNew) {
        const { data: item } = await api.get(`/interventions/${id}`);
        setData(item);
      }
    })();
  }, [id]);

  const today = new Date().toLocaleDateString("fr-FR");

  const save = async () => {
    const signature_data = sigRef.current?.toDataURL() || data.signature_data || "";
    if (isNew && !shop) {
      toast.error("Impossible de créer : aucune boutique assignée à votre compte.");
      return;
    }
    try {
      if (isNew) {
        const { data: created } = await api.post("/interventions", { ...data, shop_id: shop.id, signature_data });
        toast.success(`Intervention ${created.numero} créée`);
        navigate(`/interventions/${created.id}`);
      } else {
        await api.patch(`/interventions/${id}`, { ...data, signature_data });
        toast.success("Intervention mise à jour");
      }
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  const canEdit = isNew ? hasPerm(user, "intervention", "create") : hasPerm(user, "intervention", "edit");

  return (
    <Layout title="Fiche d'intervention">
      <div className="a4-sheet max-w-4xl mx-auto p-8 sm:p-12 rounded-md">
        <DocumentHeader shop={shop} numero={data.numero || "(auto)"} />
        <h2 className="font-heading text-xl font-bold text-center mb-6">FICHE D'INTERVENTION</h2>
        <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
          <div><span className="font-semibold">Vendeur:</span> {data.vendeur_nom || `${user.prenom} ${user.nom}`}</div>
          <div><span className="font-semibold">Date:</span> {data.date || today}</div>
          <Input data-testid="int-client-nom" disabled={!canEdit} placeholder="Nom / prénom client" value={data.client_nom} onChange={(e) => setData({ ...data, client_nom: e.target.value })} />
          <Input data-testid="int-client-tel" disabled={!canEdit} placeholder="Téléphone client" value={data.client_tel} onChange={(e) => setData({ ...data, client_tel: e.target.value })} />
          <Input data-testid="int-client-email" disabled={!canEdit} placeholder="Email client" value={data.client_email} onChange={(e) => setData({ ...data, client_email: e.target.value })} />
          <Input data-testid="int-client-adresse" disabled={!canEdit} placeholder="Adresse client" value={data.client_adresse} onChange={(e) => setData({ ...data, client_adresse: e.target.value })} />
          <Input data-testid="int-materiel" disabled={!canEdit} placeholder="Matériel concerné" value={data.materiel} onChange={(e) => setData({ ...data, materiel: e.target.value })} />
          <Input data-testid="int-imei" disabled={!canEdit} placeholder="IMEI" value={data.imei} onChange={(e) => setData({ ...data, imei: e.target.value })} />
        </div>
        <label className="text-sm font-semibold">Motif de l'intervention</label>
        <Textarea data-testid="int-motif" disabled={!canEdit} className="mb-4 h-28" value={data.motif} onChange={(e) => setData({ ...data, motif: e.target.value })} />
        <label className="text-sm font-semibold">Intervention effectuée</label>
        <Textarea data-testid="int-effectuee" disabled={!canEdit} className="mb-6 h-28" value={data.intervention_effectuee} onChange={(e) => setData({ ...data, intervention_effectuee: e.target.value })} />
        <label className="text-sm font-semibold block mb-2">Signature client</label>
        <SignaturePad ref={sigRef} testId="intervention-signature-pad" />

        <div className="flex gap-3 mt-6 no-print">
          {canEdit && <Button data-testid="intervention-save-button" onClick={save} className="gap-2"><Save size={16} />Enregistrer</Button>}
          {!isNew && (
            <a href={`${api.defaults.baseURL}/interventions/${id}/pdf`} target="_blank" rel="noreferrer">
              <Button variant="outline" data-testid="intervention-pdf-button" className="gap-2"><Printer size={16} />PDF</Button>
            </a>
          )}
        </div>
      </div>
    </Layout>
  );
}
