<template>
  <section class="max-w-[976px] mx-auto px-4 pt-36 pb-20 text-center">
    <!-- Bold, clear headline matching the technical spec -->
    <h1 class="text-5xl font-semibold mb-6 tracking-tight text-[rgb(21,21,21)]">
      Explore your data in seconds
    </h1>

    <!-- Clear, concise subheading -->
    <p class="text-xl text-[rgb(21,21,21)] mb-10 max-w-2xl mx-auto">
      Your data analyst agent
    </p>

    <!-- Interactive input area for file drops -->
    <div class="mb-8 max-w-2xl mx-auto bg-[rgb(249,249,249)] p-6 rounded-lg border border-gray-200">
      <div 
        class="border-2 border-dashed border-gray-300 rounded-lg p-8 flex flex-col items-center justify-center cursor-pointer hover:border-gray-400 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
        <p class="font-medium mb-1">Drop your CSV file here</p>
        <p class="text-sm text-gray-500">or connect your Google Sheets</p>
      </div>
    </div>

    <!-- Supporting example buttons -->
    <div class="max-w-2xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-3 mb-16">
      <button class="bg-[rgb(239,236,232)] py-3 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
        Sales Analysis
      </button>
      <button class="bg-[rgb(239,236,232)] py-3 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
        Customer Segmentation
      </button>
      <button class="bg-[rgb(239,236,232)] py-3 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
        Trend Forecasting
      </button>
      <button class="bg-[rgb(239,236,232)] py-3 px-4 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors">
        Market Research
      </button>
    </div>
  </section>
</template>

<script setup>
// Hero section with interactive input area for data exploration
</script>