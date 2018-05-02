import re

from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from pymysql import IntegrityError

from apps.users.models import User


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
            User.objects.create_user(username = username,email=email,password = password)
        except IntegrityError:
            return render(request, 'register.html', {'errmsg': '用户已存在'})

        #TODO：发送激活邮件
        # 响应请求,返回html页面
        return HttpResponse("进入登录界面")





