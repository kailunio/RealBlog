# encoding: utf-8

DEBUG = True
SECRET_KEY = 'g4#^+d4sl+-qql@=h32a_4eeys*&_qln^l5il!=nd*q=3a4ku)'

DATABASE_HOST = '127.0.0.1'
DATABASE_PORT = 27017
DATABASE_USERNAME = None
DATABASE_PASSWORD = None

STR_NAME = 'Name'
STR_ADMINS = 'Administrators'

BLOGS = {
    '127.0.0.1:8000':{
        STR_NAME: 'realBlog',
        STR_ADMINS: 'real',
    }
}