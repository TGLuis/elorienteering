from django.db import models

class SourceType(models.IntegerChoices):
    UNKNOWN = 0, "unknown"
    HELGA_WEBRES = 1, "helga webres"
    LIVERESULT_SE = 2, "liveresults.se"
    FFCO_CN = 3, "ffco cn"
    HELGA_START = 4, "helga start"

class CourseType(models.IntegerChoices):
    UNKNOWN = 0, "unknown"
    FOOTO = 1, "foot o"
    MTBO = 2, "mtb o"
    SKIO = 3, "ski o"

class CourseSubType(models.IntegerChoices):
    UNKNOWN = 0, "unknown"
    LONG = 1, "LD"
    MIDDLE = 2, "MD"
    SPRINT = 3, "sprint"

class CourseStatus(models.IntegerChoices):
    # Status of a course should go as following
    # "non existing in db" --imported--> TOPROCESS -> DONE
    # If it already exists in the DB it can go to a previous step of the workflow:
    # TODOWNLOAD --> TOIMPORT --> TOPROCESS --> DONE
    UNKNOWN = 0, "unknown"
    TODOWNLOAD = 1, "to download"
    TOIMPORT = 2, "to import"
    TOPROCESS = 3, "to process"
    FUTURE = 9, "future course" # Only there for prediction of a course
    DONE = 10, "done"
