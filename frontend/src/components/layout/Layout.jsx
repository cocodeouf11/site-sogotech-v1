import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function Layout({ title, children }) {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 min-w-0">
        <Topbar title={title} />
        <main className="p-6" data-testid="page-content">{children}</main>
      </div>
    </div>
  );
}
