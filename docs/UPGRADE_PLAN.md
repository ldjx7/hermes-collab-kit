# Hermes ACP Client Plugin 改造为全能协作系统方案

**生成者**: Gemini (gemini-3.1-pro-preview)  
**日期**: 2026-04-14  
**委托**: 通过 ACP 派发任务生成

---

## 1. 架构设计

### 1.1 目标架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     用户 / Hermes Agent                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                    PM Skill (新增)                           │
│  - 需求 intake / 任务分析 / 上下文管理 / 路由决策              │
└────┬──────────────────────────────────────────────┬─────────┘
     │                                              │
     ▼                                              ▼
┌─────────────────┐                    ┌─────────────────────┐
│  GSD 路由 (新增) │                    │  Coder Skill (新增) │
│  任务规划/分解    │                    │  专业 coding worker │
└─────────────────┘                    └─────┬───────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│              ACP Client Plugin (现有升级)                     │
│  - acp_dispatch / acp_progress / acp_result / ...           │
│  - Worker 管理：Gemini/Claude/Codex/Qwen                     │
│  - 自动故障转移 / 模型追踪                                    │
└────┬──────────────────────────────────────────────┬─────────┘
     │                                              │
     ▼                                              ▼
┌─────────────────┐                    ┌─────────────────────┐
│  任务后端 (新增) │                    │  文档后端 (新增)     │
│  - Local        │                    │  - Repo             │
│  - Feishu       │                    │  - Feishu Doc       │
└─────────────────┘                    └─────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────┐
│              飞书集成 (可选 - Phase 5)                        │
│  - Bot / OAuth / Task 同步 / Doc 同步                         │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 核心组件对比

| 组件 | 当前状态 | 改造后 | 工作量 |
|------|----------|--------|--------|
| **PM 系统** | ❌ 无 | ✅ 新增 | 3 天 |
| **任务后端** | ❌ 无 | ✅ 新增 | 2 天 |
| **文档后端** | ❌ 无 | ✅ 新增 | 2 天 |
| **Coder Skill** | ❌ 无 | ✅ 新增 | 2 天 |
| **GSD 集成** | ❌ 无 | ✅ 新增 | 1 天 |
| **飞书集成** | ❌ 无 | ✅ 可选 | 3 天 |
| **ACP Client** | ✅ 已有 | 🔧 升级 | 1 天 |

### 1.3 数据流

```
用户请求
  ↓
PM Skill (需求分析)
  ↓
判断是否需要规划？
  ├─ 是 → GSD 路由 (任务分解) → 任务列表
  └─ 否 → 直接任务
  ↓
选择执行者
  ├─ 简单任务 → 直接执行
  └─ 复杂任务 → Coder Skill
  ↓
Coder 通过 ACP Client 派发
  ↓
ACP Worker (Gemini/Claude...)
  ↓
执行完成
  ↓
更新任务后端 + 文档后端
  ↓
返回结果给用户
```

---

## 2. 分阶段实施计划

### Phase 1: PM 系统（核心）⭐⭐⭐⭐⭐

**目标**: 实现需求分析和任务路由

**新增文件**:
```
skills/pm/
├── __init__.py
├── pm.py              # PM 主逻辑
├── task_intake.py     # 需求收集
├── context_manager.py # 上下文管理
├── router.py          # 任务路由
└── scripts/
    └── pm.py          # 命令行工具
```

**核心功能**:
- 需求 intake（结构化收集）
- 任务拆解（大任务 → 小任务）
- 上下文管理（刷新/同步）
- 路由决策（Coder vs 直接执行）

**代码示例** (`skills/pm/pm.py`):
```python
class PM:
    def __init__(self, config_path: str = None):
        self.config = load_config(config_path)
        self.context = ContextManager()
        self.router = Router()
    
    async def intake(self, requirement: str) -> Task:
        """需求分析"""
        # 调用 Gemini 分析需求
        analysis = await self.analyze(requirement)
        return Task(
            title=analysis.title,
            description=analysis.description,
            priority=analysis.priority,
            estimated_tokens=analysis.estimated_tokens
        )
    
    async def route(self, task: Task) -> str:
        """路由决策"""
        if task.complexity > self.config.threshold:
            return "coder"  # 派发给 Coder
        else:
            return "direct"  # 直接执行
```

**工作量**: 3 天

**验收标准**:
- [ ] `pm init` 可以初始化项目
- [ ] `pm context --refresh` 刷新上下文
- [ ] `pm route` 正确路由任务
- [ ] 单元测试覆盖率 > 80%

