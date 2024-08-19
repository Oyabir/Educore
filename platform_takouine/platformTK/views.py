from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password


def home(requset):
    return render(requset,"platformTK/home.html")



def login(requset):
    return render(requset,"platformTK/login.html")


def homeProf(requset):
    return render(requset,"platformTK/Prof/homeProf.html")




def Groupes(requset):
    return render(requset,"platformTK/Prof/Groupes.html")





def Competitions(requset):
    return render(requset,"platformTK/Prof/Competitions.html")



def Store(requset):
    return render(requset,"platformTK/Prof/Store.html")




def Profil(requset):
    return render(requset,"platformTK/Prof/Profil.html")




def group_detail(requset):
    return render(requset,"platformTK/Prof/group_detail.html")




def Répartition_points(requset):
    return render(requset,"platformTK/Prof/Répartition_points.html")







def homeSuperAdmin(requset):
    return render(requset,"platformTK/SuperAdmin/homeSuperAdmin.html")



def add_groupe(requset):
    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Group.objects.all()
    return render(requset,"platformTK/SuperAdmin/add_groupe.html", {
        'groups': groups,
        'etudiants': etudiants,
        'profs': profs
    })




def add_student(requset):
    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Group.objects.all()
    return render(requset,"platformTK/SuperAdmin/add_student.html", {
        'groups': groups,
        'etudiants': etudiants,
        'profs': profs
    })





def group_list(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        description = request.POST.get('description')
        student_ids = request.POST.getlist('students')
        prof_ids = request.POST.getlist('profs')

        group = Group(name=group_name, description=description)
        group.save()
        
        # Add students and professors to the group
        students = Etudiant.objects.filter(id__in=student_ids)
        profs = prof.objects.filter(id__in=prof_ids)
        
        group.etudiants.set(students)
        group.profs.set(profs)
        group.save()
        
        return redirect('add_groupe')  

    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Group.objects.all()

    return render(request, 'platformTK/SuperAdmin/add_groupe.html', {
        'groups': groups,
        'etudiants': etudiants,
        'profs': profs
    })




def add_etudiant(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        date_de_naissance = request.POST.get('date_de_naissance')
        email = request.POST.get('email')
        numéro_de_téléphone = request.POST.get('numéro_de_téléphone')
        avatar = request.FILES.get('avatar')

        if not username or not password or not prenom or not nom or not date_de_naissance or not email:
            # Handle missing fields (return an error message or redirect to a form with errors)
            return render(request, "platformTK/SuperAdmin/add_student.html", {'error': 'Please fill in all required fields.'})

        try:
            # Create User
            user = User.objects.create_user(username=username, password=password)

            # Create Etudiant
            Etudiant.objects.create(
                user=user,
                prenom=prenom,
                nom=nom,
                date_de_naissance=date_de_naissance,
                email=email,
                numéro_de_téléphone=numéro_de_téléphone,
                avatar=avatar
            )
            
            group = Group.objects.get(name="Etudiants")
            user.groups.add(group)


            return redirect('add_student')  # Ensure 'add_student' is a valid URL name

        except Exception as e:
            # Handle any exceptions (return an error message or log the error)
            return render(request, "platformTK/SuperAdmin/add_student.html", {'error': str(e)})

    return render(request, "platformTK/SuperAdmin/add_student.html")
