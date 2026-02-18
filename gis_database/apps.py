from django.apps import AppConfig


class GisDatabaseConfig(AppConfig):
    name = "gis_database"

    def ready(self):
        import gis_database.signals
