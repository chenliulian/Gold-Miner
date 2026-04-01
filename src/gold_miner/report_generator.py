"""报告生成器 - 支持多种格式导出.

This module provides report generation capabilities:
- Markdown format (primary)
- PDF, Excel, Word, CSV, JSON (future extensions)
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ReportFormat(Enum):
    """支持的报告格式."""

    MARKDOWN = "md"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "xlsx"
    WORD = "docx"
    CSV = "csv"
    JSON = "json"


@dataclass
class ReportData:
    """报告数据结构."""

    title: str
    content: str  # Markdown 内容
    tables: List[Dict[str, Any]] = field(default_factory=list)  # 数据表格
    charts: List[Dict[str, Any]] = field(default_factory=list)  # 图表数据
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    session_id: Optional[str] = None


class ReportGenerator:
    """报告生成器."""

    def __init__(self, output_dir: str):
        """初始化报告生成器.

        Args:
            output_dir: 报告输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(
        self,
        report_data: ReportData,
        fmt: ReportFormat,
        output_path: Optional[str] = None,
    ) -> str:
        """生成报告文件.

        Args:
            report_data: 报告数据
            fmt: 输出格式
            output_path: 自定义输出路径（可选）

        Returns:
            生成的文件路径

        Raises:
            ValueError: 不支持的格式
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{report_data.title}_{timestamp}.{fmt.value}"
            # 清理文件名中的非法字符
            filename = self._sanitize_filename(filename)
            output_path = os.path.join(self.output_dir, filename)

        if fmt == ReportFormat.MARKDOWN:
            return self._generate_markdown(report_data, output_path)
        elif fmt == ReportFormat.HTML:
            return self._generate_html(report_data, output_path)
        elif fmt == ReportFormat.PDF:
            return self._generate_pdf(report_data, output_path)
        elif fmt == ReportFormat.EXCEL:
            return self._generate_excel(report_data, output_path)
        elif fmt == ReportFormat.WORD:
            return self._generate_word(report_data, output_path)
        elif fmt == ReportFormat.CSV:
            return self._generate_csv(report_data, output_path)
        elif fmt == ReportFormat.JSON:
            return self._generate_json(report_data, output_path)
        else:
            raise ValueError(f"不支持的格式: {fmt}")

    def _generate_markdown(self, data: ReportData, path: str) -> str:
        """生成 Markdown 报告.

        Args:
            data: 报告数据
            path: 输出路径

        Returns:
            生成的文件路径
        """
        lines = []

        # 标题
        lines.append(f"# {data.title}")
        lines.append("")

        # 元信息
        lines.append("---")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if data.session_id:
            lines.append(f"**会话ID**: {data.session_id}")
        if data.metadata.get("query_count"):
            lines.append(f"**查询次数**: {data.metadata['query_count']}")
        lines.append("---")
        lines.append("")

        # 主要内容
        content = data.content
        
        # 处理内容中的表格，优化格式
        content = self._format_tables_in_content(content)
        
        lines.append(content)
        lines.append("")

        # 写入文件
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return path

    def _format_tables_in_content(self, content: str) -> str:
        """优化内容中的 Markdown 表格格式.

        Args:
            content: 原始内容

        Returns:
            优化后的内容
        """
        # 查找所有表格
        lines = content.split('\n')
        result_lines = []
        table_lines = []
        in_table = False

        for line in lines:
            # 检测表格行（以 | 开头和结尾）
            if line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
            else:
                if in_table:
                    # 处理完一个表格，优化它
                    formatted_table = self._format_table(table_lines)
                    result_lines.extend(formatted_table)
                    in_table = False
                    table_lines = []
                result_lines.append(line)

        # 处理最后一个表格
        if in_table and table_lines:
            formatted_table = self._format_table(table_lines)
            result_lines.extend(formatted_table)

        return '\n'.join(result_lines)

    def _format_table(self, table_lines: List[str]) -> List[str]:
        """格式化单个 Markdown 表格.

        Args:
            table_lines: 表格行列表

        Returns:
            格式化后的表格行
        """
        if len(table_lines) < 2:
            return table_lines

        # 解析表格
        rows = []
        for line in table_lines:
            # 提取单元格内容
            cells = [cell.strip() for cell in line.strip()[1:-1].split('|')]
            rows.append(cells)

        if not rows:
            return table_lines

        # 确定列数
        num_cols = max(len(row) for row in rows)

        # 标准化所有行的列数
        for row in rows:
            while len(row) < num_cols:
                row.append('')
            row[:] = row[:num_cols]

        # 计算每列的最大宽度
        col_widths = []
        for col_idx in range(num_cols):
            max_width = 0
            for row in rows:
                if col_idx < len(row):
                    max_width = max(max_width, len(row[col_idx]))
            # 最小宽度为 3，最大为 25
            col_widths.append(max(min(max_width + 2, 25), 3))

        # 格式化行
        formatted = []
        for i, row in enumerate(rows):
            # 跳过分隔线行（包含 --- 的行）
            if i == 1 and all('---' in cell or cell.strip() == '' for cell in row):
                # 生成分隔线
                separators = ['-' * width for width in col_widths]
                formatted.append('| ' + ' | '.join(separators) + ' |')
            else:
                # 格式化数据行
                formatted_cells = []
                for col_idx, cell in enumerate(row):
                    width = col_widths[col_idx] if col_idx < len(col_widths) else 15
                    # 左对齐，填充空格
                    formatted_cells.append(cell.ljust(width))
                formatted.append('| ' + ' | '.join(formatted_cells) + ' |')

        return formatted

    def _generate_pdf(self, data: ReportData, path: str) -> str:
        """生成 PDF 报告（待实现）."""
        raise NotImplementedError("PDF 格式将在后续版本支持")

    def _generate_excel(self, data: ReportData, path: str) -> str:
        """生成 Excel 报告（待实现）."""
        raise NotImplementedError("Excel 格式将在后续版本支持")

    def _generate_html(self, data: ReportData, path: str) -> str:
        """生成 HTML 报告.

        Args:
            data: 报告数据
            path: 输出路径

        Returns:
            生成的文件路径
        """
        import re

        # 转换 Markdown 内容为 HTML
        content = data.content

        # 处理标题
        content = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)

        # 处理粗体
        content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)

        # 处理表格
        content = self._markdown_tables_to_html(content)

        # 处理代码块
        content = re.sub(r'`(.*?)`', r'<code>\1</code>', content)

        # 处理列表
        content = self._markdown_lists_to_html(content)

        # 处理段落（简单的换行转换）
        paragraphs = content.split('\n\n')
        processed_paragraphs = []
        for p in paragraphs:
            p = p.strip()
            if p and not p.startswith('<') and not p.startswith('---'):
                processed_paragraphs.append(f'<p>{p}</p>')
            else:
                processed_paragraphs.append(p)
        content = '\n\n'.join(processed_paragraphs)

        # 处理分隔线
        content = content.replace('---', '<hr>')

        # 生成时间
        generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data.title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            padding: 40px;
        }}

        .header {{
            border-bottom: 2px solid #e8e8e8;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}

        .header h1 {{
            font-size: 28px;
            color: #1a1a1a;
            margin-bottom: 12px;
            font-weight: 600;
        }}

        .meta {{
            color: #666;
            font-size: 14px;
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .meta-label {{
            color: #999;
        }}

        h1 {{
            font-size: 24px;
            color: #1a1a1a;
            margin: 30px 0 16px 0;
            font-weight: 600;
            padding-bottom: 8px;
            border-bottom: 2px solid #f0f0f0;
        }}

        h2 {{
            font-size: 20px;
            color: #262626;
            margin: 24px 0 12px 0;
            font-weight: 600;
        }}

        h3 {{
            font-size: 16px;
            color: #333;
            margin: 20px 0 10px 0;
            font-weight: 600;
        }}

        p {{
            margin: 12px 0;
            color: #444;
            line-height: 1.8;
        }}

        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin: 16px 0;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        th {{
            background: #f8f9fa;
            color: #333;
            font-weight: 600;
            padding: 12px 16px;
            text-align: left;
            border-bottom: 2px solid #e8e8e8;
            font-size: 14px;
        }}

        td {{
            padding: 12px 16px;
            border-bottom: 1px solid #f0f0f0;
            font-size: 14px;
            color: #444;
        }}

        tr:last-child td {{
            border-bottom: none;
        }}

        tr:hover {{
            background: #fafafa;
        }}

        code {{
            background: #f4f4f5;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: "SF Mono", Monaco, "Cascadia Code", monospace;
            font-size: 13px;
            color: #d73a49;
        }}

        strong {{
            color: #1a1a1a;
            font-weight: 600;
        }}

        ul, ol {{
            margin: 12px 0;
            padding-left: 24px;
        }}

        li {{
            margin: 6px 0;
            color: #444;
        }}

        ul li::marker {{
            color: #1890ff;
        }}

        hr {{
            border: none;
            border-top: 1px solid #e8e8e8;
            margin: 24px 0;
        }}

        .section {{
            margin: 24px 0;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}
            .container {{
                box-shadow: none;
                max-width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{data.title}</h1>
            <div class="meta">
                <div class="meta-item">
                    <span class="meta-label">生成时间:</span>
                    <span>{generated_time}</span>
                </div>
                {f'<div class="meta-item"><span class="meta-label">会话ID:</span><span>{data.session_id}</span></div>' if data.session_id else ''}
                {f'<div class="meta-item"><span class="meta-label">查询次数:</span><span>{data.metadata["query_count"]}</span></div>' if data.metadata.get("query_count") else ''}
            </div>
        </div>

        <div class="content">
            {content}
        </div>
    </div>
</body>
</html>'''

        with open(path, "w", encoding="utf-8") as f:
            f.write(html_template)

        return path

    def _markdown_tables_to_html(self, content: str) -> str:
        """将 Markdown 表格转换为 HTML 表格."""
        import re

        lines = content.split('\n')
        result = []
        table_lines = []
        in_table = False

        for line in lines:
            if line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
            else:
                if in_table:
                    # 转换表格
                    html_table = self._convert_table_to_html(table_lines)
                    result.append(html_table)
                    in_table = False
                    table_lines = []
                result.append(line)

        if in_table and table_lines:
            html_table = self._convert_table_to_html(table_lines)
            result.append(html_table)

        return '\n'.join(result)

    def _convert_table_to_html(self, table_lines: list) -> str:
        """将 Markdown 表格行转换为 HTML 表格."""
        if len(table_lines) < 2:
            return '\n'.join(table_lines)

        rows = []
        for line in table_lines:
            cells = [cell.strip() for cell in line.strip()[1:-1].split('|')]
            rows.append(cells)

        if not rows:
            return '\n'.join(table_lines)

        # 第一行是表头
        header = rows[0]
        # 第二行是分隔线，跳过
        data_rows = rows[2:] if len(rows) > 2 else []

        html = ['<table>']

        # 表头
        html.append('  <thead>')
        html.append('    <tr>')
        for cell in header:
            html.append(f'      <th>{cell}</th>')
        html.append('    </tr>')
        html.append('  </thead>')

        # 数据行
        if data_rows:
            html.append('  <tbody>')
            for row in data_rows:
                html.append('    <tr>')
                for cell in row:
                    html.append(f'      <td>{cell}</td>')
                html.append('    </tr>')
            html.append('  </tbody>')

        html.append('</table>')
        return '\n'.join(html)

    def _markdown_lists_to_html(self, content: str) -> str:
        """将 Markdown 列表转换为 HTML 列表."""
        import re

        lines = content.split('\n')
        result = []
        in_ul = False
        in_ol = False

        for line in lines:
            # 无序列表
            ul_match = re.match(r'^(\s*)[-*] (.*)$', line)
            # 有序列表
            ol_match = re.match(r'^(\s*)\d+\. (.*)$', line)

            if ul_match:
                if not in_ul:
                    result.append('<ul>')
                    in_ul = True
                result.append(f'  <li>{ul_match.group(2)}</li>')
            elif ol_match:
                if not in_ol:
                    result.append('<ol>')
                    in_ol = True
                result.append(f'  <li>{ol_match.group(2)}</li>')
            else:
                if in_ul:
                    result.append('</ul>')
                    in_ul = False
                if in_ol:
                    result.append('</ol>')
                    in_ol = False
                result.append(line)

        # 关闭未闭合的列表
        if in_ul:
            result.append('</ul>')
        if in_ol:
            result.append('</ol>')

        return '\n'.join(result)

    def _generate_word(self, data: ReportData, path: str) -> str:
        """生成 Word 报告（待实现）."""
        raise NotImplementedError("Word 格式将在后续版本支持")

    def _generate_csv(self, data: ReportData, path: str) -> str:
        """生成 CSV 报告（待实现）."""
        raise NotImplementedError("CSV 格式将在后续版本支持")

    def _generate_json(self, data: ReportData, path: str) -> str:
        """生成 JSON 报告（待实现）."""
        raise NotImplementedError("JSON 格式将在后续版本支持")

    @staticmethod
    def _sanitize_filename(filename: str) -> str:
        """清理文件名中的非法字符.

        Args:
            filename: 原始文件名

        Returns:
            清理后的文件名
        """
        # 替换非法字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename


def extract_session_content(session_data: Dict[str, Any], max_rounds: int = 10) -> Dict[str, Any]:
    """从会话数据提取内容.

    只提取用户问题和 LLM 最终回答，不包含执行日志。
    当对话轮次过多时，优先保留最近的内容。

    Args:
        session_data: 会话数据
        max_rounds: 最大保留的对话轮次（用户+助手算一轮）

    Returns:
        提取的内容字典
    """
    # 支持两种数据格式: messages (新格式) 或 steps (旧格式)
    messages = session_data.get("messages", [])
    steps = session_data.get("steps", [])

    # 如果有 steps 没有 messages，使用 steps
    if steps and not messages:
        messages = steps

    # 按轮次组织对话（一个用户消息 + 一个助手回复 = 一轮）
    rounds = []
    current_round = {}
    
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        
        if role == "user":
            # 如果已有未完成的轮次，先保存
            if current_round:
                rounds.append(current_round)
            # 开始新轮次
            current_round = {"user": content, "assistant": None}
        elif role == "assistant":
            # 提取助手回复（优先取 report_markdown，其次是最终答案）
            assistant_content = None
            if isinstance(content, str) and content.strip().startswith("{"):
                try:
                    parsed = json.loads(content)
                    if "report_markdown" in parsed:
                        assistant_content = parsed["report_markdown"]
                    elif "answer" in parsed:
                        assistant_content = parsed["answer"]
                    elif "content" in parsed:
                        assistant_content = parsed["content"]
                except json.JSONDecodeError:
                    assistant_content = content
            else:
                assistant_content = content
            
            if current_round:
                current_round["assistant"] = assistant_content
                rounds.append(current_round)
                current_round = {}
        # tool 角色的消息（执行日志）不收集
    
    # 处理最后一个未完成的轮次
    if current_round and "user" in current_round:
        rounds.append(current_round)

    # 只保留最近 N 轮对话
    if len(rounds) > max_rounds:
        rounds = rounds[-max_rounds:]

    # 格式化输出
    conversation_parts = []
    for i, round_data in enumerate(rounds, 1):
        parts = [f"【第{i}轮对话】"]
        if "user" in round_data:
            parts.append(f"用户: {round_data['user']}")
        if round_data.get("assistant"):
            # 截断过长的内容
            assistant_content = round_data["assistant"]
            if len(assistant_content) > 2000:
                assistant_content = assistant_content[:2000] + "..."
            parts.append(f"助手: {assistant_content}")
        conversation_parts.append("\n".join(parts))

    return {
        "conversation": "\n\n".join(conversation_parts),
        "message_count": len(messages),
        "query_count": len([m for m in messages if m.get("role") == "tool"]),
        "rounds_count": len(rounds),
    }


def generate_summary_with_llm(
    session_data: Dict[str, Any],
    llm_client: Optional[Any] = None,
) -> str:
    """使用 LLM 生成会话总结.

    Args:
        session_data: 会话数据
        llm_client: LLM 客户端（可选）

    Returns:
        生成的总结报告（Markdown 格式）
    """
    # 提取会话内容
    content = extract_session_content(session_data)
    session_title = session_data.get("title", "数据分析会话")

    # 构建提示词
    prompt = f"""请根据以下数据分析会话的内容，生成一份结构化的分析报告。

