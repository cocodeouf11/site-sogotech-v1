import { Navigate } from "react-router-dom";
import { useAuth, hasPerm } from "../context/AuthContext";

export function ProtectedRoute({ children, adminOnly = false, requirePermission = null }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center text-muted-foreground">Chargement...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && !user.is_admin) return <Navigate to="/" replace />;
  if (requirePermission && !hasPerm(user, requirePermission)) return <Navigate to="/" replace />;
  return children;
}

