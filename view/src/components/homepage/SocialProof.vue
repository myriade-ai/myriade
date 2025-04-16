<template>
  <div class="bg-white py-12">
    <div class="max-w-[976px] mx-auto px-6">
      <h2 class="text-center text-lg font-semibold text-[rgb(21,21,21)]">
        Trusted by the world's most innovative teams
      </h2>
      
      <!-- Logo cloud with horizontal sliding animation -->
      <div class="mt-10 overflow-hidden">
        <div class="flex animate-slide space-x-8">
          <img
            class="h-8 w-auto object-contain flex-shrink-0"
            src="https://tailwindui.com/plus-assets/img/logos/158x48/transistor-logo-gray-900.svg"
            alt="Transistor"
          />
          <img
            class="h-8 w-auto object-contain flex-shrink-0"
            src="https://tailwindui.com/plus-assets/img/logos/158x48/reform-logo-gray-900.svg"
            alt="Reform"
          />
          <img
            class="h-8 w-auto object-contain flex-shrink-0"
            src="https://tailwindui.com/plus-assets/img/logos/158x48/tuple-logo-gray-900.svg"
            alt="Tuple"
          />
          <img
            class="h-8 w-auto object-contain flex-shrink-0"
            src="https://tailwindui.com/plus-assets/img/logos/158x48/savvycal-logo-gray-900.svg"
            alt="SavvyCal"
          />
          <img
            class="h-8 w-auto object-contain flex-shrink-0"
            src="https://tailwindui.com/plus-assets/img/logos/158x48/statamic-logo-gray-900.svg"
            alt="Statamic"
          />
          <!-- Duplicated for continuous sliding effect -->
          <img
            class="h-8 w-auto object-contain flex-shrink-0"
            src="https://tailwindui.com/plus-assets/img/logos/158x48/transistor-logo-gray-900.svg"
            alt="Transistor"
          />
          <img
            class="h-8 w-auto object-contain flex-shrink-0"
            src="https://tailwindui.com/plus-assets/img/logos/158x48/reform-logo-gray-900.svg"
            alt="Reform"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes slide {
  from {
    transform: translateX(0);
  }
  to {
    transform: translateX(-50%);
  }
}

.animate-slide {
  animation: slide 20s linear infinite;
}
</style>