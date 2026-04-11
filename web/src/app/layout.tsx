import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Traffic Predictor — Ho Chi Minh City",
  description:
    "Real-time traffic monitoring and transformer-based speed forecasting for Ho Chi Minh City.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full">
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          crossOrigin=""
        />
      </head>
      <body className="h-full bg-zinc-950 text-zinc-50">{children}</body>
    </html>
  );
}
