<template>
  <div class="debate-viewer">
    <el-alert
      title="双Agent辩论机制"
      type="warning"
      description="当两个生成Agent在某知识点上产生分歧时，系统自动触发辩论机制。各方引用知识库原文佐证，仲裁方裁定胜负。"
      show-icon
      :closable="false"
    />
    <el-descriptions :column="3" border style="margin-top:16px">
      <el-descriptions-item label="辩论状态">
        <el-tag type="warning">已触发</el-tag>
      </el-descriptions-item>
      <el-descriptions-item label="辩论回合">
        {{ summary?.rounds || 0 }}
      </el-descriptions-item>
      <el-descriptions-item label="分歧知识点">
        {{ summary?.disputed_points || 0 }}个
      </el-descriptions-item>
    </el-descriptions>

    <el-timeline style="margin-top:16px">
      <el-timeline-item
        v-for="(round, i) in debateRounds"
        :key="i"
        :timestamp="`第${i + 1}轮辩论`"
        type="warning"
      >
        <el-card shadow="never">
          <p><strong>Gen A 论点：</strong>{{ round.gen_a }}</p>
          <p><strong>Gen B 论点：</strong>{{ round.gen_b }}</p>
          <el-tag :type="round.winner === 'gen_a' ? 'success' : 'primary'">
            裁定胜出: {{ round.winner === 'gen_a' ? '严格策略Agent' : '创意策略Agent' }}
          </el-tag>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ summary: any }>()

const debateRounds = computed(() => {
  const rounds = props.summary?.rounds || 0
  const arr = []
  for (let i = 0; i < Math.min(rounds, 3); i++) {
    arr.push({
      gen_a: `在知识库原文中(文档ID:kb_001)明确提到...因此我的观点是正确的。`,
      gen_b: `虽然知识库有相关描述，但从实操角度看...我建议采用更灵活的解释。`,
      winner: i % 2 === 0 ? 'gen_a' : 'gen_b',
    })
  }
  return arr
})
</script>
