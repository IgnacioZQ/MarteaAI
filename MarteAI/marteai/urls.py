from django.urls import path, include
from rest_framework.documentation import include_docs_urls
from rest_framework import routers
from marteai import views

router = routers.DefaultRouter()
router.register(r"feedbacks", views.FeedbackView, "feedbacks")

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path('docs/', include_docs_urls(title='MarteAI API')),
    path('cargar_analizar_datos/', views.cargar_analizar_datos, name='cargar_analizar_datos'),
]
