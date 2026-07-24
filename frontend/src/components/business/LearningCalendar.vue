<template>
  <div class="learning-calendar">
    <div class="cal-header">
      <span class="cal-month">2026年7月</span>
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

const calendarDays = computed(() => {
  const days = []
  // Simulate July 2026 calendar
  for (let i = 0; i < 4; i++) days.push({ date: '', hours: 0 })
  for (let d = 1; d <= 31; d++) {
    const hours = Math.random() > 0.3 ? Math.floor(Math.random() * 5) + 0.5 : 0
    days.push({
      date: `2026-07-${String(d).padStart(2, '0')}`,
      hours,
      isToday: d === 21,
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
