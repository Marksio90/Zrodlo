import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { PwaRegister } from "@/components/PwaRegister";
import { PwaOfflineBar } from "@/components/PwaOfflineBar";

const inter = Inter({ subsets: ["latin", "latin-ext"] });

export const metadata: Metadata = {
  title: "Źródło – System Parafialny",
  description: "Inteligentny system wspierający pracę parafii",
  applicationName: "Źródło",
  appleWebApp: {
    capable: true,
    title: "Źródło",
    statusBarStyle: "default",
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: "/icons/icon.svg",
    apple: "/icons/icon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#2563eb",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl">
      <body className={inter.className}>
        <PwaOfflineBar />
        <Providers>{children}</Providers>
        <PwaRegister />
      </body>
    </html>
  );
}
