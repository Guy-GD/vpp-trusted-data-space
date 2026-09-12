<template>
  <div class="container">
    <h1>虚拟电厂可信数据空间</h1>
    <h2>一键全链路 Mock 演示平台</h2>

    <DemoForm
      :running="running"
      @start="handleStart"
      @success="handleSuccess"
      @error="handleError"
    />
    <FlowSteps :activeStep="step" />
    <ResultSummary :result="result" />
    <ErrorPanel :error="error" />
    <StatusQuery />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DemoForm from './components/DemoForm.vue'
import FlowSteps from './components/FlowSteps.vue'
import ResultSummary from './components/ResultSummary.vue'
import ErrorPanel from './components/ErrorPanel.vue'
import StatusQuery from './components/StatusQuery.vue'

const result = ref(null)
const error = ref(null)
const step = ref(0)
const running = ref(false)

function handleStart() {
  running.value = true
  error.value = null
  result.value = null
  step.value = 0
}

function handleSuccess(data) {
  running.value = false
  result.value = data
  // 后端为同步全链路：runDemo 返回即代表 7 步全部完成
  step.value = 7
}

function handleError(err) {
  running.value = false
  result.value = null
  error.value = err
}
</script>

<style>
.container {
  text-align: center;
  margin-top: 50px;
}
</style>
