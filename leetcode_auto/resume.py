"""简历分析与优化：LaTeX 模板、AI 分析、对话式改进。"""

import json
from pathlib import Path
from typing import Optional

from .config import DATA_DIR, get_ai_config
from .ai_analyzer import call_ai_messages

# ---------------------------------------------------------------------------
# 数据文件
# ---------------------------------------------------------------------------

RESUME_FILE = DATA_DIR / "resume_content.txt"
RESUME_ANALYSIS_FILE = DATA_DIR / "resume_analysis.json"
RESUME_CHAT_FILE = DATA_DIR / "resume_chat_history.json"

# ---------------------------------------------------------------------------
# LaTeX 简历模板
# ---------------------------------------------------------------------------

LATEX_TEMPLATE = r"""\documentclass[11pt,a4paper]{article}

% ==================== 宏包 ====================
\usepackage[margin=1.5cm]{geometry}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{hyperref}
\usepackage{xcolor}
\usepackage{fontspec}
\usepackage{tabularx}

% ==================== 样式 ====================
\pagestyle{empty}
\setlength{\parindent}{0pt}
\definecolor{accent}{HTML}{2563EB}
\hypersetup{colorlinks=true,urlcolor=accent}

\titleformat{\section}{\large\bfseries\color{accent}}{}{0em}{}[\titlerule]
\titlespacing{\section}{0pt}{12pt}{6pt}

\newcommand{\entry}[4]{%
  \textbf{#1} \hfill \textit{#2} \\
  \textit{#3} \hfill #4 \vspace{4pt}
}

% ==================== 正文 ====================
\begin{document}

% ---------- 个人信息 ----------
\begin{center}
  {\LARGE\bfseries 你的名字} \\[6pt]
  \href{mailto:your@email.com}{your@email.com} \quad
  \href{tel:+8613800138000}{138-0013-8000} \quad
  \href{https://github.com/yourname}{GitHub} \quad
  \href{https://linkedin.com/in/yourname}{LinkedIn}
\end{center}

% ---------- 教育背景 ----------
\section{Education}

\entry{XX 大学}{硕士 · 计算机科学与技术}{GPA: 3.8/4.0}{2022 -- 2025}
\begin{itemize}[nosep,leftmargin=*]
  \item 核心课程：算法设计与分析、分布式系统、机器学习、数据库系统
  \item 奖学金：一等学业奖学金（前 5\%）
\end{itemize}

\vspace{4pt}
\entry{XX 大学}{学士 · 软件工程}{GPA: 3.6/4.0}{2018 -- 2022}

% ---------- 工作经历 ----------
\section{Work Experience}

\entry{XX 科技有限公司}{后端开发工程师（实习）}{技术栈：Go, MySQL, Redis, Kafka}{2024.06 -- 2024.09}
\begin{itemize}[nosep,leftmargin=*]
  \item 负责用户中心微服务重构，将单体接口拆分为 5 个独立服务，QPS 提升 40\%
  \item 设计并实现基于 Redis 的分布式限流方案，支撑日均 500 万次 API 调用
  \item 优化慢查询 SQL 12 条，P99 延迟从 800ms 降至 120ms
\end{itemize}

% ---------- 项目经历 ----------
\section{Projects}

\entry{分布式键值存储引擎}{个人项目}{Go, Raft, LSM-Tree}{2024.03 -- 2024.05}
\begin{itemize}[nosep,leftmargin=*]
  \item 基于 Raft 共识算法实现多节点数据复制，支持自动选主和日志压缩
  \item 存储层采用 LSM-Tree 结构，写入吞吐量达 10 万 ops/s
  \item 编写完整的单元测试和混沌测试，代码覆盖率 85\%
\end{itemize}

\vspace{4pt}
\entry{LeetForge — LeetCode 刷题锻造台}{开源项目}{Python, ECharts, REST API}{2025.01 -- 至今}
\begin{itemize}[nosep,leftmargin=*]
  \item 自动同步 LeetCode 刷题记录，基于间隔重复算法智能推送复习计划
  \item 集成 AI 代码分析，自动对比官方题解给出优化建议
  \item 交互式 Web 看板，6 标签页覆盖进度追踪、数据可视化、AI 对话
\end{itemize}

% ---------- 技能 ----------
\section{Skills}

\begin{tabularx}{\textwidth}{@{}lX@{}}
  \textbf{Languages} & Go, Python, Java, C++, SQL, JavaScript/TypeScript \\
  \textbf{Frameworks} & Gin, Spring Boot, React, gRPC, Protobuf \\
  \textbf{Infrastructure} & MySQL, Redis, Kafka, Docker, Kubernetes, Linux \\
  \textbf{Tools} & Git, CI/CD, Prometheus, Grafana, Nginx \\
  \textbf{Algorithms} & LeetCode Hot100 × 5 轮（LeetForge 记录），ACM 省赛银牌 \\
\end{tabularx}

\end{document}
"""

