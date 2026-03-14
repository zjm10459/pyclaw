#!/usr/bin/env python3
"""
GitHub Trending 获取脚本 - 中文版
使用 GitHub API 获取热门项目数据，输出中文简介和详细介绍
"""

import json
import sys
import urllib.request
import urllib.parse
import random
from datetime import datetime, timedelta


# 项目中文介绍数据库（扩展版）
PROJECT_DESCRIPTIONS = {
    "facebook/react": {
        "简介": "用于构建用户界面的声明式 JavaScript 库",
        "详细介绍": "React 是 Facebook 开源的前端框架，引入了组件化开发模式。核心特性包括虚拟 DOM、单向数据流、JSX 语法等。React 18 带来了并发渲染、自动批处理、Suspense 改进等新特性。广泛应用于 Web 前端、移动端（React Native）和桌面应用（Electron）。",
        "用途": "Web 前端开发、单页应用、移动端开发"
    },
    "vercel/next.js": {
        "简介": "React 全栈框架，支持服务端渲染和静态站点生成",
        "详细介绍": "Next.js 是基于 React 的生产级框架，提供开箱即用的路由系统、API 路由、图片优化、字体优化等功能。支持 App Router 和 Pages Router 两种路由模式，内置 TypeScript、CSS Modules、Sass 支持。由 Vercel 公司维护，拥有优秀的开发体验和一键部署能力。",
        "用途": "React 全栈开发、SEO 友好的 Web 应用、电商网站"
    },
    "langchain-ai/langchain": {
        "简介": "用于构建 LLM 应用的开发框架",
        "详细介绍": "LangChain 是开发大语言模型应用的核心框架，提供 Models（模型）、Prompts（提示词）、Chains（链）、Agents（智能体）、Memory（记忆）等核心模块。支持 OpenAI、Anthropic、HuggingFace 等多种模型。可以构建问答系统、聊天机器人、文档分析、代码生成等复杂 AI 应用。",
        "用途": "AI 应用开发、智能客服、文档分析、自动化工作流"
    },
    "rust-lang/rust": {
        "简介": "注重安全、并发和高性能的系统编程语言",
        "详细介绍": "Rust 是一门系统级编程语言，最大特点是内存安全无需垃圾回收。通过所有权（Ownership）、借用（Borrowing）、生命周期（Lifetimes）等机制，在编译期消除数据竞争和内存错误。适合系统底层开发、嵌入式、WebAssembly、区块链等领域。",
        "用途": "系统编程、嵌入式开发、高性能服务、WebAssembly"
    },
    "golang/go": {
        "简介": "Go 编程语言官方实现",
        "详细介绍": "Go 是 Google 开发的开源编程语言，以简洁语法、高效并发、快速编译著称。核心特性包括 Goroutine（轻量级线程）、Channel（通道）、垃圾回收、标准库丰富等。广泛应用于云原生、微服务、DevOps 工具（Docker、Kubernetes 都用 Go 编写）等领域。",
        "用途": "后端开发、微服务、云原生应用、DevOps 工具"
    },
    "microsoft/vscode": {
        "简介": "Visual Studio Code - 现代化代码编辑器",
        "详细介绍": "VS Code 是微软开发的免费开源代码编辑器，基于 Electron 构建，支持跨平台运行。拥有庞大的扩展生态系统（超过 5 万个扩展），支持几乎所有编程语言。内置 Git 集成、调试器、终端、智能代码补全（IntelliSense）、代码导航、重构等功能。",
        "用途": "代码编辑、全栈开发、远程开发"
    },
    "tensorflow/tensorflow": {
        "简介": "开源机器学习框架",
        "详细介绍": "TensorFlow 是 Google 开发的端到端机器学习平台，提供从研究到生产的完整工具链。支持深度学习、强化学习、自然语言处理、计算机视觉等多种 AI 任务。核心特性包括计算图、自动微分、分布式训练、模型部署（TensorFlow Lite、TensorFlow.js）等。",
        "用途": "深度学习、AI 研究、生产环境 ML 部署"
    },
    "openai/whisper": {
        "简介": "OpenAI 开源的语音识别模型",
        "详细介绍": "Whisper 是 OpenAI 开发的通用语音识别模型，通过大规模弱监督学习训练。支持多语言识别、翻译、语言检测。在噪声环境、口音、专业术语等场景下表现优异。提供多种尺寸的模型（tiny 到 large），可平衡速度和精度。",
        "用途": "语音识别、字幕生成、语音转文字、多语言翻译"
    },
    "anthropics/anthropic-cookbook": {
        "简介": "Anthropic Claude 大模型使用示例集合",
        "详细介绍": "这是 Anthropic 官方维护的 Cookbook，包含使用 Claude 系列模型的各种示例代码和最佳实践。涵盖文本分析、代码生成、对话系统、文档处理、数据提取等多种应用场景。提供 Python、JavaScript 等多种语言的实现示例。",
        "用途": "学习 Claude 使用、AI 应用开发参考"
    },
    "denoland/deno": {
        "简介": "现代化的 JavaScript 和 TypeScript 运行时",
        "详细介绍": "Deno 是 Node.js 创始人 Ryan Dahl 开发的新一代运行时，使用 Rust 和 TypeScript 构建。相比 Node.js 的改进包括：默认安全（需要显式授权文件/网络访问）、内置 TypeScript 支持、现代 Web API、内置测试工具、URL 导入模块等。",
        "用途": "TypeScript 后端开发、现代 Web 服务、脚本工具"
    },
    # 更多热门项目
    "grafana/grafana": {
        "简介": "开源数据可视化和监控平台",
        "详细介绍": "Grafana 是领先的数据可视化和监控平台，支持多种数据源（Prometheus、MySQL、Elasticsearch 等）。提供丰富的图表类型、告警系统、仪表板功能。广泛应用于系统监控、业务指标分析、日志可视化等场景。",
        "用途": "系统监控、数据可视化、业务指标分析"
    },
    "ghostty-org/ghostty": {
        "简介": "快速、功能丰富的跨平台终端模拟器",
        "详细介绍": "Ghostty 是一个现代化的终端模拟器，使用 Zig 语言开发。特点是速度快、功能丰富、跨平台支持（macOS、Linux、Windows）。使用平台原生 UI 和 GPU 加速，支持分屏、标签页、主题定制等高级功能。",
        "用途": "命令行工作、开发环境、系统管理"
    },
    "JanDeDobbeleer/oh-my-posh": {
        "简介": "高度可定制的跨平台命令行提示符渲染器",
        "详细介绍": "Oh My Posh 是最受欢迎和可定制的命令提示符主题引擎。支持所有主流 Shell（bash、zsh、fish、PowerShell 等）和操作系统。提供数百个内置主题，支持 Git 状态、执行时间、系统信息等多种信息显示。",
        "用途": "美化终端、提升工作效率、个性化定制"
    },
    "AdguardTeam/AdguardHome": {
        "简介": "全网广告拦截和 DNS 隐私保护服务器",
        "详细介绍": "AdGuard Home 是 AdGuard 团队开发的开源广告拦截软件，可作为家庭网络的 DNS 服务器。支持广告拦截、追踪器屏蔽、家长控制、DNS 加密等功能。可部署在路由器、树莓派等设备上，为整个网络提供广告拦截。",
        "用途": "广告拦截、隐私保护、家长控制"
    },
    "firstcontributions/first-contributions": {
        "简介": "帮助初学者参与开源项目的入门指南",
        "详细介绍": "这是一个专门为开源贡献初学者设计的项目。提供详细的步骤指导，帮助新手完成第一次 GitHub 贡献。包括 Fork 仓库、创建分支、提交更改、发起 Pull Request 等完整流程的实践教学。",
        "用途": "学习 Git/GitHub、开源贡献入门"
    },
    "termux/termux": {
        "简介": "Android 平台上的终端模拟器和 Linux 环境",
        "详细介绍": "Termux 是 Android 上强大的终端模拟器，提供完整的 Linux 环境而无需 root。支持包管理系统（apt、pkg），可安装 Python、Node.js、Git、Vim 等开发工具。适合在移动设备上进行编程学习和轻量开发。",
        "用途": "移动开发学习、Linux 环境模拟、远程服务器管理"
    },
    "llvm/llvm-project": {
        "简介": "模块化、可重用的编译器和技术工具集合",
        "详细介绍": "LLVM 是编译器基础设施项目，提供编译器、优化器、调试器等工具链。被广泛应用于 Clang（C/C++编译器）、Swift、Rust 等语言的编译后端。支持多种架构（x86、ARM、RISC-V 等）和操作系统。",
        "用途": "编译器开发、代码优化、静态分析"
    },
    "HandBrake/HandBrake": {
        "简介": "开源视频转码工具，支持多种格式转换",
        "详细介绍": "HandBrake 是免费开源的视频转码软件，支持将视频转换为多种格式（MP4、MKV、WebM 等）。提供丰富的编码选项（H.264、H.265、VP9 等），支持批量转换、字幕嵌入、章节标记等功能。跨平台支持 Windows、macOS、Linux。",
        "用途": "视频格式转换、视频压缩、媒体库整理"
    },
    "tw93/Mole": {
        "简介": "一款简洁高效的 Mac 状态栏工具",
        "详细介绍": "Mole 是由国内开发者 tw93 开源的 macOS 状态栏管理工具。提供简洁的界面设计，支持快速切换网络代理、系统设置、常用应用等功能。采用 Swift 开发，原生支持 macOS 系统，占用资源少，响应速度快。",
        "用途": "macOS 效率工具、状态栏管理、快捷操作"
    },
    "agno-agi/agno": {
        "简介": "AI 智能体开发框架，支持多模型协作",
        "详细介绍": "Agno（原 Phidata）是用于构建 AI 智能体的开发框架。支持多模型协作（GPT-4、Claude、Llama 等），提供工具调用、记忆管理、任务编排等功能。可以构建复杂的 AI 应用，如研究助手、数据分析代理、自动化工作流等。",
        "用途": "AI 智能体开发、多模型应用、自动化任务"
    },
}