会话标题: {session_title}

会话内容:
{content['conversation'][:4000]}

请生成一份专业的数据分析报告，要求如下:

1. **内容结构** (使用编号和emoji分层):
   - 1️⃣ 分析概述 - 简要说明分析目的和背景
   - 2️⃣ 关键发现 - 列出主要的数据洞察
   - 3️⃣ 详细分析 - 对数据进行深入解读
   - 4️⃣ 建议与结论 - 基于数据给出 actionable 的建议

2. **格式要求**:
   - 使用 Markdown 格式
   - 包含适当的标题层级（# ## ###）
   - 如果包含表格数据，使用标准的 Markdown 表格格式，确保列对齐
   - 不要包含 SQL 代码块
   - 不要包含原始数据详情

3. **表格美化要求**:
   - 使用 | 分隔列，表头后使用 |---|---| 分隔线
   - 数字列使用右对齐，确保视觉上对齐美观
   - 将大段文字描述转换为表格形式展示
   - 宽表格按维度拆分为多个小表格，每个表格聚焦一个主题

4. **视觉增强**:
   - **加粗** 重要的数字、指标和关键发现
   - 使用 ↑ ↓ 箭头表示增长/下降趋势
   - 使用 ⭐ 标注主要/最重要的项目
   - 使用 ✅ ⚠️ 🔄 等符号快速传达状态
   - 创建对比表格替代散点文字，便于快速理解

