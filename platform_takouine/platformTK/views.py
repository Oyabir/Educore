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



@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def homeEtudiant(request):
    etudiant = get_object_or_404(Etudiant, user=request.user)
    
    sections = Sections.objects.filter(etudiants=etudiant)
    
    competitions = Competitions.objects.filter(sections__in=sections).distinct()
    
    # Prepare the competition data
    competition_section_data = []
    for competition in competitions:
        for section in sections.filter(competition=competition):
            # Calculate rank within the competition
            section_rank = Sections.objects.filter(
                competition=competition, 
                points__gt=section.points
            ).count() + 1

            competition_section_data.append({
                'competition': competition,
                'section': section,
                'points': section.points,
                'rank': section_rank,
            })
    
    # Fetch all groups that the student is a part of
    etudiant = request.user.etudiant
    
    # Get all groups that the student is a part of
    memberships = Membership.objects.filter(etudiant=etudiant).select_related('group')
    
    group_data = []
    for membership in memberships:
        group = membership.group
        etudiant_pointsG = membership.pointsG
        
        # Get all memberships in the group, ordered by pointsG (descending)
        memberships_in_group = Membership.objects.filter(group=group).order_by('-pointsG')
        
        # Calculate the rank of the student in this specific group
        rank = list(memberships_in_group).index(membership) + 1
        
        group_data.append({
            'group': group,
            'points': etudiant_pointsG,
            'rank': rank,
            'total_students': group.etudiants.count()  # Get the total number of students from the group
        })
    
    context = {
        'etudiant': etudiant,
        'competition_section_data': competition_section_data,
        'group_data': group_data,
    }

    return render(request, "platformTK/Etudiant/homeEtudiant.html", context)







@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def Store(request):
    products = Product.objects.all()
    etudiant = get_object_or_404(Etudiant, user=request.user)
    context = {
        'etudiant': etudiant,
        'products': products,
    }
    return render(request, "platformTK/Etudiant/Store.html", context)




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def profile(request):
    etudiant = get_object_or_404(Etudiant, user=request.user)
    context = {
        'etudiant': etudiant,
    }
    return render(request, "platformTK/Etudiant/profile.html", context)






@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def update_profile(request):
    etudiant = get_object_or_404(Etudiant, user=request.user)
    
    if request.method == 'POST':
        etudiant.prenom = request.POST.get('prenom')
        etudiant.nom = request.POST.get('nom')
        etudiant.email = request.POST.get('email')
        etudiant.numéro_de_téléphone = request.POST.get('numéro_de_téléphone')
        
        if 'avatar' in request.FILES:
            etudiant.avatar = request.FILES['avatar']
        
        try:
            etudiant.save()
            messages.success(request, 'Profile updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating profile: {e}')
        
        return redirect('profile')  # Redirect to the profile page or another page of your choice

    return render(request, 'platformTK/Etudiant/profile.html', {'etudiant': etudiant})





@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def purchase_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    etudiant = get_object_or_404(Etudiant, user=request.user)

    if etudiant.points >= product.price:
        # Deduct points
        etudiant.points -= int(product.price)
        etudiant.save()

        # Log the purchase in the Commande table with status 'Pending'
        Commande.objects.create(
            etudiant=etudiant,
            product=product,
            total_price=product.price,
            status='Pending'
        )

        messages.success(request, f'You have successfully purchased {product.name}!')
    else:
        messages.error(request, 'You do not have enough points to purchase this product.')

    return redirect('Store')  # Redirect to the store or another page




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def list_commandes(request):
    etudiant = get_object_or_404(Etudiant, user=request.user)
    commandes = Commande.objects.filter(etudiant=etudiant)

    context = {
        'commandes': commandes,
        'etudiant': etudiant,
        'page_title': 'My Orders',
    }

    return render(request, "platformTK/Etudiant/list_commandes.html", context)






@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def my_competitions(request):
    try:
        # Fetch the current Etudiant instance
        etudiant = Etudiant.objects.get(user=request.user)
        
        # Get all Sections where this Etudiant is involved
        sections = Sections.objects.filter(etudiants=etudiant)
        
        # Get all Competitions associated with these Sections
        competitions = Competitions.objects.filter(sections__in=sections).distinct()
        
        # Create a list to store competition, section data, points, and rank
        competition_section_data = []
        for competition in competitions:
            for section in sections.filter(competition=competition):
                # Calculate rank for the section within its competition
                section_rank = Sections.objects.filter(
                    competition=competition, 
                    points__gt=section.points
                ).count() + 1

                competition_section_data.append({
                    'competition': competition,
                    'section': section,
                    'points': section.points,
                    'rank': section_rank,
                })
        
    except Etudiant.DoesNotExist:
        competition_section_data = []

    context = {
        "competition_section_data": competition_section_data,
        "etudiant": etudiant
    }
    return render(request, "platformTK/Etudiant/my_competitions.html", context)





