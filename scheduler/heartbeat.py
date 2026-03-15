#!/usr/bin/env python3
"""
Heartbeat 定时任务系统
=====================

参考 OpenClaw 的 Heartbeat 设计，实现定时任务调度。

功能：
- 定时触发任务（类似 cron）
- HEARTBEAT.md 配置文件
- 任务状态追踪
- 支持多种任务类型（邮件检查、日历提醒、天气检查等）

架构：
    HEARTBEAT.md → 解析任务配置 → 调度器 → 执行任务 → 记录状态
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import re

logger = logging.getLogger("pyclaw.scheduler")


# ============================================================================
# 配置和数据模型
# ============================================================================

@dataclass
class HeartbeatTask:
    """
    Heartbeat 任务定义
    
    属性:
        name: 任务名称
        interval_minutes: 执行间隔（分钟）
        last_run: 上次执行时间
        next_run: 下次执行时间
        enabled: 是否启用
        handler: 处理函数
    """
    name: str
    interval_minutes: int = 30  # 默认 30 分钟
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    enabled: bool = True
    handler: Optional[Callable] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "interval_minutes": self.interval_minutes,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HeartbeatTask':
        """从字典创建"""
        return cls(
            name=data.get("name", "unknown"),
            interval_minutes=data.get("interval_minutes", 30),
            last_run=datetime.fromisoformat(data["last_run"]) if data.get("last_run") else None,
            next_run=datetime.fromisoformat(data["next_run"]) if data.get("next_run") else None,
            enabled=data.get("enabled", True),
        )


class HeartbeatScheduler:
    """
    Heartbeat 调度器
    
    功能：
    - 解析 HEARTBEAT.md 配置文件
    - 管理定时任务
    - 执行任务并记录状态
    - 支持任务注册
    
    使用方式：
        scheduler = HeartbeatScheduler(workspace_path="~/.pyclaw/workspace")
        scheduler.register_task("email", check_email, interval_minutes=30)
        scheduler.register_task("calendar", check_calendar, interval_minutes=60)
        await scheduler.start()
    """
    
    def __init__(
        self,
        workspace_path: Optional[str] = None,
        state_path: Optional[str] = None,
    ):
        """
        初始化调度器
        
        参数:
            workspace_path: 工作区路径（默认 ~/.pyclaw/workspace）
            state_path: 状态文件路径（默认 ~/.pyclaw/scheduler/heartbeat-state.json）
        """
        self.workspace_path = Path.cwd() / "workspace"
        self.state_path = Path(self.workspace_path / "scheduler" / "heartbeat-state.json")
        
        # 确保状态目录存在
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 任务注册表
        self.tasks: Dict[str, HeartbeatTask] = {}
        
        # 运行状态
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # 加载状态
        self._load_state()
        
        logger.info(f"Heartbeat 调度器初始化：{self.workspace_path}")
    
    def register_task(
        self,
        name: str,
        handler: Callable,
        interval_minutes: int = 30,
        enabled: bool = True,
    ):
        """
        注册定时任务
        
        参数:
            name: 任务名称
            handler: 处理函数（异步函数）
            interval_minutes: 执行间隔（分钟）
            enabled: 是否启用
        """
        task = HeartbeatTask(
            name=name,
            interval_minutes=interval_minutes,
            enabled=enabled,
            handler=handler,
        )
        
        # 计算下次执行时间
        if task.last_run:
            task.next_run = task.last_run + timedelta(minutes=interval_minutes)
        else:
            task.next_run = datetime.now()
        
        self.tasks[name] = task
        logger.info(f"注册任务：{name} (间隔：{interval_minutes} 分钟)")
    
    def _load_state(self):
        """加载状态文件"""
        if self.state_path.exists():
            try:
                data = json.loads(self.state_path.read_text(encoding='utf-8'))
                
                for task_name, task_data in data.get("tasks", {}).items():
                    task = HeartbeatTask.from_dict(task_data)
                    self.tasks[task_name] = task
                
                logger.info(f"加载状态：{len(self.tasks)} 个任务")
            
            except Exception as e:
                logger.warning(f"加载状态失败：{e}")
        else:
            logger.info("状态文件不存在，使用默认状态")
    
    def _save_state(self):
        """保存状态文件"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "tasks": {
                    name: task.to_dict()
                    for name, task in self.tasks.items()
                },
            }
            
            self.state_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            
            logger.debug("状态已保存")
        
        except Exception as e:
            logger.error(f"保存状态失败：{e}")
    
    def parse_heartbeat_md(self) -> List[str]:
        """
        解析 HEARTBEAT.md 文件
        
        返回:
            任务列表（每行一个任务）
        """
        heartbeat_file = self.workspace_path / "HEARTBEAT.md"
        
        if not heartbeat_file.exists():
            logger.debug("HEARTBEAT.md 不存在")
            return []
        
        try:
            content = heartbeat_file.read_text(encoding='utf-8')
            
            # 提取任务列表（忽略注释和空行）
            tasks = []
            for line in content.split('\n'):
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue
                
                # 提取任务名称
                tasks.append(line)
            
            logger.debug(f"解析 HEARTBEAT.md: {len(tasks)} 个任务")
            return tasks
        
        except Exception as e:
            logger.warning(f"解析 HEARTBEAT.md 失败：{e}")
            return []
    
    async def _run_task(self, task: HeartbeatTask):
        """
        执行单个任务
        
        参数:
            task: 任务定义
        """
        try:
            logger.info(f"执行任务：{task.name}")
            
            # 更新执行时间
            task.last_run = datetime.now()
            task.next_run = task.last_run + timedelta(minutes=task.interval_minutes)
            
            # 执行处理函数
            if task.handler:
                result = await task.handler()
                logger.info(f"任务完成：{task.name} - {result}")
            
            # 保存状态
            self._save_state()
        
        except Exception as e:
            logger.exception(f"任务执行失败 {task.name}: {e}")
    
    async def _scheduler_loop(self):
        """调度器主循环"""
        logger.info("调度器启动")
        
        while self.running:
            try:
                now = datetime.now()
                
                # 检查所有任务
                for task in self.tasks.values():
                    if not task.enabled:
                        continue
                    
                    # 检查是否需要执行
                    if task.next_run and now >= task.next_run:
                        await self._run_task(task)
                
                # 每分钟检查一次
                await asyncio.sleep(60)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"调度器循环错误：{e}")
                await asyncio.sleep(60)
        
        logger.info("调度器已停止")
    
    async def start(self):
        """启动调度器"""
        if self.running:
            logger.warning("调度器已在运行中")
            return
        
        self.running = True
        self._task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("✓ Heartbeat 调度器已启动")
    
    async def stop(self):
        """停止调度器"""
        if not self.running:
            return
        
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("✓ Heartbeat 调度器已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "running": self.running,
            "task_count": len(self.tasks),
            "tasks": {
                name: {
                    "last_run": task.last_run.isoformat() if task.last_run else None,
                    "next_run": task.next_run.isoformat() if task.next_run else None,
                    "enabled": task.enabled,
                    "interval_minutes": task.interval_minutes,
                }
                for name, task in self.tasks.items()
            },
        }


