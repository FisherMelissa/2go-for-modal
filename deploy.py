import modal
import os
import time
import datetime
import argparse

# 使用更通用的应用名称
APP_NAME = "scheduled_analytics"
WORKSPACE_DIR = "/workspace"

app = modal.App.lookup(APP_NAME, create_if_missing=True)

# 配置镜像 - 添加必要的依赖
image = (
    modal.Image.debian_slim()
    .apt_install("curl", "git", "wget", "python3-pip", "net-tools")
    .pip_install("requests", "flask", "pytz", "apscheduler")
    .add_local_dir(".", remote_path=WORKSPACE_DIR)
)

def run_in_sandbox():
    print("🚀 Launching scheduled task...")
    
    # 创建Modal沙箱
    sandbox = modal.Sandbox.create(
        app=app,
        image=image,
        timeout=86400  # 24小时超时
    )
    
    # 启动服务 - 在后台运行
    command = f"cd {WORKSPACE_DIR} && python3 app.py"
    print("⏰ Starting scheduled service...")
    sandbox.exec("sh", "-c", f"nohup {command} > /dev/null 2>&1 &")
    
    print("✅ Scheduled service is now running in the background.")

def schedule_daily_run():
    """设置每天北京时间6点运行任务"""
    try:
        import pytz
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        print("❌ 缺少依赖包，请先安装: pip install pytz apscheduler")
        return
    
    scheduler = BackgroundScheduler()
    
    # 设置北京时间时区
    beijing_tz = pytz.timezone('Asia/Shanghai')
    
    # 每天6点执行任务
    scheduler.add_job(
        run_in_sandbox,
        'cron',
        hour=6,
        minute=0,
        timezone=beijing_tz
    )
    
    print(f"⏰ 已设置每天北京时间6:00自动运行")
    scheduler.start()
    
    # 保持主线程运行
    try:
        while True:
            time.sleep(3600)  # 每小时检查一次
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sandbox", action="store_true", help="立即在Modal沙箱中运行app.py")
    parser.add_argument("--schedule", action="store_true", help="设置每天北京时间6:00自动运行")
    args = parser.parse_args()

    if args.sandbox:
        run_in_sandbox()
    elif args.schedule:
        schedule_daily_run()
    else:
        print("ℹ️ 使用 --sandbox 立即运行 或 --schedule 设置定时任务")
