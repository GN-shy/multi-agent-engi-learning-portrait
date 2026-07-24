<template>
  <div ref="chartRef" style="width:100%;height:260px"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps<{ data: { dimensions: string[]; values: number[] } }>()
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function initChart() {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, textStyle: { fontSize: 10 } },
    radar: {
      center: ['50%', '45%'],
      radius: '70%',
      indicator: props.data.dimensions.map(d => ({ name: d, max: 100 })),
      axisName: { fontSize: 10 },
    },
    series: [{
      type: 'radar',
      data: [{
        value: props.data.values,
        name: '当前能力',
        areaStyle: { color: 'rgba(74, 125, 255, 0.25)' },
        lineStyle: { color: '#4a7dff', width: 2 },
        itemStyle: { color: '#4a7dff' },
      }],
    }],
  })
}

onMounted(initChart)
watch(() => props.data, initChart, { deep: true })
</script>
