<template>
  <section class="max-w-4xl mx-auto px-4 py-36 text-center relative">
    <div id="home_wave"></div>
    <!-- Bold, clear headline matching the high-converting structure -->
    <h1
      class="text-5xl font-semibold mb-6 tracking-tight relative italic"
      style="z-index: 2;"
    >
      Get answers. Find inspiration.
    </h1>

    <!-- Clear, concise subheading that explains the product features -->
    <p
      class="text-lg text-gray-600 mb-10 max-w-2xl mx-auto relative"
      style="z-index: 2;"
    >
      Your personal AI assistant that writes, brainstorms, edits, and helps you
      be more productive. Free to use, easy to try.
    </p>

    <!-- Call to action buttons - primary CTA is clear and high-contrast -->
    <div class="flex justify-center mb-16 relative" style="z-index: 2;">
      <button
        class="bg-black text-white px-5 py-3 rounded-lg font-medium hover:bg-gray-800 transition-colors flex items-center space-x-2"
      >
        Start now
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4 ml-2"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5l7 7-7 7"
          />
        </svg>
      </button>
    </div>

    <!-- Video/demo section with iframe -->
    <div class="mb-10 max-w-3xl sm:text-4xl mx-auto relative z-10">
      <div class="relative pb-[56.25%] h-0 overflow-hidden">
        <iframe
          src="https://www.youtube.com/embed/rh8CWB0ClOc"
          title="Catalys Demo Video"
          frameborder="0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowfullscreen
          class="absolute top-0 left-0 w-full h-full"
        ></iframe>
      </div>
    </div>
  </section>
</template>

<script setup>
// Hero section with clear USP, headline, CTA, and video demo placeholder
</script>