# ✅ 技能热插拔功能

## 📊 功能说明

PyClaw 技能系统现在支持**热插拔**，无需重启即可：
- ✅ 动态添加技能
- ✅ 动态移除技能
- ✅ 动态更新技能
- ✅ 自动监控技能目录变化

---

## 🔧 实现方式

### 1. 手动热插拔

**添加技能：**
```python
from skills.skill_loader import SkillLoader
from pathlib import Path

loader = SkillLoader()

# 添加新技能
skill_path = Path("/path/to/new-skill")
if loader.add_skill(skill_path):
    print("✓ 技能已添加")
```

**移除技能：**
```python
# 移除技能
if loader.remove_skill("skill-name"):
    print("✓ 技能已移除")
```

**更新技能：**
```python
# 重新加载技能
if loader.reload_skill("skill-name"):
    print("✓ 技能已更新")
```

**重新加载所有技能：**
```python
# 完全重新加载
loader.reload()
```

---

### 2. 自动监控（推荐）

**安装 watchdog：**
```bash
pip install watchdog
```

**启动监控：**
```python
from skills.skill_loader import SkillLoader, SkillWatcher

loader = SkillLoader()

# 创建监控器
def on_skill_change(action, skill_name):
    print(f"技能变化：{action} - {skill_name}")

watcher = SkillWatcher(loader, callback=on_skill_change)
watcher.start()

# 保持运行
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    watcher.stop()
```

**使用上下文管理器：**
```python
with SkillWatcher(loader, callback=on_skill_change):
    # 监控期间
    while True:
        time.sleep(1)
```

---

## 📝 使用场景

### 场景 1：开发调试

```bash
# 1. 启动 PyClaw（带监控）
python3 main.py

# 2. 修改技能代码
vim skills/my-skill/SKILL.md

# 3. 自动热更新 ✅
# 检测到修改，自动重新加载
```

### 场景 2：动态安装技能

```bash
# 1. 下载技能
cd skills-installed
git clone https://github.com/xxx/new-skill.git

# 2. 自动加载 ✅
# 监控器检测到新技能，自动加载
```

### 场景 3：移除技能

```bash
# 1. 删除技能目录
rm -rf skills-installed/old-skill

# 2. 自动卸载 ✅
# 监控器检测到删除，自动移除
```

---

## 🔍 监控事件

### 事件类型

| 事件 | 触发条件 | 操作 |
|------|---------|------|
| **on_created** | 创建技能目录 | 自动添加技能 |
| **on_modified** | 修改 SKILL.md | 自动重新加载 |
| **on_deleted** | 删除技能目录 | 自动移除技能 |

### 回调函数

```python
def on_skill_change(action, skill_name):
    """
    技能变化回调
    
    参数:
        action: "add" | "reload" | "remove"
        skill_name: 技能名称
    """
    if action == "add":
        print(f"✓ 新技能：{skill_name}")
    elif action == "reload":
        print(f"🔄 技能更新：{skill_name}")
    elif action == "remove":
        print(f"❌ 技能移除：{skill_name}")
```

---

## 📊 集成到 PyClaw

### 在 main.py 中启动监控

```python
# main.py
from skills.skill_loader import SkillLoader, SkillWatcher

# 初始化技能加载器
self.skill_loader = SkillLoader(workspace=workspace)

# 启动技能监控（如果安装了 watchdog）
if self.config.get("skills.hot_reload", True):
    def on_change(action, name):
        logger.info(f"技能变化：{action} - {name}")
    
    self.skill_watcher = SkillWatcher(self.skill_loader, callback=on_change)
    self.skill_watcher.start()
```

### 配置选项

**config.json：**
```json
{
  "skills": {
    "hot_reload": true,        // 启用热插拔
    "watch_interval": 1        // 监控间隔（秒）
  }
}
```

---

## ⚙️ API 参考

### SkillLoader

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `reload()` | 重新加载所有技能 | None |
| `reload_skill(name)` | 重新加载单个技能 | bool |
| `add_skill(path)` | 添加技能 | bool |
| `remove_skill(name)` | 移除技能 | bool |

### SkillWatcher

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `start()` | 启动监控 | bool |
| `stop()` | 停止监控 | None |
| `__enter__()` | 上下文管理器入口 | self |
| `__exit__()` | 上下文管理器出口 | None |

---

## 📦 依赖

### 必需依赖

- ✅ Python 3.7+
- ✅ pathlib
- ✅ watchdog（可选，用于自动监控）

### 安装 watchdog

```bash
pip install watchdog
```

**没有 watchdog 会怎样？**
- ✅ 手动热插拔仍可用
- ❌ 自动监控不可用

---

## 🎯 最佳实践

### 1. 开发环境

```python
# 启用自动监控
watcher = SkillWatcher(loader)
watcher.start()
```

### 2. 生产环境

```python
# 禁用自动监控，使用手动 reload
loader.reload()  # 在部署时调用
```

### 3. 测试

```python
# 测试热插拔
def test_hotplug():
    loader = SkillLoader()
    
    # 添加
    assert loader.add_skill(test_path)
    
    # 更新
    assert loader.reload_skill("test-skill")
    
    # 移除
    assert loader.remove_skill("test-skill")
```

---

## ⚠️ 注意事项

### 1. 文件锁

**问题：** 技能文件被占用时无法更新

**解决：**
```python
# 确保文件未被占用
import time
time.sleep(0.5)  # 等待文件释放
loader.reload_skill("skill-name")
```

### 2. 并发加载

**问题：** 多个请求同时触发重载

**解决：**
```python
# 使用锁
import threading
reload_lock = threading.Lock()

with reload_lock:
    loader.reload_skill("skill-name")
```

### 3. 错误处理

```python
try:
    loader.reload_skill("skill-name")
except Exception as e:
    logger.error(f"热更新失败：{e}")
    # 回滚到旧版本
```

---

## 📚 示例代码

### 完整示例

```python
#!/usr/bin/env python3
"""技能热插拔示例"""

import time
from pathlib import Path
from skills.skill_loader import SkillLoader, SkillWatcher

def main():
    # 初始化加载器
    loader = SkillLoader(workspace=".")
    print(f"初始技能数：{len(loader.skills)}")
    
    # 定义回调
    def on_change(action, name):
        print(f"[{action.upper()}] {name}")
        print(f"当前技能数：{len(loader.skills)}")
    
    # 启动监控
    with SkillWatcher(loader, callback=on_change) as watcher:
        print("技能监控已启动，按 Ctrl+C 退出...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n监控已停止")

if __name__ == "__main__":
    main()
```

---

## 🔗 相关文档

- `skills/skill_loader.py` - 技能加载器实现
- `docs/MEMORY_TOOL_SETUP.md` - 技能配置
- `docs/MULTI_AGENT_ARCHITECTURE.md` - 多 Agent 系统

---

**实现完成！** 🎉

现在 PyClaw 技能系统支持：
- ✅ 手动热插拔（add/remove/reload）
- ✅ 自动监控（需要 watchdog）
- ✅ 回调通知
- ✅ 上下文管理器支持

安装 watchdog 后自动启用热插拔功能！🐾
