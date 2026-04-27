# 系统架构设计

## 概述

本文档描述 TestCase Generation System 的完整架构设计,包括各层职责、数据流、关键决策等。

## 设计目标

1. **准确性**: 确保生成的 TestCase 准确使用 Lib API 和 YAML 配置
2. **可验证性**: 所有生成结果都可以自动校验
3. **可追溯性**: 保留完整的生成上下文和决策过程
4. **易用性**: 开发者友好的工作流
5. **可扩展性**: 支持 100-500 个 TestCase 的规模

## 核心原则

> **LLM 不允许自由猜测 Lib API;只能从已索引、已验证、已匹配的 Lib API 和 YAML schema 中选择。**

这是整个系统的核心约束,所有设计都围绕这个原则展开。

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    TestCase Generation System                │
└─────────────────────────────────────────────────────────────┘

1. Registry Layer (注册表层)
   ├── Lib API Registry Builder      # 扫描Lib生成API索引
   ├── YAML Schema Registry Builder  # 扫描YAML生成Schema
   └── TestCase Pattern Extractor    # 提取已有Case模式

2. Matching Layer (匹配层)
   ├── Requirement Parser            # 解析需求
   ├── Capability Matcher            # 匹配Lib能力
   └── Similar Case Retriever        # 检索相似Case

3. Contract Layer (契约层)
   ├── Contract Generator            # 生成TestCase Contract
   └── Contract Validator            # 验证Contract完整性

4. Generation Layer (生成层)
   └── OpenCode Integration          # OpenCode生成代码

5. Validation Layer (校验层)
   ├── API Usage Validator           # 校验API使用
   ├── YAML Schema Validator         # 校验YAML结构
   ├── Cross-Reference Validator     # 校验代码与YAML一致性
   └── Style Validator               # 校验代码风格

6. Feedback Layer (反馈层)
   ├── Error Reporter                # 生成错误报告
   └── Fix Helper                    # 修复助手
```

### 数据流

```
需求文本
    ↓
[Registry Layer] 扫描代码库,生成注册表
    ↓
[Matching Layer] 匹配相关API、Schema、相似Case
    ↓
[Contract Layer] 生成上下文包(Context Package)
    ↓
开发者复制到 OpenCode
    ↓
[Generation Layer] OpenCode 生成代码
    ↓
开发者保存到本地
    ↓
[Validation Layer] 多层校验
    ↓
[Feedback Layer] 生成修复建议
    ↓