请直接输出报告内容，不要包含任何解释性文字。"""

    # 如果有 LLM 客户端，调用 LLM 生成总结
    if llm_client:
        try:
            response = llm_client.chat(prompt)
            # 清理响应内容
            response = _clean_report_content(response)
            return response
        except Exception as e:
            print(f"[ReportGenerator] LLM 总结失败: {e}")
            # 降级到使用原始报告内容

    # 如果没有 LLM 或 LLM 调用失败，尝试提取已有的 report_markdown
    messages = session_data.get("messages", []) or session_data.get("steps", [])
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip().startswith("{"):
                try:
                    parsed = json.loads(content)
                    if "report_markdown" in parsed:
                        return _clean_report_content(parsed["report_markdown"])
                except json.JSONDecodeError:
                    pass
            # 如果是纯文本的助手回复，也作为备选
            if content and len(content) > 100:
                return _clean_report_content(content)

    # 最后的备选：返回会话标题
    return f"# {session_title}\n\n暂无详细报告内容。"


def _clean_report_content(content: str) -> str:
    """清理报告内容.

    Args:
        content: 原始内容

    Returns:
        清理后的内容
    """
    # 移除 SQL 代码块
    content = re.sub(r'```sql\n.*?```', '', content, flags=re.DOTALL)
    
    # 移除 "数据详情" 部分
    content = re.sub(r'## 数据详情.*?(?=##|$)', '', content, flags=re.DOTALL)
    
    # 移除 "查询结果" 部分
    content = re.sub(r'### 查询结果.*?(?=###|##|$)', '', content, flags=re.DOTALL)
    
    # 清理多余的空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()


def generate_report_filename_with_llm(
    session_data: Dict[str, Any],
    llm_client: Optional[Any] = None,
) -> str:
    """使用 LLM 生成报告文件名.

    Args:
        session_data: 会话数据
        llm_client: LLM 客户端（可选）

    Returns:
        生成的文件名（不含扩展名）
    """
    session_title = session_data.get("title", "数据分析报告")
    
    if not llm_client:
        # 如果没有 LLM，使用会话标题
        return session_title
    
    # 构建提示词
    prompt = f"""请根据以下会话标题，生成一个简洁、专业的报告文件名。

