# encoding: utf-8
import pymongo
from bson.objectid import ObjectId
from django.views.decorators.csrf import csrf_exempt
from realblog.func import connect_blog_database, render_admin_and_back, redirect

__author__ = '在何方'

def show_all(request):
    db = connect_blog_database(request)
    info = db.infos.find_one()
    categories = list(db.categories.find(sort=[('Order', pymongo.ASCENDING)]))
    for category in categories:
        category['Id'] = str(category['_id'])

    return render_admin_and_back(request, 'show-categories.html', {
        'page':u'分类',
        'categories':categories,
        'selection':'categories',
        })

@csrf_exempt
def new(request):

    db = connect_blog_database(request)

    # 普通访问
    if request.method == 'GET':
        return render_admin_and_back(request, 'edit-category.html', {
            'page':u'新分类',
        })

    elif request.method == 'POST':

        d = request.POST
        order = int(d['category-order']) if d['category-order'] else 0
        update = {
            'Title':d['category-title'],
            'Description':d['category-description'],
            'Order': order,
            }
        # 插入新的Category
        db.categories.insert(update)

        # 对链接重新排序
        categories = list(db.categories.find(sort=[('Order', pymongo.ASCENDING)]))
        for i in xrange(0, len(categories)):
            if categories[i]['Order'] != i:
                db.categories.update(categories[i],  {"$set":{'Order': i}})

        return redirect(request, '新建分类成功', 'admin/show-categories/')

def update_category_of_articles(coll, old_cat, new_cat):
    """
    更新文章集合的分类
    """
    old = old_cat['Title']
    new = new_cat['Title']
    if old != new:
        for a in coll.find({'Categories': old}):
            array = a['Categories']
            array[array.index(old)] = new
            coll.update({'Id': a['Id']}, {'$set': {'Categories': array}})

@csrf_exempt
def edit(request, objectId):

    db = connect_blog_database(request)
    id = ObjectId(objectId)

    # 普通访问
    if request.method == 'GET':

        category = db.categories.find_one({'_id':id})
        return render_admin_and_back(request, 'edit-category.html', {
            'page':u'编辑分类',
            'category': category,
            })

    elif request.method == 'POST':

        d = request.POST
        order = int(d['category-order']) if d['category-order'] else 0
        update = {
            'Title':d['category-title'],
            'Description':d['category-description'],
            'Order':order,
            }
        # 取得所有Category
        categories = list(db.categories.find(sort=[('Order', pymongo.ASCENDING)]))

        # 创建或取得编辑中的Category
        category = filter(lambda i: i['_id'] == id, categories)[0]
        db.categories.update(category, {'$set': update})
        categories.remove(category)
        categories.insert(order, category)

        # 对所有链接重新排序
        for i in xrange(0, len(categories)):
            if categories[i]['Order'] != i:
                db.categories.update(categories[i],  {"$set":{'Order': i}})

        # 更新所有文章的分类
        update_category_of_articles(db.articles, category, update)
        update_category_of_articles(db.hidden_articles, category, update)

        return redirect(request, '编辑分类成功', 'admin/show-categories/')

@csrf_exempt
def delete(request, objectId):

    db = connect_blog_database(request)
    id = ObjectId(objectId)

    if request.method == 'GET':

        db.categories.remove({'_id':id})

        # 取得所有Category
        categories = list(db.categories.find(sort=[('Order', pymongo.ASCENDING)]))

        # 对所有链接重新排序
        for i in xrange(0, len(categories)):
            if categories[i]['Order'] != i:
                db.categories.update(categories[i],  {"$set":{'Order': i}})

        return redirect(request, '删除分类成功', 'admin/show-categories/')