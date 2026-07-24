<template>
  <div class="source-trace">
    <el-empty v-if="!traces || traces.length === 0" description="暂无溯源数据" />
    <div v-else>
      <el-table :data="traces" stripe>
        <el-table-column prop="chunk_id" label="片段ID" width="120" />
        <el-table-column prop="title" label="来源文档" />
        <el-table-column prop="used_in" label="引用位置" />
        <el-table-column label="置信度" width="120">
          <template #default="{ row }">
            <el-tag
              :type="row.confidence >= 0.9 ? 'success' : row.confidence >= 0.7 ? 'warning' : 'danger'"
              size="small"
            >
              {{ row.confidence ? (row.confidence * 100).toFixed(0) + '%' : 'N/A' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ traces: any[] }>()
</script>
