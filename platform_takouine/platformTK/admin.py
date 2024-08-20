from django.contrib import admin
from .models import *



@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'numéro_de_téléphone', 'EtudiantCode', 'date_created')
    fields = ('user', 'prenom', 'nom', 'date_de_naissance', 'email', 'numéro_de_téléphone', 'avatar', 'slugEtudiant', 'EtudiantCode')
    readonly_fields = ('date_created',)
    
    
    
    

@admin.register(prof)
class ProfAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'numéro_de_téléphone', 'ProfCode', 'date_created')
    fields = ('user', 'prenom', 'nom', 'date_de_naissance', 'email', 'numéro_de_téléphone', 'avatar', 'slugProf', 'ProfCode')
    readonly_fields = ('date_created',)




@admin.register(Groups)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('etudiants', 'profs')
