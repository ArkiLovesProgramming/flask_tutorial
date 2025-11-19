# JWT 认证功能文档

本文档介绍如何使用项目中的 JWT 身份验证功能。

## 功能特性

- ✅ JWT Token 认证（Access Token + Refresh Token）
- ✅ 密码加密存储（使用 bcrypt）
- ✅ 单点登录（SSO）支持
- ✅ Redis 会话存储（支持分布式部署）
- ✅ Token 刷新机制
- ✅ Token 黑名单（登出时撤销）

## API 端点

### 1. 注册用户

**POST** `/api/auth/register`

创建新用户账户。

**请求体：**
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**响应：**
```json
{
  "message": "User registered successfully",
  "id": 1
}
```

### 2. 用户登录

**POST** `/api/auth/login`

用户登录并获取 JWT tokens。

**请求体：**
```json
{
  "username": "john",
  "password": "securepassword123"
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "user": {
    "id": 1,
    "username": "john",
    "email": "john@example.com"
  }
}
```

### 3. 刷新 Access Token

**POST** `/api/auth/refresh`

使用 refresh token 获取新的 access token。

**请求体：**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 4. 登出

**POST** `/api/auth/logout`

登出用户，使当前 session 失效。

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "message": "Logged out successfully"
}
```

### 5. 获取当前用户信息

**GET** `/api/auth/me`

获取当前认证用户的信息。

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应：**
```json
{
  "user_id": 1,
  "username": "john"
}
```

## 使用示例

### cURL 示例

```bash
# 1. 注册用户
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"password123"}'

# 2. 登录
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"password123"}'

# 3. 使用 token 访问受保护端点
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer <access_token>"

# 4. 刷新 token
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<refresh_token>"}'

# 5. 登出
curl -X POST http://localhost:5000/api/auth/logout \
  -H "Authorization: Bearer <access_token>"
```

### Python 示例

```python
import requests

BASE_URL = "http://localhost:5000/api"

# 1. 注册
response = requests.post(f"{BASE_URL}/auth/register", json={
    "username": "john",
    "email": "john@example.com",
    "password": "password123"
})
print(response.json())

# 2. 登录
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "john",
    "password": "password123"
})
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# 3. 访问受保护端点
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
print(response.json())

# 4. 刷新 token
response = requests.post(f"{BASE_URL}/auth/refresh", json={
    "refresh_token": refresh_token
})
new_tokens = response.json()
access_token = new_tokens["access_token"]

# 5. 登出
response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
print(response.json())
```

## 配置说明

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `JWT_SECRET_KEY` | JWT 签名密钥 | `SECRET_KEY` 的值 |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access token 过期时间（分钟） | `30` |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token 过期时间（天） | `7` |
| `SESSION_TTL` | Session 在 Redis 中的 TTL（秒） | `1800` |
| `REDIS_SESSION_DB` | Redis session 存储的数据库编号 | `2` |
| `CELERY_BROKER_URL` | Redis broker URL（用于解析 Redis 连接） | `redis://127.0.0.1:6379/0` |

### Redis 数据库分配

- **DB 0**: Celery broker（任务队列）
- **DB 1**: Celery result backend（任务结果）
- **DB 2**: Session 存储（JWT sessions）

## 单点登录（SSO）实现

系统使用 Redis 存储 session 信息，实现单点登录：

1. **登录时**：在 Redis 中存储 session，key 格式为 `session:{user_id}:{token_prefix}`
2. **验证时**：检查 Redis 中是否存在对应的 session
3. **登出时**：删除 Redis 中的 session，并将 token 加入黑名单

这样，在分布式部署环境中，所有服务实例都可以通过共享的 Redis 验证 session。

## 保护端点

使用 `@require_auth` 装饰器保护需要认证的端点：

```python
from app.utils.auth_decorator import require_auth

@require_auth
def protected_endpoint():
    # 访问当前用户信息
    user_id = request.current_user["user_id"]
    username = request.current_user["username"]
    return {"user_id": user_id, "username": username}
```

## 数据库迁移

运行数据库迁移以添加 `password_hash` 字段：

```bash
alembic upgrade head
```

或者使用 Docker：

```bash
docker compose exec web alembic upgrade head
```

## 安全建议

1. **生产环境**：
   - 使用强密码的 `JWT_SECRET_KEY`
   - 使用 HTTPS
   - 设置合理的 token 过期时间
   - 定期轮换密钥

2. **密码策略**：
   - 最小长度：6 个字符（可在代码中调整）
   - 建议使用复杂密码（大小写字母、数字、特殊字符）

3. **Token 安全**：
   - 不要在客户端存储敏感信息
   - 使用 HTTPS 传输 token
   - 及时刷新过期的 token

## 故障排查

### Token 验证失败

- 检查 token 是否过期
- 检查 token 格式是否正确（Bearer token）
- 检查 Redis 连接是否正常
- 检查 session 是否在 Redis 中存在

### Redis 连接问题

- 检查 `CELERY_BROKER_URL` 配置
- 检查 Redis 服务是否运行
- 检查网络连接和防火墙设置

### 密码验证失败

- 确认密码是否正确
- 检查用户是否存在
- 检查用户是否有 `password_hash` 字段

