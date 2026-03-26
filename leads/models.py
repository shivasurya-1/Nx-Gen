from django.db import models

class  ContactUs(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    message = models.TextField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class DemoSchedule(models.Model):

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    course = models.CharField(max_length=200)


    message = models.TextField(max_length=500, blank=True)


    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name