# encoding: utf8
import os
from StringIO import StringIO
from xml.etree import ElementTree
from datetime import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from realBlog.admin.timezone import get_timezone_object
from realBlog.func import *
from realBlog.config.server import BLOGS

__author__ = '在何方'

@csrf_exempt
def show_settings(request):
    db = connect_blog_database(request)
    info = db.infos.find_one()

    if request.method == 'GET':
        return render_admin_and_back(request, 'blog-settings.html', {
            'page': u'管理 - 设置',
            'theme': info.get('Theme'),
            'themes': get_themes(),
            'subtitle': info.get('Subtitle'),
            'description': info.get('Description'),
            'customRss': info.get('CustomRss'),
            'articlesPerPage': info.get('ArticlesPerPage'),
            'defaultTimezone': info.get('DefaultTimezone'),
            'defaultTimezoneOffset': info.get('DefaultTimezoneOffset'),
            'selection': 'blog-settings',
        })

    elif request.method == 'POST':
        d = request.POST

        update = {
            'Theme': d['blog-theme'],
            'Title': d['blog-title'],
            'Subtitle': d['blog-subtitle'],
            'Description': d['blog-description'],
            'CustomRss': d['blog-customRss'],
            'ArticlesPerPage': int(d['blog-articles-per-page']),
            'DefaultTimezone': d['blog-default-timezone'],
            'DefaultTimezoneOffset': d['blog-default-timezone-offset'],
        }

        # 时区和其与UTC的偏差
        timezone = d['blog-default-timezone']
        offset = d['blog-default-timezone-offset']
        if get_timezone_object(timezone, offset):
            update['Timezone'] = timezone
            update['TimezoneOffset'] = offset

        db.infos.update(info, {'$set': update})

        return redirect(request, '设置保存成功', 'admin/')


@csrf_exempt
def show_plugins(request):
    db = connect_blog_database(request)
    info = db.infos.find_one()

    if request.method == 'GET':#'POST'
        return render_admin_and_back(request, 'blog-plugins.html', {
            'page': u'管理 - 插件',
            'weiboCode': info.get('WeiboCode'),
            'commentCode': info.get('CommentCode'),
            'latestCommentsCode': info.get('LatestCommentsCode'),
            'statisticsCode': info.get('StatisticsCode'),
            'statisticsCodeInHead': info.get('StatisticsCodeInHead'),
            'selection': 'blog-plugins',
        })

    elif request.method == 'POST':
        d = request.POST
        update = {
            'WeiboCode': d['weibo-code'],
            'CommentCode': d['blog-comment-code'],
            'LatestCommentsCode': d['blog-latest-comments-code'],
            'StatisticsCode': d['blog-statistics-code'],
            'StatisticsCodeInHead': d.get('blog-statistics-code-in-head') == u'on',
        }

        db.infos.update(info, {'$set': update})

        return redirect(request, '插件保存成功', 'admin/')


@csrf_exempt
def upload_xml(request):
    try:
        file = request.FILES['data']
        file_save = get_upload_path(file.name)
        print file_save
        save = open(get_upload_path(file.name), 'wb')
        for chunk in file.chunks():
            save.write(chunk)
        save.close()
        return HttpResponse('上传成功', 'text/plain')
    except Exception, e:
        return HttpResponse('上传失败:' + e.message, 'text/plain')


# 命名空间
ns = {
    'content': "{http://purl.org/rss/1.0/modules/content/}",
    'excerpt': "{http://wordpress.org/export/1.0/excerpt/}",
    'wfw': "{http://wellformedweb.org/CommentAPI/}",
    'dc': "{http://purl.org/dc/elements/1.1/}",
    'wp': "{http://wordpress.org/export/1.0/}",
}

# 格式化字符串
dt_format_str = '%Y-%m-%d %H:%M:%S'

def parse_article_from(item, blog, timezone):
    title = item.find('title').text
    content = StringIO('')
    content.write(u'<p style="font-weight: bold;">本文自WordPress博客「' + blog + u'」导入</p>')
    content.write(item.find(ns['content'] + 'encoded').text)

    # 取时间
    post_on = item.find(ns['wp'] + 'post_date_gmt').text
    post_on_time = datetime.strptime(post_on, dt_format_str)

    # 取分类和标签
    categories = []
    tags = []
    for cat in item.findall('category'):
        if not cat.get('nicename'):
            continue

        if cat.get('domain') == 'category':
            categories.append(cat.text)

        elif cat.get('domain') == 'tag':
            tags.append(cat.text)

    # 取所有评论
    comments = item.findall(ns['wp'] + 'comment')
    if len(comments):
        content.write(u'<p><br /></p>')
        content.write(u'<p style="font-weight: bold;">原文评论如下：</p>')
        for c in comments:
            # 作者
            author = c.find(ns['wp'] + 'comment_author').text
            author_url = c.find(ns['wp'] + 'comment_author_url').text
            content.write(u'<p><a href="' + (author_url or '/') + u'">' + author + u'</a></p>')

            # 发布时间
            comment_date_gmt = c.find(ns['wp'] + 'comment_date_gmt').text
            dt = datetime.strptime(comment_date_gmt, dt_format_str)
            local = get_local_from_utc(dt, timezone)

            content.write(u'<p>发布于:' + local.strftime(dt_format_str) + u' ' + timezone + u'</p>')

            # 发布内容
            comment_content = c.find(ns['wp'] + 'comment_content').text
            content.write(u'<p>' + comment_content + u'</p>')

    content_str = content.getvalue()
    content.close()

    return {
        'Title': title,
        'Categories': categories,
        'Content': content_str,
        'PostOn': post_on_time,
        'Tags': tags,
    }


@csrf_exempt
def import_xml(request, file):

    # 取当前登陆用户
    user = request.session.get('user')
    if user is None:
        return HttpResponse('导入出错：管理员用户似乎没有登录！')

    db = connect_blog_database(request)
    try:
        info = db.infos.find_one()
        topId = int(info['TopId'])
        timezone = info['DefaultTimezone']

        # 解析文件
        file += '.xml'
        et = ElementTree.parse(get_upload_path(file))
        channel = et.getroot().find('channel')
        blog = channel.find('title').text

        # 导入所有文章
        cats = []
        for item in channel.findall('item'):
            d = parse_article_from(item, blog, timezone)
            d['Id'] = topId
            d['Author'] = {
                'Username': user['Username'],
                'Nickname': user['Nickname'],
                'Email': user['Email'],
            }
            d['IsPublic'] = True
            db.transactions.insert({'ArticleId': info['TopId']})
            db.articles.insert(d)
            topId += 1

            for c in d['Categories']:
                if (c not in cats) and (not db.categories.find_one({'Title': c})):
                    cats.append(c)
        db.infos.update(info, {'$set': {'TopId': topId}})

        # 导入所有分类
        order = 0
        cat_one = db.categories.find_one({}, {'Order': -1})
        if cat_one is not None:
            order = cat_one['Order'] + 1

        for c in cats:
            db.categories.insert({
                'Title': c,
                'Description': '',
                'Order': order,
            })
            order += 1

        db.transactions.drop()
        db.connection.close()
        return HttpResponse('导入成功！')

    except Exception, e:
        for i in db.transactions.find():
            db.articles.remove({'Id': i['ArticleId']})
        db.transactions.drop()
        raise e

@csrf_exempt
def import_and_export(request):
    db = connect_blog_database(request)
    info = db.infos.find_one()
    user = request.session.get('user')

    return render_admin_and_back(request, 'import-and-export.html', {
        'page': '导入与导出',
        'author': user['Nickname'],
        'timezone': info['DefaultTimezone'],
    })





