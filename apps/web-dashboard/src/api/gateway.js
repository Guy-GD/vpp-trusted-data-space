import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export async function runDemo(payload, idempotencyKey) {
   
  return {
    code: 0,
    message: "ok",
    data: {
      businessId: "demo_001",
      readingBatchId: "batch_001",
      assetId: "asset_001",
      authId: "auth_001",
      trainingTaskId: "fl_task_001",
      globalModelVersion: "global_model_v1",

      metrics: {
        mae: 2.31,
        rmse: 3.72,
        mape: 0.081
      },

      predictionId: "prediction_001",
      auditReportId: "report_001",

      ledgerTxIds: [
        "tx_data_001",
        "tx_auth_001",
        "tx_model_001"
      ]
    },

    traceId: "trace_20260710_000001"
  }

}

export async function getDemoStatus(businessId) {
  return {
  code:0,
  message:"ok",
  data:{
    businessId: businessId,
    status:"COMPLETED",
    currentStage:"AGENT_COMPLETED",
    lastEventType:"agent_report_generated",
    globalModelVersion:"global_model_v1",
    retryable:false,
    error:null
  },
  traceId:"trace_20260710_000001"
}
}