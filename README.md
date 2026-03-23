<div align="center">

# OfferPilot

**从刷题到拿 Offer，全程 AI 驾驶。**

[![Python](https://img.shields.io/badge/Python-3.9+-3776ab?logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)]()

一个面向程序员的 AI 求职全流程工具。<br>
LeetCode 自动同步 · 间隔复习 · AI 代码优化 · 简历分析 · 模拟面试 · 跨场景记忆

</div>

---

## 核心能力

<table>
<tr>
<td width="50%">

### 刷题不再凭感觉
- 自动拉取 LeetCode CN 提交记录
- 每题 5 轮间隔复习，到期自动推送
- AI 对比官方题解，告诉你代码哪里能更优
- 15 分类薄弱点雷达，哪里不行一目了然

</td>
<td width="50%">

### 求职不再打乱仗
- 粘贴简历，AI 逐项评分 + 改写建议
- 一键生成针对性面试题（项目深挖 / 技术原理 / 系统设计）
- AI 面试官逐题追问，模拟真实面试压力
- 所有对话共享记忆，面试暴露的弱点会回流到刷题计划

</td>
</tr>
</table>

## 30 秒上手

```bash
git clone https://github.com/HuangJingwang/offerpilot.git
cd leetcode_auto && pip install -e .

leetcode           # 首次运行：登录 + 同步
leetcode --web     # 打开 Web 看板
leetcode --chat    # AI 对话（终端）
```

## Web 看板一览

`leetcode --web` 打开浏览器，7 个标签页覆盖全部场景：

| 标签页 | 做什么 |
|:-------|:-------|
| **总览** | 统计卡片 + 今日新题/复习推荐 + 完成率仪表盘 + 各轮进度 + 分类雷达 + 热力图 |
| **AI 对话** | 基于真实刷题数据的 AI 助手：推荐题目、制定计划、解答算法问题 |
| **进度表** | 100 题完整进度，搜索 + 多维筛选（难度/分类/状态） |
| **待复习** | 今日到期复习题目，按逾期天数排序 |
| **打卡记录** | 打卡时间线 + 近 30 天趋势 |
| **代码优化** | AI 分析结果：复杂度对比、优化建议、改进代码 |
| **简历优化** | LaTeX 模板下载 · AI 简历评分 · 生成面试题 · 对话式改写 |
| **模拟面试** | AI 面试官：逐题提问 → 追问 → 引导 → 点评 |

> 支持中英文切换 · 30 秒自动刷新 · 移动端自适应

## 四大差异化

### 1. AI 代码分析，不只是告诉你"慢"

每次同步时自动检测 AC 提交的 runtime/memory 百分位。低于 50%？OfferPilot 会：
1. 获取 LeetCode 官方题解
2. 调用 AI 对比你的代码 vs 最优解
3. 输出：**复杂度对比 → 具体问题 → 优化方向 → 改进后完整代码**

不是一句"建议优化"，而是直接给你能跑的代码。

### 2. 跨场景记忆，越用越懂你

刷题助手、简历优化、模拟面试三个场景共享一份记忆：

```
面试中暴露 → "对 Raft 选举细节不清楚"
    ↓ 自动回流
刷题助手 → 推荐分布式相关题目，优先补强
    ↓ 同步更新
简历优化 → 建议调整项目描述，弱化不熟悉的细节
```

对话历史过长时，AI 自动压缩为摘要，不丢上下文、不爆 token。

### 3. 间隔复习，精准到天

基于艾宾浩斯遗忘曲线，每题 5 轮复习：

| R1 | R2 (+1d) | R3 (+3d) | R4 (+7d) | R5 (+14d) |
|:--:|:--------:|:--------:|:--------:|:---------:|
| 首次做题 | 次日巩固 | 短期记忆 | 中期巩固 | 长期记忆 |

自动追踪完成日期，每天推送到期题目。不用自己记"哪天该复习什么"。

### 4. 后台守护，无感运行

```bash
leetcode --daemon 1h       # 每小时自动同步
leetcode --remind-daemon   # 每天 10:00/17:00/22:00 推送通知
```

注册一次永久生效，关终端、注销都不影响。macOS / Linux / Windows 三平台适配。

## AI 配置

在 `~/.leetcode_auto/.env` 中配置（支持 OpenAI / Claude / 兼容接口）：

```bash
AI_PROVIDER=openai           # 或 claude
AI_API_KEY=sk-xxx
AI_MODEL=gpt-4o              # 可选
AI_BASE_URL=https://...      # 可选，第三方接口地址
```

未配置 AI 时，刷题同步和看板正常使用，仅跳过 AI 功能。

## 全部命令

```
leetcode                   同步今日刷题 + AI 代码分析
leetcode --web             Web 看板（全功能）
leetcode --chat            AI 对话（终端）
leetcode --status          终端进度面板（Rich 渲染）
leetcode --heatmap         刷题热力图
leetcode --optimize        待优化题目列表
leetcode --weakness        分类薄弱点分析
leetcode --report          每周报告
leetcode --badge           SVG 进度徽章
leetcode --login           重新登录
leetcode --daemon <spec>   后台同步（30m / 1h / 23:00 / status / stop）
leetcode --remind          今日待刷/待复习
leetcode --remind-daemon   每日通知（start / status / stop）
```

## 架构

```
┌─────────────┐                    ┌─────────────────────────┐
│  LeetCode   │◄── GraphQL API ──►│       OfferPilot        │
│     CN      │  submission sync   │                         │
└─────────────┘                    │  sync ──► progress data │
                                   │  AI   ──► code analysis │
┌─────────────┐                    │         ► resume review │
│  AI Engine  │◄── analysis ──────►│         ► mock interview│
│ Claude/GPT  │◄── chat ──────────►│         ► shared memory │
└─────────────┘                    │                         │
                                   │  views ─► Web SPA      │
                                   │         ► Terminal TUI  │
                                   └─────────────────────────┘
```

## FAQ

<details>
<summary><b>Cookie 过期了怎么办？</b></summary>

运行 `leetcode --login` 重新登录。交互模式下会自动检测并弹浏览器。后台 daemon 模式不弹浏览器，需手动登录一次。
</details>

<details>
<summary><b>AI 分析需要什么配置？</b></summary>

在 `~/.leetcode_auto/.env` 中设置 `AI_PROVIDER` 和 `AI_API_KEY`。支持 OpenAI、Claude 及兼容接口（通过 `AI_BASE_URL`）。未配置时 AI 功能自动跳过。
</details>

<details>
<summary><b>对话记录会保存吗？</b></summary>

会。刷题/简历/面试三个场景各自保存历史，共享跨场景记忆。历史过长时 AI 自动压缩为摘要。
</details>

<details>
<summary><b>Web 看板需要联网吗？</b></summary>

需要加载 ECharts/marked.js CDN。刷题数据全在本地，AI 功能需联网。
</details>

<details>
<summary><b>支持哪些系统？</b></summary>

macOS / Linux / Windows。后台守护分别适配 LaunchAgent / systemd / schtasks。
</details>

## Contributing

欢迎提交 Issue 和 Pull Request。

## License

[MIT](LICENSE) &copy; 2025 OfferPilot
