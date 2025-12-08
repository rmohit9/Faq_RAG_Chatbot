from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('chat/', views.chat, name='chat'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    path('admin_dashboard/bot_configurations/', views.bot_config_manage, name='bot_config_manage'),
    path('admin_dashboard/faq_training/', views.faq_training, name='faq_training'),
    path('admin_dashboard/faq_training/edit/<int:pk>/', views.edit_faq, name='edit_faq'),
    path('admin_dashboard/faq_training/delete/<int:pk>/', views.delete_faq, name='delete_faq'),
    path('admin_dashboard/user_management/', views.user_management, name='user_management'),
    path('admin_dashboard/user_management/<int:user_id>/chat_logs/', views.user_chat_logs, name='user_chat_logs'),
    path('admin_dashboard/analytics/', views.analytics, name='analytics'),
    path('api/analytics/', views.analytics_api, name='analytics_api'),
    path('api/admin_dashboard/', views.admin_dashboard_api, name='admin_dashboard_api'),
    path('delete_history/', views.delete_history, name='delete_history'),
    path('api/user_chat_sessions/', views.get_user_chat_sessions, name='get_user_chat_sessions'),
    path('api/dashboard_stats/', views.dashboard_stats, name='dashboard_stats'),
    path('api/admin_dashboard_charts/', views.admin_dashboard_charts, name='admin_dashboard_charts'),
    path('captcha/', views.captcha_image, name='captcha'),
]