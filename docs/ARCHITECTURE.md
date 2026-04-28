# 系统架构设计

## 概述

OpenCode TestCase 自动生成系统是一个轻量级、开发者友好的工具集，旨在提高 AI 代码生成的准确性和可靠性。

## 设计目标

1. **准确性**: 将 TestCase 生成准确率从 60-70% 提升到 95%+
2. **可控性**: 防止 LLM 编造不存在的 API 或配置
3. **易用性**: 简单的命令行工具，无需复杂配置
4. **可维护性**: 清晰的代码结构，易于扩展

## 核心组件

### 1. Registry Layer (注册表层)

负责扫描和索引代码库中的资源。

#### 1.1 Lib API Registry

**数据结构**:
```json
{
  "registry_version": "1.0",
  "last_updated": "2024-01-15T14:30:22Z",
  "scan_stats": {
    "total_modules": 15,
    "total_classes": 42,
    "total_functions": 156
  },
  "apis": [
    {
      "id": "lib.device.Device.__init__",
      "module": "Lib.device",
      "file_path": "Lib/device.py",
      "class_name": "Device",
      "function_name": "__init__",
      "signature": {
        "parameters": [
          {
            "name": "device_id",
            "type": "str",
            "required": true,
            "description": "设备ID"
          }
        ],
        "return_type": "None"
      },
      "docstring": "初始化设备对象",
      "usage_examples": [
        "device = Device('PS4_001')"
      ]
    }
  ]
}
```

**扫描逻辑**:
- 使用 Python AST 解析 Lib/ 目录下的所有 .py 文件
- 提取类、方法、函数的签名和文档
- 缓存 1 小时，避免重复扫描

#### 1.2 YAML Schema Registry

**数据结构**:
```json
{
  "registry_version": "1.0",
  "last_updated": "2024-01-15T14:30:22Z",
  "schemas": [
    {
      "schema_name": "test_case_config",
      "required_fields": [
        {
          "field": "case.id",
          "type": "string",
          "pattern": "^TC_[A-Z]+_\\d{8}$",
          "description": "测试用例ID"
        },
        {
          "field": "case.name",
          "type": "string",
          "description": "测试用例名称"
        }
      ],
      "optional_fields": [
        {
          "field": "case.tags",
          "type": "array",
          "description": "标签列表"
        }
      ],
      "examples": [
        {
          "file": "configs/test_power_ps4.yaml",
          "content": "..."
        }
      ]
    }
  ]
}
```

**扫描逻辑**:
- 解析 configs/ 目录下的所有 .yaml 文件
- 提取字段结构和类型
- 识别必填字段和可选字段

#### 1.3 TestCase Pattern Registry

**数据结构**:
```json
{
  "registry_version": "1.0",
  "last_updated": "2024-01-15T14:30:22Z",
  "patterns": {
    "common_imports": [
      "import unittest",
      "from Lib.device import Device"
    ],
    "common_structure": {
      "class_pattern": "class Test{Feature}(unittest.TestCase)",
      "setup_pattern": "def setUp(self): ...",
      "test_pattern": "def test_{action}(self): ..."
    },
    "common_practices": [
      "使用 try-finally 确保资源清理",
      "使用 load_case_config() 加载配置",
      "使用 self.assertEqual() 进行断言"
    ]
  },
  "cases": [
    {
      "file": "TestCase/test_power_ps4.py",
      "description": "PS4电源控制测试",
      "apis_used": [
        "Lib.device.Device",
        "Lib.power.PowerController"
      ],
      "yaml_fields_used": [
        "case.id",
        "device.id",
        "power.actions"
      ]
    }
  ]
}
```

**扫描逻辑**:
- 解析 TestCase/ 目录下的所有 .py 文件
- 提取 import 语句、类结构、方法模式
- 分析 API 使用和 YAML 字段引用

### 2. Matching Layer (匹配层)

负责根据需求匹配相关的 API、Schema 和相似案例。

#### 2.1 Requirement Parser

**输入**: 用户需求描述（自然语言）

**输出**: 结构化需求
```python
{
    "feature": "电源控制",
    "device_type": "PS4",
    "actions": ["开机", "关机", "重启"],
    "keywords": ["power", "ps4", "control"]
}
```

**解析逻辑**:
- 提取关键词（设备类型、功能、动作）
- 识别测试场景（正常流程、异常处理）

#### 2.2 API Matcher

**输入**: 结构化需求 + Lib API Registry

**输出**: 相关 API 列表

**匹配策略**:
1. **关键词匹配**: 基于需求关键词匹配 API 名称和文档
2. **依赖分析**: 如果匹配到某个类，自动包含其依赖的类
3. **相似度排序**: 按相关性排序，取 Top-K

