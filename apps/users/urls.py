from django.conf.urls import  url
from django.contrib import admin
from apps.users import views
urlpatterns = [

    url(r'^register$',views.RegisterView.as_view(),name = 'register'),
    url(r'^active/(?P<token>.+)$',views.ActiveView.as_view(),name='active'),
    url(r'^login$',views.LoginView.as_view(),name='login'),
    url(r'^logout$', views.LogoutView.as_view(), name='logout'),

]