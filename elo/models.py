from django.db import models
from django_enum import EnumField
from elo.utils import get_flag_from_nationality
from elo.fields import Source, CourseType, CourseSubType, CourseStatus

class PageView(models.Model):
    path = models.CharField(max_length=255, unique=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.path} - {self.count} views"


class Runner(models.Model):
    fullname = models.CharField(db_index=True)
    helga_id = models.IntegerField(null=True, db_index=True)
    elo = models.DecimalField(default=1600.0, max_digits=7, decimal_places=2, db_index=True)
    number_of_valid_courses = models.PositiveIntegerField(default=0, db_index=True)
    sex = models.CharField(default="", max_length=1) # TODO replace with enum
    abso = models.BooleanField(default=False, db_index=True)
    fede = models.CharField(default="")
    club = models.CharField(default="")
    nationality = models.CharField(default="")
    category = models.CharField(default="", max_length=5, db_index=True) # TODO replace with only age ?
    active = models.BooleanField(default=True, db_index=True)

    def flag_emoji(self):
        return get_flag_from_nationality(self.nationality)

    def __str__(self):
        return f"Name={self.fullname}\telo={self.elo}\thelga_id={self.helga_id}\tvalid-results={self.number_of_valid_courses}"


class Course(models.Model):
    name = models.CharField()
    date = models.DateTimeField(db_index=True)
    source_id = models.IntegerField(default=0)
    location = models.CharField()
    status = EnumField(CourseStatus, default=CourseStatus.UNKNOWN)
    source = EnumField(Source, default=Source.UNKNOWN)
    type = EnumField(CourseType, default=CourseType.UNKNOWN)
    subtype = EnumField(CourseSubType, default=CourseSubType.UNKNOWN)

    def get_year(self):
        return self.date.year

    def __str__(self):
        return f"{self.source.name} - {self.name} - {self.date} - {self.location} - {self.type.name} - {self.subtype.name}"


class Ranking(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField()
    distance = models.IntegerField()
    climb = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.name} - {self.distance}m - {self.climb}m"


class Entry(models.Model):
    ranking = models.ForeignKey(Ranking, on_delete=models.CASCADE)
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE)
    starttime = models.TimeField(null=True)
    startnumber = models.PositiveIntegerField(default=0)


class Result(models.Model):
    date = models.DateTimeField(db_index=True)
    ranking = models.ForeignKey(Ranking, on_delete=models.CASCADE)
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE)
    place = models.IntegerField()
    time = models.TimeField(null=True)
    status = models.CharField()
    elo_diff = models.DecimalField(default=0.00, max_digits=7, decimal_places=2)
    new_elo = models.DecimalField(default=0.0, max_digits=7, decimal_places=2)
    startnumber = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.place} - {self.time} - {self.status} - {self.elo_diff} - {self.new_elo}"
