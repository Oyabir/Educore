from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login_view/', views.login_view, name='login_view'),
    path('userLogout/',views.userLogout, name="userLogout"), 


    path('homeProf/', views.homeProf, name='homeProf'),
    path('Groupes/', views.Groupes, name='Groupes'),
    path('Competitions/', views.Competitions, name='Competitions'),
    path('Store/', views.Store, name='Store'),
    path('Profil/', views.Profil, name='Profil'),
    path('group_detail/', views.group_detail, name='group_detail'),
    path('Répartition_points/', views.Répartition_points, name='Répartition_points'),
    
    
    path('homeSuperAdmin/', views.homeSuperAdmin, name='homeSuperAdmin'),
    path('add_groupe/', views.add_groupe, name='add_groupe'),
    path('group_list/', views.group_list, name='group_list'),
    path('add_student/', views.add_student, name='add_student'),
    path('add_etudiant/', views.add_etudiant, name='add_etudiant'),
    path('add_students_from_file/', views.add_students_from_file, name='add_students_from_file'),
    # path('search-entities/', views.search_entities, name='search_entities'),


    path('homeEtudiant/', views.homeEtudiant, name='homeEtudiant'),









]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