---

### Phase 2: 任务/文档后端 ⭐⭐⭐⭐

**目标**: 实现任务和文档的持久化

**后端选项**:
- **Local**: 本地 JSON 文件存储
- **Feishu**: 飞书任务/文档（需 Phase 5）

**新增文件**:
```
backends/
├── task/
│   ├── __init__.py
│   ├── base.py        # 抽象基类
│   ├── local.py       # 本地实现
│   └── feishu.py      # 飞书实现（Phase 5）
└── doc/
    ├── __init__.py
    ├── base.py
    ├── repo.py        # 仓库文档
    └── feishu.py      # 飞书文档（Phase 5）
```

**配置文件** (`pm.json`):
```json
{
  "task": {
    "backend": "local",
    "storage_path": "~/.hermes/pm/tasks"
  },
  "doc": {
    "backend": "repo",
    "root": "./docs"
  },
  "context": {
    "refresh_interval": 3600,
    "max_history": 100
  }
}
```

**代码示例** (`backends/task/local.py`):
```python
class LocalTaskBackend(TaskBackend):
    def __init__(self, storage_path: str):
        self.storage = Path(storage_path).expanduser()
        self.storage.mkdir(parents=True, exist_ok=True)
    
    async def create(self, task: Task) -> str:
        task_id = generate_id()
        task_file = self.storage / f"{task_id}.json"
        task_file.write_text(json.dumps(task.dict(), indent=2))
        return task_id
    
    async def get(self, task_id: str) -> Task:
        task_file = self.storage / f"{task_id}.json"
        return Task.parse_json(task_file.read_text())
```

**工作量**: 2 天

**验收标准**:
- [ ] 任务 CRUD 操作正常
- [ ] 文档读写正常
- [ ] 支持 backend 切换
- [ ] 数据持久化验证

---

### Phase 3: Coder Skill ⭐⭐⭐⭐

**目标**: 专业 coding worker

**与现有 acp_dispatch 的区别**:
- **acp_dispatch**: 通用任务派发
- **Coder Skill**: 专注代码实现，包含代码审查、测试生成

**新增文件**:
```
skills/coder/
├── __init__.py
├── coder.py         # Coder 主逻辑
├── code_review.py   # 代码审查
├── test_gen.py      # 测试生成
└── scripts/
    └── coder.py     # 命令行工具
```

**代码示例** (`skills/coder/coder.py`):
```python
class Coder:
    def __init__(self, worker: str = "gemini"):
        self.worker = worker
        self.acp = ACPClient()
    
    async def implement(self, task: Task) -> CodeResult:
        """实现代码"""
        prompt = self.build_prompt(task)
        session_id = await self.acp.dispatch(
            task=prompt,
            worker=self.worker,
            timeout=300
        )
        result = await self.acp.result(session_id)
        return self.parse_code(result)
    
    async def review(self, code: str) -> ReviewResult:
        """代码审查"""
        # 调用 Gemini 审查
        pass
```

**工作量**: 2 天

**验收标准**:
- [ ] 可以接收任务并生成代码
- [ ] 代码审查功能正常
- [ ] 自动生成测试
- [ ] 与 PM 系统对接成功

---

### Phase 4: GSD 集成 ⭐⭐

**目标**: 任务规划能力

**依赖**: `get-shit-done-cc`

**新增文件**:
```
skills/pm/scripts/
└── route_gsd.py     # GSD 路由
```

**安装命令**:
```bash
npx get-shit-done-cc@latest --codex --global
```

**使用示例**:
```bash
# 路由到 GSD 进行规划
pm route-gsd --repo-root . --project "My Project"
```

**工作量**: 1 天

**验收标准**:
- [ ] GSD 安装成功
- [ ] `pm route-gsd` 可以调用
- [ ] 任务分解结果可用

---

### Phase 5: 飞书集成（可选）⭐⭐⭐

**目标**: 团队协作能力

**依赖**: `@larksuite/openclaw-lark`

**新增文件**:
```
skills/collab-bridge/
├── __init__.py
├── bot.py           # Bot 管理
├── oauth.py         # OAuth 流程
├── task_sync.py     # 任务同步
└── doc_sync.py      # 文档同步
```

**功能**:
- Bot 创建和配置
- OAuth 授权流程
- 任务同步到飞书
- 文档同步到飞书

**工作量**: 3 天

