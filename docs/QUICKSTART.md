# 快速开始指南

本指南将帮助你在 5 分钟内开始使用 OpenCode TestCase 自动生成系统。

## 前置条件

- Python 3.7+
- Git
- OpenCode 账号 (https://opencode.ai/)

## 步骤 1: 克隆项目

```bash
git clone https://github.com/Philoallandatru/code-gen.git
cd code-gen
```

## 步骤 2: 安装依赖

```bash
pip install -r requirements.txt
```

## 步骤 3: 准备你的项目结构

确保你的项目有以下目录结构:

```
your-project/
├── Lib/              # 你的库代码
├── TestCase/         # 测试用例目录
├── configs/          # YAML 配置目录
└── .opencode/        # 工具目录（从本项目复制）
```

将 `.opencode/` 目录复制到你的项目根目录:

```bash
cp -r .opencode /path/to/your-project/
```

## 步骤 4: 生成上下文包

```bash
cd /path/to/your-project
python .opencode/tools/generate_context.py "测试设备的电源开关功能"
```

输出:
```
🔍 Step 1: 扫描代码库...
   扫描代码库(首次运行或缓存过期)...
🔍 Step 2: 解析需求...
🔍 Step 3: 匹配Lib API...
   匹配到 5 个相关API
🔍 Step 4: 匹配YAML Schema...
   匹配到 2 个相关Schema
🔍 Step 5: 检索相似Case...
   找到 3 个相似Case
🔍 Step 6: 生成上下文包...

✅ 上下文包已生成: .opencode/context_packages/package_20240115_143022

📋 下一步:
   1. 打开 .opencode/context_packages/package_20240115_143022/prompt.md
   2. 复制全部内容到 OpenCode
   3. 让 OpenCode 生成代码
   4. 将生成的代码保存到本地
   5. 运行校验: python validate_case.py ...
```

## 步骤 5: 使用 OpenCode 生成代码

1. 打开生成的 `prompt.md` 文件
2. 复制全部内容
3. 访问 https://opencode.ai/
4. 粘贴到输入框
5. 点击生成
6. 等待 OpenCode 生成代码（通常 30-60 秒）

## 步骤 6: 保存生成的代码

OpenCode 会生成两部分:

**Python TestCase**:
```python
"""
测试设备的电源开关功能

Case ID: TC_001_20240115
"""

import unittest
from Lib.device import Device

class TestPowerControl(unittest.TestCase):
    def setUp(self):
        self.config = self.load_case_config()
        self.device = Device(self.config['device']['id'])
    
    def test_power_on(self):
        """测试开机功能"""
        try:
            result = self.device.power_on()
            self.assertTrue(result)
        finally:
            self.device.cleanup()
```

保存为: `TestCase/test_power_control.py`

**YAML 配置**:
```yaml
case_id: TC_001_20240115
description: 测试设备的电源开关功能

device:
  id: PS4_001
  type: PS4

power:
  actions:
    - on
    - off
    - restart
```

保存为: `configs/test_power_control.yaml`

## 步骤 7: 校验生成的代码

```bash
python .opencode/tools/validate_case.py \
    .opencode/context_packages/package_20240115_143022 \
    TestCase/test_power_control.py \
    configs/test_power_control.yaml
```

如果校验通过:
```
✅ 校验通过!

   错误: 0
   警告: 0
   信息: 1

✅ 代码质量良好,可以提交PR!
```

如果校验失败:
```
❌ 校验失败!

   错误: 2
   警告: 1
   信息: 0

🔴 错误:

   1. [MISSING_REQUIRED_FIELD] YAML缺少必填字段: case_id
      建议: 请添加 case_id 字段

   2. [CASE_ID_MISMATCH] Python和YAML的case_id不一致
      详情: Python: TC_001_20240115, YAML: TC_002_20240115
      建议: 请确保两个文件使用相同的case_id

💡 提示: 运行以下命令获取修复建议:
   python fix_case.py ...
```

## 步骤 8: 修复问题（如果有）

### 方案 A: 查看修复指南

```bash
python .opencode/tools/fix_case.py \
    .opencode/context_packages/package_20240115_143022 \
    TestCase/test_power_control.py \
    configs/test_power_control.yaml
```

### 方案 B: 自动修复

```bash
python .opencode/tools/fix_case.py \
    .opencode/context_packages/package_20240115_143022 \
    TestCase/test_power_control.py \
    configs/test_power_control.yaml \
    --auto-fix
```

输出:
```
🔧 尝试自动修复...

✅ 自动修复完成:
   - 添加了case_id: TC_143_20240115
   - 统一了case_id为: TC_143_20240115
   - 添加了模块docstring

📁 原文件已备份:
   - TestCase/test_power_control.py.backup_20240115_143530
   - configs/test_power_control.yaml.backup_20240115_143530

💡 建议: 重新运行校验确认修复效果
   python validate_case.py ...
```

## 步骤 9: 提交代码

```bash
git add TestCase/test_power_control.py configs/test_power_control.yaml
git commit -m "Add test case for power control"
git push origin feature/add-power-test
```

## 步骤 10: 安装 Git Hook（可选但推荐）

```bash
python .opencode/tools/opencode-tools.py setup-hooks
```

安装后，每次 `git commit` 都会自动运行校验，如果失败会阻止提交。

## 使用 CLI 工具（推荐）

为了更方便，可以使用统一的 CLI 工具:

```bash
# 生成上下文包
python .opencode/tools/opencode-tools.py generate "测试需求"

# 校验
python .opencode/tools/opencode-tools.py validate <package> <py> <yaml>

# 修复
python .opencode/tools/opencode-tools.py fix <package> <py> <yaml> --auto-fix

# 安装 Git Hooks
python .opencode/tools/opencode-tools.py setup-hooks
```

## 常见问题

### Q: 首次扫描很慢怎么办?

A: 首次扫描需要解析所有代码文件，可能需要 20-30 秒。之后会使用缓存，只需 1-2 秒。

### Q: OpenCode 生成的代码有明显错误怎么办?

A: 可以点击 "Regenerate" 重新生成，或者调整 prompt 强调某些要点。

### Q: 自动修复无法解决所有问题怎么办?

A: 自动修复只能处理简单问题。复杂问题需要根据修复指南手动修复。

### Q: 如何跳过 Git Hook 校验?

A: 使用 `git commit --no-verify`，但不推荐。

## 下一步

- 阅读 [完整文档](README.md)
- 查看 [系统架构](docs/ARCHITECTURE.md)
- 了解 [工作流程](docs/WORKFLOW.md)

## 获取帮助

- GitHub Issues: https://github.com/Philoallandatru/code-gen/issues
- 文档: https://github.com/Philoallandatru/code-gen

祝你使用愉快! 🎉
