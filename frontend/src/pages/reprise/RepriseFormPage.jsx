import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Layout } from "../../components/layout/Layout";
import { DocumentHeader } from "../../components/DocumentHeader";
import { SignaturePad } from "../../components/SignaturePad";
import { PhoneDiagram } from "../../components/PhoneDiagram";
import { Input } from "../../components/ui/input";
import { Textarea } from "../../components/ui/textarea";
import { Button } from "../../components/ui/button";
import { Checkbox } from "../../components/ui/checkbox";
import { api, formatApiError } from "../../lib/api";
import { useAuth, hasPerm } from "../../context/AuthContext";
import { toast } from "sonner";
import { Printer, Save } from "lucide-react";

const ETAT_OPTIONS = [
  { key: "fonctionnel", label: "Fonctionnel" },
  { key: "deconnexion_google_icloud", label: "Déconnexion Google / iCloud" },
  { key: "debloque_operateur", label: "Débloqué tout opérateur" },
];

const TEST_OPTIONS = [
  { key: "reseau", label: "Réseau (SIM + appel)" },
  { key: "camera_avant", label: "Appareil photo avant" },
  { key: "camera_arriere", label: "Appareil photo arrière (zoom + focus)" },
  { key: "flash", label: "Flash" },
  { key: "micro", label: "Micro" },
  { key: "haut_parleur", label: "Haut-parleur" },
  { key: "boutons_volume", label: "Boutons volume" },
  { key: "bouton_power", label: "Bouton power" },
  { key: "charge_batterie", label: "Charge / batterie" },
  { key: "bouton_mute", label: "Bouton mute (iPhone)" },
  { key: "face_touch_id", label: "Face ID / Touch ID (iPhone)" },
];

const DISCLAIMER = "Le vendeur déclare être le propriétaire du produit repris et certifie l'avoir acquis de manière légale. Il autorise la boutique à revendre, réparer, recycler ou détruire le produit à sa discrétion. En cas de blocage ultérieur du produit (compte, mot de passe, opérateur), le vendeur s'engage à débloquer immédiatement le produit ou à rembourser intégralement la somme perçue lors de la reprise.";

