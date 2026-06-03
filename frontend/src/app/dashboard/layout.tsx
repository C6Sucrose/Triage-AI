import Link from "next/link";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-slate-50/50">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col">
        <div className="flex h-14 items-center px-6 border-b border-slate-200">
          <span className="font-semibold text-sm">⚡ Triage AI</span>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <Link
            href="/dashboard"
            className="flex items-center px-3 py-2 text-sm font-medium rounded-md bg-slate-100 text-slate-900"
          >
            Ticket Board
          </Link>
          <Link
            href="/dashboard/knowledge"
            className="flex items-center px-3 py-2 text-sm font-medium rounded-md text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          >
            Knowledge Base
          </Link>
        </nav>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        <header className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between">
          <span className="text-sm text-slate-500">Credits: 10</span>
        </header>

        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}