@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def my_groups(request):
    etudiant = request.user.etudiant
    
    # Get all groups that the student is a part of
    memberships = Membership.objects.filter(etudiant=etudiant).select_related('group')
    
    group_data = []
    for membership in memberships:
        group = membership.group
        etudiant_pointsG = membership.pointsG
        
        # Get all memberships in the group, ordered by pointsG (descending)
        memberships_in_group = Membership.objects.filter(group=group).order_by('-pointsG')
        
        # Calculate the rank of the student in this specific group
        rank = list(memberships_in_group).index(membership) + 1
        
        group_data.append({
            'group': group,
            'points': etudiant_pointsG,
            'rank': rank,
            'total_students': group.etudiants.count()  # Get the total number of students from the group
        })
    
    context = {
        'group_data': group_data,
        'etudiant': etudiant
    }
    
    return render(request, 'platformTK/Etudiant/my_groupes.html', context)






from django.db.models import Sum

@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def homeProf(request):
    try:
        current_prof = prof.objects.get(user=request.user)
        
        # Filter groups and competitions associated with the current professor
        groups = Groups.objects.filter(profs=current_prof)
        competitions = Competitions.objects.filter(prof=current_prof)
        
        # Get the top 3 groups based on their total points
        top_groups = sorted(groups, key=lambda group: group.total_points(), reverse=True)[:3]
        
        # Aggregate points for each competition and sort them to get the top 3
        competitions_with_points = competitions.annotate(total_points=Sum('sections__points'))
        top_competitions = competitions_with_points.order_by('-total_points')[:3]
        
        top_students = Etudiant.objects.filter(groups__in=groups).distinct().order_by('-points')[:3]
    except prof.DoesNotExist:
        groups = Groups.objects.none()
        competitions = Competitions.objects.none()
        top_students = Etudiant.objects.none()
        top_groups = []
        top_competitions = []

    return render(request, "platformTK/Prof/homeProf.html", {
        "groups": groups,
        "competitions": competitions,
        "top_students": top_students,
        "top_groups": top_groups,
        "top_competitions": top_competitions,
    })







@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def Groupes(request):
    try:
        current_prof = prof.objects.get(user=request.user)
        groups = Groups.objects.filter(profs=current_prof)
    except prof.DoesNotExist:
        groups = Groups.objects.none()

    context = {"groups": groups}
    return render(request, "platformTK/Prof/Groupes.html", context)






@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def competitions_list(request):
    try:
        current_prof = prof.objects.get(user=request.user)
        groups = Groups.objects.filter(profs=current_prof)
        competitions = Competitions.objects.filter(prof=current_prof)
        
    except prof.DoesNotExist:
        groups = Groups.objects.none()
        competitions = Competitions.objects.none()

    context = {"competitions": competitions, "groups": groups}
    return render(request, "platformTK/Prof/Competitions.html", context)





@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def add_competition(request):
    try:
        current_prof = prof.objects.get(user=request.user)
        groups = Groups.objects.filter(profs=current_prof)
    except prof.DoesNotExist:
        groups = Groups.objects.none()
        current_prof = None  # Set to None if no prof is found

    if request.method == 'POST':
        name = request.POST.get('name')
        number_of_sections = request.POST.get('number_of_sections')
        selected_group = request.POST.get('group')  # Get selected group

        # Validate input
        if name and number_of_sections and selected_group:
            try:
                number_of_sections = int(number_of_sections)
                selected_group = Groups.objects.get(id=selected_group)  # Fetch the selected group

                if current_prof:
                    # Save the new competition to the database
                    competition = Competitions.objects.create(
                        name=name,
                        number_of_sections=number_of_sections,
                        group=selected_group,  # Associate the selected group
                        prof=current_prof  # Associate the competition with the logged-in professor
                    )

                    # Redirect to the add_section view with the new competition's ID
                    return redirect('add_section', competition_id=competition.id)
            except (ValueError, Groups.DoesNotExist):
                # Handle invalid number_of_sections or invalid group
                pass

    return render(request, 'platformTK/Prof/add_competition.html', {'groups': groups})  # Render a form to add a competition





from django.urls import reverse

