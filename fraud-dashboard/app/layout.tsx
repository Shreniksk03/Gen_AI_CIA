import type { Metadata } from 'next';
import CanvasWrapper from '@/components/CanvasWrapper';
import './globals.css';

export const metadata: Metadata = {
  title: 'Fraud Sentinel — AI Financial Fraud Detection & Investigation Platform',
  description:
    'Enterprise-grade machine learning platform for real-time transaction risk scoring and Explainable AI (SHAP) fraud investigation.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full scroll-smooth">
      <body className="min-h-screen w-full bg-[#03050B] text-slate-100 antialiased relative selection:bg-cyan-500/30 selection:text-cyan-200 font-sans">
        {/* Environmental 3D Three.js Agent Node Network Canvas (strictly background & non-blocking) */}
        <CanvasWrapper />

        {/* Atmospheric Volumetric Lighting Glow Orbs */}
        <div className="fixed inset-0 pointer-events-none overflow-hidden -z-10" aria-hidden="true">
          <div className="orb-glow w-[550px] h-[550px] -top-32 -left-32 bg-cyan-600/10 blur-[150px] animate-glow-pulse" />
          <div
            className="orb-glow w-[500px] h-[500px] top-1/4 -right-24 bg-amber-500/8 blur-[160px] animate-glow-pulse"
            style={{ animationDelay: '-3s' }}
          />
          <div
            className="orb-glow w-[650px] h-[650px] -bottom-48 left-1/3 bg-indigo-600/8 blur-[180px] animate-glow-pulse"
            style={{ animationDelay: '-5s' }}
          />
        </div>

        {/* Subtle cinematic vignette */}
        <div className="vignette-overlay" aria-hidden="true" />

        {/* Main application container */}
        <div className="relative z-10 min-h-screen w-full flex flex-col">
          {children}
        </div>
      </body>
    </html>
  );
}