会话标题: {session_title}

要求:
1. 文件名应该简洁明了，反映报告主题
2. 不要包含特殊字符（如 / \\ : * ? " < > |）
3. 长度控制在 30 个字符以内
4. 不要包含日期（系统会自动添加）
5. 不要包含文件扩展名

请直接输出文件名，不要包含任何其他文字。"""

    try:
        filename = llm_client.chat(prompt).strip()
        # 清理文件名
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # 移除扩展名（如果 LLM 添加了）
        filename = re.sub(r'\.(md|txt|doc)$', '', filename, flags=re.IGNORECASE)
        # 限制长度
        if len(filename) > 30:
            filename = filename[:30]
        return filename or session_title
    except Exception as e:
        print(f"[ReportGenerator] LLM 文件名生成失败: {e}")
        return session_title


def generate_report_from_session(
    session_data: Dict[str, Any],
    output_dir: str,
    title: Optional[str] = None,
    fmt: ReportFormat = ReportFormat.MARKDOWN,
    llm_client: Optional[Any] = None,
) -> str:
    """从会话数据生成报告.

    Args:
        session_data: 会话数据
        output_dir: 输出目录
        title: 报告标题（可选）
        fmt: 报告格式
        llm_client: LLM 客户端（可选），用于生成智能总结

    Returns:
        生成的文件路径
    """
    # 提取会话信息
    session_id = session_data.get("session_id", "unknown")
    
    print(f"[ReportGenerator] LLM client available: {llm_client is not None}")
    
    # 使用 LLM 生成报告文件名
    report_title = title
    if not report_title:
        report_title = generate_report_filename_with_llm(session_data, llm_client)
        print(f"[ReportGenerator] Generated title: {report_title}")
    
    # 使用 LLM 生成总结报告
    report_content = generate_summary_with_llm(session_data, llm_client)
    print(f"[ReportGenerator] Generated content length: {len(report_content)}")

    # 构建报告数据
    report_data = ReportData(
        title=report_title,
        content=report_content,
        tables=[],  # 不再附加数据表格
        session_id=session_id,
        metadata={
            "created_at": session_data.get("created_at") or session_data.get("start_time"),
            "updated_at": session_data.get("updated_at") or session_data.get("end_time"),
            "query_count": len([m for m in (session_data.get("steps", []) or session_data.get("messages", [])) if m.get("role") == "tool"]),
        },
    )

    # 生成报告
    generator = ReportGenerator(output_dir)
    return generator.generate(report_data, fmt)


def extract_dialogs_from_session(session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从会话数据中提取对话列表（用户问题和助手回答，不包含任务日志）.
    
    Args:
        session_data: 会话数据
        
    Returns:
        对话列表，每个对话包含 user_message 和 assistant_message
    """
    steps = session_data.get("steps", [])
    dialogs = []
    current_dialog = None
    
    for step in steps:
        role = step.get("role", "")
        content = step.get("content", "")
        timestamp = step.get("timestamp", "")
        
        if role == "user":
            # 保存上一个对话（如果存在）
            if current_dialog and current_dialog.get("user_message"):
                dialogs.append(current_dialog)
            # 开始新对话
            current_dialog = {
                "index": len(dialogs),
                "user_message": content,
                "assistant_message": None,
                "timestamp": timestamp
            }
        elif role == "assistant" and current_dialog:
            # 提取助手回答（处理 JSON 格式）
            assistant_content = content
            if isinstance(content, str) and content.strip().startswith("{"):
                try:
                    parsed = json.loads(content)
                    if "report_markdown" in parsed:
                        assistant_content = parsed["report_markdown"]
                    elif "answer" in parsed:
                        assistant_content = parsed["answer"]
                    elif "content" in parsed:
                        assistant_content = parsed["content"]
                except json.JSONDecodeError:
                    pass
            current_dialog["assistant_message"] = assistant_content
    
    # 添加最后一个对话
    if current_dialog and current_dialog.get("user_message"):
        dialogs.append(current_dialog)
    
    return dialogs


