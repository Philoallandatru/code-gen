#!/usr/bin/env python3
"""
OpenCode上下文包生成器

用法:
    python generate_context.py "验证SSD在idle后进入PS4低功耗状态"

输出:
    .opencode/context_packages/TC_XXX_YYYYMMDD/
        - context.md      # 复制到OpenCode的完整上下文
        - prompt.md       # 复制到OpenCode的prompt
        - metadata.json   # 元数据(用于后续校验)
"""

import os
import json
import ast
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
import argparse


class ContextPackageGenerator:
    """为OpenCode生成上下文包"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.lib_dir = self.project_root / "Lib"
        self.testcase_dir = self.project_root / "TestCase"
        self.config_dir = self.project_root / "configs"
        self.opencode_dir = self.project_root / ".opencode"
        self.registry_dir = self.opencode_dir / "registry"
        self.prompts_dir = self.opencode_dir / "prompts"
        self.packages_dir = self.opencode_dir / "context_packages"

        # 确保目录存在
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.packages_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, requirement: str) -> str:
        """
        生成上下文包
        返回: 上下文包目录路径
        """
        print("🔍 Step 1: 扫描代码库...")
        registries = self._scan_or_load_registries()

        print("🔍 Step 2: 解析需求...")
        parsed_req = self._parse_requirement(requirement)

        print("🔍 Step 3: 匹配Lib API...")
        matched_apis = self._match_apis(parsed_req, registries)
        print(f"   匹配到 {len(matched_apis)} 个相关API")

        print("🔍 Step 4: 匹配YAML Schema...")
        matched_schemas = self._match_yaml_schemas(parsed_req, registries)
        print(f"   匹配到 {len(matched_schemas)} 个相关Schema")

        print("🔍 Step 5: 检索相似Case...")
        similar_cases = self._find_similar_cases(parsed_req, registries)
        print(f"   找到 {len(similar_cases)} 个相似Case")

        print("🔍 Step 6: 生成上下文包...")
        package_dir = self._create_package(
            requirement,
            parsed_req,
            matched_apis,
            matched_schemas,
            similar_cases,
            registries
        )

        print(f"\n✅ 上下文包已生成: {package_dir}")
        print(f"\n📋 下一步:")
        print(f"   1. 打开 {package_dir}/prompt.md")
        print(f"   2. 复制全部内容到 OpenCode")
        print(f"   3. 让 OpenCode 生成代码")
        print(f"   4. 将生成的代码保存到本地")
        print(f"   5. 运行校验: python validate_case.py {package_dir}")

        return str(package_dir)

    def _scan_or_load_registries(self) -> Dict:
        """扫描或加载缓存的注册表"""
        lib_registry_file = self.registry_dir / "lib_api_registry.json"
        yaml_registry_file = self.registry_dir / "yaml_schema_registry.json"
        case_patterns_file = self.registry_dir / "case_patterns.json"

        # 检查缓存是否存在且新鲜(1小时内)
        cache_valid = all([
            f.exists() and (datetime.now().timestamp() - f.stat().st_mtime) < 3600
            for f in [lib_registry_file, yaml_registry_file, case_patterns_file]
        ])

        if cache_valid:
            print("   使用缓存的注册表...")
            with open(lib_registry_file, 'r', encoding='utf-8') as f:
                lib_registry = json.load(f)
            with open(yaml_registry_file, 'r', encoding='utf-8') as f:
                yaml_registry = json.load(f)
            with open(case_patterns_file, 'r', encoding='utf-8') as f:
                case_patterns = json.load(f)
        else:
            print("   扫描代码库(首次运行或缓存过期)...")
            lib_registry = self._scan_lib_apis()
            yaml_registry = self._scan_yaml_schemas()
            case_patterns = self._scan_case_patterns()

            # 保存缓存
            with open(lib_registry_file, 'w', encoding='utf-8') as f:
                json.dump(lib_registry, f, indent=2, ensure_ascii=False)
            with open(yaml_registry_file, 'w', encoding='utf-8') as f:
                json.dump(yaml_registry, f, indent=2, ensure_ascii=False)
            with open(case_patterns_file, 'w', encoding='utf-8') as f:
                json.dump(case_patterns, f, indent=2, ensure_ascii=False)

        return {
            'lib_api': lib_registry,
            'yaml_schema': yaml_registry,
            'case_patterns': case_patterns
        }

    def _scan_lib_apis(self) -> Dict:
        """扫描Lib目录,提取API信息"""
        apis = {}

        if not self.lib_dir.exists():
            print(f"   警告: Lib目录不存在: {self.lib_dir}")
            return {'apis': apis, 'total': 0}

        for py_file in self.lib_dir.rglob("*.py"):
            if py_file.name.startswith("__"):
                continue

            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())

                # 提取类和方法
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_name = node.name

                        for item in node.body:
                            if isinstance(item, ast.FunctionDef):
                                if item.name.startswith("_"):
                                    continue  # 跳过私有方法

                                func_name = item.name
                                api_id = f"{py_file.stem}.{func_name}"

                                # 提取参数
                                params = []
                                for arg in item.args.args:
                                    if arg.arg != 'self':
                                        params.append({
                                            'name': arg.arg,
                                            'type': self._get_type_annotation(arg)
                                        })

                                # 提取docstring
                                docstring = ast.get_docstring(item) or ""

                                apis[api_id] = {
                                    'api_id': api_id,
                                    'file': str(py_file.relative_to(self.project_root)),
                                    'class': class_name,
                                    'function': func_name,
                                    'params': params,
                                    'docstring': docstring,
                                    'import_statement': f"from {self._get_module_path(py_file)} import {class_name}"
                                }
            except Exception as e:
                print(f"   警告: 无法解析 {py_file}: {e}")

        return {'apis': apis, 'total': len(apis)}

    def _scan_yaml_schemas(self) -> Dict:
        """扫描configs目录,提取YAML schema"""
        schemas = {}

        if not self.config_dir.exists():
            print(f"   警告: configs目录不存在: {self.config_dir}")
            return {'schemas': schemas, 'total': 0}

        for yaml_file in self.config_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)

                if not data:
                    continue

                # 提取schema结构
                schema_id = yaml_file.stem
                fields = self._extract_yaml_fields(data)

                schemas[schema_id] = {
                    'schema_id': schema_id,
                    'file': str(yaml_file.relative_to(self.project_root)),
                    'fields': fields,
                    'example': data
                }
            except Exception as e:
                print(f"   警告: 无法解析 {yaml_file}: {e}")

        return {'schemas': schemas, 'total': len(schemas)}

    def _scan_case_patterns(self) -> Dict:
        """扫描TestCase目录,提取常见模式"""
        patterns = {}

        if not self.testcase_dir.exists():
            print(f"   警告: TestCase目录不存在: {self.testcase_dir}")
            return {'patterns': patterns, 'total': 0}

        for py_file in self.testcase_dir.rglob("test_*.py"):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                # 提取import语句
                imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith('Lib'):
                            for alias in node.names:
                                imports.append(f"from {node.module} import {alias.name}")

                # 提取test方法结构
                test_methods = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                        test_methods.append({
                            'name': node.name,
                            'has_try_finally': self._has_try_finally(node)
                        })

                if imports or test_methods:
                    patterns[py_file.stem] = {
                        'file': str(py_file.relative_to(self.project_root)),
                        'imports': imports,
                        'test_methods': test_methods,
                        'snippet': content[:500]  # 前500字符作为示例
                    }
            except Exception as e:
                print(f"   警告: 无法解析 {py_file}: {e}")

        return {'patterns': patterns, 'total': len(patterns)}

    def _parse_requirement(self, requirement: str) -> Dict:
        """简单的需求解析"""
        # 提取关键词
        keywords = []
        keyword_map = {
            'power': ['power', 'PS0', 'PS1', 'PS2', 'PS3', 'PS4', 'APST', '功耗', '低功耗'],
            'nvme': ['NVMe', 'namespace', '命名空间', 'admin', 'command'],
            'log': ['log', 'UART', '日志'],
            'sanitize': ['sanitize', '清理', '擦除'],
            'smart': ['SMART', '健康', 'health'],
        }

        req_lower = requirement.lower()
        for category, terms in keyword_map.items():
            if any(term.lower() in req_lower for term in terms):
                keywords.append(category)

        return {
            'raw_text': requirement,
            'keywords': keywords
        }

    def _match_apis(self, parsed_req: Dict, registries: Dict) -> List[Dict]:
        """匹配相关的API"""
        matched = []
        keywords = parsed_req['keywords']

        for api_id, api_info in registries['lib_api']['apis'].items():
            # 简单的关键词匹配
            api_text = f"{api_id} {api_info['docstring']}".lower()

            score = sum(1 for kw in keywords if kw in api_text)

            if score > 0:
                matched.append({
                    **api_info,
                    'match_score': score
                })

        # 按匹配分数排序
        matched.sort(key=lambda x: x['match_score'], reverse=True)

        return matched[:10]  # 返回top 10

    def _match_yaml_schemas(self, parsed_req: Dict, registries: Dict) -> List[Dict]:
        """匹配相关的YAML schema"""
        matched = []
        keywords = parsed_req['keywords']

        for schema_id, schema_info in registries['yaml_schema']['schemas'].items():
            schema_text = f"{schema_id} {schema_info['file']}".lower()

            score = sum(1 for kw in keywords if kw in schema_text)

            if score > 0:
                matched.append({
                    **schema_info,
                    'match_score': score
                })

        matched.sort(key=lambda x: x['match_score'], reverse=True)

        return matched[:3]  # 返回top 3

    def _find_similar_cases(self, parsed_req: Dict, registries: Dict) -> List[Dict]:
        """查找相似的TestCase"""
        similar = []
        keywords = parsed_req['keywords']

        for pattern_id, pattern_info in registries['case_patterns']['patterns'].items():
            pattern_text = f"{pattern_id} {pattern_info['file']}".lower()

            score = sum(1 for kw in keywords if kw in pattern_text)

            if score > 0:
                similar.append({
                    **pattern_info,
                    'match_score': score
                })

        similar.sort(key=lambda x: x['match_score'], reverse=True)

        return similar[:3]  # 返回top 3

    def _create_package(self, requirement: str, parsed_req: Dict,
                       matched_apis: List, matched_schemas: List,
                       similar_cases: List, registries: Dict) -> Path:
        """创建上下文包"""
        # 生成包目录名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"package_{timestamp}"
        package_dir = self.packages_dir / package_name
        package_dir.mkdir(parents=True, exist_ok=True)

        # 生成context.md
        context_md = self._generate_context_md(
            requirement,
            matched_apis,
            matched_schemas,
            similar_cases
        )

        with open(package_dir / "context.md", 'w', encoding='utf-8') as f:
            f.write(context_md)

        # 生成prompt.md
        prompt_md = self._generate_prompt_md(
            requirement,
            matched_apis,
            matched_schemas,
            similar_cases
        )

        with open(package_dir / "prompt.md", 'w', encoding='utf-8') as f:
            f.write(prompt_md)

        # 保存元数据
        metadata = {
            'requirement': requirement,
            'parsed_req': parsed_req,
            'matched_apis': [api['api_id'] for api in matched_apis],
            'matched_schemas': [s['schema_id'] for s in matched_schemas],
            'similar_cases': [c['file'] for c in similar_cases],
            'created_at': datetime.now().isoformat()
        }

        with open(package_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return package_dir

    def _generate_context_md(self, requirement: str, matched_apis: List,
                            matched_schemas: List, similar_cases: List) -> str:
        """生成context.md内容"""
        lines = []

        lines.append("# TestCase Generation Context")
        lines.append("")
        lines.append(f"**Requirement:** {requirement}")
        lines.append("")

        # Allowed APIs
        lines.append("## Allowed Lib APIs")
        lines.append("")
        lines.append("You MUST ONLY use the following APIs. Do NOT invent or guess other APIs.")
        lines.append("")

        if matched_apis:
            for api in matched_apis:
                lines.append(f"### {api['api_id']}")
                lines.append(f"- **File:** `{api['file']}`")
                lines.append(f"- **Class:** `{api['class']}`")
                lines.append(f"- **Function:** `{api['function']}`")
                lines.append(f"- **Import:** `{api['import_statement']}`")
                if api['params']:
                    lines.append(f"- **Parameters:**")
                    for param in api['params']:
                        lines.append(f"  - `{param['name']}`: {param.get('type', 'any')}")
                if api['docstring']:
                    lines.append(f"- **Description:** {api['docstring']}")
                lines.append("")
        else:
            lines.append("⚠️  No matching APIs found. You may need to manually specify APIs.")
            lines.append("")

        # YAML Schemas
        lines.append("## YAML Configuration Schema")
        lines.append("")
        lines.append("You MUST ONLY use the following YAML fields. Do NOT invent new fields.")
        lines.append("")

        if matched_schemas:
            for schema in matched_schemas:
                lines.append(f"### Schema: {schema['schema_id']}")
                lines.append(f"- **Example File:** `{schema['file']}`")
                lines.append(f"- **Fields:**")
                for field in schema['fields']:
                    lines.append(f"  - `{field}`")
                lines.append("")
                lines.append("**Example:**")
                lines.append("```yaml")
                lines.append(yaml.dump(schema['example'], allow_unicode=True, default_flow_style=False))
                lines.append("```")
                lines.append("")
        else:
            lines.append("⚠️  No matching YAML schemas found. You may need to manually specify schema.")
            lines.append("")

        # Similar Cases
        lines.append("## Similar TestCases (for reference)")
        lines.append("")

        if similar_cases:
            for case in similar_cases:
                lines.append(f"### {case['file']}")
                if case['imports']:
                    lines.append(f"- **Imports:**")
                    for imp in case['imports']:
                        lines.append(f"  - `{imp}`")
                lines.append("")
                lines.append("**Code Snippet:**")
                lines.append("```python")
                lines.append(case['snippet'])
                lines.append("```")
                lines.append("")
        else:
            lines.append("⚠️  No similar test cases found.")
            lines.append("")

        return "\n".join(lines)

    def _generate_prompt_md(self, requirement: str, matched_apis: List,
                           matched_schemas: List, similar_cases: List) -> str:
        """生成给OpenCode的最终prompt"""
        lines = []

        lines.append("# Task: Generate Python TestCase and YAML Config")
        lines.append("")
        lines.append(f"**Requirement:** {requirement}")
        lines.append("")

        lines.append("## CRITICAL RULES")
        lines.append("")
        lines.append("1. **API Usage:**")
        lines.append("   - You MUST ONLY use APIs listed in the 'Allowed Lib APIs' section below")
        lines.append("   - You MUST NOT invent, guess, or use any other APIs")
        lines.append("   - Use the exact import statements provided")
        lines.append("")
        lines.append("2. **YAML Configuration:**")
        lines.append("   - You MUST ONLY use YAML fields defined in the 'YAML Schema' section")
        lines.append("   - You MUST NOT invent new YAML keys")
        lines.append("   - All configurable values MUST come from YAML, not hardcoded in Python")
        lines.append("")
        lines.append("3. **Code Structure:**")
        lines.append("   - Use `try-finally` for cleanup")
        lines.append("   - Load config with `self.load_case_config()`")
        lines.append("   - Create Lib instances with `self.device`")
        lines.append("   - Follow the patterns shown in 'Similar TestCases'")
        lines.append("")

        # 嵌入context
        lines.append("---")
        lines.append("")
        lines.append(self._generate_context_md(requirement, matched_apis, matched_schemas, similar_cases))
        lines.append("")
        lines.append("---")
        lines.append("")

        lines.append("## Output Format")
        lines.append("")
        lines.append("Please generate TWO outputs:")
        lines.append("")
        lines.append("### 1. Python TestCase")
        lines.append("```python")
        lines.append("# Your Python code here")
        lines.append("```")
        lines.append("")
        lines.append("### 2. YAML Configuration")
        lines.append("```yaml")
        lines.append("# Your YAML config here")
        lines.append("```")

        return "\n".join(lines)

    # Helper methods

    def _get_type_annotation(self, arg) -> str:
        """获取类型注解"""
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                return arg.annotation.id
            elif isinstance(arg.annotation, ast.Constant):
                return str(arg.annotation.value)
        return "any"

    def _get_module_path(self, file_path: Path) -> str:
        """获取模块路径"""
        rel_path = file_path.relative_to(self.project_root)
        return str(rel_path.with_suffix('')).replace(os.sep, '.')

    def _extract_yaml_fields(self, data: Dict, prefix: str = "") -> List[str]:
        """递归提取YAML字段"""
        fields = []

        if isinstance(data, dict):
            for key, value in data.items():
                field_path = f"{prefix}.{key}" if prefix else key
                fields.append(field_path)

                if isinstance(value, dict):
                    fields.extend(self._extract_yaml_fields(value, field_path))

        return fields

    def _has_try_finally(self, node: ast.FunctionDef) -> bool:
        """检查函数是否有try-finally"""
        for item in ast.walk(node):
            if isinstance(item, ast.Try) and item.finalbody:
                return True
        return False


def main():
    parser = argparse.ArgumentParser(description='Generate context package for OpenCode')
    parser.add_argument('requirement', type=str, help='Test requirement description')
    parser.add_argument('--project-root', type=str, default='.',
                       help='Project root directory (default: current directory)')

    args = parser.parse_args()

    generator = ContextPackageGenerator(args.project_root)
    package_dir = generator.generate(args.requirement)

    print(f"\n✅ Done! Package created at: {package_dir}")


if __name__ == '__main__':
    main()
