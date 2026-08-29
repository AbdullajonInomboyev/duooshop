from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        from django.contrib import admin
        admin.site.site_header = "GoDostavka — Boshqaruv paneli"
        admin.site.site_title = "GoDostavka"
        admin.site.index_title = "Sotuv va sklad boshqaruvi"
