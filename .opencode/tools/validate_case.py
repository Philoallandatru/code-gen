#!/usr/bin/env python3
"""
TestCase校验器

用法:
    python validate_case.py <context_package_dir> <python_file> <yaml_file>

示例:
    python validate_case.py .opencode/context_packages/package_20240115_143022 TestCase/test_power_ps4.py configs/test_power_ps4.yaml

输出:
    - 校验报告(终端输出)
    - validation_report.json(保存到context_package_dir)
"""

import os
import json
import ast
import yaml
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse


class TestCaseValidator:
    """校验生成的TestCase"""

    def __init__(self, context_package_dir: str):
        self.package_dir = Path(context_package_dir)
        self.metadata_file = self.package_dir / "metadata.json"

        if not self.metadata_file.exists():
            raise FileNotFoundError(f"Metadata file not found: {self.metadata_file}")

        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

        self.errors = []
        self.warnings = []
        self.info = []

    def validate(self, python_file: str, yaml_file: str) -> Dict:
        """
        执行完整校验
        返回: 校验报告
        """
        print("🔍 开始校验...")
        print(f"   Python文件: {python_file}")
        print(f"   YAML文件: {yaml_file}")
        print()

        # 读取文件
        with open(python_file, 'r', encoding='utf-8') as f:
            python_content = f.read()

        with open(yaml_file, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
            yaml_data = yaml.safe_load(yaml_content)

        # 解析Python AST
        try:
            python_ast = ast.parse(python_content)
        except SyntaxError as e:
            self.errors.append({
                'type': 'SYNTAX_ERROR',
                'severity': 'CRITICAL',
                'message': f'Python语法错误: {e}',
                'line': e.lineno
            })
            return self._generate_report(python_file, yaml_file)

        # 执行各项校验
        print("📋 Step 1: 校验API使用...")
        self._validate_api_usage(python_ast, python_content)

        print("📋 Step 2: 校验YAML Schema...")
        self._validate_yaml_schema(yaml_data)

        print("📋 Step 3: 校验交叉引用...")
        self._validate_cross_references(python_content, yaml_data)

        print("📋 Step 4: 校验代码结构...")
        self._validate_code_structure(python_ast, python_content)

        print("📋 Step 5: 校验代码风格...")
        self._validate_code_style(python_ast, python_content)

        print()
        return self._generate_report(python_file, yaml_file)

    def _validate_api_usage(self, python_ast: ast.AST, python_content: str):
        """校验API使用"""
        allowed_apis = set(self.metadata.get('matched_apis', []))

        # 提取实际使用的API
        used_apis = set()

        for node in ast.walk(python_ast):
            # 检查函数调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # 例如: power_lib.set_power_state()
                    if isinstance(node.func.value, ast.Name):
                        api_call = f"{node.func.value.id}.{node.func.attr}"
                        used_apis.add(api_call)

        # 检查未授权的API
        # 注意: 这里需要更智能的匹配,因为实际调用可能是实例方法
        # 简化版本: 检查是否有明显的未授权调用
        for line in python_content.split('\n'):
            # 检查是否有可疑的import
            if 'from Lib' in line or 'import Lib' in line:
                # 提取import的内容
                match = re.search(r'from\s+(Lib\.\S+)\s+import\s+(\S+)', line)
                if match:
                    module = match.group(1)
                    imported = match.group(2)
                    # 检查是否在允许列表中
                    found = False
                    for allowed_api in allowed_apis:
                        if module in allowed_api or imported in allowed_api:
                            found = True
                            break

                    if not found:
                        self.warnings.append({
                            'type': 'UNAUTHORIZED_IMPORT',
                            'severity': 'WARNING',
                            'message': f'导入了可能未授权的模块: {line.strip()}',
                            'suggestion': f'请确认 {imported} 是否在允许的API列表中'
                        })

    def _validate_yaml_schema(self, yaml_data: Dict):
        """校验YAML Schema"""
        # 检查必填字段
        required_fields = ['case_id', 'description']

        for field in required_fields:
            if field not in yaml_data:
                self.errors.append({
                    'type': 'MISSING_REQUIRED_FIELD',
                    'severity': 'ERROR',
                    'message': f'YAML缺少必填字段: {field}',
                    'suggestion': f'请添加 {field} 字段'
                })

        # 检查case_id格式
        if 'case_id' in yaml_data:
            case_id = yaml_data['case_id']
            if not re.match(r'^TC_\d{3}_\d{8}$', case_id):
                self.errors.append({
                    'type': 'INVALID_CASE_ID_FORMAT',
                    'severity': 'ERROR',
                    'message': f'case_id格式错误: {case_id}',
                    'suggestion': 'case_id应该符合格式: TC_XXX_YYYYMMDD (例如: TC_001_20240115)'
                })

        # 检查是否有未知字段(可能是编造的)
        matched_schemas = self.metadata.get('matched_schemas', [])
        if matched_schemas:
            # 这里简化处理,实际应该加载完整的schema定义
            self.info.append({
                'type': 'SCHEMA_CHECK',
                'severity': 'INFO',
                'message': f'YAML使用了 {len(yaml_data)} 个字段',
                'suggestion': '请人工确认所有字段都在schema定义中'
            })

    def _validate_cross_references(self, python_content: str, yaml_data: Dict):
        """校验Python和YAML的交叉引用"""
        # 检查case_id一致性
        if 'case_id' in yaml_data:
            yaml_case_id = yaml_data['case_id']

            # 在Python中查找case_id
            python_case_id_match = re.search(r'case_id\s*=\s*["\']([^"\']+)["\']', python_content)

            if python_case_id_match:
                python_case_id = python_case_id_match.group(1)

                if python_case_id != yaml_case_id:
                    self.errors.append({
                        'type': 'CASE_ID_MISMATCH',
                        'severity': 'ERROR',
                        'message': f'Python和YAML的case_id不一致',
                        'details': f'Python: {python_case_id}, YAML: {yaml_case_id}',
                        'suggestion': '请确保两个文件使用相同的case_id'
                    })
            else:
                self.warnings.append({
                    'type': 'MISSING_CASE_ID_IN_PYTHON',
                    'severity': 'WARNING',
                    'message': 'Python代码中未找到case_id定义',
                    'suggestion': '建议在TestCase类中定义case_id属性'
                })

        # 检查YAML中的配置是否在Python中被使用
        if 'config' in yaml_data:
            config_keys = self._get_all_keys(yaml_data['config'])

            for key in config_keys:
                # 检查Python中是否引用了这个配置
                if key not in python_content:
                    self.warnings.append({
                        'type': 'UNUSED_CONFIG',
                        'severity': 'WARNING',
                        'message': f'YAML配置 "{key}" 在Python中未被使用',
                        'suggestion': f'请确认是否需要使用 config["{key}"]'
                    })

    def _validate_code_structure(self, python_ast: ast.AST, python_content: str):
        """校验代码结构"""
        # 检查是否有try-finally
        has_try_finally = False
        for node in ast.walk(python_ast):
            if isinstance(node, ast.Try) and node.finalbody:
                has_try_finally = True
                break

        if not has_try_finally:
            self.warnings.append({
                'type': 'MISSING_TRY_FINALLY',
                'severity': 'WARNING',
                'message': '代码中未找到try-finally结构',
                'suggestion': '建议使用try-finally确保资源清理'
            })

        # 检查是否调用了load_case_config
        if 'load_case_config' not in python_content:
            self.errors.append({
                'type': 'MISSING_LOAD_CONFIG',
                'severity': 'ERROR',
                'message': '未调用load_case_config()加载配置',
                'suggestion': '请在setUp或test方法开始时调用 config = self.load_case_config()'
            })

        # 检查是否使用了self.device
        if 'self.device' not in python_content:
            self.warnings.append({
                'type': 'MISSING_DEVICE_USAGE',
                'severity': 'WARNING',
                'message': '未使用self.device',
                'suggestion': '通常需要使用self.device来创建Lib实例'
            })

    def _validate_code_style(self, python_ast: ast.AST, python_content: str):
        """校验代码风格"""
        # 检查是否有docstring
        has_module_docstring = ast.get_docstring(python_ast) is not None

        if not has_module_docstring:
            self.warnings.append({
                'type': 'MISSING_MODULE_DOCSTRING',
                'severity': 'WARNING',
                'message': '缺少模块级docstring',
                'suggestion': '建议在文件开头添加docstring说明TestCase用途'
            })

        # 检查test方法是否有docstring
        for node in ast.walk(python_ast):
            if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                if not ast.get_docstring(node):
                    self.warnings.append({
                        'type': 'MISSING_TEST_DOCSTRING',
                        'severity': 'WARNING',
                        'message': f'测试方法 {node.name} 缺少docstring',
                        'suggestion': f'建议为 {node.name} 添加docstring说明测试目的'
                    })

        # 检查是否有硬编码的值(简单检查)
        hardcoded_patterns = [
            (r'\b0x[0-9a-fA-F]+\b', '十六进制值'),
            (r'\b\d{4,}\b', '大数字'),
        ]

        for pattern, desc in hardcoded_patterns:
            matches = re.findall(pattern, python_content)
            if matches:
                self.info.append({
                    'type': 'POTENTIAL_HARDCODED_VALUE',
                    'severity': 'INFO',
                    'message': f'发现可能的硬编码{desc}: {matches[:3]}',
                    'suggestion': '请确认这些值是否应该从YAML配置中读取'
                })

    def _generate_report(self, python_file: str, yaml_file: str) -> Dict:
        """生成校验报告"""
        report = {
            'python_file': python_file,
            'yaml_file': yaml_file,
            'context_package': str(self.package_dir),
            'summary': {
                'total_errors': len(self.errors),
                'total_warnings': len(self.warnings),
                'total_info': len(self.info),
                'passed': len(self.errors) == 0
            },
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }

        # 保存报告
        report_file = self.package_dir / "validation_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # 打印报告
        self._print_report(report)

        return report

    def _print_report(self, report: Dict):
        """打印校验报告"""
        print("=" * 80)
        print("📊 校验报告")
        print("=" * 80)
        print()

        summary = report['summary']

        if summary['passed']:
            print("✅ 校验通过!")
        else:
            print("❌ 校验失败!")

        print()
        print(f"   错误: {summary['total_errors']}")
        print(f"   警告: {summary['total_warnings']}")
        print(f"   信息: {summary['total_info']}")
        print()

        # 打印错误
        if self.errors:
            print("🔴 错误:")
            print()
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. [{error['type']}] {error['message']}")
                if 'details' in error:
                    print(f"      详情: {error['details']}")
                if 'suggestion' in error:
                    print(f"      建议: {error['suggestion']}")
                print()

        # 打印警告
        if self.warnings:
            print("🟡 警告:")
            print()
            for i, warning in enumerate(self.warnings, 1):
                print(f"   {i}. [{warning['type']}] {warning['message']}")
                if 'suggestion' in warning:
                    print(f"      建议: {warning['suggestion']}")
                print()

        # 打印信息
        if self.info:
            print("ℹ️  信息:")
            print()
            for i, info_item in enumerate(self.info, 1):
                print(f"   {i}. [{info_item['type']}] {info_item['message']}")
                if 'suggestion' in info_item:
                    print(f"      建议: {info_item['suggestion']}")
                print()

        print("=" * 80)
        print()

        if summary['passed']:
            print("✅ 代码质量良好,可以提交PR!")
        else:
            print("❌ 请修复上述错误后再提交!")
            print()
            print("💡 提示: 运行以下命令获取修复建议:")
            print(f"   python fix_case.py {self.package_dir} {report['python_file']} {report['yaml_file']}")

        print()

    def _get_all_keys(self, data: Dict, prefix: str = "") -> List[str]:
        """递归获取所有配置key"""
        keys = []

        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                keys.append(key)  # 只添加最后一级的key

                if isinstance(value, dict):
                    keys.extend(self._get_all_keys(value, full_key))

        return keys


def main():
    parser = argparse.ArgumentParser(description='Validate generated TestCase')
    parser.add_argument('context_package_dir', type=str,
                       help='Context package directory')
    parser.add_argument('python_file', type=str,
                       help='Python TestCase file to validate')
    parser.add_argument('yaml_file', type=str,
                       help='YAML config file to validate')

    args = parser.parse_args()

    try:
        validator = TestCaseValidator(args.context_package_dir)
        report = validator.validate(args.python_file, args.yaml_file)

        # 返回非0退出码如果有错误
        exit(0 if report['summary']['passed'] else 1)

    except Exception as e:
        print(f"❌ 校验失败: {e}")
        import traceback
        traceback.print_exc()
        exit(2)


if __name__ == '__main__':
    main()
