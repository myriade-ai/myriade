<template>
  <nav class="fixed top-0 left-0 w-full bg-white bg-opacity-80 backdrop-blur-xl z-50">
    <div class="max-w-[976px] mx-auto px-6 py-4 flex items-center justify-between">
      <!-- Company Logo -->
      <div class="flex items-center">
        <router-link to="/home" class="font-bold text-xl text-[rgb(21,21,21)]">Myriade</router-link>
      </div>

      <!-- Main Navigation Links -->
      <div class="hidden md:flex space-x-8">
        <a href="#features" class="text-[rgb(21,21,21)] hover:text-gray-900 font-medium">Features</a>
        <a href="#how-it-works" class="text-[rgb(21,21,21)] hover:text-gray-900 font-medium">How it works</a>
        <a href="#examples" class="text-[rgb(21,21,21)] hover:text-gray-900 font-medium">Examples</a>
        <a href="#faq" class="text-[rgb(21,21,21)] hover:text-gray-900 font-medium">FAQ</a>
      </div>

      <!-- CTA Buttons in Navigation -->
      <div class="flex space-x-3">
        <router-link
          to="/login"
          class="border border-gray-300 px-4 py-2 rounded-lg font-medium hover:bg-gray-100 transition-colors"
        >Login</router-link>
        <a
          href="#get-started"
          class="bg-[rgb(21,21,21)] text-white px-4 py-2 rounded-lg font-medium hover:bg-gray-800 transition-colors"
        >Get Started</a>
      </div>
    </div>
  </nav>
</template>

<script setup>
// Navigation component with sticky header, blur effect, and consistent styling
</script>