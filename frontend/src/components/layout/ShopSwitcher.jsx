import { useEffect, useState } from "react";
import { ChevronDown, Store } from "lucide-react";
import { api } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import {
  DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem,
} from "../ui/dropdown-menu";

export function ShopSwitcher() {
  const { user, switchShop } = useAuth();
  const [shops, setShops] = useState([]);

  useEffect(() => {
    if (!user?.is_multi_shop_user) return;
    api.get("/shops").then((r) => setShops(r.data.filter((s) => s.type === "boutique")));
  }, [user]);

  if (!user?.is_multi_shop_user) return null;

  const currentShop = shops.find((s) => s.id === user.effective_shop_id);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          data-testid="shop-switcher-button"
          className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border hover:bg-accent transition-colors duration-200 text-sm font-medium shrink-0 max-w-[160px] sm:max-w-none"
        >
          <Store size={14} className="text-primary shrink-0" />
          <span className="truncate">{currentShop?.nom || "Choisir une boutique"}</span>
          <ChevronDown size={14} className="shrink-0" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" data-testid="shop-switcher-menu">
        {shops.map((s) => (
          <DropdownMenuItem
            key={s.id}
            data-testid={`shop-switcher-option-${s.id}`}
            onClick={() => s.id !== user.effective_shop_id && switchShop(s.id)}
            className={s.id === user.effective_shop_id ? "font-semibold text-primary" : ""}
          >
            {s.nom}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
