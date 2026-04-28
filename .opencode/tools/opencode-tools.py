#!/usr/bin/env python3
"""
OpenCode TestCase工具集 - 统一CLI入口

用法:
    opencode-tools generate <requirement>     # 生成上下文包
    opencode-tools validate <package> <py> <yaml>  # 校验TestCase
    opencode-tools fix <package> <py> <yaml>       # 修复TestCase
    opencode-tools setup-hooks                     # 安装Git Hooks

示例:
    # 1. 生成上下文包
    opencode-tools generate "测试PS4电源开关功能"

    # 2. 在OpenCode中使用生成的prompt

    # 3. 校验生成的代码
    opencode-tools validate .opencode/context_packages/package_20240115_143022 TestCase/test_power_ps4.py configs/test_power_ps4.yaml

    # 4. 如果有错误,尝试修复
    opencode-tools fix .opencode/context_packages/package_20240115_143022 TestCase/test_power_ps4.py configs/test_power_ps4.yaml --auto-fix
"""

import sys
import os
import subprocess
from pathlib import Path
import argparse


class OpenCodeTools:
    """OpenCode工具集CLI"""

    def __init__(self):
        self.tools_dir = Path(__file__).parent
        self.repo_root = self.tools_dir.parent.parent

    def generate(self, requirement: str):
        """生成上下文包"""
        print("🚀 生成上下文包...")
        print()

        script = self.tools_dir / "generate_context.py"
        result = subprocess.run(
            [sys.executable, str(script), requirement],
            cwd=self.repo_root
        )

        return result.returncode

    def validate(self, package: str, python_file: str, yaml_file: str):
        """校验TestCase"""
        print("🔍 校验TestCase...")
        print()

        script = self.tools_dir / "validate_case.py"
        result = subprocess.run(
            [sys.executable, str(script), package, python_file, yaml_file],
            cwd=self.repo_root
        )

        return result.returncode

    def fix(self, package: str, python_file: str, yaml_file: str, auto_fix: bool = False):
        """修复TestCase"""
        print("🔧 修复TestCase...")
        print()

        script = self.tools_dir / "fix_case.py"
        cmd = [sys.executable, str(script), package, python_file, yaml_file]

        if auto_fix:
            cmd.append("--auto-fix")

        result = subprocess.run(cmd, cwd=self.repo_root)

        return result.returncode

    def setup_hooks(self):
        """安装Git Hooks"""
        print("⚙️  安装Git Hooks...")
        print()

        # 检查是否是git仓库
        git_dir = self.repo_root / ".git"
        if not git_dir.exists():
            print("❌ 错误: 当前目录不是Git仓库")
            return 1

        # 复制pre-commit hook
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        source_hook = self.tools_dir.parent / "hooks" / "pre-commit"
        target_hook = hooks_dir / "pre-commit"

        if target_hook.exists():
            print(f"⚠️  警告: {target_hook} 已存在")
            response = input("是否覆盖? (y/N): ")
            if response.lower() != 'y':
                print("❌ 取消安装")
                return 1

        # 复制文件
        with open(source_hook, 'r', encoding='utf-8') as f:
            content = f.read()

        with open(target_hook, 'w', encoding='utf-8') as f:
            f.write(content)

        # 设置可执行权限(Unix系统)
        if os.name != 'nt':
            os.chmod(target_hook, 0o755)

        print(f"✅ Git Hook已安装: {target_hook}")
        print()
        print("📋 Hook功能:")
        print("   - 在git commit前自动校验TestCase")
        print("   - 如果校验失败,阻止提交")
        print("   - 可以使用 git commit --no-verify 跳过校验")
        print()

        return 0


def main():
    parser = argparse.ArgumentParser(
        description='OpenCode TestCase工具集',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='命令')

    # generate命令
    generate_parser = subparsers.add_parser('generate', help='生成上下文包')
    generate_parser.add_argument('requirement', type=str, help='测试需求描述')

    # validate命令
    validate_parser = subparsers.add_parser('validate', help='校验TestCase')
    validate_parser.add_argument('package', type=str, help='上下文包目录')
    validate_parser.add_argument('python_file', type=str, help='Python文件')
    validate_parser.add_argument('yaml_file', type=str, help='YAML文件')

    # fix命令
    fix_parser = subparsers.add_parser('fix', help='修复TestCase')
    fix_parser.add_argument('package', type=str, help='上下文包目录')
    fix_parser.add_argument('python_file', type=str, help='Python文件')
    fix_parser.add_argument('yaml_file', type=str, help='YAML文件')
    fix_parser.add_argument('--auto-fix', action='store_true', help='自动修复')

    # setup-hooks命令
    setup_hooks_parser = subparsers.add_parser('setup-hooks', help='安装Git Hooks')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    tools = OpenCodeTools()

    try:
        if args.command == 'generate':
            return tools.generate(args.requirement)

        elif args.command == 'validate':
            return tools.validate(args.package, args.python_file, args.yaml_file)

        elif args.command == 'fix':
            return tools.fix(args.package, args.python_file, args.yaml_file, args.auto_fix)

        elif args.command == 'setup-hooks':
            return tools.setup_hooks()

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print()
        print("❌ 用户中断")
        return 130

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
