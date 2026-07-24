<template>
  <div ref="chartRef" style="width:100%;height:200px"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{ data: { name: string; value: number; color: string }[] }>()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['55%', '78%'],
      center: ['50%', '50%'],
      data: props.data,
      label: { formatter: '{b}\n{d}%', fontSize: 10 },
      emphasis: { scaleSize: 8 },
    }],
  })
}

onMounted(initChart)
watch(() => props.data, initChart, { deep: true })
</script>
