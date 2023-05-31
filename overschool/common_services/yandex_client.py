from datetime import datetime

import yadisk

from overschool import settings

y = yadisk.YaDisk(token=settings.YANDEX_TOKEN)


def upload_file(uploaded_file, base_lesson):
    course = base_lesson.section.course
    course_id = course.course_id
    # school_id = course.school.school_id
    file_path = "/{}_course/{}_lesson/{}_{}".format(
        course_id, base_lesson.id, datetime.now(), uploaded_file.name
    )
    # file_path = "/{}_school/{}_course/{}_lesson/{}_{}".format(school_id, course_id, base_lesson.id, datetime.now(), uploaded_file.name)
    try:
        y.upload(uploaded_file, file_path)
    except yadisk.exceptions.ConflictError:
        # if y.exists("/{}_school/{}_course".format(school_id, course_id)):
        #     y.mkdir("/{}_school/{}_course/{}_lesson".format(school_id, course_id, base_lesson.id))
        # elif y.exists("/{}_school".format(school_id)):
        #     y.mkdir("/{}_school/{}_course".format(school_id, course_id))
        #     y.mkdir("/{}_school/{}_course/{}_lesson".format(school_id, course_id, base_lesson.id))
        # else:
        #     y.mkdir("/{}_school".format(school_id))
        #     y.mkdir("/{}_school/{}_course".format(school_id, course_id))
        #     y.mkdir("/{}_school/{}_course/{}_lesson".format(school_id, course_id, base_lesson.id))

        if y.exists("/{}_course".format(course_id)):
            y.mkdir("/{}_course/{}_lesson".format(course_id, base_lesson.id))
        else:
            y.mkdir("/{}_course".format(course_id))
            y.mkdir("/{}_course/{}_lesson".format(course_id, base_lesson.id))
        y.upload(uploaded_file, file_path)
    return file_path


def upload_school_image(uploaded_image, school_id):
    file_path = "/{}_school/school_data/images/{}_{}".format(
        school_id, datetime.now(), uploaded_image.name
    )
    try:
        y.upload(uploaded_image, file_path)
    except yadisk.exceptions.ConflictError:
        if y.exists("/{}_school/school_data".format(school_id)):
            y.mkdir("/{}_school/school_data/images".format(school_id))
        elif y.exists("/{}_school".format(school_id)):
            y.mkdir("/{}_school/school_data".format(school_id))
            y.mkdir("/{}_school/school_data/images".format(school_id))
        else:
            y.mkdir("/{}_school".format(school_id))
            y.mkdir("/{}_school/school_data".format(school_id))
            y.mkdir("/{}_school/school_data/images".format(school_id))
        y.upload(uploaded_image, file_path)
    return file_path


def remove_from_yandex(file_path):
    try:
        y.remove(file_path, permanently=True)
        return "Success"
    except yadisk.exceptions.PathNotFoundError:
        return "Error"


def get_yandex_link(file_path):
    link = y.get_download_link(file_path)
    return link
