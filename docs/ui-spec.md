# Chat Memory — UI Spec

页面结构、元素命名、功能说明。开发时统一用这些名称沟通。

## 全局结构

```
App
├── Nav Bar — 顶部导航
│   ├── Logo — "Chat Memory"
│   ├── Tab Switcher — Home / Conversations / Journal
│   └── Global Search — 全局搜索框（路由到 Conversations 搜索）
│
├── Home Tab
├── Conversations Tab
└── Journal Tab
```

## Home Tab

周报、highlights、artifacts、最近对话的汇总首页。

```
Home Tab
├── Weekly Insight Card — 本周复盘卡片
│   ├── Date Badge
│   ├── Title + Body (markdown)
│   ├── Theme Pills — 本周主题标签
│   └── Stats Row — conversations / topics / highlights 计数
│
├── Active Topics Section — 活跃主题列表
│   └── Topic Row — date + topic name → 点击打开 Topic Thread Modal
│
├── Highlights Section — 精彩片段
│   └── Highlight Card — quote + speaker + type pill + context
│       → 点击跳转到源对话消息
│
├── Recent Artifacts Section — 最近产出物
│   └── Artifact Row — icon + name + description + date
│       → 点击打开 Artifact Preview Modal
│
└── Recent Conversations Section — 最近对话
    └── Conversation Row — date + title + tags
        → 点击进入 Session Detail
```

## Conversations Tab

左右分栏：Session List + Session Detail。

```
Conversations Tab
├── Session List (sidebar, 340px)
│   ├── Search Bar — 对话搜索
│   ├── Calendar Panel — 日历筛选（可折叠）
│   │   ├── Month Nav — 上月/下月
│   │   ├── Day Grid — 有对话的日期带圆点
│   │   └── Clear Button
│   ├── Topic Filters — topic chip 筛选栏
│   └── Session Card List
│       └── Session Card — date + project pill + title + one_line + tags
│           → 点击进入 Session Detail
│
└── Session Detail (main area)
    ├── Session Header
    │   ├── Title — session 标题
    │   ├── Meta — 日期范围 + 消息数
    │   ├── Topic Pills — 关联主题（点击打开 Topic Thread Modal）
    │   └── Action Buttons
    │       ├── Segments Toggle — 展开/收起 Segments Panel
    │       └── More Menu — 删除等操作
    │
    ├── Summary Detail — 完整 summary markdown（What we did / Key decisions / Open threads）
    │   （有 summary 时自动展示，无则隐藏）
    │
    ├── Segments Panel (可折叠)
    │   └── Segment Card — topic + summary (markdown) + time range
    │       ├── Topic Name → 点击打开 Topic Thread Modal
    │       └── Card Body → 点击滚动到对应消息
    │
    ├── Artifacts Bar — session 内的 artifact chips
    │   └── Artifact Chip — icon + filename → 点击预览
    │
    └── Chat View — 对话消息列表
        ├── Time Divider — 消息间隔 >2min 时显示
        └── Message Bubble
            ├── Content (markdown rendered)
            ├── Tool Badges — 使用的工具标签
            └── Timestamp
```

## Journal Tab

每日反思日记的时间线。

```
Journal Tab
├── Header — "Journal" + subtitle
└── Journal Entry List (时间线)
    └── Journal Entry
        ├── Date Dot — 日期 + today badge
        │   └── Session Badges — 关联 session 数量
        │       └── Session Popover — 点击展开 session 列表
        │           └── Popover Item — title + one_line → 跳转对话
        │
        └── Timeline Blocks
            ├── Daily Reflection — 自由文本 (markdown)
            ├── What I Learned — +/- 列表
            ├── Understanding the User — 文本
            ├── Growth Notes — new/updated badges
            └── Actions — → 箭头列表
```

## Modals

| Modal | 触发方式 | 内容 |
|-------|---------|------|
| All Highlights | Home "View all" | 按日期分组的全部 highlights |
| All Artifacts | Home "View all" | 全部 artifact 列表 |
| Artifact Preview | 点击任意 artifact | markdown/code 渲染预览 |
| Topic Thread | 点击 topic pill/name | 跨 session 的 segment 时间线 |
| Delete Confirm | More Menu → Delete | 删除确认对话框 |

## 搜索范围

- 默认：session title + one_line + summary 全文 + segment topic/summary + tags + project name + topic names
- `#tag` 前缀：精确匹配 tag 名称
- Tag pill 点击：自动填入 `#tagName` 触发精确搜索
- 全局搜索框：暂时隐藏（待设计真正的全局搜索）

## 配色

| 变量 | 值 | 用途 |
|------|------|------|
| `--accent` | #3b82f6 | 交互元素（链接、选中态） |
| `--user-bubble` | #dcf8c6 | 用户消息气泡 |
| `--assistant-bubble` | #fff | 助手消息气泡 |
| `--danger` | #ef4444 | 删除等危险操作 |
| `--green` | #059669 | 正面指标（+ learned） |
| `--amber` | #d97706 | 警告/中性 |
| `--purple` | #7c3aed | 特殊标记 |

## 待做标记

- [x] Session Detail 顶部加完整 Summary 展示
- [x] 搜索扩展到完整 summary 文本 + tags + #tag 精确搜索
- [x] Tag pill 点击触发搜索
- [x] Markdown 渲染修复（journal sections + user message + segment summary）
- [x] 隐藏全局搜索框
- [ ] 可视化版 UI spec（交互式 sitemap）
- [ ] 全局搜索（跨 conversations + journal + highlights + artifacts）
