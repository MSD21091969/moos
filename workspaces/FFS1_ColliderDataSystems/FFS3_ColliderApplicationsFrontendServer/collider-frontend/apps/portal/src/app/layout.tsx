import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Collider Portal",
  description: "Multi-agent application platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-gray-100 min-h-screen antialiased">
        <header className="border-b border-gray-800 px-6 py-3">
          <div className="flex items-center justify-between max-w-6xl mx-auto">
            <h1 className="text-xl font-bold">Collider</h1>
            <nav className="flex gap-4 text-sm text-gray-400">
              <a href="/" className="hover:text-gray-100">
                Applications
              </a>
            </nav>
          </div>
        </header>
        <main className="max-w-6xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
