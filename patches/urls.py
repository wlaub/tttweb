from django.urls import path, include

from . import views

app_name = 'patches'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('rss/', views.IndexFeed(), name='rss'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('compare/', views.CompareView.as_view(), name='compare'),
    path('compare/<int:pk>/', views.CompareView.as_view(), name='compare'),
    path('tags/', views.TagView.as_view(), name='tags'),

    path('api-auth/', include('rest_framework.urls')),
    path('api/entries', views.PatchEntryAPIList.as_view(), name='entry-list-api'),
    path('api/entries/<int:pk>', views.PatchEntryAPIDetail.as_view(), name='entry-api'),   

]

