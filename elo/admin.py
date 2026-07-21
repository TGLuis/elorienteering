from django.contrib import admin

# Register your models here.
from .models import Runner, Course, Ranking, Result, Entry, Source, Affiliation

admin.site.register(Runner)
admin.site.register(Result)
admin.site.register(Course)
admin.site.register(Ranking)
admin.site.register(Entry)
admin.site.register(Source)
admin.site.register(Affiliation)
