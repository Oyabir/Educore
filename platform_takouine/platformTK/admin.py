from django.contrib import admin
from .models import *



@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'numéro_de_téléphone', 'EtudiantCode', 'date_created', 'points')
    fields = ('user', 'prenom', 'nom', 'date_de_naissance', 'email', 'numéro_de_téléphone', 'avatar', 'slugEtudiant', 'EtudiantCode','points')
    readonly_fields = ('date_created',)
    
    
    
    

@admin.register(prof)
class ProfAdmin(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'numéro_de_téléphone', 'ProfCode', 'date_created')
    fields = ('user', 'prenom', 'nom', 'date_de_naissance', 'email', 'numéro_de_téléphone', 'avatar', 'slugProf', 'ProfCode')
    readonly_fields = ('date_created',)
    
    
    
    
    
@admin.register(Competitions)
class CompetitionsAdmin(admin.ModelAdmin):
    list_display = ('name', 'number_of_sections')
    readonly_fields = ('date_created',)



@admin.register(Sections)
class SectionsAdmin(admin.ModelAdmin):
    list_display = ('competition', 'section_name')
    filter_horizontal = ('etudiants',)  



@admin.register(Groups)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    filter_horizontal = ('etudiants', 'profs')




@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'date_added')
    search_fields = ('name', 'description')
    
    
    
    
@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'product', 'date_ordered', 'quantity', 'total_price', 'status')
    search_fields = ('etudiant__user__username', 'product__name')
    list_filter = ('status', 'date_ordered')
    readonly_fields = ('date_ordered', 'total_price')
    




@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'group', 'pointsG')
    search_fields = ('etudiant__prenom', 'etudiant__nom', 'group__name')
    


    

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)  
    search_fields = ('name',)  
    ordering = ('name',)    