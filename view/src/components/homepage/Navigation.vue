<template>
  <nav class="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
    <!-- Company Logo -->
    <div class="flex items-center">
      <router-link to="/" class="font-bold text-xl">Myriade</router-link>
    </div>

    <!-- Main Navigation Links - Only essential links as per structure -->
    <div class="hidden md:flex space-x-8">
      <a href="#features" class="text-gray-700 hover:text-gray-900 font-medium">Features</a>
      <a href="#pricing" class="text-gray-700 hover:text-gray-900 font-medium">Pricing</a>
      <a href="#about" class="text-gray-700 hover:text-gray-900 font-medium">About</a>
      <a href="#contact" class="text-gray-700 hover:text-gray-900 font-medium">Contact</a>
    </div>

    <!-- CTA Buttons in Navigation -->
    <div class="flex space-x-3">
      <a
        href="#signup"
        class="bg-black text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-800 transition-colors"
        >Sign up</a
      >
      <router-link
        to="/login"
        class="border border-gray-300 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
        >Login</router-link
      >
    </div>
  </nav>
</template>

<script setup>
// Simplified navigation with only essential links and a prominent CTA
</script>
