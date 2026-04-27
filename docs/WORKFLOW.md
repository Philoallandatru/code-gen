# 完整工作流指南

本文档描述使用 TestCase Generation System 的完整工作流程,包括详细步骤、最佳实践和常见问题。

## 目录

- [准备工作](#准备工作)
- [完整工作流](#完整工作流)
- [详细步骤](#详细步骤)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)
- [团队协作](#团队协作)

## 准备工作

### 环境要求

- Python 3.8+
- Git
- Bitbucket Server 访问权限
- OpenCode 账号 (https://opencode.ai/)

### 初始化项目

```bash
# 1. 克隆代码库
git clone <your-bitbucket-repo>
cd <your-repo>

# 2. 安装依赖
pip install pyyaml

# 3. 安装 Git Hook (推荐)
cp .opencode/hooks/pre-commit .git/hooks/
chmod +x .git/hooks/pre-commit

# 4. 首次扫描(生成注册表缓存)
python .opencode/tools/generate_context.py "test" --project-root .
```

## 完整工作流

```
┌─────────────────────────────────────────────────────────────┐
│                      开发者工作流                             │
└─────────────────────────────────────────────────────────────┘

1. 接收需求
   ↓
2. 生成上下文包
   ↓
3. 复制到 OpenCode
   ↓
4. OpenCode 生成代码
   ↓
5. 保存到本地
   ↓
6. 运行校验
   ↓
7. 修复问题(如果有)
   ↓
8. 提交到 Bitbucket
   ↓
9. 创建 Pull Request
   ↓
10. 团队 Review
```

## 详细步骤

### Step 1: 接收需求

**输入**: 测试需求描述

**示例**:
```
需求: 验证SSD在idle 500ms后能够进入PS4低功耗状态,并且entry latency不超过500ms
来源: JIRA-1234
优先级: P1
```

**准备工作**:
- 理解需求的核心目标
- 确认涉及的功能模块(power、nvme、log等)
- 确认是否有相似的已有 TestCase

### Step 2: 生成上下文包

**命令**:
```bash
python .opencode/tools/generate_context.py "验证SSD在idle 500ms后能够进入PS4低功耗状态"
```

**输出**:
```
🔍 Step 1: 扫描代码库...
   使用缓存的注册表...
🔍 Step 2: 解析需求...
🔍 Step 3: 匹配Lib API...
   匹配到 5 个相关API
🔍 Step 4: 匹配YAML Schema...
   匹配到 2 个相关Schema
🔍 Step 5: 检索相似Case...
   找到 3 个相似Case
🔍 Step 6: 生成上下文包...

✅ 上下文包已生成: .opencode/context_packages/package_20260428_103045

📋 下一步:
   1. 打开 .opencode/context_packages/package_20260428_103045/prompt.md
   2. 复制全部内容到 OpenCode
   3. 让 OpenCode 生成代码
   4. 将生成的代码保存到本地
   5. 运行校验: python validate_case.py <package_dir>
```

**生成的文件**:
```
.opencode/context_packages/package_20260428_103045/
├── context.md        # 完整上下文(供参考)
├── prompt.md         # 给OpenCode的prompt(复制这个)
└── metadata.json     # 元数据(用于校验)
```

**检查上下文包**:
```bash
# 查看匹配到的API
cat .opencode/context_packages/package_20260428_103045/context.md | grep "### "

# 查看匹配到的YAML Schema
cat .opencode/context_packages/package_20260428_103045/context.md | grep "Schema:"
```

### Step 3: 复制到 OpenCode

**操作步骤**:

1. 打开 `prompt.md` 文件
   ```bash
   # Windows
   notepad .opencode/context_packages/package_20260428_103045/prompt.md
   
   # Mac/Linux
   open .opencode/context_packages/package_20260428_103045/prompt.md
   ```

2. 全选并复制(Ctrl+A, Ctrl+C)

3. 打开 https://opencode.ai/

4. 粘贴到 OpenCode 的输入框

5. 点击"Generate"按钮

**注意事项**:
- 确保复制了完整的 prompt,包括所有的 CRITICAL RULES
- 不要修改 prompt 内容(除非你知道自己在做什么)
- 如果 OpenCode 生成的代码明显不对,可以重新生成

### Step 4: OpenCode 生成代码

**等待时间**: 通常 30-60 秒

**OpenCode 应该生成两部分**:
1. Python TestCase 代码
2. YAML 配置文件

**检查生成结果**:
- Python 代码是否有明显的语法错误
- YAML 配置是否是有效的 YAML 格式
- 是否使用了 prompt 中列出的 API
- 是否有明显的逻辑错误

**如果生成结果不理想**:
- 点击"Regenerate"重新生成
- 或者调整 prompt 强调某些要点
- 记录常见问题,后续优化 prompt 模板

### Step 5: 保存到本地

**创建目录**:
```bash
# 根据需求确定目录和文件名
mkdir -p TestCase/Power
mkdir -p configs/power
```

**保存 Python 代码**:
```bash
# 将 OpenCode 生成的 Python 代码保存为:
# TestCase/Power/test_low_power_entry_latency.py
```

**保存 YAML 配置**:
```bash
# 将 OpenCode 生成的 YAML 配置保存为:
# configs/power/low_power_entry_latency.yaml
```

**文件命名规范**:
- Python 文件: `test_<功能描述>.py`
- YAML 文件: `<功能描述>.yaml`
- 保持一致性,便于维护

### Step 6: 运行校验

**命令**:
```bash
python .opencode/tools/validate_case.py \
    .opencode/context_packages/package_20260428_103045 \
    TestCase/Power/test_low_power_entry_latency.py \
    configs/power/low_power_entry_latency.yaml
```

**成功输出**:
```
🔍 开始校验...

📋 [1/5] 校验API使用...
📋 [2/5] 校验YAML结构...
📋 [3/5] 校验Python与YAML一致性...
📋 [4/5] 校验代码结构...
📋 [5/5] 校验代码风格...

================================================================================
✅ 校验通过!
⚠️  但有 2 个警告
================================================================================
```

**失败输出**:
```
🔍 开始校验...

📋 [1/5] 校验API使用...
📋 [2/5] 校验YAML结构...
📋 [3/5] 校验Python与YAML一致性...
📋 [4/5] 校验代码结构...
📋 [5/5] 校验代码风格...

================================================================================
❌ 校验失败! 发现 3 个错误, 2 个警告
================================================================================

❌ ERRORS (Must Fix)
--------------------------------------------------------------------------------
1. [API Usage] 使用了未授权的API: power.wait_for_state
   💡 Suggestion: 你是否想使用 'power.wait_for_power_state'?

2. [YAML Schema] 缺少必填字段: case.id
   💡 Suggestion: 请在YAML配置中添加这个字段

3. [Cross Reference] Case ID不一致: Python中是'TC_PM_001', YAML中是'TC_PM_002'
   💡 Suggestion: 请确保Python docstring和YAML中的case.id一致
```

### Step 7: 修复问题(如果有)

#### 方案 A: 查看修复指南

```bash
python .opencode/tools/fix_case.py \
    .opencode/context_packages/package_20260428_103045 \
    TestCase/Power/test_low_power_entry_latency.py \
    configs/power/low_power_entry_latency.yaml
```

**输出**:
```
================================================================================
修复指南 (Fix Guide)
================================================================================

根据校验结果,以下是详细的修复建议:

## API Usage

### 问题 1: 使用了未授权的API: power.wait_for_state

**修复步骤:**
- 打开Python文件
- 找到使用该API的代码行
- 替换为上下文包中列出的正确API
- 检查import语句是否正确

**建议:** 你是否想使用 'power.wait_for_power_state'?

---

## YAML Schema

### 问题 2: 缺少必填字段: case.id

**修复步骤:**
- 打开YAML配置文件
- 添加字段: case.id
- 参考上下文包中的YAML示例

---
```

#### 方案 B: 尝试自动修复

```bash
python .opencode/tools/fix_case.py \
    .opencode/context_packages/package_20260428_103045 \
    TestCase/Power/test_low_power_entry_latency.py \
    configs/power/low_power_entry_latency.yaml \
    --auto-fix
```

**输出**:
```
🔧 尝试自动修复...

✅ 自动修复完成:
   - 添加了case.id: TC_PM_001
   - 添加了case.name: low_power_entry_latency
   - 统一了Case ID为: TC_PM_001
   - 添加了模块docstring

⚠️  注意: 自动修复只能处理简单问题,复杂问题仍需手动修复

📁 修复后的文件已保存:
   Python: TestCase/Power/test_low_power_entry_latency.py
   YAML: configs/power/low_power_entry_latency.yaml

💡 建议: 重新运行校验确认修复效果
```

#### 方案 C: 手动修复

根据修复指南,手动编辑文件:

1. 打开 Python 文件
2. 根据错误提示修改代码
3. 保存文件
4. 重新运行校验

**修复后重新校验**:
```bash
python .opencode/tools/validate_case.py \
    .opencode/context_packages/package_20260428_103045 \
    TestCase/Power/test_low_power_entry_latency.py \
    configs/power/low_power_entry_latency.yaml
```

**循环直到校验通过**。

### Step 8: 提交到 Bitbucket

**创建分支**:
```bash
git checkout -b feature/add-low-power-entry-test
```

**添加文件**:
```bash
git add TestCase/Power/test_low_power_entry_latency.py
git add configs/power/low_power_entry_latency.yaml

# 可选: 提交上下文包(用于追溯)
git add .opencode/context_packages/package_20260428_103045/
```

**提交**:
```bash
git commit -m "Add test case for low power entry latency

- Verify SSD enters PS4 state after idle
- Check entry latency is within 500ms
- Generated with OpenCode
- Context package: package_20260428_103045
- Covers: JIRA-1234
"
```

**注意**: 如果安装了 pre-commit hook,会自动运行校验:
```
🔍 OpenCode TestCase Pre-commit Hook

📋 Found TestCase files to validate:
TestCase/Power/test_low_power_entry_latency.py

🔍 Validating TestCase/Power/test_low_power_entry_latency.py...
✅ Validation passed for TestCase/Power/test_low_power_entry_latency.py

✅ All validations passed
```

**推送到远程**:
```bash
git push origin feature/add-low-power-entry-test
```

### Step 9: 创建 Pull Request

**在 Bitbucket Server 中**:

1. 导航到你的仓库
2. 点击"Create Pull Request"
3. 选择源分支: `feature/add-low-power-entry-test`
4. 选择目标分支: `main` 或 `develop`

**填写 PR 描述**:
```markdown
## 变更说明
添加低功耗进入延迟测试用例

## 需求
- JIRA: JIRA-1234
- 需求: 验证SSD在idle 500ms后能够进入PS4低功耗状态,并且entry latency不超过500ms

## 生成信息
- 工具: OpenCode (https://opencode.ai/)
- 上下文包: package_20260428_103045
- 生成时间: 2026-04-28

## 校验状态
- ✅ API使用校验通过
- ✅ YAML结构校验通过
- ✅ 交叉引用校验通过
- ✅ 代码结构校验通过
- ⚠️  2个警告(已确认可接受)

## 测试计划
- [ ] 在测试环境运行
- [ ] 验证覆盖需求
- [ ] 检查日志输出
- [ ] 确认cleanup正常

## 相关文件
- TestCase: `TestCase/Power/test_low_power_entry_latency.py`
- Config: `configs/power/low_power_entry_latency.yaml`
- Context: `.opencode/context_packages/package_20260428_103045/`

## Checklist
- [x] 代码已通过本地校验
- [x] 已添加必要的注释
- [x] YAML配置完整
- [x] 遵循项目编码规范
- [ ] 已在测试环境验证
```

5. 添加 Reviewers
6. 点击"Create"

### Step 10: 团队 Review

**Reviewer 检查清单**:

1. **需求覆盖**
   - [ ] 是否正确理解需求
   - [ ] 测试逻辑是否合理
   - [ ] 是否覆盖边界情况

2. **API 使用**
   - [ ] 是否使用了正确的 API
   - [ ] API 参数是否正确
   - [ ] 是否有不必要的 API 调用

3. **YAML 配置**
   - [ ] 配置是否完整
   - [ ] 配置值是否合理
   - [ ] 是否有硬编码值

4. **代码质量**
   - [ ] 代码是否清晰易读
   - [ ] 是否有适当的注释
   - [ ] 是否有 cleanup 逻辑
   - [ ] 错误处理是否完善

5. **测试完整性**
   - [ ] 是否有 setup 和 teardown
   - [ ] 断言是否充分
   - [ ] 是否考虑了失败场景

**Review 反馈**:
- 如果有问题,在 PR 中添加评论
- 开发者根据反馈修改代码
- 重新推送后,Reviewer 再次检查

**Approve 和 Merge**:
- 所有 Reviewer 都 Approve 后
- 确认 CI/CD 通过
- Merge 到主分支

## 最佳实践

### 1. 定期更新注册表

```bash
# 每周或Lib有重大更新时
rm -rf .opencode/registry/*
python .opencode/tools/generate_context.py "dummy"
```

### 2. 保留上下文包

**为什么保留**:
- 用于追溯生成时的上下文
- 用于后续校验
- 用于分析常见问题

**如何保留**:
```bash
# 提交到Git(如果不太大)
git add .opencode/context_packages/package_xxx/
git commit -m "Add context package for TC_PM_001"
```

### 3. 批量生成

```bash
# 从需求文件批量生成
cat requirements.txt | while read req; do
    python .opencode/tools/generate_context.py "$req"
done
```

### 4. 团队共享最佳实践

**建立团队 Wiki**:
- 记录常见问题和解决方案
- 分享优秀的 TestCase 示例
- 记录 OpenCode 的使用技巧

**定期 Review**:
- 每月回顾生成的 TestCase 质量
- 识别常见错误模式
- 优化 prompt 模板

### 5. 持续优化 Prompt

**记录 OpenCode 常犯的错误**:
```
常见错误:
1. 经常使用 power.wait_for_state 而不是 power.wait_for_power_state
2. 经常忘记添加 cleanup
3. 经常硬编码 PS4 而不是从 YAML 读取
```

**更新 Prompt 模板**:
```markdown
# 在 .opencode/prompts/base_prompt.md 中强调

## CRITICAL RULES (特别注意!)

1. API 命名:
   - ✅ 正确: power.wait_for_power_state
   - ❌ 错误: power.wait_for_state
   
2. Cleanup:
   - 必须在 finally 块中添加 cleanup
   - 示例: power.restore_apst()
   
3. 配置值:
   - ❌ 禁止: target_state = "PS4"
   - ✅ 正确: target_state = cfg["power"]["target_state"]
```

## 常见问题

### Q1: 上下文生成器扫描很慢怎么办?

**A**: 首次扫描会比较慢(20-30秒),之后会使用缓存。

**强制重新扫描**:
```bash
rm -rf .opencode/registry/*
python .opencode/tools/generate_context.py "..."
```

**优化建议**:
- 排除不必要的目录(在代码中配置 exclude_patterns)
- 使用 SSD 硬盘
- 定期清理无用文件

### Q2: OpenCode 生成的代码总是有同样的错误怎么办?

**A**: 需要优化 prompt 模板。

**步骤**:
1. 记录常见错误
2. 编辑 `.opencode/prompts/base_prompt.md`
3. 在 CRITICAL RULES 部分强调这些错误
4. 重新生成上下文包

### Q3: 如何跳过 pre-commit 校验?

**A**: 不推荐,但如果确实需要:
```bash
git commit --no-verify
```

**注意**: CI/CD 中仍会校验,所以最终还是要修复问题。

### Q4: 校验器报告了误报怎么办?

**A**: 可以临时禁用某个校验器。

**编辑校验脚本**:
```python
# 在 validate_case.py 中注释掉某个校验
# self._validate_code_style()  # 临时禁用
```

**长期方案**: 提 Issue 改进校验逻辑。

### Q5: 如何为特定领域定制 prompt?

**A**: 创建领域特定的 prompt 模板。

**步骤**:
1. 在 `.opencode/prompts/` 创建新文件
   ```bash
   cp .opencode/prompts/base_prompt.md .opencode/prompts/power_management.md
   ```

2. 编辑新文件,添加领域特定的规则

3. 生成时指定模板(需要修改代码支持)

### Q6: 团队多人使用时如何共享注册表?

**A**: 将注册表提交到 Git。

```bash
# 生成注册表
python .opencode/tools/generate_context.py "dummy"

# 提交
git add .opencode/registry/
git commit -m "Update API registry"
git push
```

**其他成员**:
```bash
git pull
# 现在可以直接使用最新的注册表
```

### Q7: 如何处理 OpenCode 生成的代码格式不规范?

**A**: 使用代码格式化工具。

```bash
# 安装 black
pip install black

# 格式化生成的代码
black TestCase/Power/test_low_power_entry_latency.py
```

**或者在 pre-commit hook 中自动格式化**。

## 团队协作

### 角色分工

**TestCase 开发者**:
- 生成上下文包
- 使用 OpenCode 生成代码
- 运行校验和修复
- 提交 PR

**Code Reviewer**:
- Review PR 中的 TestCase
- 检查需求覆盖
- 检查代码质量
- Approve 或提出修改建议

**维护者**:
- 维护 prompt 模板
- 优化校验规则
- 更新文档
- 处理 Issue

### 沟通渠道

**Slack / 企业微信**:
- 创建 #testcase-generation 频道
- 分享使用技巧
- 讨论常见问题

**Wiki**:
- 维护最佳实践文档
- 记录常见问题和解决方案
- 分享优秀示例

**定期会议**:
- 每月回顾生成质量
- 讨论改进方向
- 分享经验

### 质量保证

**Code Review 标准**:
- 所有生成的 TestCase 必须经过 Review
- 至少 2 个 Reviewer Approve
- 必须通过所有校验

**测试验证**:
- 在测试环境运行
- 确认覆盖需求
- 检查日志输出

**持续改进**:
- 记录生成质量指标
- 定期分析常见问题
- 优化工具和流程

## 总结

完整的工作流程确保了:
1. **准确性** - 通过上下文包和校验确保代码准确
2. **效率** - 自动化工具减少手动工作
3. **质量** - 多层校验和 Code Review 保证质量
4. **可追溯** - 保留上下文包用于追溯
5. **协作** - 清晰的流程支持团队协作

遵循这个工作流,可以高效地生成高质量的 TestCase。
