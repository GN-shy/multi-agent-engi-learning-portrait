<template>
  <div ref="chartRef" style="width:100%;height:220px"></div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

onMounted(() => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: ['7/1', '7/5', '7/10', '7/15', '7/20'],
      axisLabel: { fontSize: 10 },
    },
    yAxis: { type: 'value', min: 60, max: 100, axisLabel: { fontSize: 10 } },
    series: [{
      data: [70, 75, 78, 82, 86],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#4a7dff', width: 3 },
      itemStyle: { color: '#4a7dff' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[
        { offset: 0, color: 'rgba(74,125,255,0.3)' },
        { offset: 1, color: 'rgba(74,125,255,0.02)' },
      ])},
    }],
  })
})
</script>
