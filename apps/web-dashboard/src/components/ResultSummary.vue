<template>
  <el-card v-if="result" style="margin-top:20px">
    <h2>演示结果</h2>

    <el-descriptions :column="2" border>
      <el-descriptions-item label="业务ID">
        {{ result.data.businessId }}
      </el-descriptions-item>
      <el-descriptions-item label="状态">
        {{ result.data.status }}
      </el-descriptions-item>
      <el-descriptions-item label="资产ID">
        {{ result.data.assetId }}
      </el-descriptions-item>
      <el-descriptions-item label="模型版本">
        {{ result.data.globalModelVersion }}
      </el-descriptions-item>
      <el-descriptions-item label="Agent报告ID">
        {{ result.data.agentReportId }}
      </el-descriptions-item>
      <el-descriptions-item label="traceId">
        {{ result.traceId }}
      </el-descriptions-item>
    </el-descriptions>

    <h3>模型指标</h3>
    <el-table :data="[result.data.metrics]" border>
      <el-table-column prop="accuracy" label="准确率" />
      <el-table-column prop="rounds" label="训练轮次" />
    </el-table>
  </el-card>
</template>

<script setup>
defineProps({
  result: Object,
})
</script>
