import { useState } from "react";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { ShopSelectorModal } from "../ShopSelectorModal";
import { useAuth } from "../../context/AuthContext";

export function Layout({ title, children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user } = useAuth();
  const needsShopSelection = user?.is_multi_shop_user && !user?.effective_shop_id;

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="flex-1 min-w-0">
        <Topbar title={title} onMenuClick={() => setSidebarOpen(true)} />
        <main className="p-4 sm:p-6" data-testid="page-content">{children}</main>
      </div>
      {needsShopSelection && <ShopSelectorModal />}
    </div>
  );
}