#### 2.3 Similar Case Retriever

**输入**: 结构化需求 + TestCase Pattern Registry

**输出**: 相似测试用例列表

**检索策略**:
1. **TF-IDF 向量化**: 将需求和已有 Case 描述向量化
2. **余弦相似度**: 计算相似度分数
3. **Top-K 检索**: 返回最相似的 3-5 个案例

### 3. Generation Layer (生成层)

负责构建给 OpenCode 的 Prompt。

#### 3.1 Context Package Structure

```
.opencode/context_packages/package_20240115_143022/
├── context.md          # 完整上下文
├── prompt.md           # 给OpenCode的prompt
└── metadata.json       # 元数据
```

#### 3.2 Prompt Template

```markdown
# TestCase 生成任务

## 需求描述
{requirement}

## CRITICAL RULES - 必须严格遵守

1. **API 使用约束**:
   - 只能使用下面 "Allowed APIs" 中列出的 API
   - 禁止使用任何未列出的 import 或函数
   - 禁止编造不存在的 API

2. **YAML 配置约束**:
   - 只能使用下面 "YAML Schema" 中定义的字段
   - 必须包含所有必填字段
   - 禁止使用未定义的字段

3. **代码结构约束**:
   - 必须继承 unittest.TestCase
   - 必须调用 load_case_config() 加载配置
   - 必须使用 try-finally 确保资源清理
   - 必须有模块级 docstring

## Allowed APIs

{allowed_apis}

## YAML Schema

{yaml_schema}

## Similar Cases (参考)

{similar_cases}

## 输出要求

生成两个文件:
1. TestCase/test_{feature}.py - Python 测试代码
2. configs/test_{feature}.yaml - YAML 配置文件
```

### 4. Validation Layer (校验层)

负责校验生成的代码。

#### 4.1 API Usage Validator

**校验规则**:
- 检查所有 import 语句是否在白名单中
- 检查所有函数调用是否在白名单中
- 提供相似 API 建议

**实现**:
```python
def validate_api_usage(python_code, allowed_apis):
    issues = []
    
    # 解析 Python 代码
    tree = ast.parse(python_code)
    
    # 检查 import
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not is_allowed(alias.name, allowed_apis):
                    issues.append({
                        "type": "unauthorized_import",
                        "module": alias.name,
                        "suggestion": find_similar_api(alias.name, allowed_apis)
                    })
    
    return issues
```

#### 4.2 YAML Schema Validator

**校验规则**:
- 检查必填字段是否存在
- 检查字段类型是否正确
- 检查字段格式是否符合规范

**实现**:
```python
def validate_yaml_schema(yaml_content, schema):
    issues = []
    
    # 检查必填字段
    for field in schema["required_fields"]:
        if not has_field(yaml_content, field["field"]):
            issues.append({
                "type": "missing_required_field",
                "field": field["field"],
                "description": field["description"]
            })
    
    return issues
```

#### 4.3 Cross-Reference Validator

**校验规则**:
- 检查 Python 中读取的 YAML 字段是否存在
- 检查 Case ID 在 Python 和 YAML 中是否一致

**实现**:
```python
def validate_cross_reference(python_code, yaml_content):
    issues = []
    
    # 提取 Python 中读取的 YAML 字段
    yaml_fields = extract_yaml_field_access(python_code)
    
    # 检查字段是否存在
    for field in yaml_fields:
        if not has_field(yaml_content, field):
            issues.append({
                "type": "yaml_field_not_found",
                "field": field,
                "suggestion": "检查 YAML 配置或修改 Python 代码"
            })
    
    return issues
```

### 5. Feedback Layer (反馈层)

负责生成修复建议和自动修复。

#### 5.1 Fix Guide Generator

**输入**: 校验问题列表

**输出**: 修复指南文档

**生成逻辑**:
- 按严重程度排序问题
- 为每个问题生成详细的修复步骤
- 提供代码示例

#### 5.2 Auto Fixer

**支持的自动修复**:
1. 添加缺失的 YAML 必填字段
2. 统一 Python 和 YAML 中的 Case ID
3. 添加缺失的 docstring
4. 修正 Case ID 格式

**实现**:
```python
def auto_fix(python_file, yaml_file, issues):
    fixes_applied = []
    
    for issue in issues:
        if issue["type"] == "missing_required_field":
            # 自动添加字段
            add_yaml_field(yaml_file, issue["field"], generate_default_value(issue))
            fixes_applied.append(issue)
        
        elif issue["type"] == "case_id_mismatch":
            # 统一 Case ID
            unified_id = generate_case_id()
            update_python_case_id(python_file, unified_id)
            update_yaml_case_id(yaml_file, unified_id)
            fixes_applied.append(issue)
    
    return fixes_applied
```

