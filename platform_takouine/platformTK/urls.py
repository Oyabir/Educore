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
    
    
    path('competitions_list/', views.competitions_list, name='competitions_list'),
    path('add_competition/', views.add_competition, name='add_competition'),
    path('add-section/<int:competition_id>/', views.add_section, name='add_section'),
    path('competitions/<int:competition_id>/sections/', views.competition_sections, name='competition_sections'),
    
    path('increment_points/<int:section_id>/', views.increment_section_points, name='increment_section_points'),
    path('decrement_points/<int:section_id>/', views.decrement_section_points, name='decrement_section_points'),

    path('competition/<int:competition_id>/finish/', views.finish_competition, name='finish_competition'),
    path('competition/<int:competition_id>/results/', views.competition_results, name='competition_results'),
    
    path('competition/<int:competition_id>/rank/', views.rank_competition, name='rank_competition'),

    
    path('Store/', views.Store, name='Store'),
    path('Profil/', views.Profil, name='Profil'),
    path('group_detail/<str:code_group>/', views.group_detail, name='group_detail'),
    path('Répartition_points/<str:code_group>/', views.Répartition_points, name='Répartition_points'),
    path('update_points/<int:student_id>/', views.update_points, name='update_points'),
    path('subtract_points/<int:student_id>/', views.subtract_points, name='subtract_points'),


    
    
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
