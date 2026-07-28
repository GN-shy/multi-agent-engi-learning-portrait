<template>
  <div ref="chartRef" style="width:100%;height:220px"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = withDefaults(defineProps<{
  xData?: string[]
  yData?: number[]
  title?: string
}>(), {
  xData: () => [],
  yData: () => [],
})

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

function render() {
  if (!chartRef.value) return
  chart ??= echarts.init(chartRef.value)
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 20, top: props.title ? 36 : 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: props.xData.length ? props.xData : ['暂无数据'],
      axisLabel: { fontSize: 10 },
    },
    yAxis: { type: 'value', axisLabel: { fontSize: 10 } },
    series: [{
      data: props.yData.length ? props.yData : [0],
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
}

onMounted(render)
watch([() => props.xData, () => props.yData], render)
</script>
