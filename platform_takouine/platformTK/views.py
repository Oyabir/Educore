import logging
from pyexpat.errors import messages
from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth.models import Group, User
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.contrib.auth import authenticate,logout
from django.contrib.auth import authenticate, login
from .decorators import notLoggedUsers,allowedUsers,forAdmins
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json










def home(requset):
    return render(requset,"platformTK/home.html")



@notLoggedUsers
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if request.user.groups.filter(name='Etudiants').exists():
                return redirect('/homeEtudiant')  # Redirect to student's home
            elif request.user.groups.filter(name='Prof').exists():
                return redirect('/homeProf')
            elif request.user.groups.filter(name='SuperAdmin').exists():
                return redirect('/homeSuperAdmin')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, "platformTK/login.html")




from django.contrib.auth.decorators import login_required

#Logout for all
def userLogout(request):
   logout(request)
   return redirect('home')



def homeEtudiant(requset):
    return render(requset,"platformTK/Etudiant/homeEtudiant.html")



def homeProf(requset):
    groups = Groups.objects.all()
    competitions = Competitions.objects.all()
    return render(requset,"platformTK/Prof/homeProf.html",{"groups": groups, "competitions": competitions})




def Groupes(requset):
    groups = Groups.objects.all()
    context = {"groups":groups}
    return render(requset,"platformTK/Prof/Groupes.html",context)



def competitions_list(request):
    competitions = Competitions.objects.all()
    context = {"competitions": competitions}
    return render(request, "platformTK/Prof/Competitions.html", context)



