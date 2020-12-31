from django.urls import path

from . import views

app_name = 'patches'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('compare/', views.CompareView.as_view(), name='compare'),
    path('compare/<int:pk>/', views.CompareView.as_view(), name='compare'),
]

