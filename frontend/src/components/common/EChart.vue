<template>
  <div ref="root" class="echart-root" :style="{ height }" />
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { GraphChart, LineChart, PieChart, RadarChart } from 'echarts/charts'
import {
  GraphicComponent,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
} from 'echarts/components'
import { init, use, type ECharts } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'

use([
  GraphChart,
  LineChart,
  PieChart,
  RadarChart,
  GraphicComponent,
  GridComponent,
  LegendComponent,
  RadarComponent,
  TooltipComponent,
  CanvasRenderer,
])

const props = withDefaults(defineProps<{ option: any; height?: string }>(), {
  height: '320px',
})
const emit = defineEmits<{ click: [params: any] }>()
const root = ref<HTMLDivElement>()
let chart: ECharts | null = null
let observer: ResizeObserver | null = null

function render() {
  if (!root.value) return
  chart ??= init(root.value)
  chart.off('click')
  chart.on('click', (params) => emit('click', params))
  const radarIndicators = props.option?.radar?.indicator
  const option = Array.isArray(radarIndicators) && radarIndicators.length === 0
    ? {
        graphic: [{
          type: 'text',
          left: 'center',
          top: 'middle',
          style: { text: '暂无图表数据', fill: '#8a96aa', fontSize: 14 },
        }],
        series: [],
      }
    : props.option
  try {
    chart.setOption(option, true)
  } catch (error) {
    // 图表异常不应阻断父页面加载、表单提交或其它业务交互。
    chart.clear()
    chart.setOption({
      graphic: [{
        type: 'text',
        left: 'center',
        top: 'middle',
        style: { text: '图表暂不可用，请刷新重试', fill: '#d36a73', fontSize: 14 },
      }],
    })
    console.error('EChart render failed', error)
  }
}

onMounted(() => {
  render()
  observer = new ResizeObserver(() => chart?.resize())
  observer.observe(root.value!)
})
watch(() => props.option, render, { deep: true })
onBeforeUnmount(() => {
  observer?.disconnect()
  chart?.dispose()
})
</script>

<style scoped>
.echart-root { width: 100%; min-width: 0; }
</style>
