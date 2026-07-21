<template>

<el-card style="margin-top:20px">

<h2>状态查询</h2>


<el-input
v-model="businessId"
placeholder="请输入 businessId"
/>


<el-button
style="margin-top:15px"
@click="queryStatus"
>
查询状态
</el-button>

<div v-if="status">


<h3>查询结果</h3>


<div v-if="status.error">

<p>
查询失败：

{{status.message}}

</p>

</div>


<div v-else>
<p>
业务ID：

{{ businessId }}

</p>

<p>
状态：

{{ status.data.status }}

</p>



<p>

当前阶段：

{{ status.data.currentStage }}

</p>


</div>


</div>



</el-card>


</template>



<script setup>

import { ref } from 'vue'
import { getDemoStatus } from '../api/gateway'


const businessId = ref('')

const status = ref(null)



async function queryStatus(){

    if(!businessId.value){

 alert('请输入businessId')

 return

}

try{


 const result = await getDemoStatus(
   businessId.value
 )


 status.value=result


}catch(err){


 status.value={
   error:true,
   message:err.message
 }


}


}


</script>