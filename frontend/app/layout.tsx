import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Study Pal - AI Study Assistant",
  description: "Your intelligent multi-agent study companion",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-[#0a0a0a] text-[#ededed] antialiased">
        {children}
      </body>
    </html>
  );
}



