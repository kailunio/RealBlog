# encoding: utf-8
import os

from django.conf.urls import patterns, include, url
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from realBlog.admin import article, category, link, other
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',

    url( r'^$', article.show_articles),

    # Articles
    url( r'^show-articles/(\d+)/$', article.show_articles),
    url( r'^new-article/$', article.new),
    url( r'^edit-article/(\d+)/$', article.edit),
    url( r'^delete-article/(\d+)/$', article.delete),
    url( r'^show-hidden-article/(\d+)/$', article.show_hidden_article),

    # Categories
    url( r'^show-categories/$', category.show_all),
    url( r'^new-category/$', category.new),
    url( r'^edit-category/([0-9a-f]+)/$', category.edit),
    url( r'^delete-category/([0-9a-f]+)/$', category.delete),

    # Links
    url( r'^show-links/$', link.show_all),
    url( r'^new-link/$', link.new),
    url( r'^edit-link/([0-9a-f]+)/$', link.edit),
    url( r'^delete-link/([0-9a-f]+)/$', link.delete),

    # Settings
    url( r'^blog-settings/$', other.show_settings),
    url( r'^blog-plugins/$', other.show_plugins),

    url( r'^upload-xml/$', other.upload_xml),
    url( r'^import-xml/(.+?)/$', other.import_xml),
    url( r'^import-and-export/$', other.import_and_export),
)


