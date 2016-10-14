# import datetime
# from django.conf import settings
# from haystack import indexes
# from geocamUtil.loader import LazyGetModelByName
# 
# Note = LazyGetModelByName(getattr(settings, 'XGDS_NOTES_NOTE_MODEL'))
# 
# 
# class NoteIndex(indexes.SearchIndex, indexes.Indexable):
#     text = indexes.CharField(document=True, use_template=False, model_attr='content')
# 
#     def get_model(self):
#         return Note.get()
# 
#     def index_queryset(self, using=None):
#         """Used when the entire index for model is updated."""
#         return self.get_model().objects.filter(event_time__lte=datetime.datetime.now())