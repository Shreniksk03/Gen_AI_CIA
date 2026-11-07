'use client';

import LandingNavbar from '@/components/landing/LandingNavbar';
import HeroSection from '@/components/landing/HeroSection';
import ProductOverview from '@/components/landing/ProductOverview';
import WorkflowSection from '@/components/landing/WorkflowSection';
import CapabilitiesSection from '@/components/landing/CapabilitiesSection';
import TechnologySection from '@/components/landing/TechnologySection';
import LandingFooter from '@/components/landing/LandingFooter';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-transparent text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
      <LandingNavbar />
      <main className="flex-1">
        <HeroSection />
        <ProductOverview />
        <WorkflowSection />
        <CapabilitiesSection />
        <TechnologySection />
      </main>
      <LandingFooter />
    </div>
  );
}
