import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AuditFlow AI",
  description: "Recurring audit committee deck refresh workflow",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

