from django.db import models

# Create your models here.
class Runner(models.Model):
    fullname = models.CharField()
    helga_id = models.IntegerField(null=True)
    elo = models.DecimalField(default=1500.0, max_digits=7, decimal_places=2)

    def __str__(self):
        return f"Name={self.fullname}\telo={self.elo}"

class Course(models.Model):
    name = models.CharField()
    date = models.DateTimeField()
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
    ranking = models.ForeignKey(Ranking, on_delete=models.CASCADE)
    runner = models.ForeignKey(Runner, on_delete=models.CASCADE)
    place = models.IntegerField()
    time = models.TimeField()
    status = models.CharField()
    new_elo = models.DecimalField(default=1500.0, max_digits=7, decimal_places=2)

    def __str__(self):
        return f"{self.place} - {self.time} - {self.status} - {self.new_elo}"
