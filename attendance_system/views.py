import time
from django.contrib import messages
from django.shortcuts import render, redirect
from attendance_system.models import Student
from attendance_system.recognizer import recognizer


def home(request):
    if request.method == 'POST':
        id = request.POST['id']
        name = request.POST['name']

        try:
            Student.objects.get(student_id=id, name=name)
        except:
            messages.error(request, "学号姓名不匹配，请检查并重新输入；或联系管理员添加信息")
            return render(request, 'home.html', {"attendances": Student.objects.all()})
        if Student.objects.filter(student_id=id, status='已签到').count() != 0:
            messages.error(request, "你已经签到，请勿重复签到！")
            return redirect('home')
        else:
            names = recognizer()
            # names = recognizer2() # 调包：face_recognition
            for student in Student.objects.all():
                if str(Student.objects.get(name=student.name).profile_path).split("/")[1].split(".")[0] in names:
                    if Student.objects.get(name=student.name).name == name:
                        Student.objects.filter(student_id=id).update(status='已签到',
                                                                     time=time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                        time.localtime()))
                        messages.success(request, "签到成功!")
                        return render(request, 'home.html', {"attendances": Student.objects.all()})
                    else:
                        messages.error(request, "签到失败，人脸不匹配!")
                        return render(request, 'home.html', {"attendances": Student.objects.all()})
    return render(request, 'home.html', {"attendances": Student.objects.all()})
