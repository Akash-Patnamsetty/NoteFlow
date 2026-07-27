from django.urls import path
from home.views import *
urlpatterns = [
 path("register/", register, name="register"),
 path("login/", logins, name="login"),
 path("",home,name="home"),
 path("dashboard/",dashboard,name="dashboard"),
 path("settings/",settings,name='settings'),
 path("tasks/",tasks,name="tasks"),
 path("addnote/",addnote,name="addnote"),
 path('signout/',signout,name="signout")
 
]
