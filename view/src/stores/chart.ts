import axios from '@/plugins/axios'
import { defineStore } from 'pinia'
import { ref } from 'vue'

interface Chart {
  id: string
  name: string
  description: string
  config: Record<string, any>
  is_favorite: boolean
}

export const useChartStore = defineStore('chart', () => {
  const chart = ref<Chart | null>(null)

  const fetchChart: (chartId: string) => Promise<Chart> = async (chartId: string) => {
    const response = await axios.get(`/api/chart/${chartId}`)
    return response.data
  }

  const toggleChartFavorite: (chartId: string) => Promise<boolean> = async (chartId: string) => {
    const response = await axios.post(`/api/chart/${chartId}/favorite`)
    return response.data.is_favorite
  }

  return {
    chart,
    fetchChart,
    toggleChartFavorite
  }
})