**验收标准**:
- [ ] Bot 可以创建
- [ ] OAuth 流程正常
- [ ] 任务/文档同步成功
- [ ] 群里可以 @bot 交互

---

## 3. 文件结构

### 3.1 改造后的完整目录树

```
hermes-collab-kit/
├── README.md
├── INSTALL.md
├── plugin.yaml              # 主配置
├── pm.json                  # PM 配置
│
├── skills/
│   ├── pm/
│   │   ├── __init__.py
│   │   ├── pm.py
│   │   ├── task_intake.py
│   │   ├── context_manager.py
│   │   ├── router.py
│   │   └── scripts/
│   │       └── pm.py
│   │
│   ├── coder/
│   │   ├── __init__.py
│   │   ├── coder.py
│   │   ├── code_review.py
│   │   ├── test_gen.py
│   │   └── scripts/
│   │       └── coder.py
│   │
│   └── collab-bridge/       # Phase 5
│       ├── __init__.py
│       ├── bot.py
│       ├── oauth.py
│       ├── task_sync.py
│       └── doc_sync.py
│
├── plugins/
│   └── acp-client/          # 现有插件（升级）
│       ├── acp/
│       │   ├── protocol.py
│       │   ├── transport.py
│       │   ├── session_manager.py
│       │   └── worker_manager.py
│       ├── tools.py
│       ├── schemas.py
│       └── plugin.yaml
│
├── backends/
│   ├── task/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── local.py
│   │   └── feishu.py
│   │
│   └── doc/
│       ├── __init__.py
│       ├── base.py
│       ├── repo.py
│       └── feishu.py
│
├── examples/
│   ├── pm.json.example
│   ├── openclaw.json5.snippets.md
│   └── tasks/
│       └── sample_task.json
│
├── tests/
│   ├── test_pm.py
│   ├── test_coder.py
│   ├── test_backends.py
│   └── test_integration.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── PM_GUIDE.md
    ├── CODER_GUIDE.md
    └── DEPLOYMENT.md
```

### 3.2 目录说明

| 目录 | 作用 |
|------|------|
| `skills/pm/` | PM 系统 - 需求分析和路由 |
| `skills/coder/` | Coder - 专业 coding worker |
| `skills/collab-bridge/` | 协作桥接 - 飞书集成 |
| `plugins/acp-client/` | ACP 客户端 - 现有插件升级 |
| `backends/` | 后端实现 - 任务/文档存储 |
| `examples/` | 配置示例 |
| `tests/` | 测试套件 |
| `docs/` | 详细文档 |

---

## 4. 配置示例

### 4.1 plugin.yaml (改造后)

```yaml
name: hermes-collab-kit
version: 1.0.0
description: 全能协作系统 - PM + Coder + ACP

skills:
  - pm
  - coder
  - collab-bridge  # 可选

plugins:
  - acp-client

backends:
  task: local  # 或 feishu
  doc: repo    # 或 feishu

workers:
  default: gemini
  available:
    - gemini
    - claude
    - codex
    - qwen
```

### 4.2 pm.json 示例

```json
{
  "project": {
    "name": "My Project",
    "root": "/path/to/project"
  },
  "task": {
    "backend": "local",
    "storage_path": "~/.hermes/pm/tasks"
  },
  "doc": {
    "backend": "repo",
    "root": "./docs"
  },
  "context": {
    "refresh_interval": 3600,
    "max_history": 100
  },
  "router": {
    "complexity_threshold": 500,
    "prefer_coder": true
  },
  "worker": {
    "default": "gemini",
    "timeout": 300,
    "auto_fallback": true
  }
}
```

### 4.3 环境变量

```bash
# 必需
export HERMES_CONFIG_PATH=~/.hermes/pm.json

# 飞书集成（Phase 5）
export FEISHU_APP_ID=xxx
export FEISHU_APP_SECRET=xxx
export FEISHU_BOT_NAME=CollabBot

# Worker API Keys
export GEMINI_API_KEY=xxx  # 可选，OAuth 也可
export CLAUDE_API_KEY=xxx
```

---

## 5. 迁移路径

### 5.1 从当前插件平滑升级

**保留现有功能**:
- ✅ 8 个 ACP 工具继续可用
- ✅ Worker 管理功能保留
- ✅ 故障转移功能保留
- ✅ 配置向后兼容

**分阶段启用**:
```bash
# Phase 1: 只安装 PM 系统
hermes plugins install hermes-collab-kit@phase1

# Phase 2: 启用任务后端
hermes plugins update hermes-collab-kit --enable task-backend

# Phase 3: 启用 Coder
hermes plugins update hermes-collab-kit --enable coder

# ... 按需启用
```