def generate_raw_report_from_dialogs(dialogs: List[Dict[str, Any]]) -> str:
    """将选中的对话拼接成原始报告.
    
    Args:
        dialogs: 选中的对话列表
        
    Returns:
        拼接后的原始报告文本
    """
    parts = []
    
    for i, dialog in enumerate(dialogs, 1):
        parts.append(f"## 问题 {i}")
        parts.append("")
        parts.append(f"**用户提问：**")
        parts.append(dialog.get("user_message", ""))
        parts.append("")
        
        assistant_msg = dialog.get("assistant_message", "")
        if assistant_msg:
            parts.append(f"**分析结果：**")
            parts.append(assistant_msg)
        else:
            parts.append("*（暂无回答）*")
        
        parts.append("")
        parts.append("---")
        parts.append("")
    
    return "\n".join(parts)


def polish_report_with_llm(
    raw_report: str,
    session_title: str,
    llm_client: Optional[Any] = None,
) -> str:
    """使用 LLM 润色和整理报告格式.
    
    Args:
        raw_report: 原始报告文本
        session_title: 会话标题
        llm_client: LLM 客户端（可选）
        
    Returns:
        润色后的报告内容
    """
    if not llm_client:
        # 如果没有 LLM，直接返回原始报告
        return raw_report
    
    prompt = f"""请根据以下原始数据分析报告内容，生成一份专业、结构化的数据分析报告。

会话标题: {session_title}

原始报告内容:
{raw_report[:6000]}

请按照以下要求生成报告：

# 数据分析报告

---
**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**会话标题**: {session_title}
**查询次数**: {raw_report.count('问题 ')}
---

## 一、分析概述
简要说明本次分析的背景、目的和分析范围。

## 二、关键发现
列出本次分析的主要发现和核心洞察（3-5条）。

## 三、详细分析
根据原始报告中的各个问题，整理详细的数据分析内容：
- 按问题分类整理分析结果
- 保留重要的数据表格
- 提取关键指标和趋势

## 四、建议与结论
基于分析结果，给出可执行的建议和总结。

格式要求：
1. 使用 Markdown 格式
2. 包含适当的标题层级（# ## ###）
3. 保留原始报告中的数据表格，确保格式正确
4. 语言专业、简洁
5. 不要包含 SQL 代码块
6. 不要包含执行日志或技术细节

请直接输出报告内容，不要包含任何解释性文字。"""

    try:
        response = llm_client.chat(prompt)
        # 清理响应内容
        response = _clean_report_content(response)
        return response
    except Exception as e:
        print(f"[ReportGenerator] LLM 润色失败: {e}")
        # 降级到返回原始报告
        return raw_report


