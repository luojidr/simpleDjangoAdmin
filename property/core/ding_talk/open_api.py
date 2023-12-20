import os.path
import typing

from dingtalk import AppKeyClient
from dingtalk.model.message import BodyBase
from dingtalk.client.api.message import Message

from .parser import MessageBodyParser
from fosun_circle.libs.decorators import to_retry
from config.conf import DingTalkConfig
from fosun_circle.libs.exception import DingMsgTypeNotExist
from fosun_circle.constants.enums.ding_msg_type import DingMsgTypeEnum


class BaseDingMixin(MessageBodyParser):
    def __init__(self, corp_id="", agent_id=None, app_key=None, app_secret=None, **kwargs):
        self._corp_id = corp_id or self.default_config["corp_id"]
        self._agent_id = agent_id or self.default_config["agent_id"]
        self._app_key = app_key or self.default_config["app_key"]
        self._app_secret = app_secret or self.default_config["app_secret"]

        self._client = AppKeyClient(
            corp_id=self._corp_id,
            app_key=self._app_key,
            app_secret=self._app_secret
        )

        super(MessageBodyParser, self).__init__(**kwargs)

    @property
    def default_config(self):
        return dict(
            corp_id=DingTalkConfig.DING_CORP_ID,
            agent_id=DingTalkConfig.DING_AGENT_ID,
            app_key=DingTalkConfig.DING_APP_KEY,
            app_secret=DingTalkConfig.DING_APP_SECRET,
        )

    @to_retry
    def get_access_token(self):
        """ 获取应用 access token """
        return self._client.get_access_token()


class DingTalkMessageOpenApi(BaseDingMixin):
    """ 发送不同类型的消息 """

    def __init__(self, msg_type=None, **kwargs):
        self._msg_type = msg_type

        init_kwargs = dict(msg_type=msg_type)
        init_kwargs.update(**kwargs)
        super(DingTalkMessageOpenApi, self).__init__(**init_kwargs)

        self._message = Message(client=self._client)

    @to_retry
    def upload_media_file(self, media_filename):
        """ 上传图片、文件、语音文件
        @param media_filename: 文件路径

        resp: {
            'errcode': 0, 'errmsg': 'ok', 'media_id': '@lALPDeC2zDlm8IpiYg',
            'created_at': 1603962089663, 'type': 'image'
        }
        """
        if not os.path.exists(media_filename):
            raise ValueError("媒体文件不存在")

        media_file = open(media_filename, "rb")
        resp = self._message.media_upload(self._msg_type, media_file)

        if resp.get("errcode") != 0:
            raise ValueError("上传上传失败: {}".format(resp.get("errmsg")))

        return resp["media_id"]

    def get_msg_body(self, **body_kwargs):
        """ 根据不同的消息类型获取对应的消息体 """
        if self._msg_type == DingMsgTypeEnum.TEXT.msg_type:
            msg_body = self.get_text_body(**body_kwargs)

        elif self._msg_type == DingMsgTypeEnum.LINK.msg_type:
            msg_body = self.get_link_body(**body_kwargs)

        elif self._msg_type in self.MEDIA_TYPE_TO_MAX_SIZE:
            msg_body = self.get_media_body(**body_kwargs)

        elif self._msg_type == DingMsgTypeEnum.OA.msg_type:
            msg_body = self.get_oa_body(**body_kwargs)
        else:
            raise DingMsgTypeNotExist(msg_type=self._msg_type)

        return msg_body

    @to_retry
    def async_send(self, body_kwargs, receiver_user_ids=()):
        """ 企业会话消息异步发送
        :param body_kwargs: 不同消息体对应的参数 | Dict
        :param receiver_user_ids: 接收者的用户userid列表
        """

        if not isinstance(receiver_user_ids, (typing.Tuple, typing.List)):
            raise ValueError("parameter `user_id_list` must is list|tuple")

        msg_body = self.get_msg_body(**body_kwargs)

        if not isinstance(msg_body, BodyBase):
            raise ValueError("parameter `msg_body` must is a instance of BodyBase")

        return self._message.asyncsend_v2(msg_body, self._agent_id, receiver_user_ids)



