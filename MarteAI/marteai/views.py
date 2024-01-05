from django.shortcuts import render
from rest_framework import viewsets
from .serializer import FeedbackSerializer
from .models import Feedback

# Create your views here.

class FeedbackView(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    queryset = Feedback.objects.all()

