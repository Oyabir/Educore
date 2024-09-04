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

    
    path('update_profil_prof/', views.update_profil_prof, name='update_profil_prof'),

    
    path('StoreProf/', views.StoreProf, name='StoreProf'),
    path('Profil/', views.Profil, name='Profil'),
    
    path('group_detail/<str:code_group>/', views.group_detail, name='group_detail'),
    path('Répartition_points/<str:code_group>/', views.Répartition_points, name='Répartition_points'),
    
    path('update_points/<int:student_id>/<int:group_id>/', views.update_points, name='update_points'),
    path('subtract_points/<int:student_id>/<int:group_id>/', views.subtract_points, name='subtract_points'),


    
    
    path('homeSuperAdmin/', views.homeSuperAdmin, name='homeSuperAdmin'),
    path('add_groupe/', views.add_groupe, name='add_groupe'),
    path('group_list/', views.group_list, name='group_list'),
    path('add_student/', views.add_student, name='add_student'),
    path('add_etudiant/', views.add_etudiant, name='add_etudiant'),
    path('add_students_from_file/', views.add_students_from_file, name='add_students_from_file'),
    
    path('add_prof/', views.add_prof, name='add_prof'),
    path('prof_list/', views.prof_list, name='prof_list'),
    
    path('upload_prof_from_file/', views.upload_prof_from_file, name='upload_prof_from_file'),
    
    path('store_admin/', views.store_admin, name='store_admin'),
    path('add_product/', views.add_product, name='add_product'),
    path('store_admin/update/<str:product_code>/', views.update_product, name='update_product'),
    path('store_admin/delete/<str:product_code>/', views.delete_product, name='delete_product'),
    
    path('commandes_admin/', views.commandes_admin, name='commandes_admin'),

    path('edit_group/<int:group_id>/', views.update_group, name='update_group'),



    # path('search-entities/', views.search_entities, name='search_entities'),


    path('homeEtudiant/', views.homeEtudiant, name='homeEtudiant'),
    path('Store/', views.Store, name='Store'),
    path('purchase/<slug:slug>/', views.purchase_product, name='purchase_product'),
    path('commandes/', views.list_commandes, name='list_commandes'),
    path('profile/', views.profile, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('my_competitions/', views.my_competitions, name='my_competitions'),
    path('my_groups/', views.my_groups, name='my_groups'),








]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
