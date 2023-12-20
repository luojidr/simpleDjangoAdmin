import os
import re
import pathlib
import logging
import pkgutil
import importlib

from django.conf import settings, ENVIRONMENT_VARIABLE
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger('django')


def autodiscover_task_imports(packages=None, related_name='tasks', task_prefix='task_'):
    """
    :param packages: list of string, eg ['config.tasks', 'config.auto_tasks']
    :param related_name: find directory or package of task
    :param task_prefix: find detail task module

    Automatically discover django app tasks, compatible with the application directory task, as follows:
    Rules:
        (1): Load the directory of `tasks` name first
            tasks/
                task_aaa.py
                task_bbb.py
        (2): application the tasks.py file in the directory
        (3): tasks for the other packages specified
    """
    task_imports = []
    project_name = settings.APP_NAME
    django_settings_module = os.getenv(ENVIRONMENT_VARIABLE)

    if not django_settings_module:
        raise ImproperlyConfigured("DJANGO_SETTINGS_MODULE is wrong, module: %s" % __name__)

    packages = packages() if callable(packages) else packages or ()
    packages_or_apps = list(packages) + settings.INSTALLED_APPS

    for name in packages_or_apps:
        is_app = name in settings.INSTALLED_APPS
        package = importlib.import_module(name)

        file_path = os.path.dirname(os.path.abspath(package.__file__))
        package_name = package.__package__

        for module_info in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            mod_name = module_info.name

            if mod_name == package_name + "." + related_name:
                path = pathlib.Path(file_path)
                parent_parts_list = path.parent.parts

                # Maybe is ['data', 'apps', project_name, project_name, 'tasks', 'task_xxx', ...]
                app_name_cnt = parent_parts_list.count(project_name)
                offset = app_name_cnt - 1 if app_name_cnt > 1 else 0
                app_path_list = list(parent_parts_list[parent_parts_list.index(project_name) + offset:])

                if not module_info.ispkg:
                    task_module_name = mod_name
                    completed_task_path = ".".join(app_path_list + [task_module_name])

                    # Not `project_name` celery task
                    if not completed_task_path.startswith(project_name):
                        continue

                    task_imports.append(completed_task_path)
                    logger.warning("autodiscover_task_imports --->>> Celery task module: %s", completed_task_path)
                else:
                    task_path = path / related_name
                    sub_mod_info_list = list(pkgutil.iter_modules([str(task_path)]))

                    for sub_mod_info in sub_mod_info_list:
                        task_module_name = sub_mod_info.name
                        completed_task_path = ".".join(app_path_list + [mod_name, task_module_name])

                        # Not `project_name` celery task
                        if not completed_task_path.startswith(project_name):
                            continue

                        if not task_module_name.startswith(task_prefix):
                            continue

                        task_imports.append(completed_task_path)
                        logger.warning("autodiscover_task_imports ===>>> Celery task module: %s", completed_task_path)

    logger.warning("======>>>>> The discovery tasks are as below\n")
    return task_imports


def find_task_list_from_py(task_package_path):
    """ Find all tasks by regular expressions, eg:
        >>> @celery_app.task
        >>> def send_msg(**kwargs):
        ...     pass
    """
    task_regex = re.compile(r"(\n|\r\n|\r)"
                            r"^(@celery_app|@app)\.task.*?"
                            r"def\s+(?P<task_name>.*?)\(.*?[*]{0,2}(?P<force_kw>\w*?)\):", re.S | re.M)

    project_name = settings.APP_NAME
    current_path_list = os.path.abspath(__file__).split(os.sep)

    app_name_cnt = current_path_list.count(project_name)
    offset = app_name_cnt - 1 if app_name_cnt > 1 else 0
    project_path_list = current_path_list[:current_path_list.index(project_name) + offset]

    task_path_list = project_path_list + task_package_path.split(".")
    full_task_path = os.sep.join(task_path_list) + '.py'

    with open(full_task_path, encoding="utf-8") as fp:
        code_text = fp.read()
        match_iter = task_regex.finditer(code_text)
        match_task_list = []

        for match in match_iter:
            match_group = match.groupdict()
            force_kw = match_group.get("force_kw")
            task_name = match_group.get("task_name")

            if not force_kw:
                raise ValueError("Task<%s:%s> missed keyword arguments `**kwargs`." % (task_package_path, task_name))

            if task_name:
                match_task_list.append(task_name)

        return match_task_list


def autodiscover_task_list(imports=None, not_import_tasks=None):
    """ Get all the task function names, that Can not be obtained through `__import__(package_name)`
    >>> from celery import current_app
    >>> celery_app.loader.import_default_modules()
    >>> task_list = app.tasks.keys()

    Raise error:
        ImportError: cannot import name 'celery_app' from partially initialized module 'config'(most likely
        due to a circular import)
    """
    complete_task_mapping = {}
    not_import_tasks = not_import_tasks or []
    imports = imports or autodiscover_task_imports() or []

    for task_import_path in imports:
        match_task_list = find_task_list_from_py(task_package_path=task_import_path)
        task_list = complete_task_mapping.setdefault(task_import_path, [])

        for name in match_task_list:
            if name in not_import_tasks:
                logger.warning("Autodiscover Task Name %s:-->> %s <<-- is Skipped", task_import_path, name)
            else:
                task_list.append(dict(task_name=name, complete_name=task_import_path + "." + name))

        if task_list:
            ready_task = ', '.join([item['task_name'] for item in task_list])
            logger.warning("Autodiscover Task Name %s:==> [%s] <== is Ready", task_import_path, ready_task)

    if not complete_task_mapping:
        logger.warning("===>> Serious Warning, Autodiscover tasks is empty <<===")

    return [t_item for t_item_list in complete_task_mapping.values() for t_item in t_item_list]
