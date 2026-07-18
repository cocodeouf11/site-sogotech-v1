import { Menu, Sun, Moon } from "lucide-react";
import { useTheme } from "../../context/ThemeContext";

export function Topbar({ title, onMenuClick }) {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-10 backdrop-blur-xl bg-background/80 border-b border-border px-4 sm:px-6 py-4 flex items-center justify-between gap-3 no-print">
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onMenuClick}
          data-testid="sidebar-menu-button"
          className="lg:hidden p-2 rounded-lg border border-border hover:bg-accent transition-colors duration-200 shrink-0"
          aria-label="Ouvrir le menu"
        >
          <Menu size={18} />
        </button>
        <h1 className="font-heading text-xl sm:text-2xl font-semibold tracking-tight truncate" data-testid="page-title">{title}</h1>
      </div>
      <button
        onClick={toggle}
        data-testid="theme-toggle-button"
        className="p-2.5 rounded-lg border border-border hover:bg-accent transition-colors duration-200 shrink-0"
        aria-label="Basculer le thème"
      >
        {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
      </button>
    </header>
  );
}
