RealBlog是一个简单的博客系统，基于Django和MongoDB。我的个人网站\([www.xukailun.me](http://www.xukailun.me)\)即采用RealBlog构建。

#主要特性
 * 支持多用户
 * 支持隐藏文章
 * 支持文章的时区属性
 * 支持单一文章多个分类
 * 支持从WordPress导入文章
 * 基于Python、Django和MongoDB

#环境要求
 * Python 2.6 / 2.7
 * Django >=1.4
 * MongoDB >=1.8.0

其他依赖的Python组件：
 * pymongo(2.2.1) 
 * pytz(2012d)


#安装RealBlog
RealBlog与其他基于Django的网站的配置并无区别，我就以自己的环境为例，给出一个配置的方案。

我用Debian做服务器，Nginx做WebServer，uwsgi做应用程序容器。

##安装所有的东西

Nginx

    sudo aptitude install nginx

这样安装的Nginx版本可能偏低，您也可以下载最新源代码，编译安装。

MongoDB

    wget http://fastdl.mongodb.org/linux/mongodb-linux-x86_64-2.0.7.tgz
    tar zxvf mongodb-linux-x86_64-2.0.7.tgz
    mv mongodb-linux-x86_64-2.0.7 /usr/local/mongodb

uWSGI

这货需要C环境编译

    aptitude install build-essential python-dev libxml2-dev

没有装pip的话，也可以去下在安装包然后执行setup.py install。建议还是装下pip吧，下面还会用到的。

    pip install uwsgi

Django、pymongo和pytz

    pip install django
    pip install pymongo
    pip install pytz

##配置环境

把ReaBlog解压到某个目录，比如/var/www，假定wsgi.py的路径为/var/www/realblog/wsgi.py(注意大小写!)。<br />为Nginx的nginx.conf添加站点(置于/usr/local/nginx/conf)。在http内添加一个server：

    server {
        listen       80;
        # 此处可以有多个站点，使用空格分隔
        server_name  www.xukailun.me www.chenyan.fr;

        #  处理动态Python页面
        location / {
            root  /var/www/realblog;
            include uwsgi_params;
            uwsgi_pass unix:///var/www/realblog/uwsgi.sock; # 推荐使用sock方式
        }

        #  处理静态文件
        location ~* ^.+\.(png|jpg|jpeg|gif|html|css|js|swf)$ {
            root    /var/www/realblog;
            access_log   off;
            expires      30d;
        }
    }

为uWSGI添加配置文件realblog.conf(置于/usr/local/uwsgi)

    [uwsgi]
    chdir = /var/www
    daemonize = /var/www/realblog/uwsgi.log
    enable-threads = true
    env = DJANGO_SETTINGS_MODULE=realblog.settings
    listen = 20
    limit-as = 6048
    logdate = true
    master = true
    memory-report = true
    module = realblog.wsgi:application
    socket = /var/www/realblog/uwsgi.sock
    pidfile = /var/www/realblog/uwsgi.pid
    processes = 2
    profiler = true
    pythonpath = /var/www

为MongoDB添加配置文件mongodb.conf（置于/usr/local/mongodb/bin）

    fork = true
    dbpath = /usr/local/mongodb/data
    logpath = /usr/local/mongodb/log.log
    logappend = true
    bind_ip = 127.0.0.1

dbpath必须是已存在的目录，mongodb必须拥有读写权限<br />
logpath必须为已存在的文件，同样的mongodb需要读写权限

执行一下命令，启动环境

    # run Nginx
    /usr/local/nginx/sbin/nginx

    # run MongoDB
    cd /usr/local/mongodb/data
    if [ -e mongod.lock ]
    then 
        rm mongod.lock
    fi
    cd /usr/local/mongodb/bin
    ./mongod -f mongodb.conf

    # run uWSGI
    cd /usr/local/uwsgi
    ./uwsgi -d --ini realblog.conf

如果无误，可以把上述代码加入rc.local，在开机是自动启动。

##配置博客
编辑config/server.py:

    # encoding: utf-8

    # 请设置DEBUG为False
    DEBUG = False

    # 数据库信息
    DATABASE_HOST = '127.0.0.1'
    DATABASE_PORT = 27017
    DATABASE_USERNAME = None
    DATABASE_PASSWORD = None

    STR_NAME = 'Name'
    STR_ADMINS = 'Administrators'

    # 所有博客
    BLOGS = {
        'www.xukailun.me':{ # 博客的地址
            STR_NAME: 'realblog', # 名称，用于构成数据库名，仅字母数字下划线
            STR_ADMINS: 'real', # 一个管理员
            # STR_ADMINS: ['real', 'admin2', 'admin3'], # 也可以是多个管理员
        },
        # 可以有多个Blog
    }

##安装博客并创建管理员
访问/install/，如果指定的管理员账户未创建，则会先跳转到/register/。确认相关信息之后，安装即可。

#多用户配置
同一RealBlog实例可以配置多个用户的Blog。
在配置nginx.conf时，为server_name添加多个域名，以空格隔开：

    server_name www.xukailun.me www.chenyan.fr;

在配置server.py时，为字典BLOGS添加多项，用逗号隔开。

重新启动Nginx和uWSGI即可生效。

#更新计划
 * 特定页面
 * 允许更新文章发布时间
 * 使用AJAX提交文章
 * 数据库索引  Done@2012.08.23
 * 低版本浏览器的提示
 * 各种500和404页面
 * 函数命名规范化


（未完）
