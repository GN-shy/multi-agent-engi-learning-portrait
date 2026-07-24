<template>
  <div class="human-detail">
    <template v-if="isEmpty">
      <el-empty description="暂无可展示的详细信息" :image-size="72" />
    </template>

    <template v-else-if="isPrimitive">
      <div class="primitive">
        <strong>{{ displayPrimitive(value) }}</strong>
        <span v-if="hint">{{ hint }}</span>
      </div>
    </template>

    <template v-else-if="Array.isArray(value)">
      <div class="list">
        <article v-for="(item, index) in value" :key="index">
          <span class="index">{{ index + 1 }}</span>
          <HumanDetail :value="item" :depth="depth + 1" />
        </article>
      </div>
    </template>

    <template v-else>
      <div class="fields" :class="{ compact: depth > 0 }">
        <section v-for="[key, item] in visibleEntries" :key="key" class="field">
          <span class="label">{{ fieldLabel(key) }}</span>
          <template v-if="isSimple(item)">
            <a
              v-if="key === 'source_url' && typeof item === 'string'"
              :href="item"
              target="_blank"
              rel="noreferrer"
            >打开原始来源 ↗</a>
            <el-progress
              v-else-if="isPercentField(key) && typeof item === 'number'"
              :percentage="Math.round(item <= 1 ? item * 100 : item)"
              :stroke-width="8"
            />
            <strong v-else>{{ displayPrimitive(item, key) }}</strong>
          </template>
          <HumanDetail v-else :value="item" :depth="depth + 1" />
        </section>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { agentLabel, dateTime, fieldLabel, percent, routeLabel, valueLabel } from '@/utils/presentation'

defineOptions({ name: 'HumanDetail' })
const props = withDefaults(defineProps<{ value: any; depth?: number; hint?: string }>(), {
  depth: 0,
  hint: '',
})

const hiddenKeys = new Set([
  'id',
  'session_id',
  'user_id',
  'provider_config_id',
  'llm_config_id',
  'search_config_id',
])
const visibleEntries = computed(() => Object.entries(props.value || {})
  .filter(([key, item]) => !hiddenKeys.has(key) && item !== null && item !== undefined && item !== ''))
const isPrimitive = computed(() => isSimple(props.value))
const isEmpty = computed(() => props.value === null
  || props.value === undefined
  || (Array.isArray(props.value) && props.value.length === 0)
  || (typeof props.value === 'object' && !Array.isArray(props.value) && visibleEntries.value.length === 0))

function isSimple(item: unknown) {
  return ['string', 'number', 'boolean'].includes(typeof item) || item === null || item === undefined
}
function isPercentField(key: string) {
  return ['knowledge_coverage', 'citation_coverage', 'citation_integrity', 'profile_fit', 'hallucination_risk', 'credibility'].includes(key)
}
function displayPrimitive(item: unknown, key = '') {
  if (isPercentField(key)) return percent(item)
  if (key === 'track_code') return routeLabel(String(item))
  if (key === 'agent_code' || key === 'winner') return agentLabel(String(item))
  if (key.endsWith('_at') || key === 'created_at') return dateTime(String(item))
  if (key === 'duration_ms') return `${valueLabel(item)} 毫秒`
  if (key.includes('week') && typeof item === 'number') return `第 ${item} 周`
  if (key.includes('hours') && typeof item === 'number') return `${item} 小时`
  return valueLabel(item)
}
</script>

<style scoped>
.human-detail { color: #26334c; }
.primitive { padding: 18px; border-radius: 15px; background: linear-gradient(135deg,#f4f7ff,#f8fbff); }
.primitive strong { display:block; font-size:24px; color:#245fe5; }
.primitive span { display:block; margin-top:8px; color:var(--muted); line-height:1.7; }
.fields { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; }
.fields.compact { grid-template-columns:1fr; margin-top:8px; }
.field { min-width:0; padding:14px; border:1px solid var(--line); border-radius:14px; background:#fbfcff; }
.field>.label { display:block; margin-bottom:7px; color:#758198; font-size:12px; }
.field>strong { display:block; line-height:1.7; white-space:pre-wrap; word-break:break-word; }
.field>a { color:#2764e8; text-decoration:none; }
.list { display:grid; gap:10px; }
.list>article { display:grid; grid-template-columns:30px 1fr; gap:10px; align-items:start; padding:12px; border:1px solid var(--line); border-radius:14px; }
.index { width:27px; height:27px; border-radius:9px; display:grid; place-items:center; background:#eaf1ff; color:#3168ee; font-weight:700; font-size:12px; }
@media(max-width:680px){.fields{grid-template-columns:1fr}}
</style>
