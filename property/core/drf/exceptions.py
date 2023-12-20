import logging

from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler

from ...utils.exception import BaseError
from ...constant.enums.status_code import CodeMessageEnum

logger = logging.getLogger("django")


def get_code_and_exc_message(exc):
    """ 获取异常信息 """
    code = None

    # 自定义类的获取
    if isinstance(exc, BaseError):
        code, message = exc.code, exc.msg
    elif isinstance(exc, APIException):
        # rest_framework.exceptions.APIException 中抛出的异常
        message_list = []
        errors = exc.args[0].serializer.errors if hasattr(exc.args[0], "serializer") else {}

        for err_key, err_msg_list in errors.items():
            msg = err_key + " -> " + "|".join(err_msg_list)
            message_list.append(msg)

        message = "\n".join(message_list) or str(exc)
    else:
        if len(exc.args) == 0:
            message = str(exc)
        else:
            message = exc.args[1] if len(exc.args) > 1 else exc.args[0]

    return code, message


def exception_handler(exc, context):
    """
    Custom exception handling
    :param exc: exception instance
    :param context: throw exception context
    :return: Response
    """
    view = context['view']
    logger.error('[%s] %s' % (view, exc))

    response = drf_exception_handler(exc, context)
    code, message = get_code_and_exc_message(exc)

    if response is None:
        code = code or CodeMessageEnum.INTERNAL_ERROR.code
    else:
        code = code or response.status_code

    # traceback
    import traceback
    logger.error("-------------------- libs.exception.exception_handler 001 --------------------")
    logger.error(traceback.format_exc())
    logger.error("-------------------- libs.exception.exception_handler 002 --------------------")

    response = Response(data=dict(code=code, message=message))
    return response

