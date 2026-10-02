import type { Metadata, Viewport } from "next";
import { ServiceWorkerRegister } from "@/components/service-worker-register";
import "./globals.css";

export const metadata: Metadata = {
  title: "Flowstate — Plan with clarity",
  description: "A calmer workspace for tasks, teams, and focused progress.",
};

export const viewport: Viewport = {
  themeColor: "#182a22",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><ServiceWorkerRegister />{children}</body>
    </html>
  );
}
