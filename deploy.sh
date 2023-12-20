#!/bin/bash

if [[ ! -d "/data/apps" ]]; then
    echo "目录: /data/apps 不存在, 准备创建"
    sudo mkdir -p /data/apps
fi

cd /data/apps
echo "当前目录:"
echo `pwd`

if [[ ! -d "property_dp" ]]; then
    echo "property_dp 工程不存在，下载工程"
    sudo git clone
fi

cd /data/apps/property

echo "开始更新代码"
sudo git pull origin master


echo "开始更新包"
#sudo /home/.virtualenv/property_dp_running/bin/pip3 install -r requirements.txt -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com
#sudo /home/.virtualenv/property_dp_running/bin/pip3 install -r requirements/prod.txt -i https://pypi.python.com/simple/ --trusted-host pypi.python.com
if [[ "${APP_ENV}" -eq "DEV" ]]; then
  echo "************* Circle 开始加载 [${APP_ENV}] 包 *********************"
  sudo /home/.virtualenv/property_dp_running/bin/pip3 install -r requirements/dev.txt
else
  echo "************* Circle 开始加载 [${APP_ENV}] 包 *********************"
  sudo /home/.virtualenv/property_dp_running/bin/pip3 install -r requirements/prod.txt
fi

if [[ ! -d "/var/property_dp/" ]]; then
    sudo mkdir -p /var/property/
fi

if [[ ! -d "/data/logs/property_dp/" ]]; then
   sudo  mkdir -p /data/logs/property/
fi

echo "开始kill property_dp_uwsgi 进程"
while true
do
    ps auxww | grep 'property_dp_uwsgi.ini' | awk '{print $2}' | xargs sudo kill -9
    kill_result="$(ps -ef|grep 'property_dp_uwsgi.ini' | wc -l)"

    echo "星圈停止进程结果 kill_result: ${kill_result}"

    if [[ ${kill_result} -eq 1 ]]; then
        echo "kill property_dp_uwsgi 进程 OK"
        break
    else
        echo "kill property_dp_uwsgi 进程 Fail, 继续 Kill..............."
    fi
done

# Load Envirment Variable
source /home/.virtualenv/.setenv_property_dp.sh
echo "星圈项目运行环境：${APP_ENV}"

while true
do
    property_dp_uwsgi_cnt="$(ps -ef|grep 'property_dp_uwsgi.ini' | wc -l)"

    echo "${property_dp_uwsgi_cnt}"

    # shellcheck disable=SC2071
    if [[ ${property_dp_uwsgi_cnt} -gt 1 ]];
    then
        echo "************* Circle 后台服务已启动 Finished *********************"
        break
    else
        echo "------------- 即将开启 Circle 后台服务 Start --------------------"
        # not use sudo, or export variable don't get
        /home/.virtualenv/property_dp_running/bin/uwsgi --ini /data/apps/property/property_dp_uwsgi.ini
        # /home/.virtualenv/property_dp_running/bin/uwsgi --gevent 100 --gevent-monkey-patch --ini /data/apps/property/property_dp_uwsgi.ini
    fi
done

