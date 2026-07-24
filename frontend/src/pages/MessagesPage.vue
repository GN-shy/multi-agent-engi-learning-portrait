<template>
  <AppShell>
    <section class="panel">
      <div class="panel-title">
        <div>
          <h3>消息中心</h3>
          <p>生成完成、反馈调整和首次引导由真实业务状态触发</p>
        </div>
        <div class="tag-row">
          <el-tag v-if="unreadCount" type="danger">{{ unreadCount }} 条未读</el-tag>
          <el-button :loading="loading" @click="load">刷新</el-button>
        </div>
      </div>
      <div v-if="items.length" class="messages">
        <article
          v-for="item in items"
          :key="item.id"
          class="message clickable"
          :class="{ unread: !item.read }"
          @click="open(item)"
        >
          <div class="dot" :class="item.type"></div>
          <div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.content }}</p>
            <span>{{ new Date(item.created_at).toLocaleString() }}</span>
          </div>
          <el-tag v-if="!item.read" type="danger">新</el-tag>
          <el-tag v-else type="info">已读</el-tag>
        </article>
      </div>
      <div v-else class="empty">当前没有消息</div>
    </section>

    <DetailModal v-model="detail.visible" :title="detail.item?.title || '消息详情'">
      <p class="content">{{ detail.item?.content }}</p>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="消息类型">{{ typeLabel(detail.item?.type) }}</el-descriptions-item>
        <el-descriptions-item label="发生时间">{{ detail.item?.created_at }}</el-descriptions-item>
        <el-descriptions-item v-if="detail.item?.related_id" label="关联对象">
          {{ detail.item.related_id }}
        </el-descriptions-item>
      </el-descriptions>
      <el-button
        v-if="detail.item?.action_url"
        class="action"
        type="primary"
        @click="goAction"
      >
        前往处理
      </el-button>
    </DetailModal>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import DetailModal from '@/components/common/DetailModal.vue'
import { getData, putData } from '@/api'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(false)
const detail = reactive({ visible: false, item: null as any })
const unreadCount = computed(() => items.value.filter((item) => !item.read).length)

onMounted(load)

async function load() {
  loading.value = true
  try {
    items.value = (await getData<{ items: any[] }>('/messages')).items
  } finally {
    loading.value = false
  }
}

async function open(item: any) {
  detail.item = item
  detail.visible = true
  if (!item.read && !String(item.id).startsWith('onboarding:')) {
    await putData(`/messages/${item.id}/read`)
    item.read = true
  }
}

async function goAction() {
  const target = detail.item?.action_url
  detail.visible = false
  if (target) await router.push(target)
}

function typeLabel(type?: string) {
  return ({
    onboarding: '新手引导',
    generation: '内容生成',
    adjustment: '学习调整',
    assessment: '评测反馈',
  } as Record<string, string>)[type || ''] || type || '-'
}
</script>

<style scoped>
.messages{display:grid;gap:11px}.message{display:grid;grid-template-columns:12px 1fr auto;gap:16px;align-items:center;padding:16px;border:1px solid var(--line);border-radius:15px;transition:.2s}.message.unread{background:#f7faff;border-color:#cddcff}.dot{width:10px;height:10px;border-radius:50%;background:#3168ee}.dot.adjustment{background:#17a673}.dot.onboarding{background:#e89025}.dot.assessment{background:#7b5ce1}.message h3,.message p{margin:4px}.message p,.message span{color:var(--muted)}.message span{font-size:12px}.content{font-size:17px;line-height:1.8}.action{margin-top:20px}
</style>
