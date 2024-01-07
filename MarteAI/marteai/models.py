from django.db import models

from django.db import models

class Feedback(models.Model):
    nombre = models.CharField(max_length=255, blank=True, null=True)
    apellido = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()


