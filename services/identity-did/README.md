# DID 与授权模块 Demo

这是 `vpp-trusted-data-space` 项目中 DID 与授权模块的可运行 Mock Demo。它按照项目的接口契约实现主体/设备注册、身份校验、授权申请、授权审批和授权查询，适合本地学习、接口联调与项目演示。

> 重要：本 Demo 不是真实的区块链 DID 或生产级密码系统。数据只保存在进程内存中，服务重启后会清空。

## 已实现功能

| 接口 | 功能 |
| --- | --- |
| `GET /health` | 健康检查 |
| `POST /api/v1/identity/subjects` | 注册主体 DID |
| `POST /api/v1/identity/devices` | 为已注册主体注册设备 DID |
| `POST /api/v1/identity/verify` | 校验 DID、载荷哈希和 Mock 签名 |
| `POST /api/v1/auth/requests` | 创建数据使用授权申请 |
| `POST /api/v1/auth/requests/{authId}/approve` | 批准或拒绝授权申请 |
| `GET /api/v1/auth/requests/{authId}` | 查询授权状态 |

所有响应统一使用以下结构：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "traceId": "trace_xxx"
}
```

## 技术栈

- Python 3.11+
- FastAPI + Pydantic
- Uvicorn
- Pytest + FastAPI TestClient
- 进程内字典存储

选择这套技术栈的原因是它与当前项目的服务化接口形式匹配，代码量较小，便于在学习阶段理解 DID、签名校验、授权状态机和接口测试。

## 本地运行

在 PowerShell 中进入本目录：

```powershell
cd D:\Documents\联邦学习\vpp-trusted-data-space\services\identity-did
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

启动后可访问：

- 健康检查：`http://127.0.0.1:8000/health`
- Swagger 调试页面：`http://127.0.0.1:8000/docs`

## 手动 curl 演示

重启服务清空内存数据后，在另一个 PowerShell 窗口按顺序执行。示例中的 DID 和授权编号依赖这个执行顺序。

```powershell
# 1. 健康检查
curl.exe -s http://127.0.0.1:8000/health

# 2. 注册请求方（operator:001）
'{"name":"VPP operator","type":"operator","publicKey":"bW9jay1wdWJsaWMta2V5"}' | curl.exe -s http://127.0.0.1:8000/api/v1/identity/subjects -H 'Content-Type: application/json' -H 'X-Trace-Id: trace-curl-001' -H 'Idempotency-Key: curl-subject-001' --data-binary '@-'

# 3. 注册数据所有者（load-aggregator:002）
'{"name":"Load aggregator","type":"load_aggregator","publicKey":"bW9jay1wdWJsaWMta2V5"}' | curl.exe -s http://127.0.0.1:8000/api/v1/identity/subjects -H 'Content-Type: application/json' --data-binary '@-'

# 4. 注册设备
'{"deviceName":"Smart meter 01","deviceType":"smart_meter","ownerDid":"did:vpp:load-aggregator:002","publicKey":"bW9jay1wdWJsaWMta2V5"}' | curl.exe -s http://127.0.0.1:8000/api/v1/identity/devices -H 'Content-Type: application/json' --data-binary '@-'

# 5. 验证请求方签名
'{"subjectDid":"did:vpp:operator:001","signature":"Elqp/Rw0+M0eDhFc4ifBxyZ622sbw8ZVPivVnDRZ2Io=","payloadHash":"sha256:0000000000000000000000000000000000000000000000000000000000000000"}' | curl.exe -s http://127.0.0.1:8000/api/v1/identity/verify -H 'Content-Type: application/json' --data-binary '@-'

# 6. 创建授权申请（auth_001）
'{"requesterDid":"did:vpp:operator:001","ownerDid":"did:vpp:load-aggregator:002","assetId":"asset_demo_load_curve","purpose":"federated_training","expireAt":"2099-12-31T23:59:59+08:00"}' | curl.exe -s http://127.0.0.1:8000/api/v1/auth/requests -H 'Content-Type: application/json' -H 'X-Caller-Did: did:vpp:operator:001' --data-binary '@-'

# 7. 数据所有者批准授权
'{"approverDid":"did:vpp:load-aggregator:002"}' | curl.exe -s http://127.0.0.1:8000/api/v1/auth/requests/auth_001/approve -H 'Content-Type: application/json' -H 'X-Caller-Did: did:vpp:load-aggregator:002' --data-binary '@-'

# 8. 查询最终授权状态
curl.exe -s http://127.0.0.1:8000/api/v1/auth/requests/auth_001
```

## 一键演示

安装依赖后执行：

```powershell
python -m scripts.demo
```

脚本会按顺序演示：注册请求方和数据所有者、幂等重放、注册设备、验证签名、申请授权、批准授权、查询最终状态。

## 运行测试

```powershell
python -m pytest -q
```

当前测试覆盖健康检查、统一错误响应、主体/设备注册、签名校验、授权状态流转、幂等冲突和调用方 DID 防冒用。

## Mock 签名规则

为了让 Demo 不依赖密钥文件或区块链，签名采用可重复计算的教学规则：

```text
signature = Base64(SHA256(publicKey + ":" + payloadHash))
payloadHash = "sha256:" + 64位十六进制摘要
```

真实项目中应替换为标准非对称签名算法、DID Document 公钥解析和安全密钥管理，不能沿用此 Mock 规则。

## 请求头规则

- `X-Trace-Id`：可选；未传时服务自动生成，响应中始终返回。
- `Idempotency-Key`：写接口可选；同一键和同一请求会重放首次响应，同一键对应不同请求返回 `40901`。
- `X-Caller-Did`：授权申请和审批的跨服务调用应传；传入后必须分别与 `requesterDid`、`approverDid` 一致，否则返回 `40102`。

## 目录结构

```text
identity-did/
├── app/
│   ├── errors.py       # 统一响应与业务异常
│   ├── main.py         # FastAPI 路由
│   ├── models.py       # 请求模型
│   ├── service.py      # DID、授权、幂等业务逻辑
│   └── store.py        # 内存存储与编号生成
├── scripts/
│   └── demo.py         # 一键演示脚本
├── tests/              # 自动化测试
└── requirements.txt
```

## 补充区（为 Demo 增加）

以下内容是为了使模块能够独立运行和学习而补充的，不代表项目已确定的生产方案：

- 使用 FastAPI TestClient 编排一键演示流程。
- 使用内存存储代替 PostgreSQL/Redis。
- 使用确定性 Mock 签名代替 Ed25519/ECDSA 与真实 DID Resolver。
- `X-Caller-Did` 仅做字段一致性校验，未实现 OAuth2、JWT、mTLS 或服务身份认证。
- 幂等记录仅在当前进程有效，未实现分布式锁与持久化。