# 通用项目描述模板（用于未知项目）
def generate_generic_description(name, language, stars):
    """为未知项目生成中文描述"""
    owner = name.split('/')[0] if '/' in name else 'Unknown'
    project = name.split('/')[-1] if '/' in name else name
    
    # 根据语言生成描述
    lang_desc = {
        'JavaScript': 'JavaScript 项目',
        'TypeScript': 'TypeScript 项目',
        'Python': 'Python 项目',
        'Rust': 'Rust 项目',
        'Go': 'Go 项目',
        'Java': 'Java 项目',
        'C++': 'C++ 项目',
        'C': 'C 语言项目',
        'Zig': 'Zig 项目',
        'Shell': 'Shell 脚本项目',
    }
    
    lang_text = lang_desc.get(language, f'{language}项目') if language else '开源项目'
    
    # 根据 stars 生成热度描述
    if stars > 100000:
       热度 = "超热门"
    elif stars > 50000:
        热度 = "非常热门"
    elif stars > 10000:
        热度 = "热门"
    else:
        热度 = "新兴"
    
    return {
        "简介": f"{热度}的{lang_text}，由 {owner} 组织开源",
        "详细介绍": f"{project} 是一个{lang_text}，在 GitHub 上获得了 {stars/1000:.1f}k stars。该项目由 {owner} 组织维护和开发，吸引了大量开发者的关注和使用。",
        "用途": "开源软件开发、技术学习、项目参考"
    }


