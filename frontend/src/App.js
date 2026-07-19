import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";
import StockPage from "@/pages/stock/StockPage";
import CaissePage from "@/pages/caisse/CaissePage";
import InterventionListPage from "@/pages/intervention/InterventionListPage";
import InterventionFormPage from "@/pages/intervention/InterventionFormPage";
import DevisListPage from "@/pages/devis/DevisListPage";
import DevisFormPage from "@/pages/devis/DevisFormPage";
import RepriseListPage from "@/pages/reprise/RepriseListPage";
import RepriseFormPage from "@/pages/reprise/RepriseFormPage";
import MessagesPage from "@/pages/communication/MessagesPage";
import HelpTicketsPage from "@/pages/communication/HelpTicketsPage";
import DepotOrdersPage from "@/pages/depot/DepotOrdersPage";
import DepotOrderDetailPage from "@/pages/depot/DepotOrderDetailPage";
import DepotLabelPage from "@/pages/depot/DepotLabelPage";
import CommandeListPage from "@/pages/commande/CommandeListPage";
import CommandeDetailPage from "@/pages/commande/CommandeDetailPage";
import UsersPage from "@/pages/admin/UsersPage";
import ShopSettingsPage from "@/pages/admin/ShopSettingsPage";

function App() {
  return (
    <div className="App">
      <ThemeProvider>
        <BrowserRouter>
          <AuthProvider>
            <Toaster position="top-right" />
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/stock" element={<ProtectedRoute><StockPage /></ProtectedRoute>} />
              <Route path="/caisse" element={<ProtectedRoute><CaissePage /></ProtectedRoute>} />
              <Route path="/interventions" element={<ProtectedRoute><InterventionListPage /></ProtectedRoute>} />
              <Route path="/interventions/:id" element={<ProtectedRoute><InterventionFormPage /></ProtectedRoute>} />
              <Route path="/devis" element={<ProtectedRoute><DevisListPage /></ProtectedRoute>} />
              <Route path="/devis/:id" element={<ProtectedRoute><DevisFormPage /></ProtectedRoute>} />
              <Route path="/reprises" element={<ProtectedRoute><RepriseListPage /></ProtectedRoute>} />
              <Route path="/reprises/:id" element={<ProtectedRoute><RepriseFormPage /></ProtectedRoute>} />
              <Route path="/communication" element={<ProtectedRoute><MessagesPage /></ProtectedRoute>} />
              <Route path="/communication/tickets" element={<ProtectedRoute><HelpTicketsPage /></ProtectedRoute>} />
              <Route path="/depot" element={<ProtectedRoute requirePermission="depot"><DepotOrdersPage /></ProtectedRoute>} />
              <Route path="/depot/etiquette" element={<ProtectedRoute requirePermission="depot"><DepotLabelPage /></ProtectedRoute>} />
              <Route path="/depot/:id" element={<ProtectedRoute requirePermission="depot"><DepotOrderDetailPage /></ProtectedRoute>} />
              <Route path="/commandes" element={<ProtectedRoute><CommandeListPage /></ProtectedRoute>} />
              <Route path="/commandes/:id" element={<ProtectedRoute><CommandeDetailPage /></ProtectedRoute>} />
              <Route path="/admin/users" element={<ProtectedRoute adminOnly><UsersPage /></ProtectedRoute>} />
              <Route path="/admin/shops" element={<ProtectedRoute adminOnly><ShopSettingsPage /></ProtectedRoute>} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </ThemeProvider>
    </div>
  );
}

export default App;