# ============================================================================
# 预定义任务处理器
# ============================================================================

async def check_email_handler() -> Dict[str, Any]:
    """检查邮件示例处理器"""
    logger.info("检查新邮件...")
    # TODO: 实现邮件检查逻辑
    return {"status": "checked", "new_emails": 0}


async def check_calendar_handler() -> Dict[str, Any]:
    """检查日历示例处理器"""
    logger.info("检查日历事件...")
    # TODO: 实现日历检查逻辑
    return {"status": "checked", "upcoming_events": []}


async def check_weather_handler() -> Dict[str, Any]:
    """检查天气示例处理器"""
    logger.info("检查天气...")
    # TODO: 实现天气检查逻辑
    return {"status": "checked", "weather": "sunny"}


# ============================================================================
# 便捷函数
# ============================================================================

def create_heartbeat_scheduler(
    workspace_path: Optional[str] = None,
    enable_email: bool = False,
    enable_calendar: bool = False,
    enable_weather: bool = False,
) -> HeartbeatScheduler:
    """
    创建 Heartbeat 调度器的便捷函数
    
    参数:
        workspace_path: 工作区路径
        enable_email: 是否启用邮件检查
        enable_calendar: 是否启用日历检查
        enable_weather: 是否启用天气检查
    
    返回:
        HeartbeatScheduler 实例
    """
    scheduler = HeartbeatScheduler(workspace_path=workspace_path)
    
    # 注册预定义任务
    if enable_email:
        scheduler.register_task("email", check_email_handler, interval_minutes=30)
    
    if enable_calendar:
        scheduler.register_task("calendar", check_calendar_handler, interval_minutes=60)
    
    if enable_weather:
        scheduler.register_task("weather", check_weather_handler, interval_minutes=120)
    
    return scheduler


# ============================================================================
# 测试入口
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    
    # 创建调度器
    scheduler = create_heartbeat_scheduler(
        workspace_path=str(Path.cwd() / "workspace"),
        enable_email=True,
        enable_calendar=True,
        enable_weather=True,
    )
    
    # 打印状态
    print("\nHeartbeat 调度器状态:")
    print(json.dumps(scheduler.get_status(), indent=2, ensure_ascii=False))
    
    # 测试运行
    async def test():
        print("\n启动调度器（测试 5 分钟）...")
        await scheduler.start()
        
        try:
            await asyncio.sleep(300)  # 运行 5 分钟
        except KeyboardInterrupt:
            print("\n收到中断信号")
        finally:
            await scheduler.stop()
            print("调度器已停止")
    
    asyncio.run(test())
