"""
任务管理系统
"""
import json
import os
from datetime import datetime
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

class TaskManager:
    def __init__(self, task_file='tasks.json'):
        self.task_file = task_file
        self.tasks = self.load()
    
    def load(self):
        if os.path.exists(self.task_file):
            with open(self.task_file, 'r') as f:
                return json.load(f)
        return {'tasks': [], 'last_update': None}
    
    def save(self):
        self.tasks['last_update'] = datetime.now().isoformat()
        with open(self.task_file, 'w') as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)
    
    def add_task(self, task_id, name, category, symbol, period_start, period_end):
        """添加任务"""
        task = {
            'id': task_id,
            'name': name,
            'category': category,  # china_500, global_500, us_500
            'symbol': symbol,
            'period_start': period_start,
            'period_end': period_end,
            'status': TaskStatus.PENDING.value,
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'duration': None
        }
        self.tasks['tasks'].append(task)
        self.save()
        return task
    
    def get_pending_tasks(self):
        return [t for t in self.tasks['tasks'] if t['status'] == TaskStatus.PENDING.value]
    
    def get_running_task(self):
        tasks = [t for t in self.tasks['tasks'] if t['status'] == TaskStatus.RUNNING.value]
        return tasks[0] if tasks else None
    
    def start_task(self, task_id):
        for task in self.tasks['tasks']:
            if task['id'] == task_id:
                task['status'] = TaskStatus.RUNNING.value
                task['started_at'] = datetime.now().isoformat()
                self.save()
                return task
        return None
    
    def complete_task(self, task_id, result):
        for task in self.tasks['tasks']:
            if task['id'] == task_id:
                task['status'] = TaskStatus.COMPLETED.value
                task['completed_at'] = datetime.now().isoformat()
                task['result'] = result
                if task['started_at']:
                    start = datetime.fromisoformat(task['started_at'])
                    task['duration'] = (datetime.now() - start).total_seconds()
                self.save()
                return task
        return None
    
    def fail_task(self, task_id, error):
        for task in self.tasks['tasks']:
            if task['id'] == task_id:
                task['status'] = TaskStatus.FAILED.value
                task['completed_at'] = datetime.now().isoformat()
                task['error'] = error
                self.save()
                return task
    
    def get_summary(self):
        total = len(self.tasks['tasks'])
        completed = len([t for t in self.tasks['tasks'] if t['status'] == TaskStatus.COMPLETED.value])
        running = len([t for t in self.tasks['tasks'] if t['status'] == TaskStatus.RUNNING.value])
        failed = len([t for t in self.tasks['tasks'] if t['status'] in [TaskStatus.FAILED.value, TaskStatus.TIMEOUT.value]])
        pending = total - completed - running - failed
        
        return {
            'total': total,
            'completed': completed,
            'running': running,
            'failed': failed,
            'pending': pending,
            'progress': f"{completed}/{total}" if total > 0 else "0/0"
        }

# 股票列表
STOCK_LISTS = {
    'china_500': [
        ('SH601318', '中国平安', '金融'),
        ('SH600036', '招商银行', '金融'),
        ('SH601398', '工商银行', '金融'),
        ('SH601939', '建设银行', '金融'),
        ('SH601288', '农业银行', '金融'),
        ('SH600519', '贵州茅台', '消费'),
        ('SH600030', '中信证券', '金融'),
        ('SH600028', '中国石化', '能源'),
        ('SH601857', '中国石油', '能源'),
        ('SH600900', '长江电力', '公用事业'),
        ('SH601888', '中国中免', '消费'),
        ('SH600276', '恒瑞医药', '医药'),
        ('SH300750', '宁德时代', '新能源'),
        ('SH002594', '比亚迪', '汽车'),
        ('SH600031', '三一重工', '制造'),
        ('SH600887', '伊利股份', '消费'),
        ('SH601012', '隆基绿能', '新能源'),
        ('SH600690', '海尔智家', '消费'),
        ('SH601668', '中国建筑', '建筑'),
        ('SH600585', '海螺水泥', '建材'),
    ],
    'global_500': [
        ('SH601318', '中国平安', '金融'),
        ('SH600036', '招商银行', '金融'),
        ('SH601398', '工商银行', '金融'),
        ('SH600519', '贵州茅台', '消费'),
        ('SH601857', '中国石油', '能源'),
        ('SH600028', '中国石化', '能源'),
        ('SH601939', '建设银行', '金融'),
        ('SH601288', '农业银行', '金融'),
        ('SH601988', '中国银行', '金融'),
        ('SH600900', '长江电力', '公用事业'),
    ],
    'us_500': [
        ('BABA', '阿里巴巴', '互联网'),
        ('JD', '京东', '互联网'),
        ('PDD', '拼多多', '互联网'),
        ('NIO', '蔚来', '新能源车'),
        ('XPEV', '小鹏汽车', '新能源车'),
        ('LI', '理想汽车', '新能源车'),
    ]
}

# 时间段划分（180天一段）
PERIODS = [
    ('2000-01-01', '2000-06-30'),
    ('2000-07-01', '2000-12-31'),
    ('2001-01-01', '2001-06-30'),
    # ... 简化演示，用近年数据
    ('2024-01-01', '2024-06-30'),
    ('2024-07-01', '2024-12-31'),
    ('2025-01-01', '2025-06-30'),
    ('2025-07-01', '2025-12-31'),
    ('2026-01-01', '2026-03-11'),
]