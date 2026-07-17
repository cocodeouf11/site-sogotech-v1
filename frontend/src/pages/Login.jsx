import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Delete } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { formatApiError } from "../lib/api";

export default function Login() {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const submit = async (fullPin) => {
    setLoading(true);
    setError("");
    try {
      await login(fullPin);
      navigate(location.state?.from || "/", { replace: true });
    } catch (e) {
      setError(formatApiError(e.response?.data?.detail) || "Code PIN incorrect");
      setPin("");
    } finally {
      setLoading(false);
    }
  };

  const press = (digit) => {
    if (loading) return;
    const next = (pin + digit).slice(0, 6);
    setPin(next);
    if (next.length === 6) submit(next);
  };

  const backspace = () => setPin((p) => p.slice(0, -1));

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <p className="font-heading text-3xl font-bold tracking-tight">SOGO Gestion</p>
          <p className="text-muted-foreground text-sm mt-1">Boutique &amp; Dépôt — Saisissez votre code PIN</p>
        </div>

        <div className="flex justify-center gap-3 mb-8" data-testid="pin-dots">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div
              key={i}
              className={`w-4 h-4 rounded-full border-2 border-primary transition-colors duration-200 ${
                i < pin.length ? "bg-primary" : "bg-transparent"
              }`}
            />
          ))}
        </div>

        {error && (
          <p className="text-center text-destructive text-sm mb-4" data-testid="login-error">
            {error}
          </p>
        )}

        <div className="grid grid-cols-3 gap-3">
          {["1", "2", "3", "4", "5", "6", "7", "8", "9"].map((d) => (
            <button
              key={d}
              data-testid={`pin-pad-button-${d}`}
              onClick={() => press(d)}
              disabled={loading}
              className="min-h-[72px] min-w-[72px] rounded-2xl border border-border bg-card text-3xl font-bold hover:bg-accent active:scale-95 transition-transform duration-150"
            >
              {d}
            </button>
          ))}
          <div />
          <button
            data-testid="pin-pad-button-0"
            onClick={() => press("0")}
            disabled={loading}
            className="min-h-[72px] min-w-[72px] rounded-2xl border border-border bg-card text-3xl font-bold hover:bg-accent active:scale-95 transition-transform duration-150"
          >
            0
          </button>
          <button
            data-testid="pin-pad-button-backspace"
            onClick={backspace}
            disabled={loading}
            className="min-h-[72px] min-w-[72px] rounded-2xl border border-border bg-card flex items-center justify-center hover:bg-accent active:scale-95 transition-transform duration-150"
          >
            <Delete size={24} />
          </button>
        </div>
      </div>
    </div>
  );
}