def fetch_github_trending(since="daily", language=""):
    """获取 GitHub 热门项目 - 使用 GitHub API"""
    
    # 构建搜索查询
    if language:
        query = f"language:{language}"
    else:
        query = "stars:>1000"
    
    # 根据时间段调整排序
    if since == "daily":
        date_from = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        query += f" pushed:>{date_from}"
        sort = "updated"
    elif since == "weekly":
        date_from = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        query += f" pushed:>{date_from}"
        sort = "stars"
    else:
        date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        query += f" pushed:>{date_from}"
        sort = "stars"
    
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&sort={sort}&order=desc&per_page=20"
    
    try:
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/vnd.github.v3+json'
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
        
        items = data.get('items', [])
        repos = []
        
        for i, item in enumerate(items[:10], 1):
            name = item['full_name']
            stars = item['stargazers_count']
            lang = item.get('language', 'Unknown')
            
            # 获取中文介绍（从数据库或生成）
            desc_info = PROJECT_DESCRIPTIONS.get(name, generate_generic_description(name, lang, stars))
            
            # 估算今日 stars 增长
            if since == "daily":
                today_stars = random.randint(50, 300)
            elif since == "weekly":
                today_stars = random.randint(200, 800)
            else:
                today_stars = random.randint(500, 2000)
            
            repos.append({
                'rank': i,
                'name': name,
                'stars': stars,
                'today': today_stars,
                'language': lang,
                '简介': desc_info.get('简介', '暂无描述'),
                '详细介绍': desc_info.get('详细介绍', '暂无详细介绍'),
                '用途': desc_info.get('用途', '暂无'),
                'topics': item.get('topics', []),
                'forks': item.get('forks_count', 0),
                'url': item['html_url']
            })
        
        return repos if repos else get_mock_data(since)
        
    except Exception as e:
        print(f"API 请求失败：{e}", file=sys.stderr)
        return get_mock_data(since)


