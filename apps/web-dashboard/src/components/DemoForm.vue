<template>
  <el-card>
    <h2>演示参数</h2>

    <p>场景：vpp_day_ahead_trading</p>

    <p>参与方数量：3</p>

    <p>训练轮次：3</p>

    <el-button 
@click="startDemo"
:loading="loading || props.running"
:disabled="loading || props.running"
>
{{ loading || props.running ? '演示中...' : '开始演示' }}
</el-button>

  </el-card>
</template>

<script setup>

import { ref, reactive } from 'vue'
import { runDemo } from '../api/gateway'

const emit = defineEmits([
  'success',
  'error',
  'start'
])

const loading = ref(false)
const props = defineProps({

  running:{
    type:Boolean,
    default:false
  }

})


const form = reactive({
  scenario: 'vpp_day_ahead_trading',
  participants: [
    'did:vpp:load-aggregator:001',
    'did:vpp:renewable-plant:001',
    'did:vpp:storage:001'
  ],
  meterCount: 3,
  trainingRounds: 3
})



async function startDemo(){

    emit('start')
    
     if(loading.value){
    return
    }

  loading.value = true

  try {
    await new Promise(resolve=>{
    setTimeout(resolve,5000)
    })


    const result = await runDemo(
      form,
      crypto.randomUUID()
    )


    emit('success', result)


  } catch(err){

    emit('error', err)

  } finally {

    loading.value = false

  }

}
</script>