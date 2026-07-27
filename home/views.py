from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login ,logout
from django.contrib.auth.decorators import login_required
from .models import Profiles

# Create your views here.


def register(request):
 if request.method == "POST":
    email=request.POST.get("email")
    password=request.POST.get("password")
    full_name=request.POST.get("full_name")
    confirm_password=request.POST.get("confirm_password")
    username=request.POST.get("username")#optional 
    if password==confirm_password:
        print(email,password)
        user=User.objects.create_user(username=email,password=password)
        Profiles.objects.create(user=user,fullname=full_name,username=username if username else "")
        login(request, user)
        return render(request,'dashboard.html')
    else:   
      print(email,password)
      return render(request,'siginup.html',{'error':'conform password is missmatch'})
 return render(request, 'siginup.html')


def logins(request):
  if request.method == "POST":
    email=request.POST.get("username")
    password=request.POST.get("password")
    print(email,password)
    us=authenticate(request, username=email, password=password)
    if us:
      login(request, us)
      return redirect('dashboard')
    else:
      return  redirect("register")
  return render(request, 'login.html')

@login_required
def dashboard(request):
  return render(request,"dashboard.html")


def home(request):
  
  return render(request,"home_page.html")

@login_required
def settings(request):
  return render(request,"settings.html")

@login_required
def tasks(request):
  return render(request,"tasks.html")

@login_required
def addnote(request):
  return render(request,"addnote.html")


@login_required
def signout(request):
  logout(request)
  return redirect("login")
