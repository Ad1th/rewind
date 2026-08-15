import React from "react";
import "./globals.css";

export const metadata = {
  title: "REWIND — Ctrl+Z for AI Agents",
  description: "Intercept, verify, and deterministically reverse AI agent actions.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  );
}
