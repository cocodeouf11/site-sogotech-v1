import { Sun, Moon } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

export function Topbar({ title }) {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-10 backdrop-blur-xl bg-background/80 border-b border-border px-6 py-4 flex items-center justify-between no-print">
      <h1 className="font-heading text-2xl font-semibold tracking-tight" data-testid="page-title">{title}</h1>
      <button
        onClick={toggle}
        data-testid="theme-toggle-button"
        className="p-2.5 rounded-lg border border-border hover:bg-accent transition-colors duration-200"
        aria-label="Basculer le thème"
      >
        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
      </button>
    </header>
  );
}
