<template>
  <div class="search-test">
    <el-empty v-if="!results || results.length === 0" description="暂无检索结果" />
    <div v-else>
      <el-table :data="results" stripe max-height="400">
        <el-table-column prop="chunk_id" label="片段ID" width="100" />
        <el-table-column prop="title" label="文档标题" width="200" />
        <el-table-column prop="content" label="内容" show-overflow-tooltip />
        <el-table-column prop="similarity_score" label="相似度" width="100">
          <template #default="{ row }">
            <el-tag :type="row.similarity_score > 0.8 ? 'success' : 'warning'" size="small">
              {{ row.similarity_score ? (row.similarity_score * 100).toFixed(0) + '%' : '-' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ results: any[] }>()
</script>