开发者修复后提交
```

## 各层详细设计

### 1. Registry Layer (注册表层)

**职责**: 扫描代码库,建立 API 和 Schema 的索引

#### 1.1 Lib API Registry

**数据结构**:
```json
{
  "apis": {
    "power.wait_for_power_state": {
      "api_id": "power.wait_for_power_state",
      "file": "Lib/power/power_manager.py",
      "class": "PowerManager",
      "function": "wait_for_power_state",
      "params": [
        {"name": "target_state", "type": "str"},
        {"name": "timeout_ms", "type": "int"}
      ],
      "docstring": "Wait until SSD enters target power state.",
      "import_statement": "from Lib.power.power_manager import PowerManager"
    }
  }
}
```

**扫描策略**:
- 使用 Python AST 解析 Lib 目录下的所有 .py 文件
- 提取类、方法、参数、类型注解、docstring
- 缓存结果,1小时内有效
- 增量更新机制

#### 1.2 YAML Schema Registry

**数据结构**:
```json
{
  "schemas": {
    "low_power_latency_config": {
      "schema_id": "low_power_latency_config",
      "file": "configs/power/low_power_latency.yaml",
      "fields": [
        "case.id",
        "case.name",
        "power.target_state",
        "power.entry_timeout_ms"
      ],
      "example": { /* 完整的YAML示例 */ }
    }
  }
}
```

**扫描策略**:
- 递归扫描 configs 目录下的所有 .yaml 文件
- 提取字段路径、类型、示例值
- 识别常见模式和约束

#### 1.3 TestCase Pattern Registry

**数据结构**:
```json
{
  "patterns": {
    "test_apst_entry": {
      "file": "TestCase/Power/test_apst_entry.py",
      "imports": [
        "from Lib.power.power_manager import PowerManager"
      ],
      "test_methods": [
        {"name": "test_apst_entry", "has_try_finally": true}
      ],
      "snippet": "前500字符的代码片段"
    }
  }
}
```

**扫描策略**:
- 扫描 TestCase 目录下的所有 test_*.py 文件
- 提取 import 语句、测试方法结构
- 识别常见模式(try-finally、cleanup等)

### 2. Matching Layer (匹配层)

**职责**: 根据需求匹配相关的 API、Schema 和相似 Case

#### 2.1 Requirement Parser

**输入**: 原始需求文本
```
"验证SSD在idle 500ms后能够进入PS4低功耗状态"
```

**输出**: 结构化需求
```json
{
  "raw_text": "验证SSD在idle 500ms后能够进入PS4低功耗状态",
  "keywords": ["power", "PS4", "idle", "low_power"]
}
```

**解析策略**:
- 关键词提取(基于预定义的关键词映射表)
- 简单的模式匹配
- 未来可扩展为 NLP 解析

#### 2.2 Capability Matcher

**匹配策略**:
1. **关键词匹配** - 快速过滤候选 API
2. **语义匹配** (可选) - 使用 embedding 计算相似度
3. **依赖分析** - 自动补充相关的 API

**输出**: Top-K 匹配的 API 列表

#### 2.3 Similar Case Retriever

**检索策略**:
1. **基于 API 使用的检索** - 找到使用相同 API 的 Case
2. **基于关键词的检索** - BM25 算法
3. **混合排序** - 综合多个信号

**输出**: Top-5 相似 Case

### 3. Contract Layer (契约层)

**职责**: 生成明确的上下文包,约束 OpenCode 的生成行为

#### 3.1 Context Package 结构

```
context_packages/package_20260428_103045/
├── context.md        # 完整上下文(API、Schema、相似Case)
├── prompt.md         # 给OpenCode的最终prompt
└── metadata.json     # 元数据(用于后续校验)
```

#### 3.2 Prompt 模板

**关键部分**:
1. **CRITICAL RULES** - 严格约束
2. **Allowed Lib APIs** - 白名单
3. **YAML Configuration Schema** - Schema定义
4. **Similar TestCases** - 参考示例
5. **Output Format** - 输出格式要求

**设计原则**:
- 明确 > 隐含
- 约束 > 自由
- 示例 > 描述

### 4. Generation Layer (生成层)

**职责**: 与 OpenCode 集成,生成代码

#### 4.1 OpenCode 集成方式

**手动工作流**:
1. 开发者打开 prompt.md
2. 复制全部内容到 OpenCode
3. OpenCode 生成代码
4. 开发者保存到本地

**未来可扩展**:
- OpenCode API 集成(如果提供)
- 自动化脚本

### 5. Validation Layer (校验层)

**职责**: 多维度校验生成的代码

#### 5.1 API Usage Validator

**校验项**:
- Import 语句是否在白名单中
- 函数调用是否在白名单中
- 参数数量是否匹配
- 是否有硬编码的配置值
- 是否有 try-finally 结构

**实现方式**: Python AST 解析

#### 5.2 YAML Schema Validator

**校验项**:
- 必填字段是否存在
- 字段类型是否正确
- 字段值是否在允许范围内
- 字段格式是否符合 pattern

**实现方式**: YAML 解析 + Schema 验证

#### 5.3 Cross-Reference Validator

**校验项**:
- Python 读取的 YAML 字段是否存在
- YAML 定义的字段是否被使用
- Case ID 是否一致
- API 参数来源是否正确

**实现方式**: AST + YAML 交叉分析

#### 5.4 Style Validator

**校验项**:
- 是否有 docstring
- 代码风格是否符合规范
- 命名是否规范

**实现方式**: Pylint / Flake8 集成

### 6. Feedback Layer (反馈层)

**职责**: 生成修复建议,辅助开发者修复问题

#### 6.1 Error Reporter

**输出格式**:
```
❌ ERRORS (Must Fix)
1. [API Usage] 使用了未授权的API: power.wait_for_state
   💡 Suggestion: 你是否想使用 'power.wait_for_power_state'?

⚠️  WARNINGS (Should Fix)
1. [Code Style] 发现可能的硬编码值: PS4
   💡 Suggestion: 建议将配置值放在YAML中
