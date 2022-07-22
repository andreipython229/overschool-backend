import subprocess

from overschool.celery import app


@app.task
def auto_backup():
    subprocess.run("python manage.py dbbackup -c -z", shell=True)
    subprocess.run("python manage.py mediabackup -c -z", shell=True)
