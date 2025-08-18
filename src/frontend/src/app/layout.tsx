import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";

export const metadata: Metadata = {
  title: "Math Solver",
  description: "Solve math using LLM by text or image with step-by-step explanations."
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Header />
        <div className="container">{children}</div>
      </body>
    </html>
  );
}
