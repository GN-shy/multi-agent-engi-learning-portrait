<template>
  <div class="question-card">
    <el-card shadow="never">
      <div class="question-content">
        <el-tag type="warning" size="small" style="margin-bottom:8px">
          {{ question.type === 'open_ended' ? '开放式问题' : '选择题' }}
        </el-tag>
        <p class="question-text">{{ question.text }}</p>
      </div>

      <el-collapse v-if="question.hints?.length" style="margin-top:12px">
        <el-collapse-item title="查看提示">
          <p v-for="(hint, i) in question.hints" :key="i">{{ hint }}</p>
        </el-collapse-item>
      </el-collapse>

      <div class="answer-area">
        <el-input
          v-model="answer"
          type="textarea"
          :rows="3"
          placeholder="请输入你的回答..."
          style="margin-top:12px"
        />
        <el-button
          type="primary"
          :disabled="!answer.trim()"
          @click="submitAnswer"
          style="margin-top:8px; width:100%"
        >
          提交回答
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ question: any }>()
const emit = defineEmits<{ answer: [string] }>()

const answer = ref('')

function submitAnswer() {
  if (answer.value.trim()) {
    emit('answer', answer.value)
    answer.value = ''
  }
}
</script>

<style scoped>
.question-text { font-size: 1.05em; line-height: 1.6; }
</style>