```

#### 6.2 Fix Helper

**功能**:
1. **生成修复指南** - 详细的修复步骤
2. **自动修复** - 修复简单问题(Case ID、docstring等)
3. **相似 API 建议** - 使用 difflib 查找相似 API

## 关键设计决策

### 决策 1: 为什么使用注册表而不是实时扫描?

**原因**:
- 扫描代码库耗时(几十秒到几分钟)
- 大部分时间 Lib 和 YAML 不会变化
- 缓存可以显著提升用户体验

**权衡**:
- 优点: 快速响应
- 缺点: 可能不是最新状态
- 解决: 1小时缓存过期 + 手动刷新选项

### 决策 2: 为什么使用白名单而不是黑名单?

**原因**:
- 白名单更安全,默认拒绝
- 黑名单容易遗漏
- 符合"只能使用已验证的 API"的原则

**权衡**:
- 优点: 更严格的约束
- 缺点: 需要维护白名单
- 解决: 自动扫描生成白名单

### 决策 3: 为什么不直接调用 OpenCode API?

**原因**:
- OpenCode 可能不提供 API
- 手动工作流更灵活,开发者可以调整 prompt
- 降低系统复杂度

**权衡**:
- 优点: 简单、灵活
- 缺点: 需要手动操作
- 未来: 如果 OpenCode 提供 API,可以扩展

### 决策 4: 为什么使用 AST 而不是正则表达式?

**原因**:
- AST 更准确,不会误判
- 可以提取结构化信息(参数、类型等)
- Python 标准库支持

**权衡**:
- 优点: 准确、可靠
- 缺点: 稍微复杂
- 解决: 封装成工具函数

### 决策 5: 为什么使用 Git Hook 而不是 CI/CD?

**原因**:
- Git Hook 更早发现问题(提交前)
- 减少 CI/CD 负担
- 更快的反馈循环

**权衡**:
- 优点: 快速反馈
- 缺点: 可以被 --no-verify 绕过
- 解决: 同时在 CI/CD 中也校验

## 性能考虑

### 注册表扫描性能

**预期性能**:
- 扫描 50 个 Lib 文件: ~5 秒
- 扫描 100 个 YAML 文件: ~2 秒
- 扫描 200 个 TestCase 文件: ~10 秒
- 总计: ~20 秒(首次)

**优化策略**:
- 缓存机制(1小时)
- 增量扫描(只扫描变更的文件)
- 并发扫描(使用多进程)

### 校验性能

**预期性能**:
- API 使用校验: <1 秒
- YAML Schema 校验: <1 秒
- 交叉引用校验: <1 秒
- 总计: ~3 秒

**优化策略**:
- AST 缓存
- 并行校验

## 可扩展性

### 支持更多 AI 工具

当前设计针对 OpenCode,但架构是通用的:
- Contract Layer 生成的上下文包可以用于任何 LLM
- 只需调整 prompt 模板格式

### 支持更多语言

当前实现是 Python,但架构可以扩展:
- Registry Layer: 使用对应语言的 AST 解析器
- Validation Layer: 使用对应语言的校验工具

### 支持更复杂的匹配

当前使用简单的关键词匹配,可以扩展:
- 语义匹配(使用 embedding)
- 图匹配(基于 API 依赖图)
- 机器学习模型

## 安全考虑

### 代码注入风险

**风险**: OpenCode 生成的代码可能包含恶意代码

**缓解措施**:
- 校验层检查危险操作
- 人工 Code Review
- 沙箱测试环境

### 敏感信息泄露

**风险**: 上下文包可能包含敏感信息

**缓解措施**:
- 不扫描包含敏感信息的文件
- 脱敏处理
- 访问控制

## 监控和度量

### 关键指标

1. **生成成功率** - 校验通过的比例
2. **首次通过率** - 不需要修复就通过的比例
3. **平均修复次数** - 平均需要修复几次
4. **常见错误类型** - 统计最常见的错误

### 日志记录

- 每次生成记录完整的上下文包
- 每次校验记录详细的错误信息
- 每次修复记录修复前后的对比

## 未来改进方向

1. **智能 Prompt 优化** - 根据历史错误自动优化 prompt
2. **API 推荐** - 基于需求自动推荐最合适的 API
3. **自动化测试** - 生成后自动运行测试
4. **团队协作** - 共享上下文包和最佳实践
5. **可视化界面** - Web UI 替代命令行工具

## 总结

本系统通过分层架构和严格的约束机制,确保 OpenCode 生成的 TestCase 准确使用 Lib API 和 YAML 配置。核心思想是:

> **不让 LLM 自由发挥,而是给它明确的约束和参考。**

通过注册表、白名单、多层校验等机制,将生成准确率提升到 95% 以上。
