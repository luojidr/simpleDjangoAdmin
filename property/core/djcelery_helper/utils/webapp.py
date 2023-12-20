import logging
import threading
import asyncio

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.platform.asyncio
from tornado.options import define, options

# define("port", default=8000, help="run on the give port", type=int)
asyncio.set_event_loop_policy(tornado.platform.asyncio.AnyThreadEventLoopPolicy())


class HealthCheckHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Celery health check is ok.")


def run_app():
    # tornado.options.parse_command_line()
    app = tornado.web.Application(handlers=[(r"/celery/health/check", HealthCheckHandler)])
    http_server = tornado.httpserver.HTTPServer(app)
    # http_server.listen(options.port)
    http_server.listen(8000)
    # tornado.ioloop.IOLoop.current().start()  # NonBlock
    tornado.ioloop.IOLoop.instance().start()  # Block


def run_with_thread(signal=None):
    """ Docker中Celery启动 worker, beat 命令所需得web服务(健康检查) """
    logger = logging.getLogger("celery.worker")

    if signal:
        signal_name = signal.name
        logger.warning("Now will daemon start app => %s", signal_name)

        t_app = threading.Thread(target=run_app)
        t_app.setDaemon(True)
        t_app.start()

        logger.warning("Daemon start app is successful => %s", signal_name)
    else:
        logger.error("No signal to start the app")


if __name__ == "__main__":
    run_app()
