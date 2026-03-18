from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('lost/', views.lost_items_list, name='lost_items'),
    path('lost/report/', views.report_lost, name='report_lost'),
    path('lost/<int:pk>/', views.lost_item_detail, name='lost_item_detail'),
    path('found/', views.found_items_list, name='found_items'),
    path('found/report/', views.report_found, name='report_found'),
    path('found/<int:pk>/', views.found_item_detail, name='found_item_detail'),
    path('my-items/', views.my_items, name='my_items'),
    path('notifications/', views.notifications, name='notifications'),
    path('api/unread-count/', views.unread_count, name='unread_count'),
    # Admin panel
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/matches/', views.admin_matches, name='admin_matches'),
    path('admin-panel/matches/create/', views.create_manual_match, name='create_manual_match'),
    path('admin-panel/matches/<int:pk>/', views.match_detail, name='match_detail'),
    path('admin-panel/matches/<int:pk>/approve/', views.approve_match, name='approve_match'),
    path('admin-panel/matches/<int:pk>/reject/', views.reject_match, name='reject_match'),
    path('admin-panel/matches/<int:pk>/complete/', views.complete_match, name='complete_match'),
]
