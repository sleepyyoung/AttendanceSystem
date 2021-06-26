from django.db import models


def student_directory_path(instance, filename):
    name, ext = filename.split(".")
    filename = name + '.' + ext
    return 'student_images/{}'.format(filename)


class Student(models.Model):
    STATUS = (('未签到', '未签到'), ('已签到', '已签到'))

    student_id = models.CharField(max_length=100, null=False, blank=True, unique=True, primary_key=True)
    name = models.CharField(max_length=100, null=False, blank=True)
    time = models.DateTimeField(auto_now=True, null=True)
    status = models.CharField(max_length=100, default='未签到', choices=STATUS)
    profile_path = models.ImageField(upload_to=student_directory_path, null=False, blank=True)

    def __str__(self):
        return str(self.student_id + " - " + self.name + " - " + self.status + (
            " - 签到时间: " + " " + str(self.time) if self.status == "已签到" else ""))
