<template>
  <svg :width="width" :height="height" viewBox="45 22 95 50" preserveAspectRatio="xMidYMid meet">
    <path
      stroke="#2563EB"
      id="outline"
      fill="none"
      stroke-width="4"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-miterlimit="10"
      d="M93.9,46.4c9.3,9.5,13.8,17.9,23.5,17.9s17.5-7.8,17.5-17.5s-7.8-17.6-17.5-17.5c-9.7,0.1-13.3,7.2-22.1,17.1 				c-8.9,8.8-15.7,17.9-25.4,17.9s-17.5-7.8-17.5-17.5s7.8-17.5,17.5-17.5S86.2,38.6,93.9,46.4z"
    />
    <path
      id="outline-bg"
      opacity="0.05"
      fill="none"
      stroke="#2563EB"
      stroke-width="4"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-miterlimit="10"
      d="				M93.9,46.4c9.3,9.5,13.8,17.9,23.5,17.9s17.5-7.8,17.5-17.5s-7.8-17.6-17.5-17.5c-9.7,0.1-13.3,7.2-22.1,17.1 				c-8.9,8.8-15.7,17.9-25.4,17.9s-17.5-7.8-17.5-17.5s7.8-17.5,17.5-17.5S86.2,38.6,93.9,46.4z"
    />
  </svg>
</template>

<script setup lang="ts">
interface Props {
  width?: number | string
  height?: number | string
}

withDefaults(defineProps<Props>(), {
  width: 70,
  height: 30
})
</script>

<style scoped>
*,
*:before,
*:after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}
html,
body {
  font-size: 62.5%;
  height: 100%;
  overflow: hidden;
}
body {
  background: #7981b2;
}

#outline {
  stroke-dasharray: 2.42776657104492px, 242.776657104492px;
  stroke-dashoffset: 0;
  animation: anim 1.6s linear infinite;
}

@keyframes anim {
  12.5% {
    stroke-dasharray: 33.988532514888px, 242.776657104492px;
    stroke-dashoffset: -26.705122715941px;
  }
  43.75% {
    stroke-dasharray: 84.971629786572px, 242.776657104492px;
    stroke-dashoffset: -84.971629786572px;
  }
  100% {
    stroke-dasharray: 2.42776657104492px, 242.776657104492px;
    stroke-dashoffset: -240.348890629447px;
  }
}
</style>
