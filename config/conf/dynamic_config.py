from collections import OrderedDict

CONSTANCE_IGNORE_ADMIN_VERSION_CHECK = True

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'

CONSTANCE_ADDITIONAL_FIELDS = {
    # 定义一个选项字段，在 admin 页面上将使用 Select 组件来修改它的值
    'option_field': [
        'django.forms.fields.ChoiceField',
        {
            'widget': 'django.forms.Select',
            'choices': (
                            ('option1', 'option1'),
                            ('option2', 'option2'),
                            ('option3', 'option3'),
                        )
        }
    ],

    # 定义一个文件字段，它的值是不带路径的文件名，后面可以添加 upload_to 参数指定上传路径
    'file_field': ['django.forms.FileField'],
}

EMPTY_FILE = 'empty'

CONSTANCE_CONFIG = OrderedDict({
    'option': ('option1', '选项', 'option_field'),
    'tags': ('tag1,tag2', '标签'),
    'threshold': (100, '阈值'),
    'doc': (EMPTY_FILE, '文档', 'file_field'),
})