def add_competition(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        number_of_sections = request.POST.get('number_of_sections')

        # Validate input
        if name and number_of_sections:
            try:
                number_of_sections = int(number_of_sections)
                # Save the new competition to the database
                competition = Competitions.objects.create(
                    name=name,
                    number_of_sections=number_of_sections
                )
                # Redirect to the add_section view with the new competition's ID
                return redirect('add_section', competition_id=competition.id)
            except ValueError:
                # Handle invalid number_of_sections
                pass

    return redirect('competitions_list')  # Redirect to a page listing competitions if GET request





def add_section(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    students = Etudiant.objects.all()

    # Get the current number of sections for this competition
    current_sections_count = competition.sections.count()

    if request.method == 'POST':
        section_name = request.POST.get('section_name')
        selected_students = request.POST.getlist('students')  # Get the list of selected students

        # Check if the current number of sections is less than the allowed number of sections
        if current_sections_count < competition.number_of_sections:
            if section_name:
                # Create the new section for the competition
                section = Sections.objects.create(
                    competition=competition,
                    section_name=section_name
                )

                # Add selected students to the section
                section.etudiants.set(selected_students)
                section.save()

                # Redirect back to the same page to add more sections if needed
                return redirect('add_section', competition_id=competition.id)
        else:
            # Display an error message if the limit is reached
            error_message = "You cannot add more sections than the allowed number."
            return render(request, 'platformTK/Prof/add_section.html', {
                'competition': competition,
                'students': students,
                'error_message': error_message
            })

    return render(request, 'platformTK/Prof/add_section.html', {'competition': competition, 'students': students})





def competition_sections(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    sections = competition.sections.all()  # Get all sections related to the competition
    return render(request, 'platformTK/Prof/competition_sections.html', {'competition': competition, 'sections': sections})






def update_section_points(request, section_id):
    section = get_object_or_404(Sections, id=section_id)
    if request.method == 'POST':
        points = request.POST.get('points')
        try:
            section.points = int(points)
            section.save()
            return redirect('competition_sections', competition_id=section.competition.id)
        except ValueError:
            # Handle invalid points input
            pass

    return redirect('competition_sections', competition_id=section.competition.id)






def Store(requset):
    return render(requset,"platformTK/Prof/Store.html")




def Profil(requset):
    return render(requset,"platformTK/Prof/Profil.html")




def group_detail(request, code_group):
    # Retrieve the group using the unique code_group
    group = get_object_or_404(Groups, code_group=code_group)
    # Get all students associated with this group
    students = group.etudiants.all()
    return render(request, "platformTK/Prof/group_detail.html", {"group": group, "students": students})





def Répartition_points(request, code_group):
    # Retrieve the group using the unique code_group
    group = get_object_or_404(Groups, code_group=code_group)
    # Get all students associated with this group
    students = group.etudiants.all().order_by('-points')
    return render(request, "platformTK/Prof/Répartition_points.html", {"group": group, "students": students})





@csrf_exempt  
def update_points(request, student_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        amount = data.get('amount')
        
        try:
            student = Etudiant.objects.get(id=student_id)
            student.points += int(amount)
            student.save()
            return JsonResponse({'success': True})
        except Etudiant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})





@csrf_exempt  
def subtract_points(request, student_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        amount = abs(int(data.get('amount')))  

        try:
            student = Etudiant.objects.get(id=student_id)
            if student.points >= amount:
                student.points -= amount  
                student.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Insufficient points'})
        except Etudiant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})





def homeSuperAdmin(requset):
    return render(requset,"platformTK/SuperAdmin/homeSuperAdmin.html")



def add_groupe(requset):
    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Groups.objects.all()
    return render(requset,"platformTK/SuperAdmin/add_groupe.html", {
        'groups': groups,
        'etudiants': etudiants,
        'profs': profs
    })




def add_student(requset):
    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Groups.objects.all()
    return render(requset,"platformTK/SuperAdmin/add_student.html", {
        'groups': groups,
        'etudiants': etudiants,
        'profs': profs
    })



def group_list(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        description = request.POST.get('description')
        student_ids_str = request.POST.get('students', '')  # Get the comma-separated student IDs as a string
        prof_ids_str = request.POST.get('profs', '')  # Get the comma-separated professor IDs as a string

        # Convert the comma-separated strings into lists of integers
        student_ids = [int(id) for id in student_ids_str.split(',') if id.isdigit()]
        prof_ids = [int(id) for id in prof_ids_str.split(',') if id.isdigit()]

        # Debugging output to verify received data
        print("Group Name:", group_name)
        print("Description:", description)
        print("Selected Students IDs:", student_ids)
        print("Selected Professors IDs:", prof_ids)

        # Create and save the new group
        group = Groups(name=group_name, description=description)
        group.save()

        # Add students and professors to the group
        students = Etudiant.objects.filter(id__in=student_ids)
        profs = prof.objects.filter(id__in=prof_ids)
        
        group.etudiants.set(students)
        group.profs.set(profs)
        group.save()

        return redirect('add_groupe')  # Ensure 'add_groupe' is defined in your URL patterns

    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Groups.objects.all()

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








import csv
import pandas as pd



logger = logging.getLogger(__name__)

def add_students_from_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        
        if not file:
            messages.error(request, 'No file uploaded.')
            return render(request, "platformTK/SuperAdmin/add_student.html")

        if file.name.endswith('.csv'):
            try:
                data = csv.reader(file.read().decode('utf-8').splitlines())
                next(data)  # Skip the header row

                for row in data:
                    if len(row) < 6:
                        continue  # Skip rows with insufficient data

                    username, password, prenom, nom, date_de_naissance, email, *rest = row
                    numéro_de_téléphone = rest[0] if rest else ""
                    avatar = None  # Handling avatar from CSV is complex; assume it's not provided

                    if not username or not password or not prenom or not nom or not date_de_naissance or not email:
                        continue  # Skip rows with missing required fields

                    try:
                        user = User.objects.create_user(username=username, password=password)
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
                        
                    except Exception as e:
                        # Log the error with more user-friendly output
                        logger.error(f"Error processing row with username '{username}': {e}")
                        messages.error(request, f"Error processing row with username '{username}': {e}")

            except Exception as e:
                logger.error(f"Error reading CSV file: {e}")
                messages.error(request, 'An error occurred while reading the CSV file.')
                return redirect('add_student')

            messages.success(request, 'Students added successfully from the CSV file.')
            return redirect('add_student')

        elif file.name.endswith('.xlsx'):
            try:
                df = pd.read_excel(file)

                # Drop irrelevant or unnamed columns
                df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
                
                for _, row in df.iterrows():
                    username = row.get('username')
                    password = row.get('password')
                    prenom = row.get('prenom')
                    nom = row.get('nom')
                    date_de_naissance = row.get('date_de_naissance')
                    email = row.get('email')
                    numéro_de_téléphone = row.get('numéro_de_téléphone', '')
                    avatar = None  # Handling avatar from Excel is complex; assume it's not provided

                    # Skip rows with missing required fields
                    if pd.isna(username) or pd.isna(password) or pd.isna(prenom) or pd.isna(nom) or pd.isna(date_de_naissance) or pd.isna(email):
                        logger.warning(f"Skipping row due to missing data: {row.to_dict()}")
                        continue

                    try:
                        user = User.objects.create_user(username=username, password=password)
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
                        
                    except Exception as e:
                        # Log the error with more user-friendly output
                        logger.error(f"Error processing row with username '{username}': {e}")
                        messages.error(request, f"Error processing row with username '{username}': {e}")
            
            except Exception as e:
                logger.error(f"Error reading Excel file: {e}")
                messages.error(request, 'An error occurred while reading the Excel file.')
                return redirect('add_student')

            messages.success(request, 'Students added successfully from the Excel file.')
            return redirect('add_student')

        else:
            messages.error(request, 'Unsupported file type. Please upload a CSV or Excel file.')
            return render(request, "platformTK/SuperAdmin/add_student.html")

    return render(request, "platformTK/SuperAdmin/add_student.html")
