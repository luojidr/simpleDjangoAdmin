import json
import logging

from django.apps import apps
from django.conf import settings
from django.db import DatabaseError

logger = logging.getLogger("django")


class DatabaseRouter(object):
    """ MySQL database replication arch or single.
    Replication:
        First you hane to set database config in DATABASES, it must have `app_name` or `default` as db alias,
        in addition set `app_name_slave` or `default_slave` as db slave alias

        eg:
            DATABASES = {
                'default': {...},
                'default_slave': {...},

                'user': {...},
                'user_slave': {...},
            }

    # Sharding:
    #     Evenly write data to DB by unique keys, also read data by unique keys.
    #
    #     eg:
    #         DATABASES = {
    #             'user_001': {...},
    #             'user_002': {...},
    #             'user_003': {...},
    #         }
    """

    APPS = apps
    DEFAULT_ALIAS = "default"
    DEFAULT_SLAVE_ALIAS = "_slave"
    DATABASES_MAPPING = settings.DATABASES
    NO_LOGGING_APP_LABEL = ["silk", "django_celery_beat"]

    def db_for_write(self, model, **hints):
        """ Write Database """
        app_label = model._meta.app_label
        self._check_app_to_db_config(app_label)

        if settings.DEBUG and app_label not in self.NO_LOGGING_APP_LABEL:
            logger.info("DatabaseRouter.db_for_write() => model use db: %s, app_label: %s\n"
                        % (self.apps_router_mapping[app_label], app_label)
                        )

        return self.apps_router_mapping[app_label]

    def db_for_read(self, model, **hints):
        """ Read Database """
        app_label = model._meta.app_label
        self._check_app_to_db_config(app_label)

        app_label_slave = app_label + self.DEFAULT_SLAVE_ALIAS
        self._check_app_to_db_config(app_label_slave)

        db_slave = self.apps_router_mapping[app_label] + self.DEFAULT_SLAVE_ALIAS

        if settings.DEBUG and app_label not in self.NO_LOGGING_APP_LABEL:
            logger.info("DatabaseRouter.db_for_read() => model use db: %s, app_label: %s\n" % (db_slave, app_label))

        return db_slave

    def allow_relation(self, obj1, obj2, **hint):
        """ Object whether to run the association operation """
        return None

    def allow_syncdb(self, db, model):
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        """ Make sure the auth app only appears in the 'auth_db' database."""
        migrate_log_kwargs = dict(db=db, app_label=app_label, model=model, hints=hints)
        migrate_log_msg = "DatabaseRouter.allow_migrate() app_label [{include}] `settings.DATABASES` " \
                          "=> db:{db}, app_label:{app_label}, model:{model}, hints: {hints}"

        if app_label in self.apps_router_mapping:
            new_ab_alias = self.apps_router_mapping[app_label]
            migrate_log_msg += "new db: {new_ab_alias}"
            migrate_log_kwargs.update(new_ab_alias=new_ab_alias, include="IN")

            if settings.DEBUG:
                migrate_log_msg.format(**migrate_log_kwargs)

            return db == self.apps_router_mapping[app_label]
        else:
            migrate_log_kwargs.update(include="NOT IN")

            if settings.DEBUG:
                migrate_log_msg.format(**migrate_log_kwargs)

        return None

    def _check_app_to_db_config(self, app_label):
        """ Check whether app_label is in settings.DATABASES configuration """
        if app_label not in self.apps_router_mapping:
            raise DatabaseError("`DATABASES` don't contain ['%s': {...}] config" % app_label)

    @property
    def apps_router_mapping(self):
        """ Get each app relation to model, default is `default` alias
        apps_router_mapping:
            {
                'app1': 'default',                  # 'app1'
                'app1_slave': 'default_slave',      # 'app1_slave'
                ....
            }
        """
        _apps_router_mapping = getattr(self, "_apps_router_mapping", {})

        if _apps_router_mapping:
            return _apps_router_mapping

        slave_alias = self.DEFAULT_SLAVE_ALIAS
        app_name_list = self.APPS.app_configs.keys()

        for app_name in app_name_list:
            if app_name not in self.DATABASES_MAPPING:
                # Default db alias
                _apps_router_mapping[app_name] = self.DEFAULT_ALIAS
                _apps_router_mapping[app_name + slave_alias] = self.DEFAULT_ALIAS + slave_alias
            else:
                # Using app name as db alias
                _apps_router_mapping[app_name] = app_name
                _apps_router_mapping[app_name + slave_alias] = app_name + slave_alias

        setattr(self, "_apps_router_mapping", _apps_router_mapping)
        return _apps_router_mapping

