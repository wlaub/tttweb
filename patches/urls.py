from django.urls import path, include

from rest_framework.routers import DefaultRouter

from . import views

app_name = 'patches'


api_router = DefaultRouter()
api_router.register('entries', views.PatchEntryAPIVS)
api_router.register('authors', views.PatchAuthorAPIVS)
api_router.register('images', views.PatchImageAPIVS)
api_router.register('attachments', views.PatchAttachAPIVS)
api_router.register('tags', views.PatchTagAPIVS)

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('rss/', views.IndexFeed(), name='rss'),
    path('<int:pk>/', views.DetailView.as_view(), name='detail'),
    path('compare/', views.CompareView.as_view(), name='compare'),
    path('compare/<int:pk>/', views.CompareView.as_view(), name='compare'),
    path('tags/', views.TagView.as_view(), name='tags'),

    path('api-auth/', include('rest_framework.urls')),
    path('api/', include(api_router.urls)),


]

