import re

from django.contrib.auth import login, authenticate, logout
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.views.generic import View
from itsdangerous import TimedJSONWebSignatureSerializer, SignatureExpired
from pymysql import IntegrityError

from apps.users.models import User
from fresh01 import settings
from celery_tasks.tasks import send_active_mail

class RegisterView(View):
    """显示注册界面"""
    def get(self,request):
        return render(request,'register.html')
    def post(self,request):
        """
        1.获取请求参数
        2.校验数据合法性
        3.利用Django自带的方法把用户保存到数据库，并对用户密码加密
        4.发送激活邮件
        5.响应请求,返回html页面
        """

        #获取请求参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        email = request.POST.get('email')
        allow = request.POST.get('allow')

        # 校验数据合法性
        # 所有的参数都不为空时,all方法才会返回True
        if not all([username,password,password2,email]):
            return render(request,'register.html',{'errmsg':'参数不能为空'})

        if password != password2:
            return render(request,'register.html',{'errmsg':'两次输入的密码不一致'})

        if not re.match('^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
            return render(request, 'register.html', {'errmsg': '请输入正确的邮箱格式'})

        #checkbox勾选中会返回on
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意协议'})


        # 业务处理
        # 保存用户到数据库中
        # create_user: 是django提供的方法, 会对密码进行加密后再保存到数据库
        try:
            user = User.objects.create_user(username=username,email=email,password = password)
        except IntegrityError:
            return render(request, 'register.html', {'errmsg': '用户已存在'})

        #发送激活邮件
        #1.给用户id加密
        #2.定义一个发送邮件的方法，给用户发送激活连接
        #3.把用户的激活状态改为Flase未激活

        #1.给用户id加密
        # 参数1: 密钥(可以随便写东西，但是为了安全，使用Django自动生成的密钥)
        # 参数2: 过期时间,1小时
        s = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,3600)
        token = s.dumps({'confirm':user.id}) #是字节类型(要转为字符串类型)
        token = token.decode() #字节转为字符串

        # 2.给用户发送激活连接
        #第一种发送邮件方法
        # self.send_active_mail(username,email,token)
        #第二种：用异步发送邮件方法
        send_active_mail.delay(username, email, token)
        #3.把用户的激活状态改为Flase未激活
        user.is_active  = False
        user.save()


        # 响应请求,返回html页面
        return HttpResponse("进入登录界面")

    def send_active_mail(self, username, email, token):
        """
        发送激活邮件
        :param username: 注册的用户
        :param email:  注册用户的邮箱
        :param token: 对字典 {'confirm':用户id} 加密后的结果
        :return:
        """

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

        # 调用django的send_mail方法发送邮件
        send_mail(subject, message, from_email, recipient_list,
                  html_message=html_message)  # 使用关键字参数传递html_message


class ActiveView(View):
    def get(self,request,token):

        #将用dumps方法加密的用户id转为字典格式拿到用户id的明文格式
        try:
            s=TimedJSONWebSignatureSerializer(settings.SECRET_KEY,3600)
            dict_token = s.loads(token)
            user_id = dict_token.get('confirm')
        except SignatureExpired:
            return HttpResponse('url连接已过期')

        #得到用户id后在数据库查出用户信息，把激活状态改为true
        user = User.objects.get(id=user_id)
        user.is_active = True
        user.save()

        return redirect(reverse('users:login'))


class LoginView(View):

    def get(self,request):
        """显示登陆页面"""
        return render(request,'login.html')
    def post(self,request):
        """处理登录逻辑
        1.获取登录请求参数
        2.校验参数合法性
        3.使用django提供的认证方法，调用django提供的方法,判断用户名和密码是否正确
        4.判断用户名是否有激活
        5.调用django的login方法, 记录登录状态(session)
        6.设置session有效期

        """
        #1.获取登录请求参数
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        #2.校验参数合法性
        if not all([username,password]):
            return render(request,'login.html',{'errmsg':'请输入参数'})

        #3.使用django提供的认证方法，调用django提供的方法,判断用户名和密码是否正确
        user = authenticate(username=username,password=password)
        if user is None:
            return render(request,'login.html',{'errmsg':'请输入正确的用户名和密码'})

        #4.判断用户名是否有激活
        if not user.is_active:
            return render(request, 'login.html', {'errmsg': '账号未激活'})

        #5.调用django的login方法, 记录登录状态(session)
        login(request,user)

        #6.设置session有效期
        if remember == 'on':# 勾选保存用户登录状态
            request.session.set_expiry(None)  # 保存登录状态两周
        else:
            request.session.set_expiry(0)  # 关闭浏览器后,清除登录状态


        # 获取next跳转参数
        next_url = request.GET.get('next', None)
        if next_url is None: # 默认情况,进入首页
            # 响应请求. 进入首页
            return redirect(reverse('goods:index'))
        else:
            # return redirect(reverse(next_url)) # error
            return redirect(next_url)


class LogoutView(View):
    #注销用户
    def get(self,request):
        logout(request) #Django自带清除session方法
        return redirect(reverse('goods:index'))