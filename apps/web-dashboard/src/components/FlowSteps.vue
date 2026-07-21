<template>

<el-card style="margin-top:20px">

<h2>演示流程</h2>


<el-steps
  :active="activeStep"
  finish-status="success"
>

<el-step title="源端采集" />

<el-step title="数据接入" />

<el-step title="身份授权" />

<el-step title="联邦训练" />

<el-step title="隐私聚合" />

<el-step title="模型生成" />

<el-step title="Agent 输出" />


</el-steps>


</el-card>

</template>


<script setup>

defineProps({

activeStep:{
type:Number,
default:0
}

})


</script>