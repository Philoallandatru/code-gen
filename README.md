# OpenCode TestCase 自动生成系统

一个为 OpenCode AI 代码生成工具设计的 TestCase 自动生成系统，确保生成的测试用例准确使用项目的 Lib 库和 YAML 配置。

## 🎯 核心特性

- **白名单机制**: 防止 LLM 编造不存在的 API
- **Schema 约束**: 确保 YAML 配置符合项目规范
- **相似案例检索**: 基于已有 TestCase 生成新用例
- **多层校验**: API 使用、YAML 结构、交叉引用、代码风格
- **自动修复**: 智能修复常见问题
- **Git 集成**: Pre-commit hook 自动校验

## 📋 系统要求

- Python 3.7+
- Git
- OpenCode 账号 (https://opencode.ai/)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 安装 Git Hooks

```bash
python .opencode/tools/opencode-tools.py setup-hooks
```

### 3. 生成上下文包

```bash
python .opencode/tools/opencode-tools.py generate "测试PS4电源开关功能"
```

输出示例:
```
✅ 上下文包已生成: .opencode/context_packages/package_20240115_143022/

📋 生成的文件:
   - context.md: 完整上下文（Allowed APIs、YAML Schema、Similar Cases）
   - prompt.md: 给OpenCode的prompt
   - metadata.json: 元数据

📝 下一步:
   1. 打开 prompt.md
   2. 复制全部内容
   3. 粘贴到 OpenCode (https://opencode.ai/)
   4. 等待生成代码
   5. 运行校验: python .opencode/tools/validate_case.py ...
```

### 4. 在 OpenCode 中生成代码

1. 访问 https://opencode.ai/
2. 打开生成的 `prompt.md` 文件
3. 复制全部内容到 OpenCode
4. 点击生成
5. 下载生成的代码

### 5. 校验生成的代码

```bash
python .opencode/tools/opencode-tools.py validate \
    .opencode/context_packages/package_20240115_143022 \
    TestCase/test_power_ps4.py \
    configs/test_power_ps4.yaml
```

### 6. 修复问题（如果有）

```bash
# 查看修复指南
python .opencode/tools/opencode-tools.py fix \
    .opencode/context_packages/package_20240115_143022 \
    TestCase/test_power_ps4.py \
    configs/test_power_ps4.yaml

# 尝试自动修复
python .opencode/tools/opencode-tools.py fix \
    .opencode/context_packages/package_20240115_143022 \
    TestCase/test_power_ps4.py \
    configs/test_power_ps4.yaml \
    --auto-fix
```

### 7. 提交代码

```bash
git add TestCase/test_power_ps4.py configs/test_power_ps4.yaml
git commit -m "Add test case for PS4 power control"
```

Git hook 会自动运行校验，如果失败会阻止提交。

## 📁 项目结构

```
.
├── .opencode/
│   ├── tools/
│   │   ├── generate_context.py    # 上下文生成器
│   │   ├── validate_case.py       # 校验器
│   │   ├── fix_case.py            # 修复助手
│   │   └── opencode-tools.py      # CLI工具
│   ├── hooks/
│   │   └── pre-commit             # Git pre-commit hook
│   ├── registry/                  # 注册表缓存
│   ├── context_packages/          # 生成的上下文包
│   └── prompts/                   # Prompt模板
├── TestCase/                      # 测试用例目录
├── configs/                       # YAML配置目录
├── Lib/                          # 项目库目录
├── docs/                         # 文档
│   ├── ARCHITECTURE.md           # 系统架构
│   └── WORKFLOW.md               # 工作流程
└── README.md
```

## 🔧 工具说明

### generate_context.py - 上下文生成器

扫描代码库，生成包含以下内容的上下文包：

- **Allowed APIs**: 白名单 API 列表（从 Lib/ 扫描）
- **YAML Schema**: YAML 配置规范（从 configs/ 提取）
- **Similar Cases**: 相似测试用例（从 TestCase/ 检索）
- **Prompt**: 给 OpenCode 的完整 prompt

**特性**:
- 注册表缓存（1小时有效期）
- 智能 API 匹配
- 相似度检索（TF-IDF + Cosine）

### validate_case.py - 校验器

对生成的代码进行多维度校验：

1. **API 使用校验**: 检查是否使用了未授权的 API
2. **YAML Schema 校验**: 检查必填字段、字段格式
3. **交叉引用校验**: Python 与 YAML 一致性
4. **代码结构校验**: test 方法、try-finally、load_case_config()
5. **代码风格校验**: docstring、硬编码值

**输出**:
- 详细的校验报告
- 修复建议
- 相似 API 推荐

### fix_case.py - 修复助手

根据校验结果提供修复方案：

**手动修复模式**:
- 生成详细的修复指南
- 分步骤的修复说明

**自动修复模式**:
- 添加缺失的 YAML 字段
- 统一 Python 和 YAML 中的 Case ID
- 添加缺失的 docstring
- 修正 Case ID 格式

### opencode-tools.py - CLI 工具

统一的命令行入口：

```bash
# 生成上下文包
opencode-tools generate <requirement>

# 校验TestCase
opencode-tools validate <package> <py> <yaml>

# 修复TestCase
opencode-tools fix <package> <py> <yaml> [--auto-fix]

# 安装Git Hooks
opencode-tools setup-hooks
```

## 🔍 校验规则

### API 使用校验

- ✅ 只能使用上下文包中列出的 API
- ❌ 禁止使用未授权的 import
- ❌ 禁止使用未授权的函数调用

### YAML Schema 校验

- ✅ 必须包含所有必填字段
- ✅ 字段格式必须正确
- ❌ 禁止使用未定义的字段

### 交叉引用校验

- ✅ Python 中读取的 YAML 字段必须存在
- ✅ Case ID 在 Python 和 YAML 中必须一致
- ❌ 禁止硬编码配置值

### 代码结构校验

- ✅ 必须有 test 方法
- ✅ 必须调用 load_case_config()
- ✅ 必须有 try-finally 结构
- ✅ 必须有模块 docstring

## 🎨 最佳实践

### 1. 编写清晰的需求描述

```bash
# ❌ 不好
python .opencode/tools/generate_context.py "测试电源"

# ✅ 好
python .opencode/tools/generate_context.py "测试PS4设备的电源开关功能，包括开机、关机和重启"
```

### 2. 定期更新注册表

```bash
# 删除缓存，强制重新扫描
rm -rf .opencode/registry/*
python .opencode/tools/generate_context.py "..."
```

### 3. 使用 Git Hooks

安装 pre-commit hook 后，每次提交都会自动校验，避免提交有问题的代码。

### 4. 迭代修复

如果自动修复无法解决所有问题，按照修复指南手动修复，然后重新校验。

### 5. 保留上下文包

上下文包包含了生成时的完整上下文，便于后续追溯和调试。

## 🐛 常见问题

### Q: 校验失败，提示 "Unauthorized import"

**A**: 生成的代码使用了不在白名单中的 API。

**解决方案**:
1. 检查上下文包中的 Allowed APIs 列表
2. 如果 API 确实存在但未被扫描到，删除注册表缓存重新生成
3. 如果 API 不存在，使用修复助手查看替代方案

### Q: Case ID 格式错误

**A**: Case ID 必须符合格式 `TC_XXX_YYYYMMDD`

**解决方案**:
```bash
# 自动修复
python .opencode/tools/fix_case.py <package> <py> <yaml> --auto-fix
```

### Q: YAML 缺少必填字段

**A**: YAML 配置缺少 `case_id` 或 `description` 等必填字段

**解决方案**:
```bash
# 自动修复
python .opencode/tools/fix_case.py <package> <py> <yaml> --auto-fix
```

### Q: Git hook 阻止提交

**A**: 代码未通过校验

**解决方案**:
```bash
# 1. 查看错误信息
git commit  # 会显示详细错误

# 2. 修复问题
python .opencode/tools/fix_case.py <package> <py> <yaml> --auto-fix

# 3. 重新提交
git add .
git commit

# 或者跳过校验（不推荐）
git commit --no-verify
```

## 📚 更多文档

- [系统架构](docs/ARCHITECTURE.md) - 详细的系统设计
- [工作流程](docs/WORKFLOW.md) - 完整的使用流程
- [贡献指南](CONTRIBUTING.md) - 如何贡献代码

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- OpenCode: https://opencode.ai/
- GitHub: https://github.com/Philoallandatru/code-gen