### 5.2 用户升级步骤

```bash
# 1. 备份当前配置
cp -r ~/.hermes/plugins/acp-client ~/.hermes/plugins/acp-client.bak

# 2. 安装新版本
hermes plugins install https://github.com/xxx/hermes-collab-kit.git

# 3. 初始化 PM
pm init --project-name my-project

# 4. 验证
pm --version
coder --version
acp_worker_status

# 5. 运行第一个任务
pm intake "实现一个登录功能"
pm route
```

---

## 6. 工作量和时间线

### 6.1 总工作量预估

| Phase | 工作量 | 累计 |
|-------|--------|------|
| Phase 1: PM 系统 | 3 天 | 3 天 |
| Phase 2: 任务/文档后端 | 2 天 | 5 天 |
| Phase 3: Coder Skill | 2 天 | 7 天 |
| Phase 4: GSD 集成 | 1 天 | 8 天 |
| Phase 5: 飞书集成 | 3 天 | 11 天 |
| **总计** | **11 天** | - |

### 6.2 关键里程碑

| 时间 | 里程碑 | 交付物 |
|------|--------|--------|
| Week 1 | Phase 1 完成 | PM 系统可用 |
| Week 2 | Phase 2-3 完成 | 任务后端 + Coder |
| Week 3 | Phase 4-5 完成 | 完整系统 |

### 6.3 风险提示

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| GSD 兼容性 | 中 | 中 | 提前测试 |
| 飞书 API 变更 | 低 | 高 | 关注官方文档 |
| 性能问题 | 中 | 中 | 负载测试 |
| OAuth 流程复杂 | 高 | 中 | 详细文档 |

---

## 7. 与 OpenClaw 的差异化

### 7.1 保持的优势

| 优势 | 说明 |
|------|------|
| **轻量级** | 单插件安装，不依赖 OpenClaw |
| **多 Worker** | 4 个 Worker 支持，不绑定 Codex |
| **故障转移** | 自动切换，OpenClaw 没有 |
| **模型追踪** | 实时知道用了哪个模型 |

### 7.2 新增竞争力

| 竞争力 | 说明 |
|--------|------|
| **PM 系统** | 需求分析和路由 |
| **任务管理** | Local/Feishu 双后端 |
| **文档同步** | Repo/Feishu 双后端 |
| **渐进式** | 按需启用功能 |

---

## 8. 快速开始

### 8.1 安装命令

```bash
# 方式 1: 从 GitHub 安装
hermes plugins install https://github.com/xxx/hermes-collab-kit.git

# 方式 2: 本地开发安装
cd /path/to/hermes-collab-kit
ln -s $(pwd) ~/.hermes/plugins/collab-kit
```

### 8.2 验证流程

```bash
# 1. 检查版本
pm --version
coder --version
acp_worker_status

# 2. 初始化项目
pm init --project-name demo --task-backend local --doc-backend repo

# 3. 刷新上下文
pm context --refresh

# 4. 路由任务
pm route-gsd --repo-root .

# 5. 派发任务
coder "实现一个 hello world"
```

### 8.3 第一个任务示例

```bash
# 需求 intake
pm intake "创建一个用户登录模块，包含注册、登录、JWT 认证"

# 自动路由
pm route

# 执行
coder "实现登录模块"

# 查看进度
acp_progress --task_id <session_id>

# 获取结果
acp_result --task_id <session_id>
```

---

## 总结

### 改造后你将获得

✅ **完整的协作系统** - PM + Coder + ACP + 任务/文档管理

✅ **渐进式升级** - 按需启用功能，不影响现有使用

✅ **保持优势** - 多 Worker 支持、故障转移、模型追踪

✅ **新增能力** - 需求分析、任务规划、团队协作

### 建议实施顺序

1. **先做 Phase 1** - PM 系统（3 天），验证核心价值
2. **再做 Phase 2-3** - 任务后端 + Coder（4 天），完整工作流
3. **最后 Phase 4-5** - GSD+ 飞书（4 天），团队协作

### 可以立即开始的

```bash
# 1. 创建项目结构
mkdir -p hermes-collab-kit/{skills,plugins,backends,examples,tests,docs}

# 2. 开始 Phase 1
cd hermes-collab-kit/skills/pm
# 开始编写 pm.py...
```

---

**方案完成！可以开始实施了！** 🚀
