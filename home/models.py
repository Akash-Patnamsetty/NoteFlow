from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profiles(models.Model):
 user=models.OneToOneField(User,on_delete=models.CASCADE)
 fullname=models.CharField(max_length=100)
 username = models.CharField(max_length=100, blank=True, default="")
 def __str__(self):
  return self.user.username
 
 

 
 