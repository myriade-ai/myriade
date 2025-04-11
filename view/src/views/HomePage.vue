<template>
  <MainLayout>
    <!-- Navigation with Logo and Essential Links -->
    <Navigation />

    <!-- Hero Section with Clear Heading, Subheading, and CTA -->
    <HeroSection />

    <!-- Social Proof Section - Company Logos -->
    <SocialProof />

    <!-- Benefits Section -->
    <Benefits />

    <!-- Examples Grid Section - showing use cases -->
    <section id="examples" class="max-w-5xl mx-auto px-4 py-12 pb-16">
      <h2 class="text-3xl sm:text-4xl font-semibold mb-8 text-center">
        What you can do with Myriade
      </h2>
      <ExamplesGrid />
    </section>

    <!-- How It Works Section - Breaking down functionality -->
    <HowItWorks />

    <!-- Testimonials Section - Social Proof -->
    <Testimonials />

    <!-- FAQ Section - Simple answers to common questions -->
    <FAQ />

    <!-- Final CTA Section - Action-oriented conversion element -->
    <FinalCTA />

    <!-- Footer -->
    <Footer />
  </MainLayout>
</template>

<script setup>
import Benefits from '@/components/homepage/Benefits.vue'
import ExamplesGrid from '@/components/homepage/ExamplesGrid.vue'
import FAQ from '@/components/homepage/FAQ.vue'
import FinalCTA from '@/components/homepage/FinalCTA.vue'
import Footer from '@/components/homepage/Footer.vue'
import HeroSection from '@/components/homepage/HeroSection.vue'
import HowItWorks from '@/components/homepage/HowItWorks.vue'
import MainLayout from '@/components/homepage/MainLayout.vue'
import Navigation from '@/components/homepage/Navigation.vue'
import SocialProof from '@/components/homepage/SocialProof.vue'
import Testimonials from '@/components/homepage/Testimonials.vue'
</script>
