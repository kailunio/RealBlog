# encoding: utf-8
import os
import pytz
from pymongo import Connection
from pymongo.database import Collection
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import Context
from django.template.loader import get_template
from django.conf import settings
from realBlog.config.server import *
from datetime import datetime

__author__ = 'realh'

def ensure_index_of_blog(db):
    """
    创建博客数据库的索引
    """
    db.articles.ensure_index([('Id', -1)])
    db.articles.ensure_index([('PostOn', -1)])
    db.articles.ensure_index([('IsPublic', -1)])
    db.articles.ensure_index('Tags')
    db.articles.ensure_index('Categories')
    db.categories.ensure_index([('Title', 1)])

def get_upload_path(name):
    return os.path.join(os.path.dirname(__file__), 'upload', name)

def get_themes():
    directory = os.path.join(os.path.dirname(__file__), 'themes')
    return os.listdir(directory)

def set_template_dir(*d):
    settings.TEMPLATE_DIRS = (
        os.path.join(os.path.dirname(__file__), *d),
    )

def get_utc_from_local(dt, timezone):
    if timezone not in pytz.all_timezones:
        return dt

    # 验证客户端给出的时区是否有效
    tz = pytz.timezone(timezone)
    utc = pytz.utc.normalize(tz.localize(dt))
    return utc

def get_local_from_utc(dt, timezone):
    if timezone not in pytz.all_timezones:
        return dt

    # 验证客户端给出的时区是否有效
    tz = pytz.timezone(timezone)
    local = tz.normalize(pytz.utc.localize(dt))
    return local

def calculate_local_time(info, article):

    # 取得时区
    article['Timezone'] = article.get('Timezone')
    timezone = article.get('Timezone') or info.get('DefaultTimezone')
    if timezone is None:
        return

    # 重新计算时间
    tz = pytz.timezone(timezone)
    postOn = article['PostOn']
    article['PostOn'] = tz.normalize(pytz.utc.localize(postOn))

    # 时差
    article['TimezoneOffset'] = article.get('TimezoneOffset')

    # 是否出于夏令时
    article['IsDst'] = tz.dst(postOn).seconds != 0

def calculate_local_timeinfo(info, article):

    # 取得时区
    timezone = article.get('Timezone') or info.get('DefaultTimezone')
    if timezone is None:
        return

    article['Timezone'] = timezone

    # 重新计算时间
    tz = pytz.timezone(timezone)
    postOn = article['PostOn']
    article['PostOn'] = tz.normalize(pytz.utc.localize(postOn))

    # 时差
    offset = article.get('TimezoneOffset') or info.get('DefaultTimezoneOffset')
    article['TimezoneOffset'] = offset

    # 是否出于夏令时
    article['IsDst'] = tz.dst(postOn).seconds != 0

def render_and_back(request, template, d):
    """
    渲染博客的普通页面
    """
    db = connect_blog_database(request)
    info = db.infos.find_one(fields = {
        'Theme': 1,
        'Title': 1,
        'Subtitle': 1,
        'Description': 1,
        'CustomRss': 1,
        'WeiboCode': 1,
        'CommentCode': 1,
        'LatestCommentsCode': 1,
        'StatisticsCode': 1,
        'StatisticsCodeInHead' :1
    })

    # 设定模板目录
    set_template_dir('themes', info['Theme'])

    # 增加项
    d['host'] = request.get_host()
    d['user'] = request.session.get('user')
    d['info'] = info
    d['theme'] = info['Theme']
    d['title'] = info['Title']

    # 渲染模板
    t = get_template(template)
    html = t.render(Context(d))

    # 关闭数据库
    db.connection.close()

    return HttpResponse(html)


def render_admin_and_back(request, template, d):
    """
    渲染博客的管理页面
    """

    db = connect_blog_database(request)
    info = db.infos.find_one()

    # 设定模板目录
    set_template_dir('admin')

    # 增加项
    d['title'] = info['Title']
    d['host'] = request.get_host()
    d['user'] = request.session.get('user')

    # 渲染模板
    t = get_template(template)
    html = t.render(Context(d))

    # 关闭数据库
    #db.connection.close()

    return HttpResponse(html)



def redirect(request, title, path = None, delay = 2000):
    set_template_dir('admin')
    if path is None:
        path = request.get_full_path()[1:]
    return render_to_response('redirect.html', {
        'host':request.get_host(),
        'title': title,
        'redirect': path,
        'delay': delay,
        })

def get_current_blog(request):

    host = request.get_host()
    return BLOGS.get(host)

def connect_blog_database(request):
    """
    连接到对应的博客数据库
    """
    blog = get_current_blog(request)
    if blog is None:
        return None

    name = blog[STR_NAME]

    # 缺省连接到本地数据库
    host = None
    if DATABASE_USERNAME is None:
        host = 'mongodb://%s:%d' % (DATABASE_HOST, DATABASE_PORT)
    else:
        host = 'mongodb://%s:%s@%s:%d' %\
               (DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT)
    c = Connection(host)

    return c['realBlog_blogs_' + name]

def connect_account_database():
    """
    连接到账户数据库
    """
    # 缺省连接到本地数据库
    if DATABASE_USERNAME is None:
        host = 'mongodb://%s:%d' % (DATABASE_HOST, DATABASE_PORT)
    else:
        host = 'mongodb://%s:%s@%s:%d' %\
               (DATABASE_USERNAME, DATABASE_PASSWORD, DATABASE_HOST, DATABASE_PORT)

    c = Connection(host)
    return c['realBlog_users']