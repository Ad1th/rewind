import React from "react";

export const metadata = {
  title: "REWIND — Ctrl+Z for AI Agents",
  description: "Transactional Execution Runtime & Time Machine Interface for Autonomous AI Agents",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, backgroundColor: "#090D16", color: "#F9FAFB", fontFamily: "system-ui, sans-serif" }}>
        {children}
      </body>
    </html>
  );
}
