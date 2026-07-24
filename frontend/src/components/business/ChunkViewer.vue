<template>
  <div class="chunk-viewer">
    <el-empty v-if="!chunks || chunks.length === 0" description="知识库为空" />
    <div v-else>
      <el-table :data="chunks" stripe max-height="500">
        <el-table-column prop="chunk_id" label="ID" width="100" />
        <el-table-column prop="title" label="标题" width="200" />
        <el-table-column prop="domain" label="领域" width="120" />
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ chunks: any[] }>()
</script>
