import { useEffect, useState } from "react";
import { Store } from "lucide-react";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { Button } from "./ui/button";

export function ShopSelectorModal() {
  const { switchShop } = useAuth();
  const [shops, setShops] = useState([]);
  const [selected, setSelected] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get("/shops").then((r) => setShops(r.data.filter((s) => s.type === "boutique")));
  }, []);

  const confirm = async () => {
    if (!selected) return;
    setSubmitting(true);
    await switchShop(selected);
  };

  return (
    <div className="fixed inset-0 z-[100] bg-background/95 backdrop-blur-sm flex items-center justify-center p-4" data-testid="shop-selector-modal">
      <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-xl">
        <h2 className="font-heading text-xl font-bold mb-1">Choisir une boutique</h2>
        <p className="text-sm text-muted-foreground mb-5">
          Votre compte a accès à plusieurs boutiques. Sélectionnez celle avec laquelle vous souhaitez travailler.
        </p>
        <div className="space-y-2 mb-6 max-h-72 overflow-y-auto">
          {shops.map((s) => (
            <button
              key={s.id}
              data-testid={`shop-selector-option-${s.id}`}
              onClick={() => setSelected(s.id)}
              className={`w-full flex items-center gap-3 rounded-lg border p-3 text-left transition-colors duration-200 ${
                selected === s.id ? "border-primary bg-primary/10" : "border-border hover:border-primary/50"
              }`}
            >
              <Store size={16} className="text-primary shrink-0" />
              <span className="text-sm font-medium">{s.nom}</span>
            </button>
          ))}
          {shops.length === 0 && <p className="text-sm text-muted-foreground">Aucune boutique disponible.</p>}
        </div>
        <Button data-testid="shop-selector-confirm-button" className="w-full" disabled={!selected || submitting} onClick={confirm}>
          {submitting ? "Chargement..." : "Continuer"}
        </Button>
      </div>
    </div>
  );
}