## 数据流

```
用户需求
    ↓
[1. Registry Layer]
    ├─ 扫描 Lib/ → Lib API Registry
    ├─ 扫描 configs/ → YAML Schema Registry
    └─ 扫描 TestCase/ → TestCase Pattern Registry
    ↓
[2. Matching Layer]
    ├─ 解析需求 → 结构化需求
    ├─ 匹配 API → 相关 API 列表
    └─ 检索相似 Case → 相似案例列表
    ↓
[3. Generation Layer]
    └─ 构建 Prompt → context.md + prompt.md
    ↓
[人工操作: 复制 prompt.md 到 OpenCode]
    ↓
[OpenCode 生成代码]
    ↓
[人工操作: 下载代码到本地]
    ↓
[4. Validation Layer]
    ├─ API 使用校验
    ├─ YAML Schema 校验
    └─ 交叉引用校验
    ↓
[5. Feedback Layer]
    ├─ 生成修复指南
    └─ 自动修复（可选）
    ↓
[人工审核: 检查代码]
    ↓
[Git Commit]
    ↓
[Pre-commit Hook: 自动校验]
    ↓
[Push to Bitbucket]
```

## 技术选型

### 核心技术

- **Python 3.7+**: 主要开发语言
- **AST (Abstract Syntax Tree)**: 代码解析和分析
- **PyYAML**: YAML 文件解析
- **Git Hooks**: 自动化校验

### 为什么不使用数据库？

- **轻量级**: 避免额外的依赖和配置
- **可移植**: 基于文件系统，易于版本控制
- **快速启动**: 无需安装和配置数据库

### 为什么不使用向量数据库？

- **规模适中**: 100-500 个 TestCase，TF-IDF + Cosine 足够
- **简单高效**: 避免引入复杂的依赖
- **可扩展**: 如果规模增长，可以轻松迁移到向量数据库

## 性能优化

### 1. 注册表缓存

- 缓存有效期: 1 小时
- 缓存失效策略: 时间戳检查
- 强制刷新: 删除缓存文件

### 2. 增量扫描

- 只扫描修改过的文件
- 基于文件修改时间判断

### 3. 并行处理

- 多个文件的扫描可以并行
- 使用 Python multiprocessing

## 扩展性

### 1. 支持更多语言

当前系统专注于 Python，但架构设计支持扩展到其他语言：

- 替换 AST 解析器（如 Java 使用 JavaParser）
- 调整 API 提取逻辑
- 其他组件保持不变

### 2. 支持更多 AI 工具

当前系统针对 OpenCode，但可以轻松适配其他 AI 工具：

- 调整 Prompt 模板
- 保持校验和修复逻辑不变

### 3. 集成 CI/CD

可以集成到 Bitbucket Pipelines：

```yaml
# bitbucket-pipelines.yml
pipelines:
  pull-requests:
    '**':
      - step:
          name: Validate TestCases
          script:
            - pip install -r requirements.txt
            - python .opencode/tools/validate_all.py
```

## 安全性

### 1. 代码注入防护

- 使用 AST 解析，不执行用户代码
- 校验器只读取文件，不执行

### 2. 路径遍历防护

- 限制文件访问范围在项目目录内
- 验证文件路径合法性

### 3. 敏感信息保护

- 不在日志中输出敏感信息
- 不上传代码到外部服务（除了 OpenCode）

## 监控和日志

### 1. 生成日志

记录每次生成的详细信息：
- 需求描述
- 匹配的 API 数量
- 相似案例数量
- 生成时间

### 2. 校验日志

记录每次校验的结果：
- 校验通过/失败
- 问题类型和数量
- 修复建议

### 3. 统计指标

- 生成成功率
- 校验通过率
- 自动修复成功率
- 平均生成时间

## 未来改进

### 1. 智能 Prompt 优化

- 根据历史生成结果优化 Prompt
- A/B 测试不同的 Prompt 模板

### 2. 增强相似度检索

- 使用语义向量（如 Sentence-BERT）
- 支持多模态检索（代码 + 文档）

### 3. 交互式修复

- 提供 Web UI 进行交互式修复
- 实时预览修复效果

### 4. 团队协作

- 共享注册表和上下文包
- 团队级别的最佳实践库

## 总结

OpenCode TestCase 自动生成系统通过多层防御策略，确保 AI 生成的代码准确、可靠、可维护。系统设计轻量级、易用、可扩展，适合中小型团队快速落地使用。
