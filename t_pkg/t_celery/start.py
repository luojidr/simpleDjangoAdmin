import sys
from optparse import OptionParser

from celery import current_app
from celery.apps.worker import Worker


def app_start():
    """
      app 脚本启动 celery
      注意： app 脚本启动时 -P 参数只能是：threads,prefork(默认)，但是 gevent和eventlet会造成卡顿

    """
    from config.celery import app

    # 任务正常消费1
    # Execute Ok
    app.start(argv=["-A", "config.celery", "worker", "-l", "info", "-c", "50"])
    # app.start(argv=["-A", "config.celery", "worker", "-l", "info", "-P", "threads", "-c", "150"])

    # Execute Pause, Failed
    # app.start(argv=["-A", "config.celery", "worker", "-l", "info", "-P", "gevent", "-c", "10"])

    # Execute Pause, Failed
    # app.worker_main(argv=["-A", "config.celery", "worker", "-l", "info", "-P", "eventlet", "-c", "10"])

    # 任务正常消费2
    # w = app.Worker()
    # w.start()

    # 任务正常消费3 -> 等同2
    # pool_cls="gevent": Execute Pause, Failed
    # from celery.apps import worker
    # w = worker.Worker(app=app,
    #                   concurrency=10, loglevel="INFO", pool_cls="gevent"
    #                   )
    # w.start()


def worker_start():
    """ start failed """
    from config.celery import app
    from celery.bin import worker
    from click.core import Context

    usage = "Usage: %prog [crawler|worker|scheduler|admin|shell] [options] arg"
    parser = OptionParser(usage)

    parser.add_option("-c", "--concurrency", dest="concurrency",
                      help="concurrency number",
                      type=int, default=4)
    parser.add_option("-l", "--loglevel", dest="loglevel",
                      help="set loglevel, default is 'INFO'.", default='INFO')
    options, args = parser.parse_args(args=sys.argv[1:])

    opts = dict(
        hostname="dj_celery@properety",
        concurrency=options.concurrency,
        loglevel=options.loglevel,
        traceback=True
    )

    # celery > 5.0.x， start failed
    # app = current_app._get_current_object()
    worker.worker(["--app", "config.celery", "--loglevel", "info"])


if __name__ == "__main__":
    # 启动1
    app_start()
    # worker_start()


