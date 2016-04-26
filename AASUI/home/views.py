from django.shortcuts import render,HttpResponse,render_to_response,HttpResponseRedirect
from django.contrib import auth
from home.models import  Teacher , Attendance , Student ,Log ,ImageData

from digitalEye import Objects as obj
from digitalEye import Recog as rec
import sys
import cv2
import os
import datetime
import time
from django.views.decorators.csrf import csrf_exempt

import redis
import pickle
__location__ = os.path.realpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

def cpath(fpath):
    return os.path.join(__location__, fpath)
def onTeacher(request):
      return Teacher.objects.get(emailId=request.session.get('teacher'))

def getStudent(rollNumber):
    return Student.objects.get(rollNumber=rollNumber)

def index(request):
    if request.session.get('teacher',None):
        teacher=onTeacher(request)
        return render(request,'home/home.html',{"user":teacher,'range':range(2010,2222)})
    else:

       return HttpResponseRedirect('/login')



def login(request):
    error=""
    if request.POST:
     data=request.POST
     emailId=data.get('emailId')
     password=data.get('password')
     print emailId,password
     flag=False
     try:
          teacher=Teacher.objects.get(emailId=emailId)
          if teacher.emailId==emailId and teacher.password==password:
               flag=True
               request.session['teacher']=emailId
               return HttpResponseRedirect('/home')
          else:
               flag=False
     except Exception,e:
          error=e
    return render(request,'home/login.html',{"error":error})


def logout(request):
      del request.session['teacher']
      return HttpResponseRedirect('/home')


def help(request):
    return render(request,'home/help.html',{})



def history(request,year=0,month=0,day=0):

    teacher=onTeacher(request)
    attendanceList=Attendance.objects.filter(teacher=teacher)
    return render(request,'home/history.html',{'attendanceList':attendanceList,'user':teacher})


def startcapturing(request):
      path=cpath("/home/haikent/Desktop/fyp/digitalEye/AASUI/media/media/dic.mp4")
      print path
      cap=cv2.VideoCapture(0) #"http://10.42.0.41:8080/video"
      course=request.POST.get('course')
      branch=request.POST.get('branch')
      batch=request.POST.get('batch')
      students=Student.objects.filter(course__iexact=course,branch__iexact=branch,batch__iexact=batch) # __iexact ignore case

      images=[]
      lables=[]
      for student in students:
          for image in student.imagedata_set.all():
              lables.append(int(student.rollNumber))
              img='media/%s' % image
              img=cv2.imread(img)
              img=cv2.resize(img,(600,600),interpolation=cv2.INTER_AREA)
              img=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
              images.append(img)
      print images
      print lables

      recog = rec.Recognizer()
      recog1 = rec.Recognizer()
      recog2 = rec.Recognizer()
      recog.train(images,lables,0)
      recog1.train(images,lables,1)
      recog2.train(images,lables,2)
      face=obj.Face(1.6,5,20,20)
      hk=True
      while(True):
         ret,frame=cap.read()
         if not ret: continue
         cv2.imshow('frame',frame)
         faces=face.getFaces(frame)
         print "No of faces found",len(faces)
         for f in faces:
                simg=cv2.cvtColor(f,cv2.COLOR_BGR2GRAY)
                simg=cv2.resize(simg,(600,600),interpolation=cv2.INTER_AREA)
                a=recog.getLable(simg)
                b=recog1.getLable(simg)
                c=recog2.getLable(simg)
                print "predictedLable:",a,b,c
                if False: #c[1] <  24000
                    cv2.imshow(str(b[0])+":"+str(b[1])+","+str(c[0])+":"+str(c[1]),simg)
                if hk:
                   log=Log()
                   log.text= "predictedLable: %s %s %s" % (a,b,c)
                   log.save()

         if cv2.waitKey(1)& 0xFF==ord('q'):
                 break
      cv2.destroyAllWindows()

      print "complete task"
      return HttpResponse("ho gya")


def handle_uploaded_file(f,name):
    imagePath='media/'+name
    imageSavePath='media/'+imagePath
    with open(imageSavePath, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return imagePath

def mupload(request):
    images=request.FILES.getlist('file')
    for image in images:
          imagePath=handle_uploaded_file(image,image.name)
          rollNumber=image.name.split(".")[0]  # demo 12103074.9 -> 12103074
          imgd=ImageData()
          imgd.image=imagePath
          student=getStudent(rollNumber)
          if student :
              imgd.student = student
              imgd.save()
          else:
             print "error rollNumber:",rollNumber
    return HttpResponse("done")

def domore(request):
    return render(request,'home/domore.html',{'user': onTeacher(request)})




def webcamtest(request):
        return render(request,'home/testwebcam.html',{'user': onTeacher(request)})



#this function take Inmemoryuploadedfile and save into temp file read as openCV image and return then del tem
def get_uploaded_image(f,name):
    imagePath='media/'+name
    imageSavePath='media/'+imagePath
    with open(imageSavePath, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    img=cv2.imread(imageSavePath)
    os.remove(imageSavePath)
    return img


#this function get webcam.upload using FILES upload method
#csrf_exempt remove csrf missing server side error

@csrf_exempt
def webcamimage(request):
       teacher=onTeacher(request)
       if request.FILES:
           image=request.FILES.get('webcam')
           image=get_uploaded_image(image,teacher.emailId)
           
       return HttpResponse("done")