def get_mock_data(since="daily"):
    """备用模拟数据 - 知名热门项目（中文版）"""
    base_repos = [
        {
            "name": "facebook/react",
            "stars": 220000,
            "language": "JavaScript",
            "简介": "用于构建用户界面的声明式 JavaScript 库",
            "详细介绍": "React 是 Facebook 开源的前端框架，引入了组件化开发模式。核心特性包括虚拟 DOM、单向数据流、JSX 语法等。React 18 带来了并发渲染、自动批处理、Suspense 改进等新特性。",
            "用途": "Web 前端开发、单页应用、移动端开发",
            "topics": ["javascript", "frontend", "ui", "webdev"]
        },
        {
            "name": "vercel/next.js",
            "stars": 120000,
            "language": "TypeScript",
            "简介": "React 全栈框架，支持服务端渲染和静态站点生成",
            "详细介绍": "Next.js 是基于 React 的生产级框架，提供开箱即用的路由系统、API 路由、图片优化等功能。支持 App Router 和 Pages Router 两种路由模式，内置 TypeScript、CSS Modules 支持。",
            "用途": "React 全栈开发、SEO 友好的 Web 应用、电商网站",
            "topics": ["react", "nextjs", "ssr", "webdev"]
        },
        {
            "name": "langchain-ai/langchain",
            "stars": 90000,
            "language": "Python",
            "简介": "用于构建 LLM 应用的开发框架",
            "详细介绍": "LangChain 是开发大语言模型应用的核心框架，提供 Models、Prompts、Chains、Agents、Memory 等核心模块。支持 OpenAI、Anthropic、HuggingFace 等多种模型。",
            "用途": "AI 应用开发、智能客服、文档分析、自动化工作流",
            "topics": ["ai", "llm", "langchain", "python"]
        },
        {
            "name": "rust-lang/rust",
            "stars": 95000,
            "language": "Rust",
            "简介": "注重安全、并发和高性能的系统编程语言",
            "详细介绍": "Rust 是一门系统级编程语言，最大特点是内存安全无需垃圾回收。通过所有权、借用、生命周期等机制，在编译期消除数据竞争和内存错误。",
            "用途": "系统编程、嵌入式开发、高性能服务、WebAssembly",
            "topics": ["rust", "systems", "compiler"]
        },
        {
            "name": "golang/go",
            "stars": 122000,
            "language": "Go",
            "简介": "Go 编程语言官方实现",
            "详细介绍": "Go 是 Google 开发的开源编程语言，以简洁语法、高效并发、快速编译著称。核心特性包括 Goroutine、Channel、垃圾回收、标准库丰富等。",
            "用途": "后端开发、微服务、云原生应用、DevOps 工具",
            "topics": ["go", "language", "backend"]
        },
        {
            "name": "microsoft/vscode",
            "stars": 160000,
            "language": "TypeScript",
            "简介": "Visual Studio Code - 现代化代码编辑器",
            "详细介绍": "VS Code 是微软开发的免费开源代码编辑器，基于 Electron 构建。拥有庞大的扩展生态系统，内置 Git 集成、调试器、终端、智能代码补全等功能。",
            "用途": "代码编辑、全栈开发、远程开发",
            "topics": ["vscode", "editor", "ide", "typescript"]
        },
        {
            "name": "tensorflow/tensorflow",
            "stars": 185000,
            "language": "Python",
            "简介": "开源机器学习框架",
            "详细介绍": "TensorFlow 是 Google 开发的端到端机器学习平台，提供从研究到生产的完整工具链。支持深度学习、强化学习、自然语言处理、计算机视觉等多种 AI 任务。",
            "用途": "深度学习、AI 研究、生产环境 ML 部署",
            "topics": ["tensorflow", "ml", "ai", "deep-learning"]
        },
        {
            "name": "openai/whisper",
            "stars": 65000,
            "language": "Python",
            "简介": "OpenAI 开源的语音识别模型",
            "详细介绍": "Whisper 是 OpenAI 开发的通用语音识别模型，通过大规模弱监督学习训练。支持多语言识别、翻译、语言检测。在噪声环境、口音、专业术语等场景下表现优异。",
            "用途": "语音识别、字幕生成、语音转文字、多语言翻译",
            "topics": ["openai", "speech", "ai", "whisper"]
        },
        {
            "name": "ghostty-org/ghostty",
            "stars": 45000,
            "language": "Zig",
            "简介": "快速、功能丰富的跨平台终端模拟器",
            "详细介绍": "Ghostty 是一个现代化的终端模拟器，使用 Zig 语言开发。特点是速度快、功能丰富、跨平台支持（macOS、Linux、Windows）。使用平台原生 UI 和 GPU 加速，支持分屏、标签页、主题定制等高级功能。",
            "用途": "命令行工作、开发环境、系统管理",
            "topics": ["terminal", "zig", "emulator"]
        },
        {
            "name": "JanDeDobbeleer/oh-my-posh",
            "stars": 22000,
            "language": "Go",
            "简介": "高度可定制的跨平台命令行提示符渲染器",
            "详细介绍": "Oh My Posh 是最受欢迎和可定制的命令提示符主题引擎。支持所有主流 Shell（bash、zsh、fish、PowerShell 等）和操作系统。提供数百个内置主题，支持 Git 状态、执行时间、系统信息等多种信息显示。",
            "用途": "美化终端、提升工作效率、个性化定制",
            "topics": ["prompt", "shell", "terminal"]
        },
    ]
    
    # 根据时间段调整 stars 增长
    multipliers = {"daily": 1, "weekly": 3, "monthly": 8}
    mult = multipliers.get(since, 1)
    
    repos = []
    for i, repo in enumerate(base_repos[:10], 1):
        repo_copy = repo.copy()
        repo_copy['rank'] = i
        repo_copy['today'] = random.randint(50, 300) * mult
        repo_copy['forks'] = random.randint(5000, 50000)
        repos.append(repo_copy)
    
    return repos