export default function RepriseFormPage() {
  const { id } = useParams();
  const isNew = id === "new";
  const navigate = useNavigate();
  const { user } = useAuth();
  const sigRef = useRef(null);
  const [shop, setShop] = useState(null);
  const [data, setData] = useState({
    numero: "", client_nom: "", client_tel: "", client_email: "", client_adresse: "",
    modele: "", capacite: "", imei: "", etat_produit: {}, tests: {}, batterie_pourcentage: "",
    remarques: "", defauts_marks: [], piece_a_remplacer: "", offre_rachat: 0, bon_pour_accord: false,
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
        const { data: item } = await api.get(`/reprises/${id}`);
        setData(item);
      }
    })();
  }, [id]);

  const today = new Date().toLocaleDateString("fr-FR");
  const canEdit = isNew ? hasPerm(user, "reprise", "create") : hasPerm(user, "reprise", "edit");

  const toggleEtat = (key) => setData({ ...data, etat_produit: { ...data.etat_produit, [key]: !data.etat_produit[key] } });
  const toggleTest = (key) => setData({ ...data, tests: { ...data.tests, [key]: !data.tests[key] } });
  const addMark = (mark) => setData({ ...data, defauts_marks: [...data.defauts_marks, mark] });

  const save = async () => {
    const signature_data = sigRef.current?.toDataURL() || data.signature_data || "";
    if (isNew && !shop) {
      toast.error("Impossible de créer : aucune boutique assignée à votre compte.");
      return;
    }
    const payload = {
      ...data,
      signature_data,
      batterie_pourcentage: data.batterie_pourcentage === "" || data.batterie_pourcentage === null ? null : Number(data.batterie_pourcentage),
      offre_rachat: data.offre_rachat === "" || data.offre_rachat === null || Number.isNaN(Number(data.offre_rachat)) ? 0 : Number(data.offre_rachat),
    };
    try {
      if (isNew) {
        const { data: created } = await api.post("/reprises", { ...payload, shop_id: shop.id });
        toast.success(`Reprise ${created.numero} créée`);
        navigate(`/reprises/${created.id}`);
      } else {
        await api.patch(`/reprises/${id}`, payload);
        toast.success("Reprise mise à jour");
      }
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <Layout title="Fiche de reprise téléphone">
      <div className="a4-sheet max-w-4xl mx-auto p-8 sm:p-12 rounded-md">
        <DocumentHeader shop={shop} numero={data.numero || "(auto)"} />
        <h2 className="font-heading text-xl font-bold text-center mb-6">FICHE DE REPRISE TÉLÉPHONE</h2>

        <div className="grid grid-cols-2 gap-4 mb-6 text-sm">
          <div><span className="font-semibold">Vendeur:</span> {data.vendeur_nom || `${user.prenom} ${user.nom}`}</div>
          <div><span className="font-semibold">Date:</span> {data.date || today}</div>
          <Input data-testid="rep-client-nom" disabled={!canEdit} placeholder="Nom client" value={data.client_nom} onChange={(e) => setData({ ...data, client_nom: e.target.value })} />
          <Input data-testid="rep-client-tel" disabled={!canEdit} placeholder="Téléphone" value={data.client_tel} onChange={(e) => setData({ ...data, client_tel: e.target.value })} />
          <Input data-testid="rep-client-email" disabled={!canEdit} placeholder="Email" value={data.client_email} onChange={(e) => setData({ ...data, client_email: e.target.value })} />
          <Input data-testid="rep-client-adresse" disabled={!canEdit} placeholder="Adresse" value={data.client_adresse} onChange={(e) => setData({ ...data, client_adresse: e.target.value })} />
          <Input data-testid="rep-modele" disabled={!canEdit} placeholder="Modèle téléphone" value={data.modele} onChange={(e) => setData({ ...data, modele: e.target.value })} />
          <Input data-testid="rep-capacite" disabled={!canEdit} placeholder="Capacité" value={data.capacite} onChange={(e) => setData({ ...data, capacite: e.target.value })} />
          <Input data-testid="rep-imei" disabled={!canEdit} placeholder="IMEI" value={data.imei} onChange={(e) => setData({ ...data, imei: e.target.value })} />
        </div>

        <p className="font-semibold text-sm mb-2">État du produit</p>
        <div className="flex flex-wrap gap-4 mb-5">
          {ETAT_OPTIONS.map((o) => (
            <label key={o.key} className="flex items-center gap-2 text-sm">
              <Checkbox data-testid={`rep-etat-${o.key}`} disabled={!canEdit} checked={!!data.etat_produit[o.key]} onCheckedChange={() => toggleEtat(o.key)} />
              {o.label}
            </label>
          ))}
        </div>

        <p className="font-semibold text-sm mb-2">Tests à effectuer</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
          {TEST_OPTIONS.map((o) => (
            <label key={o.key} className="flex items-center gap-2 text-sm">
              <Checkbox data-testid={`rep-test-${o.key}`} disabled={!canEdit} checked={!!data.tests[o.key]} onCheckedChange={() => toggleTest(o.key)} />
              {o.label}
            </label>
          ))}
        </div>
        <Input data-testid="rep-batterie" disabled={!canEdit} type="number" placeholder="Batterie %" className="w-32 mb-6" value={data.batterie_pourcentage} onChange={(e) => setData({ ...data, batterie_pourcentage: e.target.value })} />

        <p className="font-semibold text-sm mb-2">Schéma - cliquez pour marquer un défaut</p>
        <div className="flex gap-8 justify-center mb-6">
          <div>
            <p className="text-xs text-center mb-1 text-muted-foreground">Avant</p>
            <PhoneDiagram marks={data.defauts_marks} onAdd={canEdit ? addMark : () => {}} face="avant" />
          </div>
          <div>
            <p className="text-xs text-center mb-1 text-muted-foreground">Arrière</p>
            <PhoneDiagram marks={data.defauts_marks} onAdd={canEdit ? addMark : () => {}} face="arriere" />
          </div>
        </div>

        <label className="text-sm font-semibold">Remarques</label>
        <Textarea data-testid="rep-remarques" disabled={!canEdit} className="mb-4 h-24" value={data.remarques} onChange={(e) => setData({ ...data, remarques: e.target.value })} />

        <div className="grid grid-cols-2 gap-4 mb-6">
          <Input data-testid="rep-piece" disabled={!canEdit} placeholder="Pièce à remplacer" value={data.piece_a_remplacer} onChange={(e) => setData({ ...data, piece_a_remplacer: e.target.value })} />
          <Input data-testid="rep-offre" disabled={!canEdit} type="number" placeholder="Offre de rachat (€)" value={data.offre_rachat} onChange={(e) => setData({ ...data, offre_rachat: Number(e.target.value) })} />
        </div>

        <p className="text-xs text-muted-foreground mb-4">{DISCLAIMER}</p>

        <div className="flex items-center gap-3 mb-3">
          <label className="flex items-center gap-2 text-sm font-semibold">
            <Checkbox data-testid="rep-bon-accord" disabled={!canEdit} checked={data.bon_pour_accord} onCheckedChange={(v) => setData({ ...data, bon_pour_accord: !!v })} />
            Bon pour accord
          </label>
        </div>
        <label className="text-sm font-semibold block mb-2">Signature</label>
        <SignaturePad ref={sigRef} testId="reprise-signature-pad" />

        <div className="flex gap-3 mt-6 no-print">
          {canEdit && <Button data-testid="reprise-save-button" onClick={save} className="gap-2"><Save size={16} />Enregistrer</Button>}
          {!isNew && (
            <a href={`${api.defaults.baseURL}/reprises/${id}/pdf`} target="_blank" rel="noreferrer">
              <Button variant="outline" data-testid="reprise-pdf-button" className="gap-2"><Printer size={16} />PDF</Button>
            </a>
          )}
        </div>
      </div>
    </Layout>
  );
}
