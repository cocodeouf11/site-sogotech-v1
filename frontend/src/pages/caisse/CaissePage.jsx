import { useEffect, useState } from "react";
import { Layout } from "../../components/layout/Layout";
import { api, UPLOADS_BASE, formatApiError } from "../../lib/api";
import { useAuth, hasPerm } from "../../context/AuthContext";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Trash2, Plus, Minus, Printer, FileDown } from "lucide-react";
import { toast } from "sonner";

export default function CaissePage() {
  const { user } = useAuth();
  const [articles, setArticles] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [cart, setCart] = useState([]);
  const [prestationName, setPrestationName] = useState("");
  const [prestationPrice, setPrestationPrice] = useState("");
  const [tva, setTva] = useState(20);
  const [docType, setDocType] = useState("ticket");
  const [clientInfo, setClientInfo] = useState({ nom: "", adresse: "", email: "" });

  const load = async () => {
    const [a, t] = await Promise.all([api.get("/stock"), api.get("/caisse")]);
    setArticles(a.data);
    setTickets(t.data.slice(0, 15));
  };
  useEffect(() => { load(); }, []);

  const addArticle = (article) => {
    setCart((c) => {
      const existing = c.find((i) => i.article_id === article.id);
      if (existing) return c.map((i) => (i.article_id === article.id ? { ...i, quantite: i.quantite + 1 } : i));
      return [...c, { type: "article", article_id: article.id, nom: article.nom, prix_unitaire: article.prix || 0, quantite: 1 }];
    });
  };

  const addPrestation = () => {
    if (!prestationName || !prestationPrice) return;
    setCart((c) => [...c, { type: "prestation", nom: prestationName, prix_unitaire: Number(prestationPrice), quantite: 1 }]);
    setPrestationName(""); setPrestationPrice("");
  };

  const updateQty = (idx, delta) => {
    setCart((c) => c.map((item, i) => (i === idx ? { ...item, quantite: Math.max(1, item.quantite + delta) } : item)));
  };

  const removeItem = (idx) => setCart((c) => c.filter((_, i) => i !== idx));

  const ht = cart.reduce((s, i) => s + i.prix_unitaire * i.quantite, 0);
  const tvaAmount = (ht * tva) / 100;
  const ttc = ht + tvaAmount;

  const shopId = user?.shop_id;

  const validate = async () => {
    if (cart.length === 0) return;
    try {
      const { data } = await api.post("/caisse", {
        type: docType,
        shop_id: shopId,
        items: cart,
        tva_percent: tva,
        client_info: docType === "facture" ? clientInfo : null,
      });
      toast.success(`${docType === "facture" ? "Facture" : "Ticket"} ${data.numero} créé`);
      setCart([]);
      load();
      window.open(`${api.defaults.baseURL}/caisse/${data.id}/pdf`, "_blank");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    }
  };

  return (
    <Layout title="Caisse">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-3 mb-6" data-testid="caisse-article-grid">
            {articles.map((a) => (
              <button
                key={a.id}
                data-testid={`caisse-article-${a.id}`}
                onClick={() => addArticle(a)}
                className="aspect-square rounded-xl border border-border bg-card p-2 flex flex-col hover:border-primary transition-colors duration-200"
              >
                <div className="flex-1 rounded-md bg-secondary overflow-hidden flex items-center justify-center mb-1">
                  {a.photo_url ? <img src={`${UPLOADS_BASE}${a.photo_url}`} className="w-full h-full object-cover" /> : <span className="text-xs text-muted-foreground">Photo</span>}
                </div>
                <p className="text-xs font-medium truncate">{a.nom}</p>
                <p className="text-xs text-muted-foreground">{(a.prix || 0).toFixed(2)} €</p>
              </button>
            ))}
          </div>

          <div className="rounded-xl border border-border bg-card p-4">
            <p className="font-heading font-semibold mb-3">Prestation libre</p>
            <div className="flex gap-2">
              <Input data-testid="prestation-name-input" placeholder="Nom de la prestation" value={prestationName} onChange={(e) => setPrestationName(e.target.value)} />
              <Input data-testid="prestation-price-input" type="number" placeholder="Prix €" value={prestationPrice} onChange={(e) => setPrestationPrice(e.target.value)} className="w-32" />
              <Button data-testid="prestation-add-button" onClick={addPrestation}><Plus size={16} /></Button>
            </div>
          </div>

          <div className="mt-6">
            <p className="font-heading font-semibold mb-3">Historique récent</p>
            <div className="space-y-1" data-testid="caisse-history-list">
              {tickets.map((t) => (
                <div key={t.id} className="flex justify-between items-center text-sm py-2 px-3 rounded-lg border border-border bg-card">
                  <span data-testid={`history-numero-${t.id}`}>{t.numero} — {t.type}</span>
                  <span>{t.total_ttc?.toFixed(2)} €</span>
                  <a href={`${api.defaults.baseURL}/caisse/${t.id}/pdf`} target="_blank" rel="noreferrer" data-testid={`history-pdf-${t.id}`}>
                    <FileDown size={16} className="text-primary" />
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5 h-fit sticky top-24">
          <div className="flex gap-2 mb-4">
            <Button variant={docType === "ticket" ? "default" : "outline"} size="sm" data-testid="doctype-ticket" onClick={() => setDocType("ticket")}>Ticket</Button>
            <Button variant={docType === "facture" ? "default" : "outline"} size="sm" data-testid="doctype-facture" onClick={() => setDocType("facture")}>Facture</Button>
          </div>

          {docType === "facture" && (
            <div className="space-y-2 mb-4">
              <Input data-testid="facture-client-nom" placeholder="Nom du client" value={clientInfo.nom} onChange={(e) => setClientInfo({ ...clientInfo, nom: e.target.value })} />
              <Input data-testid="facture-client-adresse" placeholder="Adresse" value={clientInfo.adresse} onChange={(e) => setClientInfo({ ...clientInfo, adresse: e.target.value })} />
              <Input data-testid="facture-client-email" placeholder="Email" value={clientInfo.email} onChange={(e) => setClientInfo({ ...clientInfo, email: e.target.value })} />
            </div>
          )}

          <div className="space-y-2 mb-4 max-h-64 overflow-y-auto" data-testid="cart-list">
            {cart.length === 0 && <p className="text-sm text-muted-foreground">Panier vide</p>}
            {cart.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm border-b border-border pb-2">
                <div className="flex-1 truncate">{item.nom}</div>
                <div className="flex items-center gap-1">
                  <button onClick={() => updateQty(idx, -1)} data-testid={`cart-item-minus-${idx}`}><Minus size={13} /></button>
                  <span className="w-6 text-center">{item.quantite}</span>
                  <button onClick={() => updateQty(idx, 1)} data-testid={`cart-item-plus-${idx}`}><Plus size={13} /></button>
                  <button onClick={() => removeItem(idx)} className="text-destructive ml-1" data-testid={`cart-item-remove-${idx}`}><Trash2 size={13} /></button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-2 mb-3">
            <label className="text-sm text-muted-foreground">TVA %</label>
            <Input data-testid="tva-input" type="number" value={tva} onChange={(e) => setTva(Number(e.target.value))} className="w-20" />
          </div>

          <div className="text-sm space-y-1 mb-4">
            <div className="flex justify-between"><span>Total HT</span><span data-testid="cart-total-ht">{ht.toFixed(2)} €</span></div>
            <div className="flex justify-between"><span>TVA</span><span data-testid="cart-total-tva">{tvaAmount.toFixed(2)} €</span></div>
            <div className="flex justify-between font-heading font-bold text-lg"><span>Total TTC</span><span data-testid="cart-total-ttc">{ttc.toFixed(2)} €</span></div>
          </div>

          <Button data-testid="validate-sale-button" className="w-full gap-2" onClick={validate}>
            <Printer size={16} /> Valider &amp; Imprimer
          </Button>
        </div>
      </div>
    </Layout>
  );
}
