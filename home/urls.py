from django.urls import path
from home.views import *
from . import views
urlpatterns = [
 path("register/", register, name="register"),
 path("login/", logins, name="login"),
 path("",home,name="home"),
 path("dashboard/",dashboard,name="dashboard"),
 path("settings/",settings,name='settings'),
#  path("tasks/",tasks,name="tasks"),
 # path("addnote/",addnote,name="addnote"),
 path("addnote/", views.addnote, name="addnote"),
 path("view/<int:note_id>/", views.view_note, name="view_note"),
 
    # Edit existing note (GET renders page pre-loaded, POST saves updates)
 path("addnote/<int:note_id>/", views.addnote, name="edit_note"),
 
    # AJAX helpers
 path("note/<int:note_id>/", views.get_note, name="get_note"),
 path("note/<int:note_id>/share/", views.toggle_share, name="toggle_share"),
 path("note/<int:note_id>/pin/", views.toggle_pin, name="toggle_pin"),
 path("note/<int:note_id>/delete/", views.delete_note, name="delete_note"),
 
    # Public read-only shared note
 path("n/<uuid:token>/", views.shared_note_view, name="shared_note"),
 path('signout/',signout,name="signout")
 
]
