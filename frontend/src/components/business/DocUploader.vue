<template>
  <div class="doc-uploader">
    <el-upload
      drag
      :auto-upload="false"
      :on-change="handleChange"
      accept=".txt,.md,.pdf,.json,.csv"
    >
      <el-icon :size="40"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        拖拽文件到此处或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 .txt / .md / .pdf / .json / .csv 格式的知识文档
        </div>
      </template>
    </el-upload>
  </div>
</template>

<script setup lang="ts">
import { UploadFilled } from '@element-plus/icons-vue'

const emit = defineEmits<{ uploaded: [any] }>()

function handleChange(file: any) {
  emit('uploaded', {
    name: file.name,
    size: file.size,
    uploaded_at: new Date().toISOString(),
  })
}
</script>
