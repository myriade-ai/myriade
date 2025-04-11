<template>
  <div class="max-w-5xl mx-auto py-12">
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div v-for="(example, index) in examples" :key="index" 
           class="p-5 rounded-lg border border-gray-200 hover:border-gray-300 hover:shadow-sm transition-all cursor-pointer">
        <p class="text-[15px] text-gray-800">
          {{ example }}
          <span class="text-gray-400 ml-1">→</span>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
const examples = [
  "Write a Python script to automate sending daily email reports",
  "Create a personal webpage for me after asking me three questions",
  "Create a morning routine to boost my productivity",
  "Plan a 'mental health day' to help me relax and recharge",
  "Drop an ancient civilizations",
  "Write a text asking a friend to be my plus-one at a wedding",
  "Improve my essay writing: ask me to outline my thoughts",
  "Tell me a fun fact about the Roman Empire",
  "Content calendar for a TikTok",
  "Suggest fun activities to help me make friends in a new city",
  "Make a sandwich using ingredients from my kitchen",
  "Quiz me on world capitals to enhance my geography skills"
]
</script>