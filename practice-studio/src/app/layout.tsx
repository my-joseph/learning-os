import type { Metadata } from "next";
import localFont from "next/font/local";
// Learner font choice 2026-11-19: Source Sans Pro (text), Roboto Slab (display / secondary
// accent: scores, counters, timers, curriculum IDs), Geist Mono (code only), KaTeX (math).
import "@fontsource/source-sans-pro/400.css";
import "@fontsource/source-sans-pro/400-italic.css";
import "@fontsource/source-sans-pro/600.css";
import "@fontsource/source-sans-pro/700.css";
import "@fontsource-variable/roboto-slab";
import "./globals.css";
import { MotionProvider } from "@/components/motion/MotionProvider";
import { THEME_INIT_SCRIPT } from "@/lib/studioRules";

const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
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
      <body
        className={`${geistMono.variable} antialiased`}
      >
        <MotionProvider>{children}</MotionProvider>
      </body>
    </html>
  );
}
