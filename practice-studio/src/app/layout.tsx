import type { Metadata } from "next";
import localFont from "next/font/local";
// Learner font choice 2026-11-22: Geist / Geist Fallback (font-sans), Roboto Slab (display /
// secondary accent: scores, counters, timers, curriculum IDs), Geist Mono (code only), KaTeX (math).
import "@fontsource-variable/roboto-slab";
import "katex/dist/katex.min.css";
import "./globals.css";
import { MotionProvider } from "@/components/motion/MotionProvider";
import { THEME_INIT_SCRIPT } from "@/lib/studioRules";

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
  fallback: ["Geist Fallback", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
});

export const metadata: Metadata = {
  title: "Practice Studio",
  description: "LearningOS practice drills",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: THEME_INIT_SCRIPT,
          }}
        />
      </head>
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <MotionProvider>{children}</MotionProvider>
      </body>
    </html>
  );
}
