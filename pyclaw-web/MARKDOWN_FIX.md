# ✅ marked.js CDN 路径修复

## 🐛 问题

**原路径：**
```html
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
```

**问题：** 该路径可能无法访问或返回 404。

---

## ✅ 修复方案

**使用 cdnjs CDN：**
```html
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.0/marked.min.js"></script>
```

**优势：**
- ✅ cdnjs 更稳定
- ✅ 指定版本号（12.0.0）
- ✅ 全球 CDN 加速

---

## 🔧 修改的文件

**`pyclaw-web/templates/index.html`**

**修改位置：** 第 8 行

**修改内容：**
```diff
- <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
+ <script src="https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.0/marked.min.js"></script>
```

---

## ✅ 验证方法

### 1. 检查页面加载

打开 PyClaw Web 页面，按 F12 打开开发者工具：

**Console 中应该看到：**
```
✅ 没有 marked.js 相关的 404 错误
```

### 2. 测试 Markdown 渲染

发送一条包含 Markdown 的消息：

```markdown
## 测试

- 列表项 1
- 列表项 2

```python
print("Hello")
```
```

**预期效果：**
- ✅ 标题正确渲染
- ✅ 列表正确显示
- ✅ 代码块有样式

### 3. 检查 marked 对象

在 Console 中输入：
```javascript
typeof marked
// 应该返回 "function"

marked.parse("# Hello")
// 应该返回 "<h1>Hello</h1>"
```

---

## 📚 其他可用的 CDN

如果 cdnjs 也访问不了，可以尝试以下备选：

### 1. unpkg
```html
<script src="https://unpkg.com/marked/marked.min.js"></script>
```

### 2. jsDelivr（新版）
```html
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.0/marked.min.js"></script>
```

### 3. 本地部署（推荐生产环境）

下载 marked.js 到本地：
```bash
cd pyclaw-web/static/js
wget https://cdnjs.cloudflare.com/ajax/libs/marked/12.0.0/marked.min.js
```

修改模板：
```html
<script src="/static/js/marked.min.js"></script>
```

---

## ⚠️ 注意事项

1. **版本号** - 建议使用固定版本号（12.0.0），避免 API 变更
2. **网络连接** - 需要能访问 cdnjs.cloudflare.com
3. **HTTPS** - 使用 HTTPS 协议，避免混合内容警告
4. **本地测试** - 如果本地开发，确保能访问外网

---

## 🔗 参考资源

- [marked.js 官方文档](https://marked.js.org/)
- [cdnjs marked 页面](https://cdnjs.com/libraries/marked)
- [npm marked 包](https://www.npmjs.com/package/marked)

---

**修复完成！** 🎉

现在页面应该能正常加载 marked.js 并渲染 Markdown 了！

---

**最后更新：** 2026-03-14  
**状态：** ✅ 已修复
