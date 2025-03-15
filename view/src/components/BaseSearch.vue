<template>
  <div>
    <div class="relative mt-2 flex items-center">
      <input
        type="text"
        name="search"
        id="search"
        placeholder="Search"
        class="block w-full rounded-md border-0 py-1.5 pr-14 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
      />
      <div class="absolute inset-y-0 right-0 flex py-1.5 pr-1.5">
        <kbd
          class="inline-flex items-center rounded border border-gray-200 px-1 font-sans text-xs text-gray-400"
          >⌘K</kbd
        >
      </div>
    </div>
  </div>
</template>
