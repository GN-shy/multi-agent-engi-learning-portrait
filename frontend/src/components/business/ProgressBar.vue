<template>
  <div class="progress-bar">
    <el-progress
      :percentage="percentage"
      :stroke-width="20"
      :color="progressColor"
    >
      <span>{{ completed }} / {{ total }} 已完成</span>
    </el-progress>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ completed: number; total: number }>()

const percentage = computed(() => Math.round((props.completed / Math.max(props.total, 1)) * 100))

const progressColor = computed(() => {
  if (percentage.value >= 80) return '#67c23a'
  if (percentage.value >= 40) return '#e6a23c'
  return '#409eff'
})
</script>
