# TestCase Generation System for OpenCode + Bitbucket

一个为 OpenCode AI 代码生成平台设计的 TestCase 自动生成系统,专门用于 Bitbucket Server 环境。

## 核心问题

在使用 OpenCode 生成 TestCase 时,常见的问题:
- OpenCode 容易编造不存在的 Lib API
- 生成的 YAML 配置可能与实际 schema 不符
- 缺乏有效的上下文提供机制
- 缺乏生成后的自动校验

## 解决方案

本系统通过以下机制确保生成代码的准确性:

1. **上下文包生成器** - 自动扫描代码库,生成精准的 API 和 YAML schema 上下文
2. **标准化 Prompt 模板** - 严格约束 OpenCode 只使用已验证的 API
3. **多层校验系统** - 自动检测 API 使用、YAML 结构、交叉引用等
4. **修复助手** - 提供详细的修复指南和自动修复功能
5. **Git Hooks 集成** - 提交前自动校验,防止错误代码进入代码库

## 项目结构

```
.opencode/
├── tools/                      # 工具脚本
│   ├── generate_context.py    # 上下文生成器
│   ├── validate_case.py        # 校验器
│   └── fix_case.py             # 修复助手
├── registry/                   # 注册表缓存
│   ├── lib_api_registry.json
│   ├── yaml_schema_registry.json
│   └── case_patterns.json
├── prompts/                    # Prompt 模板库
├── context_packages/           # 生成的上下文包
├── hooks/                      # Git hooks
│   └── pre-commit              # 提交前校验
└── docs/                       # 文档
    ├── ARCHITECTURE.md         # 系统架构设计
    ├── WORKFLOW.md             # 完整工作流
    └── API.md                  # API 文档
```

## 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/Philoallandatru/code-gen.git
cd code-gen

# 安装依赖
pip install pyyaml

# 安装 Git Hook (推荐)
cp .opencode/hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit
```

### 2. 生成上下文包

```bash
python .opencode/tools/generate_context.py "验证SSD在idle后进入PS4低功耗状态"
```

### 3. 使用 OpenCode 生成代码

1. 打开生成的 `prompt.md` 文件
2. 复制全部内容到 https://opencode.ai/
3. 让 OpenCode 生成代码
4. 保存生成的代码到本地

### 4. 校验生成的代码

```bash
python .opencode/tools/validate_case.py \
    .opencode/context_packages/package_xxx \
    TestCase/Power/test_xxx.py \
    configs/power/xxx.yaml
```

### 5. 修复问题(如果有)

```bash
# 查看修复指南
python .opencode/tools/fix_case.py \
    .opencode/context_packages/package_xxx \
    TestCase/Power/test_xxx.py \
    configs/power/xxx.yaml

# 或尝试自动修复
python .opencode/tools/fix_case.py \
    .opencode/context_packages/package_xxx \
    TestCase/Power/test_xxx.py \
    configs/power/xxx.yaml \
    --auto-fix
```

### 6. 提交到 Bitbucket

```bash
git add TestCase/Power/test_xxx.py configs/power/xxx.yaml
git commit -m "Add test case for xxx"
git push origin feature/add-xxx-test
```

## 核心特性

### 🎯 精准的上下文提供

- 自动扫描 Lib API,提取函数签名、参数、docstring
- 自动扫描 YAML 配置,提取 schema 结构
- 检索相似的 TestCase 作为参考
- 生成结构化的上下文包

### 🔒 严格的 API 约束

- 白名单机制:只允许使用已验证的 API
- 黑名单机制:禁止危险操作
- Import 语句校验
- 函数调用校验
- 参数数量和类型校验

### ✅ 多层校验系统

1. **API 使用校验** - 检查是否使用了未授权的 API
2. **YAML Schema 校验** - 检查 YAML 结构和字段类型
3. **交叉引用校验** - 检查 Python 和 YAML 的一致性
4. **代码结构校验** - 检查 try-finally、cleanup 等
5. **代码风格校验** - 检查 docstring、硬编码值等

### 🔧 智能修复助手

- 自动生成详细的修复指南
- 自动修复简单问题(Case ID、docstring 等)
- 提供相似 API 建议
- 提供修复步骤说明

### 🔗 Bitbucket 集成

- Git pre-commit hook 自动校验
- Bitbucket Pipelines CI/CD 集成
- Pull Request 模板
- 团队协作工作流

## 工作流程

```
需求 → 生成上下文包 → OpenCode 生成 → 本地校验 → 修复 → 提交 → PR → Review
```

详细工作流程请参考 [WORKFLOW.md](docs/WORKFLOW.md)

## 系统架构

系统采用分层架构:

1. **Registry Layer** - 注册表层,扫描和索引代码库
2. **Matching Layer** - 匹配层,匹配相关 API 和 schema
3. **Contract Layer** - 契约层,生成明确的使用约束
4. **Generation Layer** - 生成层,OpenCode 生成代码
5. **Validation Layer** - 校验层,多维度校验生成结果
6. **Feedback Layer** - 反馈层,修复和优化

详细架构设计请参考 [ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 文档

- [系统架构设计](docs/ARCHITECTURE.md) - 完整的系统架构和设计决策
- [完整工作流](docs/WORKFLOW.md) - 详细的使用流程和最佳实践
- [API 文档](docs/API.md) - 工具脚本的 API 文档
- [常见问题](docs/FAQ.md) - 常见问题和解决方案

## 适用场景

- 中大型团队(10+ 人)使用 OpenCode 生成 TestCase
- 代码托管在 Bitbucket Server
- 项目结构: TestCase/ + Lib/ + YAML 配置
- 需要 95%+ 的生成准确率
- 需要严格的代码审查流程

## 技术栈

- Python 3.8+
- OpenCode (https://opencode.ai/)
- Bitbucket Server
- Git Hooks
- YAML

## 贡献

欢迎贡献!请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT License

## 联系方式

- 项目主页: https://github.com/Philoallandatru/code-gen
- 问题反馈: https://github.com/Philoallandatru/code-gen/issues
