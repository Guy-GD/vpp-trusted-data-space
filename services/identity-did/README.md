# Identity DID 第一周 Mock 服务

`identity-did` 提供身份注册、Mock 身份验证和授权状态流转，用于第一周演示与跨模块联调。数据仅保存在当前进程内存中，服务重启后恢复为四个预置主体；本模块不连接数据库、DID 链或真实密钥系统。

> 安全提示：签名校验是 **Mock-only** 教学规则，不是生产密码学。禁止将它用于真实身份认证，也不要向服务提交真实凭据、私钥或生产数据。

## 开发环境与安装

统一从仓库根目录执行以下命令，并使用项目共享的 Python 3.11 环境。不要在 `services/identity-did` 内创建模块独立虚拟环境。

```powershell
python -m pip install -e packages/common -e "services/identity-did[test]"
```

安装完成后，从仓库根目录启动本地服务：

```powershell
python -m uvicorn identity_did.main:app --reload --port 8003
```

健康检查为 `http://127.0.0.1:8003/health`，交互文档为 `http://127.0.0.1:8003/docs`。

## 公开接口

本服务只提供以下七个业务接口：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| `GET` | `/health` | 健康检查 |
| `POST` | `/api/v1/identity/subjects` | 注册主体 DID |
| `POST` | `/api/v1/identity/devices` | 注册设备 DID |
| `POST` | `/api/v1/identity/verify` | 执行确定性的 Mock 签名校验 |
| `POST` | `/api/v1/auth/requests` | 创建 `requested` 授权 |
| `POST` | `/api/v1/auth/requests/{authId}/approve` | 批准或拒绝授权 |
| `GET` | `/api/v1/auth/requests/{authId}` | 查询授权并刷新过期状态 |

所有响应使用项目公共信封，包含 `code`、`message`、`data`、`traceId` 和 UTC `timestamp`。写接口支持 `Idempotency-Key`；授权创建与审批可传 `X-Caller-Did`，传入时必须与请求体中的调用方 DID 一致。

## 预置 DID

每次启动后，以下四个主体均已存在且状态为 `active`，联调无需先注册它们：

- `did:vpp:operator:001`
- `did:vpp:load-aggregator:001`
- `did:vpp:renewable-plant:001`
- `did:vpp:storage:001`

## 可重复正常路径演示

先在一个终端启动端口 `8003` 的服务，再在仓库根目录的另一个终端运行：

```powershell
python services/identity-did/scripts/demo.py
```

脚本使用预置的 `operator` 作为请求方、`load-aggregator` 作为数据所有者，并为每次 POST 生成新的幂等键。它会依次创建 `requested` 授权、将其批准为 `approved`、再查询最终记录，仅打印 Mock 响应中的 `data`。

如需改变服务地址或超时时间，可设置环境变量：

```powershell
$env:IDENTITY_DID_BASE_URL = "http://127.0.0.1:8003"
$env:IDENTITY_DID_TIMEOUT = "10"
python services/identity-did/scripts/demo.py
```

## 失败路径检查清单

可通过 Swagger 或任意 HTTP 客户端重复验证：

- `40102 unknown DID`：用不存在的 `requesterDid` 或 `ownerDid` 创建授权，或让 `X-Caller-Did` 与请求体不一致。
- `40303 authorization expired`：批准一个短有效期授权，越过 `expireAt` 后查询或再次审批。
- `40401 authorization not found`：查询或审批不存在的 `authId`。
- `40901 idempotency conflict`：对同一路径复用一个 `Idempotency-Key`，但改变请求体。
- `40902 authorization already decided`：对已批准或已拒绝且尚未过期的授权再次审批。

这些错误必须保持对应的 HTTP 状态码和公共错误信封；不要通过增加兼容接口或修改公共契约来规避失败。

## 自动化测试

从仓库根目录执行：

```powershell
python -m pytest services/identity-did/tests -v
```

测试覆盖七个公开端点、动态 ID、幂等、调用方校验、正常与失败状态流转、自动过期和并发边界。

## Docker

构建上下文必须是仓库根目录，以便同时安装 `vpp-common` 和本服务：

```powershell
docker build -f services/identity-did/Dockerfile -t vpp/identity-did:week1 .
docker run --rm -p 8003:8000 vpp/identity-did:week1
```

容器内服务监听 `8000`，以非 root 用户运行；映射后仍通过 `http://127.0.0.1:8003/health` 检查。

## Mock 边界

- 仓库为进程内字典，不提供持久化或分布式一致性。
- Mock 签名为 `Base64(SHA256(publicKey + ":" + payloadHash))`，不能替代 Ed25519/ECDSA、DID Document 解析或密钥管理。
- `X-Caller-Did` 只检查字段一致性，不实现 OAuth2、JWT、mTLS 或服务身份认证。
- 本交付物不包含生产基础设施、真实凭据和额外业务接口。
