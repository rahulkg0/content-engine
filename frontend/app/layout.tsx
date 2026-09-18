import "./globals.css";
import Navbar from "@/components/Navbar";

export const metadata = {
  title: "AI Content Engine | Phase 1 Automation Platform",
  description: "CSV-driven multi-agent AI content generation system publishing directly to Strapi CMS.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-slate-950 text-slate-100 flex flex-col antialiased">
        <Navbar />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-800 py-6 text-center text-xs text-slate-500">
          Content Engine &copy; 2026 — Production-grade CSV-driven AI Content Automation System
        </footer>
      </body>
    </html>
  );
}
