import logging

from datetime import datetime, timedelta, timezone

from dataimport.calculate import elo_for_courses as process_elo, rollback_to_date
from dataimport.helga_webres import download_courses as helga_download_courses
from dataimport.helga_webres import import_courses_in_db as helga_import_courses
from elo.models import Runner,Course
from elo.fields import CourseStatus

logger = logging.getLogger(__name__)


def download_courses():
    logger.info("download courses")
    helga_download_courses()
    
def import_courses():
    logger.info("import courses")
    helga_import_courses()



def rerun_all():
    download_courses()
    import_courses()
    Runner.objects.all().update(elo=1600.00, number_of_valid_courses=0)
    Course.objects.all().update(status=CourseStatus.TOPROCESS)
    process_elo()

def last_two_weeks_to_download():
    logger.info("Last two weeks to download")
    the_date = datetime.now(timezone.utc) - timedelta(weeks=2)
    last_courses = Course.objects.filter(date__gte=the_date.isoformat(sep=" ", timespec="seconds"))
    if last_courses.count() > 1:
        last_courses.update(status=CourseStatus.TODOWNLOAD)

def reverse_courses_toimport():
    logger.info("reverse courses toimport")
    oldest_toimport_course = Course.objects.filter(status=CourseStatus.TOIMPORT).order_by("date").first()
    if oldest_toimport_course is not None:
        the_date = oldest_toimport_course.date.isoformat(sep=" ", timespec="seconds")
        last_courses = Course.objects.filter(date__gte=the_date)
        last_courses.update(status=CourseStatus.TOIMPORT)
        rollback_to_date(oldest_toimport_course.date)


def normal_run():
    last_two_weeks_to_download()
    download_courses()
    reverse_courses_toimport()
    import_courses()
    process_elo()

if __name__ == "__main__":
    rerun_all()