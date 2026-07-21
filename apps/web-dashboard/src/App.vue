<template>
  <div class="container">
    <h1>虚拟电厂可信数据空间</h1>

    <h2>一键全链路 Mock 演示平台</h2>

    <DemoForm 
    :running="running"
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
import DemoForm from './components/DemoForm.vue'
import FlowSteps from './components/FlowSteps.vue'
import ResultSummary from './components/ResultSummary.vue'
import ErrorPanel from './components/ErrorPanel.vue'
import StatusQuery from './components/StatusQuery.vue'
import { ref } from 'vue'

const result = ref(null)
const error = ref(null)
const step = ref(0)
const running = ref(false)


async function handleSuccess(data){

 running.value = true


  await startFlow()


  result.value=data


  running.value = false

}


 running.value=false




function handleError(data){
   result.value=null

  error.value = data

}

async function startFlow(){

  for(let i=0;i<7;i++){

    step.value=i

    await new Promise(resolve=>{

      setTimeout(resolve,1000)

    })

  }

}



</script>

<style>
.container {
  text-align: center;
  margin-top: 50px;
}
</style>