import datetime
from haystack import indexes
from haystack import site

from backtrac.apps.catalog.models import Item

class ItemIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, model_attr='path')

    def prepare_text(self, item):
        return item.path.replace("/", " ")

site.register(Item, ItemIndex)
