from celery.app.base import Celery
from django.core.mail import send_mail

from fresh01 import settings

"""
1.创建celery应用对象
2.send_active_email()：内部封装激活邮件内容，并用装饰器@app.task注册
3.调用python的send_mail()将激活邮件发送出去
"""



#1.创建celery应用对象
# 参数1是异步任务路径
# 参数2是指定的broker
# redis://密码@redis的ip:端口/数据库
app = Celery('celery_tasks.tasks',broker='redis://127.0.0.1:6379/1')


#2.send_active_email()：内部封装激活邮件内容，并用装饰器@app.task注册
@app.task
def send_active_mail(username, email, token):
    subject = '天天生鲜注册激活'        # 邮件标题
    message = ''                      # 邮件的正文(不带样式)
    from_email = settings.EMAIL_FROM  # 发送者
    recipient_list = [email]          # 接收者, 注意: 需要是一个list
    # 邮件的正文(带有html样式)
    html_message = '<h3>尊敬的%s:</h3>  欢迎注册天天生鲜' \
                   '请点击以下链接激活您的账号:<br/>' \
                   '<a href="http://127.0.0.1:8000/users/active/%s">' \
                   'http://127.0.0.1:8000/users/active/%s</a>' % \
                   (username, token, token)

    # 3.调用django的send_mail方法发送邮件
    send_mail(subject, message, from_email, recipient_list,
              html_message=html_message)     # 使用关键字参数传递html_message