# Skills - 技能代码模块

## 📁 目录说明

本目录 (`skills/`) 用于存放**技能代码模块**，即技能的实现代码。

**安装的技能**存放在上级目录的 `skills-installed/` 文件夹中。

---

## 📂 目录结构

```
workspace/
├── skills/                 # 本目录：技能代码模块
│   └── README.md          # 本文件
│
└── skills-installed/       # 安装的技能
    ├── context7/
    ├── email-sender/
    ├── github/
    ├── github-trending-cn/
    ├── multi-search-engine/
    └── tavily-search/
```

---

## 🔧 用途

### `skills/` - 技能代码模块

存放：
- 技能的核心实现代码
- 工具函数
- 辅助脚本

**示例：**
```
skills/
└── my-custom-skill/
    ├── SKILL.md
    ├── tools.py
    └── utils.py
```

---

### `skills-installed/` - 安装的技能

存放：
- 通过 ClawHub 安装的技能
- 手动下载的第三方技能
- 预配置的完整技能包

**示例：**
```
skills-installed/
├── email-sender/
│   ├── SKILL.md
│   ├── scripts/
│   └── config.json
├── tavily-search/
│   └── SKILL.md
└── github/
    └── SKILL.md
```

---

## 🎯 加载优先级

技能加载器按以下优先级加载技能：

1. **`workspace/skills/`** - 工作区技能（最高优先级）
2. **`workspace/skills-installed/`** - 安装的技能
3. **`~/.pyclaw/skills-installed/`** - 全局管理技能
4. **`~/.pyclaw/bundled-skills/`** - 捆绑技能（最低优先级）

**高优先级技能会覆盖低优先级技能**（如果同名）。

---

## 📝 使用方式

### 添加自定义技能

1. 在 `skills/` 目录创建技能文件夹
2. 添加 `SKILL.md` 和技能代码
3. 重启 PyClaw 自动加载

### 安装第三方技能

1. 使用 ClawHub 安装
2. 或手动复制到 `skills-installed/`
3. 重启 PyClaw 自动加载

---

## ⚠️ 注意事项

1. **不要混用** - 代码模块和安装的技能分开存放
2. **命名规范** - 使用小写字母和连字符（如 `my-skill`）
3. **版本管理** - 自定义技能建议用 Git 管理
4. **依赖管理** - 每个技能的依赖独立管理

---

## 🔗 相关文档

- [AgentSkills 规范](https://agentskills.io)
- [ClawHub](https://clawhub.com) - 技能市场
- [PyClaw 技能系统](../docs/MEMORY_TOOL_SETUP.md)

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已重组
