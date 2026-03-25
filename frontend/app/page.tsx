import HeroSection from "@/components/landing/HeroSection";
import ProjectGuideSection from "@/components/landing/ProjectGuideSection";
import HowItWorksSection from "@/components/landing/HowItWorksSection";
import FeaturesSection from "@/components/landing/FeaturesSection";
import PricingSection from "@/components/landing/PricingSection";
import ArchitectureSection from "@/components/landing/ArchitectureSection";
import FraudLogicSection from "@/components/landing/FraudLogicSection";
import SecuritySection from "@/components/landing/SecuritySection";
import TestimonialsSection from "@/components/landing/TestimonialsSection";
import CTASection from "@/components/landing/CTASection";

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
      <TestimonialsSection />
      <CTASection />
    </main>
  );
}
