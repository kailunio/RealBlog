# encoding: utf-8
from django.conf.urls import patterns, include, url
import views
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()


urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'realBlog.views.home', name='home'),
    # url(r'^realBlog/', include('realBlog.foo.urls')),

    # 首页
    url( r'^$', views.show_homepage, {'page': 1}),
    url( r'^page/(\d+?)/$', views.show_homepage),

    # 调试时取得静态文件
    url( r'\.(css|js|png|jpg|gif|xml|swf|html)$', views.get_file),

    url( r'^login/', views.login),
    url( r'^logout/', views.logout),
    url( r'^register/$', views.register),
    url( r'^install/$', views.install),
    url( r'^article/(\d+?)/$', views.show_article),
    url( r'^category/(.+?)/$', views.show_category),
    url( r'^tag/(.+?)/$', views.show_tag),
    url( r'^rss/$', views.rss),

    # Admin
    url( r'^admin/', include('realBlog.admin.urls')),


    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
