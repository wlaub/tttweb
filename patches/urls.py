from django.urls import path

from . import views

app_name = 'patches'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:patch_id>/', views.entry, name='entry')
]

