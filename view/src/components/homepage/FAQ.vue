<template>
  <div class="bg-white">
    <div class="mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8 lg:py-40">
      <div class="mx-auto max-w-4xl">
        <h2
          class="text-3xl sm:text-4xl font-semibold tracking-tight text-gray-900 text-center"
        >
          Frequently asked questions
        </h2>
        <dl class="mt-16 divide-y divide-gray-900/10">
          <Disclosure
            as="div"
            v-for="faq in faqs"
            :key="faq.question"
            class="py-6 first:pt-0 last:pb-0"
            v-slot="{ open }"
          >
            <dt>
              <DisclosureButton
                class="flex w-full items-start justify-between text-left text-gray-900"
              >
                <span
                  class="text-base/7 font-semibold"
                  >{{ faq.question }}</span
                >
                <span class="ml-6 flex h-7 items-center">
                  <PlusSmallIcon
                    v-if="!open"
                    class="size-6"
                    aria-hidden="true"
                  />
                  <MinusSmallIcon v-else class="size-6" aria-hidden="true" />
                </span>
              </DisclosureButton>
            </dt>
            <DisclosurePanel as="dd" class="mt-2 pr-12">
              <p class="text-base/7 text-gray-600">{{ faq.answer }}</p>
            </DisclosurePanel>
          </Disclosure>
        </dl>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue'
import { MinusSmallIcon, PlusSmallIcon } from '@heroicons/vue/24/outline'

const faqs = [
  {
    question: "How can ChatGPT help with data analysis?",
    answer: "ChatGPT can assist with various data analysis tasks including data cleaning suggestions, statistical analysis guidance, visualization recommendations, interpreting results, and generating code snippets for data processing in languages like Python, R, and SQL.",
  },
  {
    question: "Can ChatGPT perform complex data analysis on my datasets?",
    answer: "ChatGPT cannot directly analyze your datasets as it cannot access or process your files. However, it can guide you through the analysis process, suggest methodologies, help troubleshoot code issues, and explain statistical concepts relevant to your analysis.",
  },
  {
    question: "What data analysis questions work best with ChatGPT?",
    answer: "ChatGPT works best with questions about methodology, code debugging, statistical concept explanations, visualization techniques, and data interpretation guidance. Specific questions with context about your data and analysis goals will yield the most helpful responses.",
  },
  {
    question: "Is my data secure when discussing analysis with ChatGPT?",
    answer: "When discussing data analysis with ChatGPT, avoid sharing sensitive or confidential data. While conversations may be used for training, it's best to use anonymized examples or general descriptions of your data when seeking assistance.",
  },
  // More questions...
]
</script>
