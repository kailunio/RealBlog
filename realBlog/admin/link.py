# encoding: utf8
import pymongo
from bson.objectid import ObjectId
from django.views.decorators.csrf import csrf_exempt
from realBlog.func import redirect, render_admin_and_back, connect_blog_database

__author__ = '在何方'

def show_all(request):

    db = connect_blog_database(request)
    info = db.infos.find_one()
    links = list(db.links.find(sort=[('Order', pymongo.ASCENDING)]))
    for link in links:
        link['Id'] = str(link['_id'])

    return render_admin_and_back(request, 'show-links.html', {
        'page': u'链接',
        'links':links,
        'selection':'links',
        })

@csrf_exempt
def new(request):

    db = connect_blog_database(request)

    # 普通访问
    if request.method == 'GET':
        return render_admin_and_back(request, 'edit-link.html', {
            'page': u'新链接',
        })

    elif request.method == 'POST':

        d = request.POST
        order = int(d['link-order']) if d['link-order'] else 0
        update = {
            'Title':d['link-title'],
            'Address':d['link-address'],
            'Description':d['link-description'],
            'Order': order,
            }
        # 插入新的Link
        db.links.insert(update)

        # 对链接重新排序
        links = list(db.links.find(sort=[('Order', pymongo.ASCENDING)]))
        for i in xrange(0, len(links)):
            if links[i]['Order'] != i:
                db.links.update(links[i],  {"$set":{'Order': i}})

        return redirect(request, '新建链接成功', 'admin/show-links/')

@csrf_exempt
def edit(request, objectId):

    db = connect_blog_database(request)
    id = ObjectId(objectId)

    # 普通访问
    if request.method == 'GET':
        link = db.links.find_one({'_id':id})
        return render_admin_and_back(request, 'edit-link.html', {
            'page': u'编辑链接',
            'link': link
        })

    elif request.method == 'POST':

        d = request.POST
        order = int(d['link-order']) if d['link-order'] else 0
        update = {
            'Title':d['link-title'],
            'Address':d['link-address'],
            'Description':d['link-description'],
            'Order':order,
            }
        # 取得所有链接
        links = list(db.links.find(sort=[('Order', pymongo.ASCENDING)]))

        # 创建或取得编辑中的Link
        link = filter(lambda i: i['_id'] == id, links)[0]
        db.links.update(link, {'$set': update})
        links.remove(link)
        links.insert(order, link)

        # 对所有链接重新排序
        for i in xrange(0, len(links)):
            if links[i]['Order'] != i:
                db.links.update(links[i],  {"$set":{'Order': i}})

        return redirect(request, '编辑链接成功', 'admin/show-links/')

@csrf_exempt
def delete(request, objectId):

    db = connect_blog_database(request)
    id = ObjectId(objectId)

    # 普通访问
    if request.method == 'GET':
        db.links.remove({'_id':id})

        # 取得所有链接
        links = list(db.links.find(sort=[('Order', pymongo.ASCENDING)]))

        # 对所有链接重新排序
        for i in xrange(0, len(links)):
            if links[i]['Order'] != i:
                db.links.update(links[i],  {"$set":{'Order': i}})

        return redirect(request, '删除链接成功', 'admin/show-links/')

