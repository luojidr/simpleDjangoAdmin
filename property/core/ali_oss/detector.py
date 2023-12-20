import uuid
import json
from datetime import datetime

from aliyunsdkgreen.request.v20180509 import TextScanRequest
from aliyunsdkgreen.request.v20180509 import ImageSyncScanRequest
from aliyunsdkgreenextension.request.extension import ClientUploader
from aliyunsdkgreenextension.request.extension import HttpContentHelper

from .base import AliOssBase

__all__ = ["AliScanDetector"]


class AliScanDetector(AliOssBase):
    """ 阿里文本、图片、文件等的审核
    (1): 提交图片同步检测任务，对图片进行多个风险场景的识别，
         包括色情、暴恐涉政、广告、二维码、不良场景、Logo（商标台标）识别
    """

    def _get_request(self, req_type=2):
        """
        :param req_type: 1 文件，2 图片
        :return:
        """
        request = None

        if req_type == 1:
            request = TextScanRequest.TextScanRequest()

        if req_type == 2:
            request = ImageSyncScanRequest.ImageSyncScanRequest()

        if req_type is None:
            raise ValueError("阿里云扫描 request 不合法!")

        request.set_accept_format('JSON')
        return request

    def detect_text(self, content):
        """ 文本反垃圾审核
        https://help.aliyun.com/document_detail/53436.html?spm=a2c4g.11186623.6.754.55362542wxRL4C
        """
        request = self._get_request(req_type=1)
        task = dict(
            dataId=str(uuid.uuid1()), content=content,
            time=datetime.now().microsecond
        )
        # 文本反垃圾检测场景的场景参数是 antispam
        request.set_content(HttpContentHelper.toValue({"tasks": [task], "scenes": ["antispam"]}))
        return self._do_action(request)

    def detect_image(self, image_bytes):
        """ 图片反垃圾审核
        https://help.aliyun.com/document_detail/53432.html?spm=a2c4g.11186623.6.752.57567981axKU0M
        """
        request = self._get_request(req_type=2)
        uploader = ClientUploader.getImageClientUploader(self._client)
        url = uploader.uploadBytes(image_bytes)
        task = dict(dataId=str(uuid.uuid1()), url=url)

        request.set_content(HttpContentHelper.toValue({"tasks": [task], "scenes": ["porn"]}))
        return self._do_action(request)

    def _do_action(self, request):
        is_valid = False

        response = self._client.do_action_with_exception(request)
        result = json.loads(response)

        if 200 == result["code"]:
            task_results = result["data"]
            for task_result in task_results:
                if 200 == task_result["code"]:
                    scene_results = task_result["results"]
                    for scene_result in scene_results:
                        scene = scene_result["scene"]
                        is_valid = scene_result["suggestion"] == "pass"

                        return is_valid

        return is_valid