def add_section(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    
    # Get all students in the competition's group
    all_students = competition.group.etudiants.all()

    # Get students already assigned to any section in this competition
    assigned_students = Etudiant.objects.filter(sections__competition=competition).distinct()

    # Exclude assigned students from the list of available students
    available_students = all_students.exclude(id__in=assigned_students.values_list('id', flat=True))

    # Get the current number of sections for this competition
    current_sections_count = competition.sections.count()

    if request.method == 'POST':
        section_name = request.POST.get('section_name')
        selected_students_str = request.POST.get('students')  # Get the string of selected students

        # Clean the string to remove any trailing comma and split into a list of IDs
        selected_students = list(map(int, selected_students_str.strip(',').split(',')))

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
            # Build the competition_sections URL
            competition_sections_url = reverse('competition_sections', args=[competition.id])

            # Display an error message with a link to the competition sections page
            error_message = f"You cannot add more sections than the allowed number. <a href='{competition_sections_url}'>Go to Competition Sections</a>"
            return render(request, 'platformTK/Prof/add_section.html', {
                'competition': competition,
                'students': available_students,
                'error_message': error_message,
                'current_sections_count': current_sections_count,
            })

    return render(request, 'platformTK/Prof/add_section.html', {
        'competition': competition,
        'students': available_students,  # Use the filtered list of available students
        'current_sections_count': current_sections_count,
    })




def competition_sections(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    sections = competition.sections.all().order_by('-points')  # Get all sections related to the competition
    return render(request, 'platformTK/Prof/competition_sections.html', {'competition': competition, 'sections': sections})






def finish_competition(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)

    # Check if the competition has already been finished
    if competition.is_finished:
        # Redirect to the results page without awarding points again
        return redirect('competition_results', competition_id=competition.id)
    
    # Get sections ordered by points in descending order
    top_sections = competition.sections.all().order_by('-points')[:3]  # Get top 3 sections
    
    # Points distribution for 1st, 2nd, and 3rd places
    points_distribution = [10, 5, 1]
    
    # Award points to the etudiants in each of the top 3 sections
    for index, section in enumerate(top_sections):
        points_to_add = points_distribution[index]  # Points based on rank (1st, 2nd, 3rd)
        for etudiant in section.etudiants.all():
            etudiant.points = (etudiant.points or 0) + points_to_add  # Add points
            etudiant.save()  # Save the updated points

    # Mark the competition as finished
    competition.is_finished = True
    competition.save()

    # Redirect to the results page after finishing the competition
    return redirect('competition_results', competition_id=competition.id)






def competition_results(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    sections = competition.sections.all().order_by('-points')  # Order sections by points descending

    return render(request, 'platformTK/Prof/competition_results.html', {
        'competition': competition,
        'sections': sections,
    })




def rank_competition(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    return redirect('competition_results', competition_id=competition.id)




@csrf_exempt
def increment_section_points(request, section_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        amount = data.get('amount', 0)
        try:
            section = Sections.objects.get(id=section_id)
            # Ensure amount is an integer
            amount = int(amount)
            section.points += amount
            section.save()
            return JsonResponse({'success': True, 'new_points': section.points})
        except Sections.DoesNotExist:
            return JsonResponse({'error': 'Section not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)



@csrf_exempt
def decrement_section_points(request, section_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        amount = data.get('amount', 0)
        try:
            section = Sections.objects.get(id=section_id)
            # Ensure amount is an integer
            amount = int(amount)
            section.points -= amount
            section.save()
            return JsonResponse({'success': True, 'new_points': section.points})
        except Sections.DoesNotExist:
            return JsonResponse({'error': 'Section not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)





def StoreProf(requset):
    products = Product.objects.all()
    return render(requset,"platformTK/Prof/Store.html", {'products': products})



@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def Profil(requset):
    Prof = get_object_or_404(prof, user=requset.user)
    context = {
        'Prof': Prof,
    }
    return render(requset,"platformTK/Prof/Profil.html",context)





@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def update_profil_prof(request):
    prof_instance = get_object_or_404(prof, user=request.user)

    if request.method == 'POST':
        # Extract form data
        prenom = request.POST.get('firstName')
        nom = request.POST.get('lastName')
        email = request.POST.get('email')
        numéro_de_téléphone = request.POST.get('phone')
        avatar = request.FILES.get('avatar')

        # Validate and update the prof instance
        if prenom and nom and email:
            prof_instance.prenom = prenom
            prof_instance.nom = nom
            prof_instance.email = email
            prof_instance.numéro_de_téléphone = numéro_de_téléphone

            if avatar:
                prof_instance.avatar = avatar
            
            try:
                prof_instance.save()
                messages.success(request, 'Profile updated successfully!')
            except Exception as e:
                messages.error(request, f'Error updating profile: {e}')
        else:
            messages.error(request, 'Please fill in all required fields.')

        return redirect('Profil')  # Redirect back to the profile page after updating

    context = {
        'Prof': prof_instance,
    }
    return render(request, "platformTK/Prof/Profil.html", context)








from django.db.models import Sum, OuterRef, Subquery

def group_detail(request, code_group):
    group = get_object_or_404(Groups, code_group=code_group)
    
    # Subquery to get pointsG for memberships related to the specific group
    memberships_subquery = Membership.objects.filter(
        group=group,
        etudiant=OuterRef('pk')
    ).values('etudiant').annotate(
        total_points=Sum('pointsG')
    ).values('total_points')
    
    # Annotate each student with the total pointsG from the subquery
    students = group.etudiants.annotate(
        pointsG=Subquery(memberships_subquery, output_field=models.IntegerField())
    ).order_by('-pointsG')  # Order by pointsG in descending order
    
    return render(request, "platformTK/Prof/group_detail.html", {"group": group, "students": students})




def Répartition_points(request, code_group):
    group = get_object_or_404(Groups, code_group=code_group)
    students = group.etudiants.all()
    memberships = Membership.objects.filter(group=group)
    memberships_dict = {membership.etudiant.id: membership.pointsG for membership in memberships}

    # Add pointsG to each student and sort
    for student in students:
        student.pointsG = memberships_dict.get(student.id, 0)

    students = sorted(students, key=lambda s: s.pointsG, reverse=True)

    return render(request, "platformTK/Prof/Répartition_points.html", {
        "group": group,
        "students": students,
        "memberships_dict": memberships_dict
    })




#Another way for do this

# from django.db.models import OuterRef, Subquery

# def Répartition_points(request, code_group):
#     group = get_object_or_404(Groups, code_group=code_group)
    
#     # Subquery to get pointsG for each student
#     pointsG_subquery = Membership.objects.filter(
#         etudiant=OuterRef('pk'),
#         group=group
#     ).values('pointsG')[:1]

#     students = group.etudiants.annotate(
#         pointsG=Subquery(pointsG_subquery)
#     ).order_by('-pointsG')

#     memberships = Membership.objects.filter(group=group)
#     memberships_dict = {membership.etudiant.id: membership.pointsG for membership in memberships}
    
#     # Debugging: Print memberships_dict to console
#     print("Memberships Dict:", memberships_dict)

#     return render(request, "platformTK/Prof/Répartition_points.html", {
#         "group": group,
#         "students": students,
#         "memberships_dict": memberships_dict
#     })





@csrf_exempt  
def update_points(request, student_id, group_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        amount = data.get('amount')

        try:
            student = Etudiant.objects.get(id=student_id)
            student.points += int(amount)
            student.save()

            # Update pointsG in Membership for the specific group
            memberships = Membership.objects.filter(etudiant=student, group_id=group_id)
            for membership in memberships:
                membership.pointsG += int(amount)
                membership.save()

            return JsonResponse({'success': True})
        except Etudiant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})



@csrf_exempt  
def subtract_points(request, student_id, group_id):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        amount = abs(int(data.get('amount')))  

        try:
            student = Etudiant.objects.get(id=student_id)
            if student.points >= amount:
                student.points -= amount  
                student.save()

                # Subtract pointsG in Membership for the specific group
                memberships = Membership.objects.filter(etudiant=student, group_id=group_id)
                for membership in memberships:
                    membership.pointsG -= amount
                    membership.save()

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

        # Create and save the new group
        group = Groups(name=group_name, description=description)
        group.save()

        # Add students and professors to the group
        students = Etudiant.objects.filter(id__in=student_ids)
        profs = prof.objects.filter(id__in=prof_ids)
        
        group.etudiants.set(students)
        group.profs.set(profs)
        group.save()

        # Create Membership records for each student added to the group, with pointsG initialized to 0
        for student in students:
            Membership.objects.create(etudiant=student, group=group, pointsG=0)

        return redirect('add_groupe')  # Ensure 'add_groupe' is defined in your URL patterns

    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Groups.objects.all()

    return render(request, 'platformTK/SuperAdmin/add_groupe.html', {
        'groups': groups,
        'etudiants': etudiants,
        'profs': profs
    })


# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages 
from .models import Groups

def edit_group(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        if group_id and name and description:
            group = get_object_or_404(Groups, id=group_id)
            group.name = name
            group.description = description
            group.save()
            messages.success(request, 'Group updated successfully!')
        else:
            messages.error(request, 'Please provide all required fields.')
        
        return redirect('add_groupe')  # Change to your desired redirect URL

    return redirect('add_groupe')  # Handle GET request or invalid form submission




from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages

def delete_group(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        group = get_object_or_404(Groups, id=group_id)
        group.delete()
        messages.success(request, 'Group deleted successfully.')
    return redirect('add_groupe')




from django.shortcuts import get_object_or_404, redirect, render
from django.core.exceptions import ValidationError

def add_profs_etudiants(request, group_id):
    group = get_object_or_404(Groups, id=group_id)

    # Filter professors and students not already in the group
    professors = prof.objects.exclude(id__in=group.profs.values_list('id', flat=True))
    etudiants = Etudiant.objects.exclude(id__in=group.etudiants.values_list('id', flat=True))

    if request.method == 'POST':
        # Get selected IDs from POST request
        selected_profs = request.POST.get('profs', '')
        selected_etudiants = request.POST.get('etudiants', '')

        # Convert selected IDs to lists
        prof_ids = [int(prof_id) for prof_id in selected_profs.split(',') if prof_id.isdigit()]
        etudiant_ids = [int(etudiant_id) for etudiant_id in selected_etudiants.split(',') if etudiant_id.isdigit()]

        # Add valid professors and students to the group
        group.profs.add(*prof_ids)
        group.etudiants.add(*etudiant_ids)

        # For each student added, create a Membership entry
        for etudiant_id in etudiant_ids:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            Membership.objects.get_or_create(etudiant=etudiant, group=group)

        # Redirect to the same view with the updated group_id
        return redirect('add_profs_etudiants', group_id=group.id)

    return render(request, 'platformTK/SuperAdmin/add_profs_etudiants.html', {
        'group': group,
        'professors': professors,
        'etudiants': etudiants,
    })




def delete_profs_etudiants(request, group_id):
    group = get_object_or_404(Groups, id=group_id)
    
    if request.method == 'POST':
        # Get selected IDs from POST request
        selected_profs = request.POST.getlist('profs')
        selected_etudiants = request.POST.getlist('etudiants')

        # Convert selected IDs to lists
        prof_ids = [int(prof_id) for prof_id in selected_profs if prof_id.isdigit()]
        etudiant_ids = [int(etudiant_id) for etudiant_id in selected_etudiants if etudiant_id.isdigit()]

        # Remove professors and students from the group
        group.profs.remove(*prof_ids)
        group.etudiants.remove(*etudiant_ids)

        # Delete Membership entries for the removed students (make sure to filter by both group and etudiant)
        for etudiant_id in etudiant_ids:
            Membership.objects.filter(etudiant_id=etudiant_id, group=group).delete()

        # Redirect back to the same page or another page as needed
        return redirect('delete_profs_etudiants', group_id=group.id)

    # Fetch the professors and students currently in the group
    professors = group.profs.all()
    etudiants = group.etudiants.all()

    return render(request, 'platformTK/SuperAdmin/delete_profs_etudiants.html', {
        'group': group,
        'professors': professors,
        'etudiants': etudiants,
    })





def add_etudiant(request):
    groups = Groups.objects.all()

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        date_de_naissance = request.POST.get('date_de_naissance')
        email = request.POST.get('email')
        numéro_de_téléphone = request.POST.get('numéro_de_téléphone')
        avatar = request.FILES.get('avatar')
        group_id = request.POST.get('group')

        # print("Group ID:", group_id)  # Debugging line

        if not username or not password or not prenom or not nom or not date_de_naissance or not email:
            return render(request, "platformTK/SuperAdmin/add_student.html", {'error': 'Please fill in all required fields.', 'groups': groups})

        try:
            user = User.objects.create_user(username=username, password=password)

            etudiant = Etudiant.objects.create(
                user=user,
                prenom=prenom,
                nom=nom,
                date_de_naissance=date_de_naissance,
                email=email,
                numéro_de_téléphone=numéro_de_téléphone,
                avatar=avatar
            )

            if group_id:
                group = Groups.objects.get(id=group_id)
                group.etudiants.add(etudiant)
                
            group = Group.objects.get(name="Etudiants")
            user.groups.add(group)

            messages.success(request, 'Etudiant added successfully!')
            return redirect('add_student')

        except Exception as e:
            return render(request, "platformTK/SuperAdmin/add_student.html", {'error': str(e), 'groups': groups})

    return render(request, "platformTK/SuperAdmin/add_student.html", {'groups': groups})





def update_etudiant(request):
    if request.method == 'POST':
        etudiant_id = request.POST.get('id')
        if not etudiant_id:
            return redirect('add_student')  # Redirect if no ID is provided
        
        etudiant = get_object_or_404(Etudiant, id=etudiant_id)

        # Update fields
        etudiant.prenom = request.POST.get('prenom', etudiant.prenom)
        etudiant.nom = request.POST.get('nom', etudiant.nom)
        etudiant.date_de_naissance = request.POST.get('date_de_naissance', etudiant.date_de_naissance)
        etudiant.email = request.POST.get('email', etudiant.email)
        etudiant.numéro_de_téléphone = request.POST.get('numéro_de_téléphone', etudiant.numéro_de_téléphone)

        # Handle file upload
        if 'avatar' in request.FILES:
            etudiant.avatar = request.FILES['avatar']

        # Handle group assignment (for ManyToManyField)
        group_ids = request.POST.getlist('groups')  # Can select multiple groups
        selected_groups = Groups.objects.filter(id__in=group_ids) 
        try:
            # Save etudiant details and update groups
            etudiant.save()
            etudiant.groups.set(selected_groups)  # Update the many-to-many relationship with selected groups
            messages.success(request, 'etudiant details and groups updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating etudiant: {str(e)}')

        etudiant.save()
        return redirect('add_student')  # Redirect to the list of students or relevant page

    return redirect('add_student')  # Redirect in case of GET request or failure




def delete_etudiant(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)

    if request.method == 'POST':
        etudiant.delete()
        messages.success(request, 'Etudiant deleted successfully!')
        return redirect('add_student')  # Redirect after deletion

    return redirect('add_student')  # Redirect if not a POST request





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





def add_prof(requset):
    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Groups.objects.all()
    return render(requset,"platformTK/SuperAdmin/add_prof.html", {
        'groups': groups,
        'etudiants': etudiants,
        'profs': profs,
    })
    
    
    
    
    




@login_required(login_url='login')
def prof_list(request):
    groups = Groups.objects.all()
    profs = prof.objects.all()

    if request.method == 'POST':
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        date_de_naissance = request.POST.get('date_de_naissance')
        email = request.POST.get('email')
        numéro_de_téléphone = request.POST.get('numéro_de_téléphone')
        avatar = request.FILES.get('avatar')
        group_id = request.POST.get('group')

        username = request.POST.get('username')
        password = request.POST.get('password')

        # Validate the inputs
        if not (prenom and nom and date_de_naissance and email and username and password):
            return render(request, 'platformTK/SuperAdmin/add_prof.html', {
                'error': 'Please fill in all required fields.',
                'groups': groups,
            })

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'platformTK/SuperAdmin/add_prof.html', {
                'error': 'Username already exists.',
                'groups': groups,
            })

        try:
            # Create the user object
            # user = User.objects.create_user(username=username, password=password, email=email)
            user = User.objects.create_user(username=username, password=password)

            # Create the prof instance
            new_prof = prof.objects.create(
                user=user,
                prenom=prenom,
                nom=nom,
                date_de_naissance=date_de_naissance,
                email=email,
                numéro_de_téléphone=numéro_de_téléphone,
                avatar=avatar,
                slugProf=slugify(username)
            )

            # Add professor to the selected group if group_id is provided
            if group_id:
                try:
                    group = Groups.objects.get(id=group_id)
                    group.profs.add(new_prof)
                except Groups.DoesNotExist:
                    return render(request, 'platformTK/SuperAdmin/add_prof.html', {
                        'error': f'Group with ID {group_id} does not exist.',
                        'groups': groups,
                    })

            # Add user to default "Prof" group
            prof_group = Group.objects.get(name="Prof")
            user.groups.add(prof_group)

            # Redirect to a success page or another view
            messages.success(request, 'Prof added successfully!')
            return redirect('add_prof')
        except Exception as e:
            # Handle any errors that occur during the creation
            return render(request, 'platformTK/SuperAdmin/add_prof.html', {
                'error': f'Error creating professor: {e}',
                'groups': groups,
            })

    return render(request, 'platformTK/SuperAdmin/add_prof.html', {
        'groups': groups,
        'profs': profs,
    })






@login_required
def update_prof(request, prof_id):
    # Fetch the professor using the provided ID
    professor = get_object_or_404(prof, id=prof_id)
    
    if request.method == 'POST':
        # Update professor's basic info
        professor.prenom = request.POST.get('prenom')
        professor.nom = request.POST.get('nom')
        professor.email = request.POST.get('email')
        professor.date_de_naissance = request.POST.get('date_de_naissance')
        professor.numéro_de_téléphone = request.POST.get('numéro_de_téléphone')

        # Handle avatar update
        if request.FILES.get('avatar'):
            professor.avatar = request.FILES['avatar']

        # Update the groups the professor belongs to
        group_ids = request.POST.getlist('groups')  # Get selected group IDs from the form
        selected_groups = Groups.objects.filter(id__in=group_ids)  # Fetch the groups from the database

        try:
            # Save professor details and update groups
            professor.save()
            professor.groups.set(selected_groups)  # Update the many-to-many relationship with selected groups
            messages.success(request, 'Professor details and groups updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating professor: {str(e)}')

        return redirect('add_prof')  # Redirect to the list of professors
    else:
        all_groups = Groups.objects.all()  # Get all available groups to display in the form
        return render(request, 'platformTK/SuperAdmin/add_prof.html', {'professor': professor, 'all_groups': all_groups})




@login_required
def delete_prof(request, prof_id):
    professor = get_object_or_404(prof, id=prof_id)

    if request.method == 'POST':
        try:
            professor.delete()
            messages.success(request, 'Professor deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting professor: {str(e)}')
        
        return redirect('prof_list')  # Redirect to the list of professors

    return render(request, 'delete_prof.html', {'professor': professor})






# Setup logger
logger = logging.getLogger(__name__)

@login_required(login_url='login')
def upload_prof_from_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')

        if not file:
            messages.error(request, 'No file uploaded.')
            return render(request, "platformTK/SuperAdmin/add_prof.html")

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
                        user = User.objects.create_user(username=username, password=password, email=email)
                        prof.objects.create(
                            user=user,
                            prenom=prenom,
                            nom=nom,
                            date_de_naissance=date_de_naissance,
                            email=email,
                            numéro_de_téléphone=numéro_de_téléphone,
                            avatar=avatar
                        )
                        group = Group.objects.get(name="Prof")
                        user.groups.add(group)
                        
                    except Exception as e:
                        logger.error(f"Error processing row with username '{username}': {e}")
                        messages.error(request, f"Error processing row with username '{username}': {e}")

            except Exception as e:
                logger.error(f"Error reading CSV file: {e}")
                messages.error(request, 'An error occurred while reading the CSV file.')
                return redirect('add_prof')

            messages.success(request, 'Professors added successfully from the CSV file.')
            return redirect('add_prof')

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
                    numéro_de_téléphone = row.get('numéro_de-téléphone', '')
                    avatar = None  # Handling avatar from Excel is complex; assume it's not provided

                    if pd.isna(username) or pd.isna(password) or pd.isna(prenom) or pd.isna(nom) or pd.isna(date_de_naissance) or pd.isna(email):
                        logger.warning(f"Skipping row due to missing data: {row.to_dict()}")
                        continue

                    try:
                        user = User.objects.create_user(username=username, password=password, email=email)
                        prof.objects.create(
                            user=user,
                            prenom=prenom,
                            nom=nom,
                            date_de_naissance=date_de_naissance,
                            email=email,
                            numéro_de_téléphone=numéro_de_téléphone,
                            avatar=avatar
                        )
                        group = Group.objects.get(name="Prof")
                        user.groups.add(group)
                        
                    except Exception as e:
                        logger.error(f"Error processing row with username '{username}': {e}")
                        messages.error(request, f"Error processing row with username '{username}': {e}")

            except Exception as e:
                logger.error(f"Error reading Excel file: {e}")
                messages.error(request, 'An error occurred while reading the Excel file.')
                return redirect('add_prof')

            messages.success(request, 'Professors added successfully from the Excel file.')
            return redirect('add_prof')

        else:
            messages.error(request, 'Unsupported file type. Please upload a CSV or Excel file.')
            return render(request, "platformTK/SuperAdmin/add_prof.html")

    return render(request, "platformTK/SuperAdmin/add_prof.html")







@login_required(login_url='login')
def store_admin(request):
    products = Product.objects.all()  # Fetch all products (or filter as needed)
    categories = Category.objects.all()  # Fetch all categories
    
    return render(request,"platformTK/SuperAdmin/store_admin.html", {
        'products': products,
        'categories': categories
    })




@login_required(login_url='login')
def add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        image = request.FILES.get('image')

        if name and description and category_id and price and stock:
            try:
                category = Category.objects.get(id=category_id)
                product = Product(
                    name=name,
                    description=description,
                    category=category,
                    price=price,
                    stock=stock,
                    image=image
                )
                product.save()
                messages.success(request, 'Product added successfully!')
            except Category.DoesNotExist:
                messages.error(request, 'Selected category does not exist.')
        else:
            messages.error(request, 'Please fill out all required fields.')

    return redirect('store_admin')




@login_required(login_url='login')
def update_product(request, product_code):
    product = get_object_or_404(Product, ProductCode=product_code)

    if request.method == 'POST':
        product.name = request.POST['name']
        product.description = request.POST['description']
        
        # Fetch the Category instance based on the category ID from the form
        category_id = request.POST.get('category')
        try:
            category = Category.objects.get(id=category_id)
            product.category = category
        except Category.DoesNotExist:
            messages.error(request, 'Selected category does not exist.')
            return redirect('store_admin')  # Handle the error as appropriate

        product.price = request.POST['price']
        product.stock = request.POST['stock']

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('store_admin')

    context = {
        'product': product,
        'categories': Category.objects.all(),  # Pass categories to the template
    }
    return render(request, 'platformTK/SuperAdmin/update_product.html', context)




@login_required(login_url='login')
def delete_product(request, product_code):
    product = get_object_or_404(Product, ProductCode=product_code)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('store_admin')





@login_required(login_url='login')  
def commandes_admin(request):
    commandes = Commande.objects.all()
    context = {
        'commandes': commandes,
    }
    return render(request, "platformTK/SuperAdmin/commandes_admin.html", context)





def update_commande_status(request):
    if request.method == 'POST':
        commande_id = request.POST.get('commande_id')
        new_status = request.POST.get('status')
        
        commande = get_object_or_404(Commande, id=commande_id)
        commande.status = new_status
        commande.save()

        messages.success(request, 'Commande status updated successfully.')
        return redirect('commandes_admin')  # Redirect to the page displaying commandes or relevant view

    return redirect('commandes_admin')  # Redirect if the request is not POST




@login_required(login_url='login')
def list_categories(request):
    categories = Category.objects.all().order_by('-date_added')
    return render(request, 'platformTK/SuperAdmin/list_categories.html', {'categories': categories})



@login_required(login_url='login')
def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        if category_name:
            if not Category.objects.filter(name=category_name).exists():
                Category.objects.create(name=category_name)
                messages.success(request, 'Category added successfully!')
            else:
                messages.error(request, 'Category already exists.')
        else:
            messages.error(request, 'Category name is required.')

    return redirect('list_categories')  # Redirect to the store admin page



@login_required(login_url='login')
def edit_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category_name = request.POST.get('category_name')
        
        # Retrieve and update the category
        category = get_object_or_404(Category, id=category_id)
        category.name = category_name
        category.save()

        # Success message
        messages.success(request, 'Category updated successfully!')
        return redirect('list_categories')

    return redirect('list_categories')



@login_required(login_url='login')
def delete_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        
        # Retrieve and delete the category
        category = get_object_or_404(Category, id=category_id)
        category.delete()

        # Success message
        messages.success(request, 'Category deleted successfully!')
        return redirect('list_categories')

    return redirect('list_categories')





# @login_required(login_url='login')
# def dashboard(request):
#     return render(request, 'platformTK/dashboard.html')




@login_required(login_url='login')
def dashboard(request):
    groups = Groups.objects.all()
    competitions = Competitions.objects.all()
    
    group_data = []
    competition_data = []

    # Initialize total points
    total_points = 0
    total_competition_points = 0
    
    # Collect group data and calculate total points for groups
    for group in groups:
        group_points = group.total_points()  # Assumes you have a `total_points` method in the Groups model
        group_data.append({
            'name': group.name,
            'points': group_points
        })
        total_points += group_points

    total_groups = len(groups)
    avg_points = total_points / total_groups if total_groups > 0 else 0

    # Collect competition data and calculate total points for competitions
    for competition in competitions:
        competition_points = competition.number_of_sections  # Assuming `number_of_sections` as points
        competition_data.append({
            'name': competition.name,
            'points': competition_points
        })
        total_competition_points += competition_points

    total_competitions = len(competitions)
    avg_competition_points = total_competition_points / total_competitions if total_competitions > 0 else 0

    context = {
        'group_data': group_data,
        'competition_data': competition_data,
        'total_groups': total_groups,
        'total_points': total_points,
        'avg_points': avg_points,
        'avg_competition_points': avg_competition_points  # Pass avg competition points to the template
    }
    return render(request, 'platformTK/dashboard.html', context)
