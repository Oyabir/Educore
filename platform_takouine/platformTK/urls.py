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

    path('mark-attendance/<str:code_group>/<int:schedule_id>/', views.mark_attendance, name='mark_attendance'),
    path('view-attendance/<str:code_group>/<int:schedule_id>/', views.view_attendance, name='view_attendance'),
    path('group/<str:code_group>/birthday/',views.birthday_list, name='birthday_list'),

    path('change-password-prof/', views.change_password_prof, name='change_password_prof'),

    
    
    path('homeSuperAdmin/', views.homeSuperAdmin, name='homeSuperAdmin'),
    path('add_groupe/', views.add_groupe, name='add_groupe'),
    path('group_list/', views.group_list, name='group_list'),
    path('add_student/', views.add_student, name='add_student'),
    path('add_etudiant/', views.add_etudiant, name='add_etudiant'),
    path('add_students_from_file/', views.add_students_from_file, name='add_students_from_file'),
    
    path('add_prof/', views.add_prof, name='add_prof'),
    path('prof_list/', views.prof_list, name='prof_list'),
    
    path('upload_prof_from_file/', views.upload_prof_from_file, name='upload_prof_from_file'),
    
    path('list_parents/', views.list_parents, name='list_parents'),
    path('add-parent/', views.add_parent, name='add_parent'),
    path('export_parents_to_excel/', views.export_parents_to_excel, name='export_parents_to_excel'),
    path('parent/update/<int:parent_id>/', views.update_parent, name='update_parent'),
    path('parent/delete/<int:parent_id>/',  views.delete_parent, name='delete_parent'),



    
    path('store_admin/', views.store_admin, name='store_admin'),
    path('add_product/', views.add_product, name='add_product'),
    path('store_admin/update/<str:product_code>/', views.update_product, name='update_product'),
    path('store_admin/delete/<str:product_code>/', views.delete_product, name='delete_product'),
    path('commandes_admin/', views.commandes_admin, name='commandes_admin'),






    path('edit-group/', views.edit_group, name='edit_group'),
    path('add-profs-etudiants/<int:group_id>/', views.add_profs_etudiants, name='add_profs_etudiants'),
    path('delete-profs-etudiants/<int:group_id>/', views.delete_profs_etudiants, name='delete_profs_etudiants'),
    path('delete_group/', views.delete_group, name='delete_group'),



    path('update_etudiant/', views.update_etudiant, name='update_etudiant'),
    path('delete_etudiant/<int:etudiant_id>/', views.delete_etudiant, name='delete_etudiant'),
    
    path('update_prof/<int:prof_id>/', views.update_prof, name='update_prof'),
    path('delete_prof/<int:prof_id>/', views.delete_prof, name='delete_prof'),
    
    path('update_commande_status/', views.update_commande_status, name='update_commande_status'),
    
    path('add_category/', views.add_category, name='add_category'),
    path('categories/', views.list_categories, name='list_categories'),  
    path('edit-category/', views.edit_category, name='edit_category'),    
    path('delete-category/', views.delete_category, name='delete_category'), 
    
    path('dashboard/', views.dashboard, name='dashboard'), 

    path('schedule-list/', views.schedule_list, name='schedule_list'),
    path('add-schedule/', views.add_schedule, name='add_schedule'),
    path('list-classes/', views.list_classes, name='list_classes'),
    path('edit_schedule/<int:schedule_id>/', views.edit_schedule, name='edit_schedule'),
    path('delete_schedule/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('view-students-in-class/<str:class_code>/', views.view_students_in_class, name='view_students_in_class'),
    path('class/<str:class_code>/download/', views.download_students_attendance_pdf, name='download_students_attendance_pdf'),

    path('rapports/', views.rapports, name='rapports'), 
    path('absence_by_group/', views.absence_by_group, name='absence_by_group'),
    
    path('download-group-report/csv/<str:group_name>/', views.download_group_report_csv, name='download_group_report_csv'),
    path('download-group-report/pdf/<str:group_name>/', views.download_group_report_pdf, name='download_group_report_pdf'),
    
    path('generate_absence_pdf/', views.generate_absence_pdf, name='generate_absence_pdf'),

    path('create_classes_aa/', views.create_classes_aa, name='create_classes_aa'),
    path('create-classes/', views.create_classes_for_next_week, name='create_classes'),


    path('absence_by_student/', views.absence_by_student, name='absence_by_student'),
    path('download_absence_report/<int:student_id>/', views.download_absence_report, name='download_absence_report'),


    path('rapport_soldes/', views.rapport_soldes, name='rapport_soldes'),
    path('student/<int:id>/report/', views.student_detail_report, name='student_detail_report'),
    path('competition/history/', views.competition_history, name='competition_history'),
    path('participation_discipline/', views.participation_discipline, name='participation_discipline'),
    path('validate_absences_history/', views.validate_absences_history, name='validate_absences_history'),
    
    path('absenteeism_report/', views.absenteeism_report, name='absenteeism_report'),
    path('real_time_absenteeism_by_group/', views.real_time_absenteeism_by_group, name='real_time_absenteeism_by_group'),
    path('calculate-absenteeism-rate/', views.calculate_absenteeism_rate, name='calculate_absenteeism_rate'),
    path('calculate_absenteeism_by_language/', views.calculate_absenteeism_by_language, name='calculate_absenteeism_by_language'),
    path('calculate_global_absenteeism_rate/', views.calculate_global_absenteeism_rate, name='calculate_global_absenteeism_rate'),
    path('show_absenteeism_statistics/', views.show_absenteeism_statistics, name='show_absenteeism_statistics'),







    




    # path('search-entities/', views.search_entities, name='search_entities'),


    path('homeEtudiant/', views.homeEtudiant, name='homeEtudiant'),
    path('Store/', views.Store, name='Store'),
    path('purchase/<slug:slug>/', views.purchase_product, name='purchase_product'),
    path('commandes/', views.list_commandes, name='list_commandes'),
    path('profile/', views.profile, name='profile'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('my_competitions/', views.my_competitions, name='my_competitions'),
    path('my_groups/', views.my_groups, name='my_groups'),
    path('change-password/', views.change_password, name='change_password'),






    path('homeParents/', views.homeParents, name='homeParents'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('groupes/', views.parent_groupes, name='parent_groupes'),
    path('competitions/', views.parent_competitions, name='parent_competitions'),
    path('profil_parent/', views.profil_parent, name='profil_parent'),
    path('update-profil/', views.update_profil_parent, name='update_profil_parent'),








]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