def generate_report_from_selected_dialogs(
    session_data: Dict[str, Any],
    selected_indices: List[int],
    output_dir: str,
    title: Optional[str] = None,
    fmt: ReportFormat = ReportFormat.MARKDOWN,
    llm_client: Optional[Any] = None,
) -> str:
    """从选中的对话生成报告.
    
    流程：
    1. 提取会话中的所有对话
    2. 根据选中的索引筛选对话
    3. 将选中的对话拼接成原始报告
    4. 调用 LLM 润色整理格式
    5. 生成最终报告文件
    
    Args:
        session_data: 会话数据
        selected_indices: 选中的对话索引列表
        output_dir: 输出目录
        title: 报告标题（可选）
        fmt: 报告格式
        llm_client: LLM 客户端（可选）
        
    Returns:
        生成的文件路径
    """
    session_id = session_data.get("session_id", "unknown")
    session_title = session_data.get("title", "数据分析报告")
    
    print(f"[ReportGenerator] 从选中对话生成报告，选中索引: {selected_indices}")
    
    # 1. 提取所有对话
    all_dialogs = extract_dialogs_from_session(session_data)
    print(f"[ReportGenerator] 总会话数: {len(all_dialogs)}")
    
    # 2. 筛选选中的对话
    selected_dialogs = []
    for idx in selected_indices:
        if 0 <= idx < len(all_dialogs):
            selected_dialogs.append(all_dialogs[idx])
    
    if not selected_dialogs:
        print("[ReportGenerator] 没有选中的有效对话，使用全部对话")
        selected_dialogs = all_dialogs
    
    print(f"[ReportGenerator] 选中对话数: {len(selected_dialogs)}")
    
    # 3. 生成原始报告
    raw_report = generate_raw_report_from_dialogs(selected_dialogs)
    print(f"[ReportGenerator] 原始报告长度: {len(raw_report)}")
    
    # 4. 使用 LLM 润色报告
    report_content = polish_report_with_llm(raw_report, session_title, llm_client)
    print(f"[ReportGenerator] 润色后报告长度: {len(report_content)}")
    
    # 5. 生成报告标题
    report_title = title
    if not report_title:
        report_title = generate_report_filename_with_llm(session_data, llm_client)
    
    # 6. 构建报告数据
    report_data = ReportData(
        title=report_title,
        content=report_content,
        tables=[],
        session_id=session_id,
        metadata={
            "created_at": session_data.get("created_at") or session_data.get("start_time"),
            "updated_at": session_data.get("updated_at") or session_data.get("end_time"),
            "query_count": len(selected_dialogs),
            "selected_dialogs": selected_indices,
        },
    )
    
    # 7. 生成报告文件
    generator = ReportGenerator(output_dir)
    return generator.generate(report_data, fmt)
