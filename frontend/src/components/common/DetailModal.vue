<template>
  <el-dialog
    v-model="visible"
    :title="title"
    width="min(820px, 88vw)"
    destroy-on-close
    align-center
    class="detail-modal"
  >
    <div class="detail-modal__body">
      <slot />
    </div>
    <template #footer>
      <slot name="footer">
        <el-button @click="visible = false">关闭</el-button>
      </slot>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ modelValue: boolean; title: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean] }>()
const visible = computed({
  get: () => props.modelValue,
  set: (value: boolean) => emit('update:modelValue', value),
})
</script>

<style>
.detail-modal {
  max-height: 86vh;
  border-radius: 22px !important;
  overflow: hidden;
  box-shadow: 0 28px 80px rgba(25, 52, 106, 0.28) !important;
}
.detail-modal .el-dialog__header {
  padding: 22px 26px 16px;
  border-bottom: 1px solid #edf1f7;
}
.detail-modal .el-dialog__body {
  padding: 0;
}
.detail-modal__body {
  max-height: 62vh;
  overflow: auto;
  padding: 24px 26px;
}
.dialog-fade-enter-active .detail-modal,
.dialog-fade-leave-active .detail-modal {
  transition: transform 0.28s cubic-bezier(.2,.85,.28,1.15), opacity 0.22s ease;
}
.dialog-fade-enter-from .detail-modal,
.dialog-fade-leave-to .detail-modal {
  transform: translateY(20px) scale(.96);
  opacity: 0;
}
</style>
