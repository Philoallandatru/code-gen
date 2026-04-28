#!/usr/bin/env python3
"""
TestCase修复助手

用法:
    # 生成修复指南
    python fix_case.py <context_package_dir> <python_file> <yaml_file>

    # 尝试自动修复
    python fix_case.py <context_package_dir> <python_file> <yaml_file> --auto-fix

示例:
    python fix_case.py .opencode/context_packages/package_20240115_143022 TestCase/test_power_ps4.py configs/test_power_ps4.yaml --auto-fix
"""

import os
import json
import re
import yaml
from pathlib import Path
from datetime import datetime
import argparse


class FixHelper:
    """TestCase修复助手"""

    def __init__(self, context_package_dir: str):
        self.package_dir = Path(context_package_dir)
        self.validation_report_file = self.package_dir / "validation_report.json"

        if not self.validation_report_file.exists():
            raise FileNotFoundError(
                f"请先运行validate_case.py生成校验报告: {self.validation_report_file}"
            )

        with open(self.validation_report_file, 'r', encoding='utf-8') as f:
            self.report = json.load(f)

    def generate_fix_guide(self) -> str:
        """生成修复指南"""
        if self.report['summary']['passed']:
            return "✅ 没有需要修复的问题!"

        lines = []

        lines.append("=" * 80)
        lines.append("🔧 修复指南")
        lines.append("=" * 80)
        lines.append("")
        lines.append("根据校验结果,以下是详细的修复建议:")
        lines.append("")

        # 按错误类型分组
        errors_by_type = {}
        for error in self.report['errors']:
            error_type = error['type']
            if error_type not in errors_by_type:
                errors_by_type[error_type] = []
            errors_by_type[error_type].append(error)

        # 生成修复步骤
        for error_type, errors in errors_by_type.items():
            lines.append(f"## {error_type}")
            lines.append("")

            for i, error in enumerate(errors, 1):
                lines.append(f"### 问题 {i}: {error['message']}")
                lines.append("")

                # 生成具体的修复步骤
                fix_steps = self._generate_fix_steps(error)
                if fix_steps:
                    lines.append("**修复步骤:**")
                    for step in fix_steps:
                        lines.append(f"- {step}")
                    lines.append("")

                if 'suggestion' in error:
                    lines.append(f"**建议:** {error['suggestion']}")
                    lines.append("")

                lines.append("---")
                lines.append("")

        # 添加重新生成的建议
        if len(self.report['errors']) > 5:
            lines.append("## ⚠️  错误较多,建议重新生成")
            lines.append("")
            lines.append("如果错误超过5个,建议:")
            lines.append("1. 回到OpenCode")
            lines.append("2. 重新复制上下文包的prompt")
            lines.append("3. 强调CRITICAL RULES")
            lines.append("4. 重新生成代码")
            lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    def _generate_fix_steps(self, error: dict) -> list:
        """根据错误类型生成修复步骤"""
        error_type = error['type']
        steps = []

        if error_type == 'UNAUTHORIZED_IMPORT':
            steps.append("打开Python文件")
            steps.append("找到未授权的import语句")
            steps.append("检查上下文包中的允许API列表")
            steps.append("替换为正确的import语句")

        elif error_type == 'MISSING_REQUIRED_FIELD':
            steps.append("打开YAML配置文件")
            steps.append(f"添加缺少的字段")
            steps.append("参考上下文包中的YAML示例")

        elif error_type == 'INVALID_CASE_ID_FORMAT':
            steps.append("打开YAML配置文件")
            steps.append("修改case_id字段")
            steps.append("格式: TC_XXX_YYYYMMDD (例如: TC_001_20240115)")

        elif error_type == 'CASE_ID_MISMATCH':
            steps.append("确定正确的case_id")
            steps.append("在Python文件中更新case_id")
            steps.append("在YAML文件中更新case_id")
            steps.append("确保两处完全一致")

        elif error_type == 'MISSING_LOAD_CONFIG':
            steps.append("打开Python文件")
            steps.append("在test方法开始处添加:")
            steps.append("  config = self.load_case_config()")

        else:
            steps.append("请根据错误信息手动修复")

        return steps

    def auto_fix(self, python_file: str, yaml_file: str) -> dict:
        """尝试自动修复"""
        print("🔧 尝试自动修复...")
        print()

        fixes_applied = []

        # 读取文件
        with open(python_file, 'r', encoding='utf-8') as f:
            python_content = f.read()

        with open(yaml_file, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
            yaml_data = yaml.safe_load(yaml_content)

        # 修复YAML缺少的必填字段
        for error in self.report['errors']:
            if error['type'] == 'MISSING_REQUIRED_FIELD':
                field = error['message'].split(':')[-1].strip()

                if field == 'case_id':
                    # 生成case_id
                    case_id = self._generate_case_id()
                    yaml_data['case_id'] = case_id
                    fixes_applied.append(f"添加了case_id: {case_id}")

                elif field == 'description':
                    # 从metadata获取需求作为description
                    metadata_file = self.package_dir / "metadata.json"
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    description = metadata.get('requirement', 'Test case description')
                    yaml_data['description'] = description
                    fixes_applied.append(f"添加了description")

        # 修复case_id格式错误
        for error in self.report['errors']:
            if error['type'] == 'INVALID_CASE_ID_FORMAT':
                # 重新生成符合格式的case_id
                case_id = self._generate_case_id()
                yaml_data['case_id'] = case_id
                fixes_applied.append(f"修正了case_id格式: {case_id}")

        # 修复case_id不一致
        for error in self.report['errors']:
            if error['type'] == 'CASE_ID_MISMATCH':
                # 使用YAML中的case_id作为标准
                if 'case_id' in yaml_data:
                    yaml_case_id = yaml_data['case_id']
                    # 在Python中更新case_id
                    python_content = re.sub(
                        r'case_id\s*=\s*["\'][^"\']+["\']',
                        f'case_id = "{yaml_case_id}"',
                        python_content
                    )
                    fixes_applied.append(f"统一了case_id为: {yaml_case_id}")

        # 修复缺少load_case_config
        for error in self.report['errors']:
            if error['type'] == 'MISSING_LOAD_CONFIG':
                # 在test方法开始处添加load_case_config
                # 这个比较复杂,简化处理:在setUp方法中添加
                if 'def setUp' in python_content:
                    python_content = python_content.replace(
                        'def setUp(self):',
                        'def setUp(self):\n        self.config = self.load_case_config()'
                    )
                    fixes_applied.append("添加了load_case_config()调用")

        # 添加模块docstring(如果缺少)
        if not python_content.strip().startswith('"""') and not python_content.strip().startswith("'''"):
            case_id = yaml_data.get('case_id', 'TC_XXX_YYYYMMDD')
            description = yaml_data.get('description', 'Test case')
            docstring = f'"""\n{description}\n\nCase ID: {case_id}\n"""\n\n'
            python_content = docstring + python_content
            fixes_applied.append("添加了模块docstring")

        # 保存修复后的文件
        if fixes_applied:
            # 备份原文件
            backup_suffix = datetime.now().strftime("%Y%m%d_%H%M%S")
            python_backup = f"{python_file}.backup_{backup_suffix}"
            yaml_backup = f"{yaml_file}.backup_{backup_suffix}"

            with open(python_backup, 'w', encoding='utf-8') as f:
                with open(python_file, 'r', encoding='utf-8') as orig:
                    f.write(orig.read())

            with open(yaml_backup, 'w', encoding='utf-8') as f:
                with open(yaml_file, 'r', encoding='utf-8') as orig:
                    f.write(orig.read())

            # 写入修复后的内容
            with open(python_file, 'w', encoding='utf-8') as f:
                f.write(python_content)

            with open(yaml_file, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False)

            print("✅ 自动修复完成:")
            for fix in fixes_applied:
                print(f"   - {fix}")
            print()
            print(f"📁 原文件已备份:")
            print(f"   - {python_backup}")
            print(f"   - {yaml_backup}")
            print()
            print("⚠️  注意: 自动修复只能处理简单问题,复杂问题仍需手动修复")
            print()
            print("💡 建议: 重新运行校验确认修复效果")
            print(f"   python validate_case.py {self.package_dir} {python_file} {yaml_file}")

        else:
            print("ℹ️  没有可以自动修复的问题")
            print()
            print("💡 请根据修复指南手动修复:")
            print(f"   python fix_case.py {self.package_dir} {python_file} {yaml_file}")

        return {
            'fixes_applied': fixes_applied,
            'python_file': python_file,
            'yaml_file': yaml_file
        }

    def _generate_case_id(self) -> str:
        """生成case_id"""
        # 格式: TC_XXX_YYYYMMDD
        seq = datetime.now().strftime("%H%M%S")[-3:]  # 使用时分秒的后3位作为序号
        date = datetime.now().strftime("%Y%m%d")
        return f"TC_{seq}_{date}"


def main():
    parser = argparse.ArgumentParser(description='Fix generated TestCase issues')
    parser.add_argument('context_package_dir', type=str,
                       help='Context package directory')
    parser.add_argument('python_file', type=str,
                       help='Python TestCase file')
    parser.add_argument('yaml_file', type=str,
                       help='YAML config file')
    parser.add_argument('--auto-fix', action='store_true',
                       help='Attempt automatic fixes')

    args = parser.parse_args()

    try:
        helper = FixHelper(args.context_package_dir)

        if args.auto_fix:
            # 自动修复
            result = helper.auto_fix(args.python_file, args.yaml_file)
        else:
            # 生成修复指南
            guide = helper.generate_fix_guide()
            print()
            print(guide)

            # 保存修复指南
            guide_file = Path(args.context_package_dir) / "fix_guide.md"
            with open(guide_file, 'w', encoding='utf-8') as f:
                f.write(guide)

            print()
            print(f"📄 修复指南已保存到: {guide_file}")
            print()
            print("💡 提示: 使用 --auto-fix 参数尝试自动修复")

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == '__main__':
    main()