# ---------------------------------------------------------------------------
# 简历存取
# ---------------------------------------------------------------------------


def save_resume(content: str):
    """保存用户简历内容。"""
    RESUME_FILE.write_text(content, encoding="utf-8")


def load_resume() -> str:
    """加载用户简历内容。"""
    if RESUME_FILE.exists():
        return RESUME_FILE.read_text(encoding="utf-8")
    return ""


def save_analysis(analysis: dict):
    """保存分析结果。"""
    RESUME_ANALYSIS_FILE.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2), encoding="utf-8")


def load_analysis() -> dict:
    """加载分析结果。"""
    if RESUME_ANALYSIS_FILE.exists():
        try:
            return json.loads(RESUME_ANALYSIS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            pass
    return {}


# ---------------------------------------------------------------------------
# 简历对话历史
# ---------------------------------------------------------------------------

_MAX_RESUME_HISTORY = 30


def load_resume_chat() -> list:
    if not RESUME_CHAT_FILE.exists():
        return []
    try:
        data = json.loads(RESUME_CHAT_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_resume_chat(history: list):
    trimmed = history[-_MAX_RESUME_HISTORY * 2:]
    RESUME_CHAT_FILE.write_text(
        json.dumps(trimmed, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_resume_chat():
    if RESUME_CHAT_FILE.exists():
        RESUME_CHAT_FILE.unlink()


# ---------------------------------------------------------------------------
# AI 分析
# ---------------------------------------------------------------------------

_ANALYSIS_SYSTEM = """你是一位资深技术招聘专家和简历顾问，擅长帮助程序员优化简历。

请从以下维度分析这份简历，给出具体、可操作的建议：

### 整体评分（满分 100）
给出一个总分和简短评语。

### 内容分析
1. **个人信息**：联系方式是否完整、专业
2. **教育背景**：是否突出了相关课程和成绩
3. **工作/实习经历**：是否用 STAR 法则描述，是否量化了成果
4. **项目经历**：是否体现技术深度和解决问题能力
5. **技能清单**：是否与目标岗位匹配，排列是否合理

### 格式与排版
- 长度是否合适（建议 1 页）
- 要点是否精炼（每条 1-2 行）
- 是否有拼写/语法错误

### 亮点
列出 2-3 个简历中做得好的地方。

### 改进建议
按优先级列出 3-5 条具体的改进建议，每条说明：
- 当前问题
- 修改方向
- 修改示例（如适用）

请用中文回答，简洁专业。"""

_CHAT_SYSTEM = """你是一位资深技术招聘专家和简历顾问。用户正在优化他们的简历，请帮助他们改进。

用户当前的简历内容：
---
{resume}
---

{analysis_context}

请根据用户的问题给出具体、可操作的建议。如果用户要求修改某部分内容，请直接给出修改后的文字。用中文回答。"""


def analyze_resume(content: str) -> Optional[str]:
    """AI 分析简历，返回分析文本。"""
    ai_config = get_ai_config()
    if not ai_config["enabled"]:
        return None

    messages = [{"role": "user", "content": f"请分析以下简历：\n\n{content}"}]
    return call_ai_messages(messages, ai_config, system=_ANALYSIS_SYSTEM)


def chat_resume(user_message: str, history: list,
                resume_content: str, analysis_text: str = "") -> Optional[str]:
    """简历优化对话。"""
    ai_config = get_ai_config()
    if not ai_config["enabled"]:
        return None

    analysis_ctx = ""
    if analysis_text:
        analysis_ctx = f"之前的 AI 分析结果：\n{analysis_text[:2000]}"

    system = _CHAT_SYSTEM.format(
        resume=resume_content[:4000],
        analysis_context=analysis_ctx,
    )

    messages = list(history)
    messages.append({"role": "user", "content": user_message})
    return call_ai_messages(messages, ai_config, system=system)
