from django.db import models

class ItemManager(models.Manager):
    def present(self):
        return self.get_query_set().filter(deleted=False)
    def deleted(self):
        return self.get_query_set().filter(deleted=True)
