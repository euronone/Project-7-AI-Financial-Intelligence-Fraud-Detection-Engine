import { lazy, Suspense } from "react";
import HeroSection from "@/components/landing/HeroSection";
import ProjectGuideSection from "@/components/landing/ProjectGuideSection";
import HowItWorksSection from "@/components/landing/HowItWorksSection";
import FeaturesSection from "@/components/landing/FeaturesSection";
import PricingSection from "@/components/landing/PricingSection";
import ArchitectureSection from "@/components/landing/ArchitectureSection";
import FraudLogicSection from "@/components/landing/FraudLogicSection";
import SecuritySection from "@/components/landing/SecuritySection";
import PrivacySection from "@/components/landing/PrivacySection";
import CTASection from "@/components/landing/CTASection";

// Lazy load non-critical sections for better performance
const LazyTestimonialsSection = lazy(() => import("@/components/landing/TestimonialsSection"));

function SectionLoader() {
  return (
    <div className="py-24 px-6 bg-[#0A0A0F] min-h-[400px]">
      <div className="max-w-7xl mx-auto animate-pulse space-y-4">
        <div className="h-10 bg-[#111118] rounded-xl w-3/4" />
        <div className="h-6 bg-[#111118] rounded-xl w-1/2" />
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <main className="bg-[#0A0A0F] min-h-screen">
      <HeroSection />
      <ProjectGuideSection />
      <HowItWorksSection />
      <FeaturesSection />
      <PricingSection />
      <ArchitectureSection />
      <FraudLogicSection />
      <SecuritySection />
      <PrivacySection />
      <Suspense fallback={<SectionLoader />}>
        <LazyTestimonialsSection />
      </Suspense>
      <CTASection />
    </main>
  );
}
