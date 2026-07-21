<template>

<el-card v-if="result" style="margin-top:20px">

<h2>演示结果</h2>


<el-descriptions
  :column="2"
  border
>

<el-descriptions-item label="业务ID">
{{ result.data.businessId }}
</el-descriptions-item>


<el-descriptions-item label="数据批次ID">
{{ result.data.readingBatchId }}
</el-descriptions-item>


<el-descriptions-item label="资产ID">
{{ result.data.assetId }}
</el-descriptions-item>


<el-descriptions-item label="授权ID">
{{ result.data.authId }}
</el-descriptions-item>


<el-descriptions-item label="训练任务ID">
{{ result.data.trainingTaskId }}
</el-descriptions-item>


<el-descriptions-item label="模型版本">
{{ result.data.globalModelVersion }}
</el-descriptions-item>


</el-descriptions>



<h3>模型指标</h3>

<el-table
:data="[result.data.metrics]"
border
>

<el-table-column
prop="mae"
label="MAE"
/>

<el-table-column
prop="rmse"
label="RMSE"
/>

<el-table-column
prop="mape"
label="MAPE"
/>

</el-table>



<h3>Agent输出</h3>


<el-descriptions
:column="1"
border
>

<el-descriptions-item label="预测ID">
{{result.data.predictionId}}
</el-descriptions-item>


<el-descriptions-item label="审计报告ID">
{{result.data.auditReportId}}
</el-descriptions-item>


</el-descriptions>



<h3>区块链存证</h3>


<el-tag
v-for="tx in result.data.ledgerTxIds"
:key="tx"
style="margin-right:10px"
>
{{tx}}
</el-tag>



</el-card>


</template>



<script setup>

defineProps({

result:Object

})


</script>