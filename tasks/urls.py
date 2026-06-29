from django.urls import path

from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='list'),
    path('create/', views.task_create, name='create'),
    path('<int:pk>/', views.task_detail, name='detail'),
    path('<int:pk>/edit/', views.task_update, name='update'),
    path('<int:pk>/delete/', views.task_delete, name='delete'),
    path('<int:pk>/status/', views.task_update_status, name='update_status'),
    path('<int:pk>/priority/', views.task_update_priority, name='update_priority'),

    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]
