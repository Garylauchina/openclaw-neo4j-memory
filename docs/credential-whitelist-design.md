# 凭证白名单机制设计

**版本：** v1.0  
**创建时间：** 2026-04-09  
**关联 Issue：** #33  
**安全级别：** 🔴 高（涉及敏感信息处理）

---

## 一、设计目标

在扩展记忆系统摄入范围的同时，**确保不会意外摄入个人隐私信息**，只摄入工作相关的凭证和配置。

### 核心原则

1. **白名单机制 > 黑名单机制** - 只允许明确配置的类型，而非"除了禁止的都是允许的"
2. **最小权限原则** - 只摄入完成任务必需的信息
3. **透明可审计** - 所有摄入的凭证都有日志记录
4. **用户可控** - 用户可以随时查看、删除已摄入的凭证

---

## 二、信息分类框架

### 2.1 信息类型矩阵

| 信息类型 | 例子 | 是否摄入 | 理由 |
|----------|------|----------|------|
| **工作凭证** | API Key (Moltbook, OpenAI, GitHub) | ✅ 允许 | Agent 工作需要 |
| **服务配置** | 数据库连接字符串、服务端点 | ✅ 允许 | Agent 工作需要 |
| **Agent 身份** | Agent ID、注册信息 | ✅ 允许 | 身份识别需要 |
| **用户偏好** | 回答风格、时区、语言 | ✅ 允许 | 个性化服务需要 |
| **个人隐私** | 身份证号、护照号、社保号 | ❌ 禁止 | 与 Agent 工作无关 |
| **金融信息** | 银行卡号、支付密码、信用卡 | ❌ 禁止 | 高风险，无关 |
| **健康信息** | 病历、诊断记录 | ❌ 禁止 | 高度敏感，无关 |
| **家庭信息** | 家庭住址、家人信息 | ❌ 禁止 | 隐私，无关 |

### 2.2 凭证分级

| 级别 | 类型 | 存储方式 | 访问控制 |
|------|------|----------|----------|
| **L1 - 公开** | 公开 API 端点、文档链接 | 明文 | 无限制 |
| **L2 - 工作凭证** | API Key、Access Token | 加密 | 仅 Agent |
| **L3 - 敏感** | 数据库密码、私钥 | 加密 + 审计 | 仅 Agent + 日志 |
| **L4 - 禁止** | 个人隐私、金融信息 | 不存储 | N/A |

---

## 三、白名单实现方案

### 3.1 配置文件结构

```json
{
  "plugins": {
    "entries": {
      "neo4j-memory": {
        "config": {
          "auto_ingest": true,
          "ingest_paths": [
            "/Users/liugang/.openclaw/workspace",
            "/Users/liugang/.openclaw/neo4j-memory.env"
          ],
          "credential_whitelist": {
            "enabled": true,
            "allowed_patterns": [
              "MOLTBOOK_API_KEY",
              "OPENAI_API_KEY",
              "GITHUB_TOKEN",
              "NEO4J_PASSWORD",
              ".*_API_KEY$",
              ".*_TOKEN$",
              ".*_SECRET$"
            ],
            "denied_patterns": [
              ".*PASSWORD.*HOME.*",
              ".*CREDIT_CARD.*",
              ".*SSN.*",
              ".*PASSPORT.*",
              ".*BANK_ACCOUNT.*"
            ],
            "allowed_file_patterns": [
              "*.env",
              "*.config",
              "moltbook_api_key.txt",
              "credentials.json"
            ],
            "denied_file_patterns": [
              "*.private",
              "*.secret",
              "*passwords*",
              "*personal*"
            ]
          }
        }
      }
    }
  }
}
```

### 3.2 过滤逻辑

```python
def should_ingest_key(key_name, file_path):
    """判断是否应该摄入该配置项"""
    
    # 1. 检查是否在白名单中
    is_allowed = any(
        re.match(pattern, key_name, re.IGNORECASE) 
        for pattern in whitelist.allowed_patterns
    )
    
    if not is_allowed:
        return False, "Not in whitelist"
    
    # 2. 检查是否在黑名单中（双重保护）
    is_denied = any(
        re.match(pattern, key_name, re.IGNORECASE)
        for pattern in whitelist.denied_patterns
    )
    
    if is_denied:
        return False, "Explicitly denied"
    
    # 3. 检查文件类型
    file_allowed = any(
        fnmatch(file_path, pattern)
        for pattern in whitelist.allowed_file_patterns
    )
    
    if not file_allowed:
        return False, "File type not allowed"
    
    return True, "Approved"
```

