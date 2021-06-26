import time

from django.contrib import admin
from attendance_system.models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    actions = ['clear', 'already']

    def clear(self, request, queryset):
        queryset.update(status='未签到')
        self.message_user(request, '修改成功')

    clear.short_description = '更改为“未签到”'

    def already(self, request, queryset):
        queryset.update(status='已签到', time=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        self.message_user(request, '修改成功')

    already.short_description = '更改为“已签到”'
