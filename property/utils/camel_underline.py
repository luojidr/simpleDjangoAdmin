""" 本模块解决变量名驼峰与下划线的转换 """

import re


def camel2underline(camel_var_name):
    """ 驼峰转下划线 """
    
    pattern = re.compile(r'([a-z]|\d)([A-Z])')
    underline_var_name = re.sub(pattern, r'\1_\2', camel_var_name).lower()
    return underline_var_name


def underline2camel(underline_var_name):
    """ 下划线转驼峰 """

    camel_var_name = re.sub(r'(_\w)', lambda x: x.group(1)[1].upper(), underline_var_name)
    return camel_var_name


def underline_dict(camel_params):
    """ 可嵌套将驼峰字典或驼峰列表转为下划线 """

    underline_params = camel_params

    if isinstance(camel_params, dict):
        underline_params = {}
        for k, v in camel_params.items():
            underline_params[camel2underline(k)] = underline_dict(camel_params[k])

    elif isinstance(camel_params, list):
        underline_params = []
        for param in camel_params:
            underline_params.append(underline_dict(param))

    return underline_params


def camel_dict(underline_params):
    """ 可嵌套将下划线字典或下划线列表转为驼峰  """
    
    camel_params = underline_params

    if isinstance(underline_params, dict):
        camel_params = {}
        for k, v in underline_params.items():
            camel_params[underline2camel(k)] = camel_dict(underline_params[k])

    elif isinstance(underline_params, list):
        camel_params = []
        for param in underline_params:
            camel_params.append(camel_dict(param))

    return camel_params


if __name__ == "__main__":
    print(camel2underline("Abcd_Edf_"))
    print(underline2camel("abcd_edf_"))
    print(underline_dict(
        {
            "weChat": "WoDe",
            "aliYun": {
                "yunConsole": "SMS"
            }
        }
    ))

    print(camel_dict({'we_chat': 'WoDeAbcdFg', 'ali_yun': {'yun_console': 'SMS'}}))


