import json

from aliyunsdkvod.request.v20170321.CreateUploadVideoRequest import CreateUploadVideoRequest

from .base import AliOssBase


class AliOssVodTicket(AliOssBase):
    """ 阿里云OSS点播功能 """

    CATEGORY_ID = 1000096308

    def __init__(self, title, filename, **kwargs):
        self._title = title
        self._filename = filename
        self._request = CreateUploadVideoRequest()

        super(AliOssVodTicket, self).__init__(**kwargs)

    def _add_ticket_body(self):
        self._request.set_accept_format(self.ACCEPT_FORMAT)
        self._request.set_Title(self._title)
        self._request.set_FileName(self._filename)
        self._request.set_CateId(self.CATEGORY_ID)

    def get_upload_ticket(self):
        """ 获取凭证 """
        self._add_ticket_body()

        response = self._client.do_action_with_exception(self._request)
        ticket_data = json.loads(str(response, encoding='utf-8'))
        return ticket_data