---

## 四、安全控制措施

### 4.1 加密存储

**方案 A：Neo4j 属性加密**
```cypher
// 创建凭证节点时加密 value 属性
CREATE (c:Credential {
    name: $name,
    value: encrypt($value, $encryption_key),
    encrypted: true,
    created_at: datetime()
})
```

**方案 B：外部密钥管理**
```python
# 使用系统钥匙串存储实际值
import keyring
keyring.set_password("neo4j-memory", "MOLTBOOK_API_KEY", api_key)

# Neo4j 只存储引用
CREATE (c:Credential {
    name: "MOLTBOOK_API_KEY",
    keyring_ref: "neo4j-memory:MOLTBOOK_API_KEY"
})
```

### 4.2 访问审计

```python
def access_credential(name, purpose):
    """访问凭证时记录审计日志"""
    log_audit({
        "action": "access_credential",
        "credential_name": name,
        "purpose": purpose,
        "timestamp": datetime.now(),
        "agent_id": get_agent_id()
    })
    return get_credential(name)
```

**审计日志格式：**
```json
{
  "timestamp": "2026-04-09T06:30:00Z",
  "action": "access_credential",
  "credential_name": "MOLTBOOK_API_KEY",
  "purpose": "Moltbook API call",
  "agent_id": "openclaw_neo4j_gary",
  "result": "success"
}
```

### 4.3 定期轮换提醒

```python
def check_credential_rotation():
    """检查凭证是否需要轮换"""
    credentials = get_all_credentials()
    for cred in credentials:
        age_days = (datetime.now() - cred.created_at).days
        if age_days > 90:  # 90 天轮换
            notify_user(f"Credential '{cred.name}' should be rotated")
```

---

## 五、实施计划

### Phase 1：基础白名单（本周）

- [ ] 实现白名单过滤逻辑
- [ ] 配置允许的模式列表
- [ ] 添加审计日志
- [ ] 测试验证

### Phase 2：加密存储（下周）

- [ ] 实现 Neo4j 属性加密
- [ ] 或集成系统钥匙串
- [ ] 更新检索逻辑支持解密

### Phase 3：高级功能（本月）

- [ ] 访问审计日志查询界面
- [ ] 凭证轮换提醒
- [ ] 凭证使用统计

---

## 六、测试用例

### 测试 1：允许工作凭证
```bash
# 配置 MOLTBOOK_API_KEY
echo "MOLTBOOK_API_KEY=test_key_123" >> test.env

# 摄入
curl -X POST http://127.0.0.1:18900/ingest -d '{"file": "test.env"}'

# 验证：应该成功摄入
curl -X POST http://127.0.0.1:18900/search -d '{"query": "MOLTBOOK_API_KEY"}'
# 预期：返回凭证实体
```

### 测试 2：禁止个人隐私
```bash
# 配置个人信息
echo "ID_CARD_NUMBER=123456" >> test.env

# 摄入
curl -X POST http://127.0.0.1:18900/ingest -d '{"file": "test.env"}'

# 验证：应该被过滤
curl -X POST http://127.0.0.1:18900/search -d '{"query": "ID_CARD_NUMBER"}'
# 预期：无结果
```

### 测试 3：审计日志
```bash
# 访问凭证
curl -X POST http://127.0.0.1:18900/credential/access -d '{"name": "MOLTBOOK_API_KEY", "purpose": "test"}'

# 查看审计日志
curl http://127.0.0.1:18900/audit/log?credential=MOLTBOOK_API_KEY
# 预期：返回访问记录
```

---

## 七、风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 误摄入个人隐私 | 低 | 高 | 白名单 + 黑名单双重保护 |
| 凭证泄露 | 低 | 高 | 加密存储 + 访问审计 |
| 凭证过期 | 中 | 中 | 定期轮换提醒 |
| 性能影响 | 低 | 低 | 缓存解密结果 |

---

## 八、决策记录

### 决策 1：白名单机制
**时间：** 2026-04-09  
**决策：** 采用白名单机制，只允许明确配置的模式  
**理由：** 比黑名单更安全，避免意外摄入

### 决策 2：加密存储
**时间：** 2026-04-09  
**决策：** Phase 1 先用明文（快速验证），Phase 2 实现加密  
**理由：** 平衡安全性和实施速度

### 决策 3：审计日志
**时间：** 2026-04-09  
**决策：** 所有凭证访问必须记录审计日志  
**理由：** 安全合规要求，便于追溯

---

**批准人：** OpenClaw Agent  
**下次审查：** 2026-04-16
