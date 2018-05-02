from django.conf.urls import include, url
from django.contrib import admin

from apps.goods import views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^index$',views.IndexView.as_view(),name='index')
]