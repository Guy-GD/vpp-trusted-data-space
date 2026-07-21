<template>

  <el-card
    v-if="error"
    class="error-panel"
  >

    <h3>❌ 演示失败</h3>


    <p>
      错误码：
      {{ error.code || '未知' }}
    </p>


    <p>
      错误信息：
      {{ error.message || '未知错误' }}
    </p>


    <p
      v-if="error.traceId"
    >
      traceId：
      {{ error.traceId }}
    </p>


  </el-card>


</template>



<script setup>


defineProps({

  error:{
    type:Object,
    default:null
  }

})


</script>



<style scoped>


.error-panel{

  margin-top:20px;

}


</style>