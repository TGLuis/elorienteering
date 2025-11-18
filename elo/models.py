from django.db import models

class PageView(models.Model):
    path = models.CharField(max_length=255, unique=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.path} - {self.count} views"


class Runner(models.Model):
    fullname = models.CharField()
    helga_id = models.IntegerField(null=True, db_index=True)
    elo = models.DecimalField(default=1500.0, max_digits=7, decimal_places=2)
    active = models.BooleanField(default=True, db_index=True)

    def __str__(self):
        return f"Name={self.fullname}\telo={self.elo}\thelga_id={self.helga_id}"


class Course(models.Model):
    name = models.CharField()
    date = models.DateTimeField(db_index=True)
    helga_id = models.IntegerField(default=0)
    location = models.CharField()
    status = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.name} - {self.date} - {self.location}"


class Ranking(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField()
    distance = models.IntegerField()
    climb = models.IntegerField(null=True)

    def __str__(self):
        return f"{self.name} - {self.distance}m - {self.climb}m"


class Result(models.Model):
    date = models.DateTimeField(db_index=True)
    ranking = models.ForeignKey(Ranking, on_delete=models.CASCADE)
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE)
    place = models.IntegerField()
    time = models.TimeField(null=True)
    status = models.CharField()
    new_elo = models.DecimalField(default=1500.0, max_digits=7, decimal_places=2)

    def __str__(self):
        return f"{self.place} - {self.time} - {self.status} - {self.new_elo}"
