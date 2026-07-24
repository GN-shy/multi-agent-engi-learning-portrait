<template>
  <div class="tutor-chat">
    <div class="chat-messages" ref="chatContainer">
      <div
        v-for="(msg, i) in messages"
        :key="i"
        :class="['chat-message', msg.role]"
      >
        <div class="msg-meta">
          <el-tag size="small" :type="msg.role === 'user' ? 'info' : 'success'">
            {{ msg.role === 'user' ? '你' : '导学助手' }}
          </el-tag>
          <span v-if="msg.type" class="msg-type">
            <el-tag size="small" type="warning">{{ msg.type }}</el-tag>
          </span>
          <span class="msg-time">{{ msg.time }}</span>
        </div>
        <div class="msg-content">{{ msg.content }}</div>
      </div>
    </div>
    <div class="chat-input">
      <el-input
        v-model="input"
        placeholder="输入你的问题..."
        @keyup.enter="send"
      >
        <template #append>
          <el-button @click="send" :disabled="!input.trim()">发送</el-button>
        </template>
      </el-input>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'

defineProps<{ messages: any[] }>()
const emit = defineEmits<{ send: [string] }>()

const input = ref('')
const chatContainer = ref<HTMLElement>()

async function send() {
  if (!input.value.trim()) return
  emit('send', input.value)
  input.value = ''
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-messages {
  max-height: 300px;
  overflow-y: auto;
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  margin-bottom: 12px;
}
.chat-message {
  margin-bottom: 12px;
  padding: 8px 12px;
  border-radius: 8px;
}
.chat-message.user {
  background: #ecf5ff;
  margin-left: 20px;
}
.chat-message.assistant {
  background: #f0f9eb;
  margin-right: 20px;
}
.msg-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.msg-time { font-size: 0.8em; color: #909399; }
.msg-content { line-height: 1.6; white-space: pre-wrap; }
</style>
