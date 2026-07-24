<template>
  <div ref="chartRef" style="width:100%;height:350px"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{
  data: { mastered: string[]; in_progress: string[]; not_started: string[] }
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  updateChart()
}

function updateChart() {
  if (!chart) return
  const all = [
    ...props.data.mastered.map((n, i) => ({ name: n, value: 1, itemStyle: { color: '#67c23a' }, y: i * 80 + 40 })),
    ...props.data.in_progress.map((n, i) => ({ name: n, value: 0.6, itemStyle: { color: '#e6a23c' }, y: i * 80 + 40 })),
    ...props.data.not_started.map((n, i) => ({ name: n, value: 0, itemStyle: { color: '#c0c4cc' }, y: i * 80 + 40 })),
  ]

  const option: echarts.EChartsOption = {
    tooltip: { trigger: 'item' },
    legend: {
      data: ['已掌握', '学习中', '未开始'],
      bottom: 0,
    },
    series: [{
      type: 'graph',
      layout: 'force',
      force: { repulsion: 80, edgeLength: [60, 120], gravity: 0.15 },
      roam: true,
      data: all,
      symbolSize: 40,
      label: { show: true, fontSize: 12 },
    }],
  }
  chart.setOption(option)
}

onMounted(initChart)

watch(() => props.data, updateChart, { deep: true })
</script>
