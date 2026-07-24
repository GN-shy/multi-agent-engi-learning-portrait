<template>
  <div class="learning-calendar">
    <div class="cal-header">
      <span class="cal-month">{{ monthLabel }}</span>
      <div class="cal-legend">
        <span class="legend-dot low"></span>少
        <span class="legend-dot mid"></span>中
        <span class="legend-dot high"></span>多
      </div>
    </div>
    <div class="cal-grid">
      <span v-for="d in ['一','二','三','四','五','六','日']" :key="d" class="cal-day-label">{{ d }}</span>
      <div v-for="day in calendarDays" :key="day.date"
           :class="['cal-day', { empty: !day.date, today: day.isToday }]"
           :style="{ background: dayColor(day.hours) }"
           :title="day.date ? `${day.date}: ${day.hours}h` : ''">
        <span v-if="day.date">{{ day.date.split('-')[2] }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  month?: string
  entries?: Array<{ date: string; hours: number }>
}>(), {
  month: () => new Date().toISOString().slice(0, 7),
  entries: () => [],
})
const monthLabel = computed(() => {
  const [year, month] = props.month.split('-')
  return `${year}年${Number(month)}月`
})
const calendarDays = computed(() => {
  const [year, month] = props.month.split('-').map(Number)
  const firstDay = new Date(year, month - 1, 1)
  const dayCount = new Date(year, month, 0).getDate()
  const today = new Date().toISOString().slice(0, 10)
  const hoursByDate = new Map(props.entries.map(item => [item.date, item.hours]))
  const days = []
  const mondayOffset = (firstDay.getDay() + 6) % 7
  for (let i = 0; i < mondayOffset; i++) days.push({ date: '', hours: 0, isToday: false })
  for (let d = 1; d <= dayCount; d++) {
    const date = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    days.push({
      date,
      hours: hoursByDate.get(date) || 0,
      isToday: date === today,
    })
  }
  return days
})

function dayColor(hours: number): string {
  if (hours === 0) return 'rgba(0,0,0,0.03)'
  if (hours < 1) return 'rgba(74,125,255,0.15)'
  if (hours < 2.5) return 'rgba(74,125,255,0.35)'
  return 'rgba(74,125,255,0.65)'
}
</script>

<style scoped>
.cal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.cal-month { font-weight: 600; font-size: 14px; }
.cal-legend { display: flex; align-items: center; gap: 4px; font-size: 11px; color: var(--text-muted); }
.legend-dot { width: 10px; height: 10px; border-radius: 2px; }
.legend-dot.low { background: rgba(74,125,255,0.15); }
.legend-dot.mid { background: rgba(74,125,255,0.35); }
.legend-dot.high { background: rgba(74,125,255,0.65); }
.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px; }
.cal-day-label { font-size: 11px; color: var(--text-muted); text-align: center; padding: 4px; }
.cal-day {
  aspect-ratio: 1; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; cursor: default;
}
.cal-day.empty { background: transparent; }
.cal-day.today { box-shadow: 0 0 0 2px #4a7dff; }
</style>
