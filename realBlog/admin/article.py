# encoding: utf-8

import pytz
import pymongo

from datetime import datetime, timedelta
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from realBlog.admin.timezone import get_timezone_object, is_daylight_saving_time
from realBlog.func import *

ERROR = 'error'
SUCCEED = 'succeed'

@csrf_exempt
def new(request):

    db = connect_blog_database(request)

    if request.method == 'GET':
        info = db.infos.find_one()
        return render_admin_and_back(request, 'edit-article.html', {
            'page':u'新文章',
            'categories': db.categories.find(),
            'article':{
                'Timezone': info.get('DefaultTimezone'),
                'TimezoneOffset': info.get('DefaultTimezoneOffset'),
                'UseDefaultTimezone': False,
                },
            })

    elif request.method == 'POST':
        d = request.POST

        # 取得Article内容
        a, res = get_article_content(d)
        if res is not None:
            return HttpResponse(res)

        # Author
        user = request.session.get('user')
        if user is None:
            return HttpResponse(ERROR + '用户状态已过期，请重新登录')
        a['Author'] = {
            'Username':user['Username'],
            'Nickname':user['Nickname'],
            'Email':user['Email'],
        }

        # 取得Id
        info = db.infos.find_one()
        a['Id'] = info['TopId']

        db.articles.insert(a)
        db.infos.update(info, {"$set":{'TopId': info['TopId']+1}}) # TopId++

        return HttpResponse(SUCCEED)

@csrf_exempt
def edit(request, id):

    id = int(id)
    db = connect_blog_database(request)

    if request.method == 'GET':

        a = db.articles.find_one({'Id': id})
        if a is None:
            return HttpResponse('404')

        # 取得分类和Tags
        categories = list(db.categories.find())
        for c in categories:
            c['Checked'] = c['Title'] in a['Categories']

        cats = ','.join(a['Categories'])
        tags = ','.join(a['Tags'])

        # 取得时区信息
        info = db.infos.find_one()
        a['UseDefaultTimezone'] = a.get('Timezone') is None
        a['Timezone'] = a.get('Timezone') or info.get('Timezone')
        a['TimezoneOffset'] = a.get('TimezoneOffset') or info.get('TimezoneOffset')

        return render_admin_and_back(request, 'edit-article.html', {
            'page':u'编辑文章',
            'categories': categories,
            'cats': cats, 'tags': tags, 'article': a,
            'content': a['Content'] if a['IsPublic'] else a['HiddenContent']
        })

    elif request.method == 'POST':
        d = request.POST

        article = db.articles.find_one({'Id': id})

        # 取得Article内容
        a, res = get_article_content(d, article['PostOn'])
        if res is not None:
            return HttpResponse(res)

        # 验证用户
        user = request.session.get('user')
        if user is None:
            return HttpResponse(ERROR + '用户状态已过期，请重新登录')

        db.articles.update({'Id': id}, {'$set': a})
        return HttpResponse(SUCCEED)

def delete(request, id):

    db = connect_blog_database(request)
    id = int(id)

    if request.method == 'GET':
        article = db.articles.find_one({'Id': id})
        if article is None:
            return HttpResponse(404)

        db.articles.remove({'Id': id})

        return redirect(request, '删除成功，即将返回前一页...', 'admin/')

ARTICLES_PER_PAGE = 20

def show_articles(request, page = 1):

    page = int(page)
    db = connect_blog_database(request)
    info = db.infos.find_one()
    articles = list(db.articles.find(
        sort = [('PostOn', pymongo.DESCENDING)],
        skip = (page - 1) * ARTICLES_PER_PAGE,
        limit = ARTICLES_PER_PAGE,
    ))

    for a in articles:
        calculate_local_time(info, a)

    article_count = db.articles.count()
    page_count = article_count / ARTICLES_PER_PAGE +\
                 (1 if article_count % ARTICLES_PER_PAGE else 0)

    # 计算页码
    page_range = []
    if page <= page_count:
        low = (page - 1) / 10 * 10 + 1 # 利用整数除法
        if low + 10 <= page_count:
            page_range = range(low, 10 + 1)
        else:
            page_range = range(low, page_count + 1)

    return render_admin_and_back(request, 'articles.html', {
        'page':u'文章',
        'articles':articles,
        'selection':'articles',
        'page_current': page,
        'page_range': page_range,
        'page_count': page_count,
    })

def show_hidden_article(request, id):

    db = connect_blog_database(request)

    article = db.articles.find_one({
        'Id':int(id), 'IsPublic': False
    })
    if article is None:
        return HttpResponse(404)

    return render_admin_and_back(request, 'show-hidden-article.html', {
        'page':u'隐私文章 - '+ article['Title'],
        'article':article,
        })

def get_article_content(d, postOn = None):
    """
    取得表单中文章的内容
    """
    title = d.get('title')
    if title is None or title == '':
        return None, ERROR + '标题不能为空'

    content = d.get('content')
    if content is None or content == '':
        return None, ERROR + '正文都不能为空'

    is_public = d.get('is-set-public') == 'true'
    a = {
        'Title': title,
        'IsPublic': is_public,
        'Content': content if is_public else None,
        'HiddenContent': content if not is_public else None,
    }

    # 分类和Tags
    def split_and_strip(s):
        return [i.strip() for i in s.split(',') if i!='' ]

    categories = d.get('categories') or ''
    a['Categories'] = split_and_strip(d['categories'])

    tags = d.get('tags') or ''
    a['Tags'] = split_and_strip(d['tags'])

    # 发布时间
    if postOn is None or d.get('update-post-on') == 'true':
        postOn = datetime.utcnow()
    a['PostOn'] = postOn

    # 时区相关
    if d.get('use-default-timezone') != 'true':
        timezone = d.get('timezone')
        offset = d.get('timezone-offset')

        # 验证时区是否有效
        tz = get_timezone_object(timezone, offset)
        if tz is not None:
            a['Timezone'] = timezone
            a['TimezoneOffset'] = offset
            a['IsDst'] = is_daylight_saving_time(tz, postOn)
        else:
            return None, ERROR + '无效的时区'
    else:
        a['Timezone'] = None
        a['TimezoneOffset'] = None
        a['IsDst'] = None

    return a, None
