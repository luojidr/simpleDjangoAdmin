#!/bin/bash

if [[ ! -d "/data/apps" ]]; then
    echo "目录: /data/apps 不存在, 准备创建"
    sudo mkdir -p /data/apps
fi

cd /data/apps
echo "当前目录:"
echo `pwd`

if [[ ! -d "/data/logs/property_dp/" ]]; then
   sudo  mkdir -p /data/logs/property/
fi

cd /data/apps/property

echo "开始kill celery worker 进程"
while true
do
    ps auxww | grep 'worker -A config.celery' | awk '{print $2}' | xargs sudo kill -9
    kill_result="$(ps -ef|grep 'worker -A config.celery' | wc -l)"

    echo "星圈停止 Worker 进程结果 kill_result: ${kill_result}"

    if [[ ${kill_result} -eq 1 ]]; then
        echo "kill Worker 进程 OK"
        break
    else
        echo "kill Worker 进程 Fail, 继续 Kill..............."
    fi
done


# Load Envirment Variable
source /home/.virtualenv/.setenv_property_dp.sh
echo "Celery运行环境：${APP_ENV}"


while true
do
    property_dp_worker_cnt="$(ps -ef|grep 'worker -A config.celery' | wc -l)"

    echo "${property_dp_worker_cnt}"

    # shellcheck disable=SC2071
    if [[ ${property_dp_worker_cnt} -gt 1 ]];
    then
        echo "************* Circle Worker 后台服务已启动 Finished *********************"
        break
    else
        echo "------------- 即将开启 Fosun-Circle Worker 后台服务 Start --------------------"
        # not use sudo, or export variable don't get
        nohup sudo /home/.virtualenv/property_dp_running/bin/celery worker -A config.celery -l info > /data/logs/property/property_dp_worker.log 2>&1 &
    fi
done