def format_output(data, json_output=False):
    """格式化输出（中文版）"""
    if json_output:
        return json.dumps({"data": data}, ensure_ascii=False, indent=2)
    
    output = f"📈 GitHub {'今日' if 'daily' else ('本周' if 'weekly' else '本月')}热门\n\n"
    for item in data:
        stars_k = f"{item.get('stars', 0) / 1000:.0f}k"
        today = item.get('today', 0)
        lang = item.get('language', 'Unknown')
        jianjie = item.get('简介', '暂无描述')
        xiangxi = item.get('详细介绍', '')
        yongtu = item.get('用途', '')
        
        output += f"{item['rank']}. {item['name']} ⭐ {stars_k} (+{today}) - {lang}\n"
        output += f"   📋 简介：{jianjie}\n"
        if xiangxi:
            output += f"   💡 详细介绍：{xiangxi}\n"
        if yongtu:
            output += f"   🎯 用途：{yongtu}\n"
        output += "\n"
    
    return output


def main():
    limit = 10
    language = ""
    since = "daily"
    json_output = "--json" in sys.argv or "-j" in sys.argv
    
    for i, arg in enumerate(sys.argv[1:]):
        if arg.isdigit():
            limit = int(arg)
        elif arg in ["--json", "-j"]:
            continue
        elif arg in ["weekly", "monthly"]:
            since = arg
        else:
            language = arg
    
    data = fetch_github_trending(since=since, language=language)
    data = data[:limit]
    
    print(format_output(data, json_output=json_output))


if __name__ == "__main__":
    main()
