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
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models import Sum
from django.urls import reverse
from django.db.models import Sum, OuterRef, Subquery
from django.core.exceptions import ValidationError






def home(request):  
    context = {}
    # Check if the user is authenticated
    if request.user.is_authenticated:
        context['is_etudiant'] = request.user.groups.filter(name='Etudiants').exists()
        context['is_prof'] = request.user.groups.filter(name='Prof').exists()
        context['is_superadmin'] = request.user.groups.filter(name='SuperAdmin').exists()

    return render(request, "platformTK/home.html", context)  



@notLoggedUsers
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if request.user.groups.filter(name='Etudiants').exists():
                return redirect('/homeEtudiant') 
            elif request.user.groups.filter(name='Prof').exists():
                return redirect('/homeProf')
            elif request.user.groups.filter(name='SuperAdmin').exists():
                return redirect('/add_groupe')
            elif request.user.groups.filter(name='Parents').exists():
                return redirect('/homeParents')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, "platformTK/login.html")




from django.contrib.auth.decorators import login_required

#Logout for all
def userLogout(request):
   logout(request)
   return redirect('home')



from django.utils import timezone

def is_birthday(etudiant):
    today = timezone.now().date()
    return today.day == etudiant.date_de_naissance.day and today.month == etudiant.date_de_naissance.month



@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def homeEtudiant(request):
    etudiant = request.user.etudiant
    today = timezone.now().date()

    # Check if it's the student's birthday
    birthday_message = is_birthday(etudiant)

    # Show the birthday message only once per login on the birthday
    if birthday_message and request.session.get('birthday_message_shown') != str(today):
        request.session['birthday_message_shown'] = str(today) 
    else:
        birthday_message = False
        
    try:
        etudiant = Etudiant.objects.get(user=request.user)
    except Etudiant.DoesNotExist:
        messages.error(request, "You are not associated with any student profile.")
        return redirect('home')

    sections = Sections.objects.filter(etudiants=etudiant)

    competitions = Competitions.objects.filter(sections__in=sections).distinct()


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

    memberships = Membership.objects.filter(etudiant=etudiant).select_related('group')

    group_data = []
    for membership in memberships:
        group = membership.group
        etudiant_pointsG = membership.pointsG

        memberships_in_group = Membership.objects.filter(group=group).order_by('-pointsG')

        # Calculate the rank of the student in this specific group
        rank = list(memberships_in_group).index(membership) + 1

        group_data.append({
            'group': group,
            'points': etudiant_pointsG,
            'rank': rank,
            'total_students': group.etudiants.count() 
        })

    context = {
        'etudiant': etudiant,
        'competition_section_data': competition_section_data,
        'group_data': group_data,
        'birthday_message': birthday_message,
    }

    return render(request, "platformTK/Etudiant/homeEtudiant.html", context)




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def Store(request):
    etudiant = get_object_or_404(Etudiant, user=request.user)
    
    category_id = request.GET.get('category')
    name_query = request.GET.get('name')
    
    products = Product.objects.all()

    if category_id:
        products = products.filter(category__id=category_id)
        
    if name_query and name_query != "None":  
        products = products.filter(name__icontains=name_query) 
    
    # Pagination
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    
    categories = Category.objects.all()
    
    context = {
        'etudiant': etudiant,
        'page_obj': page_obj,  # The paginated products
        'categories': categories,
        'selected_category': category_id, 
        'name_query': name_query if name_query != "None" else "", 
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
        
        return redirect('profile')

    return render(request, 'platformTK/Etudiant/profile.html', {'etudiant': etudiant})



from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.models import User

@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def change_password(request):
    etudiant = get_object_or_404(Etudiant, user=request.user)
    if request.method == 'POST':
        # Get the current password, new password, and confirm password from the request
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Check if the current password is valid
        user = get_object_or_404(User, username=request.user.username)
        if user.check_password(current_password):
            if new_password == confirm_password:
                # Change the password
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep the user logged in
                messages.success(request, 'Mot de passe changé avec succès !')
                return redirect('profile')
            else:
                messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
        else:
            messages.error(request, 'Le mot de passe actuel est incorrect.')
            
    context = {
        'etudiant': etudiant,
    }
    return render(request, 'platformTK/Etudiant/change_password.html',context)




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def purchase_product(request, slug):
    product = get_object_or_404(Product, slug=slug)
    etudiant = get_object_or_404(Etudiant, user=request.user)

    if etudiant.points >= product.price:
        etudiant.points -= int(product.price)
        etudiant.save()

        # add the purchase in the Commande
        Commande.objects.create(
            etudiant=etudiant,
            product=product,
            total_price=product.price,
            status='Pending'
        )

        messages.success(request, f'You have successfully purchased {product.name}!')
    else:
        messages.error(request, 'You do not have enough points to purchase this product.')

    return redirect('list_commandes') 





@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def list_commandes(request):
    etudiant = get_object_or_404(Etudiant, user=request.user)
    
    commande_code_query = request.GET.get('commande_code', '')
    status_query = request.GET.get('status', '')


    commandes = Commande.objects.filter(etudiant=etudiant).order_by('-date_ordered')
    if commande_code_query:
        commandes = commandes.filter(commande_code__icontains=commande_code_query).order_by('-date_ordered')
    if status_query:
        commandes = commandes.filter(status=status_query).order_by('-date_ordered')

    # Paginate
    paginator = Paginator(commandes, 10)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'etudiant': etudiant,
        'page_title': 'My Orders',
        'commande_code_query': commande_code_query,
        'status_query': status_query,
    }

    return render(request, "platformTK/Etudiant/list_commandes.html", context)






@login_required(login_url='login')
@allowedUsers(allowedGroups=['Etudiants'])
def my_competitions(request):
    try:
        etudiant = Etudiant.objects.get(user=request.user)
        
        sections = Sections.objects.filter(etudiants=etudiant)
        
        competitions = Competitions.objects.filter(sections__in=sections).distinct()
        
        competition_section_data = []
        for competition in competitions:
            for section in sections.filter(competition=competition):
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
    
    memberships = Membership.objects.filter(etudiant=etudiant).select_related('group')
    
    group_data = []
    for membership in memberships:
        group = membership.group
        etudiant_pointsG = membership.pointsG
        
        memberships_in_group = Membership.objects.filter(group=group).order_by('-pointsG')
        
        rank = list(memberships_in_group).index(membership) + 1
        
        group_data.append({
            'group': group,
            'points': etudiant_pointsG,
            'rank': rank,
            'total_students': group.etudiants.count() 
        })
    
    context = {
        'group_data': group_data,
        'etudiant': etudiant
    }
    
    return render(request, 'platformTK/Etudiant/my_groupes.html', context)



@login_required(login_url='login')
@allowedUsers(allowedGroups=['Parents'])
def homeParents(request):
    return render(request, "platformTK/Parents/homeParents.html")



@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def homeProf(request):
    try:
        current_prof = prof.objects.get(user=request.user)
        
        groups = Groups.objects.filter(profs=current_prof)
        competitions = Competitions.objects.filter(prof=current_prof)
        
        # Get the top 3 groups
        top_groups = sorted(groups, key=lambda group: group.total_points(), reverse=True)[:3]
        
        # The the top 3 competition
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
        competitions = Competitions.objects.filter(prof=current_prof).order_by("-date_created")
        
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
        selected_group = request.POST.get('group')

        # Validate input
        if name and number_of_sections and selected_group:
            try:
                number_of_sections = int(number_of_sections)
                selected_group = Groups.objects.get(id=selected_group) 

                if current_prof:
                    competition = Competitions.objects.create(
                        name=name,
                        number_of_sections=number_of_sections,
                        group=selected_group,  
                        prof=current_prof  
                    )
                    return redirect('add_section', competition_id=competition.id)
            except (ValueError, Groups.DoesNotExist):
                pass

    return render(request, 'platformTK/Prof/add_competition.html', {'groups': groups})



import random

@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def add_section(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    
    # Keep all_students as a QuerySet
    all_students = competition.group.etudiants.all()
    current_sections_count = competition.sections.count()

    # Fetch assigned students for the competition
    assigned_students = Etudiant.objects.filter(sections__competition=competition).distinct()

    # Determine available students who are not already assigned to a section
    available_students = all_students.exclude(id__in=assigned_students.values_list('id', flat=True))
    
    if request.method == 'POST':
        section_type = request.POST.get('section_type')
        
        if section_type == 'manual':
            section_name = request.POST.get('section_name')
            selected_students_str = request.POST.get('students')
            selected_students = list(map(int, selected_students_str.strip(',').split(','))) if selected_students_str else []

            if current_sections_count < competition.number_of_sections:
                if section_name:
                    section = Sections.objects.create(
                        competition=competition,
                        section_name=section_name
                    )
                    section.etudiants.set(selected_students)
                    section.save()
                    return redirect('add_section', competition_id=competition.id)

        elif section_type == 'automatic':
            num_sections = competition.number_of_sections - current_sections_count
            
            if num_sections > 0:
                available_students_list = list(available_students)  # Convert to list for manipulation
                random.shuffle(available_students_list)  # Shuffle the list of available students
                
                students_per_section = len(available_students_list) // num_sections
                remainder = len(available_students_list) % num_sections
                
                index = 0
                for i in range(num_sections):
                    section_name = f"Group {current_sections_count + i + 1}"
                    section = Sections.objects.create(
                        competition=competition,
                        section_name=section_name
                    )

                    num_students = students_per_section + (1 if i < remainder else 0)
                    
                    # Randomly select a unique set of students for the section
                    section_students = available_students_list[index:index + num_students]  # Select students
                    section.etudiants.set(section_students)  # Set students to the section
                    section.save()

                    index += num_students  # Move index forward for the next selection

                return redirect('competition_sections', competition_id=competition.id)

    return render(request, 'platformTK/Prof/add_section.html', {
        'competition': competition,
        'students': available_students,  # Pass the filtered available students
        'current_sections_count': current_sections_count,
    })






@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def competition_sections(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    sections = competition.sections.all().order_by('-points')
    return render(request, 'platformTK/Prof/competition_sections.html', {'competition': competition, 'sections': sections})



@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def finish_competition(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)

    if competition.is_finished:
        return redirect('competition_results', competition_id=competition.id)

    top_sections = competition.sections.all().order_by('-points')[:3]
    points_distribution = [10, 5, 1]  # Points for top 3 sections

    for index, section in enumerate(top_sections):
        points_to_add = points_distribution[index]
        for etudiant in section.etudiants.all():
            # Update or create UserCompetition record
            user_competition, created = UserCompetition.objects.get_or_create(
                user=etudiant.user,
                competition=competition,
                defaults={'earned_points': 0}
            )
            user_competition.earned_points += points_to_add
            user_competition.save()

            # Update student points
            etudiant.points = (etudiant.points or 0) + points_to_add 
            etudiant.save()

    competition.is_finished = True
    competition.save()

    return redirect('competition_results', competition_id=competition.id)




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def competition_results(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    sections = competition.sections.all().order_by('-points')

    return render(request, 'platformTK/Prof/competition_results.html', {
        'competition': competition,
        'sections': sections,
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def rank_competition(request, competition_id):
    competition = get_object_or_404(Competitions, id=competition_id)
    return redirect('competition_results', competition_id=competition.id)




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
@csrf_exempt
def increment_section_points(request, section_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        amount = data.get('amount', 0)
        try:
            section = Sections.objects.get(id=section_id)
            amount = int(amount)
            section.points += amount
            section.save()
            return JsonResponse({'success': True, 'new_points': section.points})
        except Sections.DoesNotExist:
            return JsonResponse({'error': 'Section not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
@csrf_exempt
def decrement_section_points(request, section_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        amount = data.get('amount', 0)
        try:
            section = Sections.objects.get(id=section_id)
            amount = int(amount)
            section.points -= amount
            section.save()
            return JsonResponse({'success': True, 'new_points': section.points})
        except Sections.DoesNotExist:
            return JsonResponse({'error': 'Section not found'}, status=404)
        except ValueError:
            return JsonResponse({'error': 'Invalid amount'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)





@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def StoreProf(request):
    search_query = request.GET.get('name', '')
    category_id = request.GET.get('category', '')

    products = Product.objects.all()
    if search_query:
        products = products.filter(name__icontains=search_query)
    if category_id:
        products = products.filter(category_id=category_id)

    # Pagination
    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = Category.objects.all()

    context = {
        'page_obj': page_obj,
        'name_query': search_query,
        'categories': categories,
        'selected_category': category_id,
    }
    return render(request, "platformTK/Prof/Store.html", context)





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
        prenom = request.POST.get('firstName')
        nom = request.POST.get('lastName')
        email = request.POST.get('email')
        numéro_de_téléphone = request.POST.get('phone')
        avatar = request.FILES.get('avatar')

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

        return redirect('Profil') 

    context = {
        'Prof': prof_instance,
    }
    return render(request, "platformTK/Prof/Profil.html", context)



from django.contrib.auth.models import User
from .models import prof 

@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def change_password_prof(request):
    prof_instance = get_object_or_404(prof, user=request.user)

    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Get the User instance
        user = get_object_or_404(User, username=request.user.username)

        if user.check_password(current_password):
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Mot de passe changé avec succès !')
                return redirect('Profil')
            else:
                messages.error(request, 'Les nouveaux mots de passe ne correspondent pas.')
        else:
            messages.error(request, 'Le mot de passe actuel est incorrect.')

    context = {
        'Prof': prof_instance,  
    }
    return render(request, 'platformTK/Prof/change_password_prof.html', context)





from django.utils import timezone
from django.db.models import OuterRef, Subquery, Sum
from datetime import timedelta


@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def group_detail(request, code_group):
    group = get_object_or_404(Groups, code_group=code_group)
    schedules = group.schedules.all()

    memberships_subquery = Membership.objects.filter(
        group=group,
        etudiant=OuterRef('pk')
    ).values('etudiant').annotate(
        total_points=Sum('pointsG')
    ).values('total_points')
    
    students = group.etudiants.annotate(
        pointsG=Subquery(memberships_subquery, output_field=models.IntegerField())
    ).order_by('-pointsG') 

    return render(request, "platformTK/Prof/group_detail.html", {
        "group": group,
        "students": students,
        "schedules": schedules,
    })



@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def birthday_list(request, code_group):
    group = get_object_or_404(Groups, code_group=code_group)
    students = group.etudiants.all()

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Start of the current week (Monday)
    end_of_week = start_of_week + timedelta(days=6)  # End of the current week (Sunday)


    birthday_students = students.filter(
        date_de_naissance__month__in=[start_of_week.month, end_of_week.month],
        date_de_naissance__day__gte=start_of_week.day,
        date_de_naissance__day__lte=end_of_week.day
    ).distinct()

    return render(request, 'platformTK/Prof/birthday_list.html', {
        'group': group,
        'birthday_students': birthday_students,
    })



@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def Répartition_points(request, code_group):
    group = get_object_or_404(Groups, code_group=code_group)
    students = group.etudiants.all()
    memberships = Membership.objects.filter(group=group)
    
    memberships_dict = {membership.etudiant.id: membership.pointsG for membership in memberships}

    # Add pointsG to each student dynamically
    students_with_points = []
    for student in students:
        pointsG = memberships_dict.get(student.id, 0)
        students_with_points.append((student, pointsG))

    students_with_points = sorted(students_with_points, key=lambda x: x[1], reverse=True)

    # Extract sorted students and their pointsG
    students_sorted, points_sorted = zip(*students_with_points) if students_with_points else ([], [])

    prenom_filter = request.GET.get('prenom', '')
    nom_filter = request.GET.get('nom', '')
    code_filter = request.GET.get('code', '')

    if prenom_filter:
        students_sorted = [s for s in students_sorted if prenom_filter.lower() in s.prenom.lower()]
    if nom_filter:
        students_sorted = [s for s in students_sorted if nom_filter.lower() in s.nom.lower()]
    if code_filter:
        students_sorted = [s for s in students_sorted if code_filter.lower() in s.EtudiantCode.lower()]

    # Create a dictionary of points for filtered students
    memberships_dict_filtered = dict(zip([s.id for s in students_sorted], [points_sorted[students_with_points.index((s, p))] for s, p in students_with_points if s in students_sorted]))

    return render(request, "platformTK/Prof/Répartition_points.html", {
        "group": group,
        "students": students_sorted,
        "memberships_dict": memberships_dict_filtered,
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




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
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




@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
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





from django.db.models import Max

@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def view_attendance(request, code_group, schedule_id):
    group = get_object_or_404(Groups, code_group=code_group)
    schedule = get_object_or_404(Schedule, id=schedule_id)

    # Get the current date
    today = timezone.now().date()

    # Check if there are classes for today
    classes_today = schedule.classes.filter(date_added=today)

    # Get the classes to show (today's classes or the last class before today)
    if classes_today.exists():
        classes_to_show = classes_today
    else:
        last_class_before_today = schedule.classes.filter(date_added__lt=today).order_by('-date_added').first()
        classes_to_show = [last_class_before_today] if last_class_before_today else []

    attendance_records = []

    for class_instance in classes_to_show:
        records = Attendance.objects.filter(class_instance=class_instance, schedule=schedule)
        attendance_records.append({
            'class_instance': class_instance,
            'records': records
        })

    if classes_to_show:
        prof_name = classes_to_show[0].prof 
    else:
        prof_name = None

    return render(request, 'platformTK/Prof/view_attendance.html', {
        'group': group,
        'schedule': schedule,
        'attendance_records': attendance_records,
        'prof_name': prof_name 
    })




from django.db import IntegrityError
import locale

@login_required(login_url='login')
@allowedUsers(allowedGroups=['Prof'])
def mark_attendance(request, code_group, schedule_id):
    group = get_object_or_404(Groups, code_group=code_group)
    schedule = get_object_or_404(Schedule, id=schedule_id)

    # try:
    #     locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    # except locale.Error:
    #     locale.setlocale(locale.LC_TIME, '')  # Fallback locale

    # current_date = timezone.now().date()
    # formatted_date = current_date.strftime('%Y-%m-%d')

    # day_name = current_date.strftime('%A').capitalize()
    # class_name = f"{day_name} Cours du {formatted_date}"

    # existing_class = schedule.classes.filter(name=class_name).first()

    # if not existing_class:
    #     try:
    #         new_class = Class.objects.create(schedule=schedule, name=class_name, prof=request.user.prof)
    #         messages.success(request, f"New class '{class_name}' created for this schedule.")
    #     except IntegrityError:
    #         messages.error(request, f"Class '{class_name}' already exists.")
    #         new_class = schedule.classes.filter(name=class_name).first()
    # else:
    #     new_class = existing_class

    if request.method == 'POST':
        attendance_records = []  # Collect attendance records for later validation
        for etudiant in group.etudiants.all():
            present_status = request.POST.get(f'present_{new_class.id}_{etudiant.id}', 'off') == 'on'
            participation = request.POST.get(f'participation_{new_class.id}_{etudiant.id}') or None
            discipline = request.POST.get(f'discipline_{new_class.id}_{etudiant.id}') or None

            try:
                attendance, created = Attendance.objects.get_or_create(
                    student=etudiant,
                    group=group,
                    schedule=schedule,
                    class_instance=new_class,
                    defaults={
                        'is_present': present_status,
                        'participation': participation,
                        'discipline': discipline
                    }
                )
                if not created:
                    attendance.is_present = present_status
                    attendance.participation = participation
                    attendance.discipline = discipline
                    attendance.save()

                # Log the validation in AbsenceValidationHistory model
                attendance_records.append(attendance)  # Store attendance for later validation

            except IntegrityError:
                messages.error(request, f"Attendance already exists for {etudiant.prenom} {etudiant.nom} in {new_class.name}.")
        
        # Validate attendance records for the class on the current date
        for attendance in attendance_records:
            AbsenceValidationHistory.objects.create(
            professor=request.user.prof,
            group=group,
            date=current_date,
            absence_status="Validated",  # Set to "Validated"
            class_instance=new_class  # Link to the current class
            # Removed is_attendance since it's not a field in the model
        )

        messages.success(request, "Attendance and feedback marked successfully.")
        return redirect('group_detail', code_group=group.code_group)

    return render(request, 'platformTK/Prof/mark_attendance.html', {
        'group': group,
        'schedule': schedule,
        # 'classes': [new_class]
    })







@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def homeSuperAdmin(requset):
    return render(requset,"platformTK/SuperAdmin/homeSuperAdmin.html")



@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def add_schedule(request):
    if request.method == 'POST':
        group_id = request.POST.get('group')
        day_of_week = request.POST.get('day_of_week')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')

        schedule = Schedule(
            group_id=group_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time
        )
        schedule.save()
        return redirect('schedule_list')

    groups = Groups.objects.all()
    return render(request, 'platformTK/SuperAdmin/add_schedule.html', {'groups': groups})



@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def schedule_list(request):
    schedules = Schedule.objects.all().order_by('-date_added')
    return render(request, 'platformTK/SuperAdmin/schedule_list.html', {'schedules': schedules})




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def edit_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)

    if request.method == 'POST':
        schedule.day_of_week = request.POST.get('day_of_week')
        schedule.start_time = request.POST.get('start_time')
        schedule.end_time = request.POST.get('end_time')
        schedule.save()
        return redirect('schedule_list')

    groups = Groups.objects.all()
    return render(request, 'platformTK/SuperAdmin/edit_schedule.html', {
        'schedule': schedule,
        'groups': groups,
    })



@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def delete_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)

    if request.method == 'POST':
        schedule.delete()
        return redirect('schedule_list')

    return render(request, 'platformTK/SuperAdmin/schedule_list.html')




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def list_classes(request):
    filter_date = request.GET.get('date')
    filter_group_id = request.GET.get('group')

    classes = Class.objects.all().order_by('-date_added')


    if filter_group_id:
        classes = classes.filter(attendances__group_id=filter_group_id).distinct()

    if filter_date:
        classes = classes.filter(date_added=filter_date)

    # Pagination
    paginator = Paginator(classes, 10)
    page_number = request.GET.get('page', 1)
    paginated_classes = paginator.get_page(page_number)

    groups = Groups.objects.all()

    return render(request, 'platformTK/SuperAdmin/list_classes.html', {
        'classes': paginated_classes,
        'groups': groups,
        'filter_date': filter_date,
        'filter_group': filter_group_id,
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def view_students_in_class(request, class_code):
    class_instance = get_object_or_404(Class, class_code=class_code)
    group = class_instance.schedule.group
    students = group.etudiants.all()

    # Fetch attendance records for the specific class instance
    attendance_records = Attendance.objects.filter(class_instance=class_instance)

    professor = class_instance.prof

    return render(request, 'platformTK/SuperAdmin/view_students_in_class.html', {
        'class_instance': class_instance,
        'students': students,
        'attendance_records': attendance_records,
        'professor': professor
    })



from django.http import HttpResponse
from django.template.loader import render_to_string
from xhtml2pdf import pisa

@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def download_students_attendance_pdf(request, class_code):
    class_instance = get_object_or_404(Class, class_code=class_code)
    group = class_instance.schedule.group
    students = group.etudiants.all()
    attendance_records = Attendance.objects.filter(class_instance=class_instance)
    professor = class_instance.prof

    # Render the HTML template to a string
    html_string = render_to_string('platformTK/SuperAdmin/pdf_students_attendance.html', {
        'class_instance': class_instance,
        'students': students,
        'attendance_records': attendance_records,
        'professor': professor
    })

    # Create a PDF response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{class_instance.name}_{class_instance.prof.prenom}_{class_instance.schedule.group.name}_présence.pdf"'
    
    # Use xhtml2pdf to convert the HTML string to PDF
    pisa_status = pisa.CreatePDF(html_string, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors while generating the PDF.')

    return response





@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def add_groupe(request):
    name_filter = request.GET.get('name', '')
    code_group_filter = request.GET.get('code_group', '')

    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Groups.objects.order_by('-date_created')

    if name_filter:
        groups = groups.filter(name__icontains=name_filter)
    if code_group_filter:
        groups = groups.filter(code_group__icontains=code_group_filter)

    # Pagination
    paginator = Paginator(groups, 10)
    page_number = request.GET.get('page', 1)
    paginated_groups = paginator.get_page(page_number)

    return render(request, "platformTK/SuperAdmin/add_groupe.html", {
        'groups': paginated_groups,
        'etudiants': etudiants,
        'profs': profs,
        'name_filter': name_filter,
        'code_group_filter': code_group_filter,
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def add_student(request):
    prenom_filter = request.GET.get('prenom', '')
    nom_filter = request.GET.get('nom', '')
    etudiant_code_filter = request.GET.get('etudiant_code', '')

    etudiants = Etudiant.objects.order_by('-date_created')

    if prenom_filter:
        etudiants = etudiants.filter(prenom__icontains=prenom_filter)
    if nom_filter:
        etudiants = etudiants.filter(nom__icontains=nom_filter)
    if etudiant_code_filter:
        etudiants = etudiants.filter(EtudiantCode__icontains=etudiant_code_filter)

    # Pagination
    paginator = Paginator(etudiants, 15)  
    page_number = request.GET.get('page', 1)
    paginated_etudiants = paginator.get_page(page_number)

    groups = Groups.objects.all()
    profs = prof.objects.all()

    return render(request, "platformTK/SuperAdmin/add_student.html", {
        'groups': groups,
        'etudiants': paginated_etudiants,
        'profs': profs,
        'prenom_filter': prenom_filter,
        'nom_filter': nom_filter,
        'etudiant_code_filter': etudiant_code_filter,
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def group_list(request):
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        description = request.POST.get('description')
        student_ids_str = request.POST.get('students', '')
        prof_ids_str = request.POST.get('profs', '')

        try:
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

            # Create Membership
            for student in students:
                Membership.objects.create(etudiant=student, group=group, pointsG=0)

            messages.success(request, 'Group created successfully!')

        except Exception as e:
            messages.error(request, f'Error occurred while creating the group: {str(e)}')

        return redirect('add_groupe') 

    etudiants = Etudiant.objects.all()
    profs = prof.objects.all()
    groups = Groups.objects.all()

    return render(request, 'platformTK/SuperAdmin/add_groupe.html', {
        'groups': groups,
        'etudiants': etudiants,
        'profs': profs
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
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
        
        return redirect('add_groupe')  

    return redirect('add_groupe') 





@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def delete_group(request):
    if request.method == 'POST':
        group_id = request.POST.get('group_id')
        group = get_object_or_404(Groups, id=group_id)
        group.delete()
        messages.success(request, 'Group deleted successfully.')
    return redirect('add_groupe')



@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def add_profs_etudiants(request, group_id):
    group = get_object_or_404(Groups, id=group_id)

    professors = prof.objects.exclude(id__in=group.profs.values_list('id', flat=True))
    etudiants = Etudiant.objects.exclude(id__in=group.etudiants.values_list('id', flat=True))

    if request.method == 'POST':
        selected_profs = request.POST.get('profs', '')
        selected_etudiants = request.POST.get('etudiants', '')

        # Convert selected IDs to lists
        prof_ids = [int(prof_id) for prof_id in selected_profs.split(',') if prof_id.isdigit()]
        etudiant_ids = [int(etudiant_id) for etudiant_id in selected_etudiants.split(',') if etudiant_id.isdigit()]

        group.profs.add(*prof_ids)
        group.etudiants.add(*etudiant_ids)

        for etudiant_id in etudiant_ids:
            etudiant = Etudiant.objects.get(id=etudiant_id)
            Membership.objects.get_or_create(etudiant=etudiant, group=group)

        return redirect('add_profs_etudiants', group_id=group.id)

    return render(request, 'platformTK/SuperAdmin/add_profs_etudiants.html', {
        'group': group,
        'professors': professors,
        'etudiants': etudiants,
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def delete_profs_etudiants(request, group_id):
    group = get_object_or_404(Groups, id=group_id)
    
    if request.method == 'POST':
        selected_profs = request.POST.getlist('profs')
        selected_etudiants = request.POST.getlist('etudiants')

        # Convert selected IDs to lists
        prof_ids = [int(prof_id) for prof_id in selected_profs if prof_id.isdigit()]
        etudiant_ids = [int(etudiant_id) for etudiant_id in selected_etudiants if etudiant_id.isdigit()]

        group.profs.remove(*prof_ids)
        group.etudiants.remove(*etudiant_ids)

        # Delete Membership
        for etudiant_id in etudiant_ids:
            Membership.objects.filter(etudiant_id=etudiant_id, group=group).delete()

        return redirect('delete_profs_etudiants', group_id=group.id)

    professors = group.profs.all()
    etudiants = group.etudiants.all()

    return render(request, 'platformTK/SuperAdmin/delete_profs_etudiants.html', {
        'group': group,
        'professors': professors,
        'etudiants': etudiants,
    })



@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
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

        # Check if required fields
        if not username or not password or not prenom or not nom or not date_de_naissance or not email:
            return render(request, "platformTK/SuperAdmin/add_student.html", {
                'error': 'Please fill in all required fields.',
                'groups': groups
            })

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

                Membership.objects.create(etudiant=etudiant, group=group, pointsG=0)

            group = Group.objects.get(name="Etudiants")
            user.groups.add(group)

            messages.success(request, 'Etudiant added successfully!')
            return redirect('add_student')

        except Exception as e:
            return render(request, "platformTK/SuperAdmin/add_student.html", {
                'error': str(e),
                'groups': groups
            })

    return render(request, "platformTK/SuperAdmin/add_student.html", {'groups': groups})




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def update_etudiant(request):
    if request.method == 'POST':
        etudiant_id = request.POST.get('id')
        if not etudiant_id:
            return redirect('add_student')

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

        group_ids = request.POST.getlist('groups')
        selected_groups = Groups.objects.filter(id__in=group_ids)

        try:
            etudiant.save()

            etudiant.groups.set(selected_groups)

            existing_memberships = Membership.objects.filter(etudiant=etudiant)

            for membership in existing_memberships:
                if membership.group not in selected_groups:
                    membership.delete()

            for group in selected_groups:
                membership, created = Membership.objects.get_or_create(etudiant=etudiant, group=group)
                if created:
                    membership.pointsG = 0 
                    membership.save()

            messages.success(request, 'Etudiant details and memberships updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating etudiant: {str(e)}')

        return redirect('add_student')

    return redirect('add_student')



@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def delete_etudiant(request, etudiant_id):
    etudiant = get_object_or_404(Etudiant, id=etudiant_id)

    if request.method == 'POST':
        etudiant.delete()
        messages.success(request, 'Etudiant deleted successfully!')
        return redirect('add_student')

    return redirect('add_student')





import pandas as pd
import logging

logger = logging.getLogger(__name__)

@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def add_students_from_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        
        if not file:
            messages.error(request, 'No file uploaded.')
            return render(request, "platformTK/SuperAdmin/add_student.html")

        if file.name.endswith('.xlsx'):
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
                    email = row.get('email', '')  # Email is now optional
                    numéro_de_téléphone = row.get('numéro_de_téléphone', '')
                    avatar = None

                    # Skip rows with missing critical fields (except email)
                    if pd.isna(username) or pd.isna(password) or pd.isna(prenom) or pd.isna(nom) or pd.isna(date_de_naissance):
                        logger.warning(f"Skipping row due to missing data: {row.to_dict()}")
                        continue

                    try:
                        user = User.objects.create_user(username=username, password=password)
                        Etudiant.objects.create(
                            user=user,
                            prenom=prenom,
                            nom=nom,
                            date_de_naissance=date_de_naissance,
                            email=email if email else "",  # Use empty string if email is missing
                            numéro_de_téléphone=numéro_de_téléphone,
                            avatar=avatar
                        )

                        try:
                            group = Group.objects.get(name="Etudiants")
                            user.groups.add(group)
                        except Group.DoesNotExist:
                            logger.error(f"Group 'Etudiants' not found.")
                            messages.error(request, "The group 'Etudiants' does not exist.")
                            continue

                    except Exception as e:
                        logger.error(f"Error processing row with username '{username}': {e}")
                        messages.error(request, f"Error processing row with username '{username}': {e}")

            except Exception as e:
                logger.error(f"Error reading Excel file: {e}")
                messages.error(request, 'An error occurred while reading the Excel file.')
                return redirect('add_student')

            messages.success(request, 'Students added successfully from the Excel file.')
            return redirect('add_student')

        else:
            messages.error(request, 'Unsupported file type. Please upload an Excel (.xlsx) file.')
            return render(request, "platformTK/SuperAdmin/add_student.html")

    return render(request, "platformTK/SuperAdmin/add_student.html")






@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def add_prof(request):
    prenom_filter = request.GET.get('prenom', '')
    nom_filter = request.GET.get('nom', '')
    prof_code_filter = request.GET.get('prof_code', '')

    profs = prof.objects.order_by('-date_created')

    if prenom_filter:
        profs = profs.filter(prenom__icontains=prenom_filter)
    if nom_filter:
        profs = profs.filter(nom__icontains=nom_filter)
    if prof_code_filter:
        profs = profs.filter(ProfCode__icontains=prof_code_filter)

    # Pagination
    paginator = Paginator(profs, 10)
    page_number = request.GET.get('page', 1)
    paginated_profs = paginator.get_page(page_number)

    groups = Groups.objects.all()
    etudiants = Etudiant.objects.all()

    return render(request, "platformTK/SuperAdmin/add_prof.html", {
        'groups': groups,
        'etudiants': etudiants,
        'profs': paginated_profs,
        'prenom_filter': prenom_filter,
        'nom_filter': nom_filter,
        'prof_code_filter': prof_code_filter,
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
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

        if not (prenom and nom and date_de_naissance and email and username and password):
            return render(request, 'platformTK/SuperAdmin/add_prof.html', {
                'error': 'Please fill in all required fields.',
                'groups': groups,
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'platformTK/SuperAdmin/add_prof.html', {
                'error': 'Username already exists.',
                'groups': groups,
            })

        try:
            # user = User.objects.create_user(username=username, password=password, email=email)
            user = User.objects.create_user(username=username, password=password)

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

            messages.success(request, 'Prof added successfully!')
            return redirect('add_prof')
        except Exception as e:
            return render(request, 'platformTK/SuperAdmin/add_prof.html', {
                'error': f'Error creating professor: {e}',
                'groups': groups,
            })

    return render(request, 'platformTK/SuperAdmin/add_prof.html', {
        'groups': groups,
        'profs': profs,
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def update_prof(request, prof_id):
    professor = get_object_or_404(prof, id=prof_id)
    
    if request.method == 'POST':
        professor.prenom = request.POST.get('prenom')
        professor.nom = request.POST.get('nom')
        professor.email = request.POST.get('email')
        professor.date_de_naissance = request.POST.get('date_de_naissance')
        professor.numéro_de_téléphone = request.POST.get('numéro_de_téléphone')

        # Handle avatar update
        if request.FILES.get('avatar'):
            professor.avatar = request.FILES['avatar']

        group_ids = request.POST.getlist('groups') 
        selected_groups = Groups.objects.filter(id__in=group_ids)

        try:
            professor.save()
            professor.groups.set(selected_groups) 
            messages.success(request, 'Professor details and groups updated successfully.')
        except Exception as e:
            messages.error(request, f'Error updating professor: {str(e)}')

        return redirect('add_prof')
    else:
        all_groups = Groups.objects.all()
        return render(request, 'platformTK/SuperAdmin/add_prof.html', {'professor': professor, 'all_groups': all_groups})




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def delete_prof(request, prof_id):
    professor = get_object_or_404(prof, id=prof_id)

    if request.method == 'POST':
        try:
            professor.delete()
            messages.success(request, 'Professor deleted successfully.')
        except Exception as e:
            messages.error(request, f'Error deleting professor: {str(e)}')
        
        return redirect('prof_list')

    return render(request, 'delete_prof.html', {'professor': professor})






# Setup logger
logger = logging.getLogger(__name__)

@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def upload_prof_from_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')

        if not file:
            messages.error(request, 'No file uploaded.')
            return render(request, "platformTK/SuperAdmin/add_prof.html")

        if file.name.endswith('.csv'):
            try:
                data = csv.reader(file.read().decode('utf-8').splitlines())
                next(data)

                for row in data:
                    if len(row) < 6:
                        continue

                    username, password, prenom, nom, date_de_naissance, email, *rest = row
                    numéro_de_téléphone = rest[0] if rest else ""
                    avatar = None

                    if not username or not password or not prenom or not nom or not date_de_naissance or not email:
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
                    avatar = None

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
@allowedUsers(allowedGroups=['SuperAdmin'])
def list_parents(request):
    parents = Parents.objects.all().order_by('-date_created')
    # Fetch all etudiants to populate the selection options
    etudiants = Etudiant.objects.all()
    
    return render(request, 'platformTK/SuperAdmin/list_parents.html', {
        'parents': parents, 
        'etudiants': etudiants,
    })



from django.core.files.storage import FileSystemStorage

@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def add_parent(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        prenom = request.POST.get('prenom')
        nom = request.POST.get('nom')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        avatar = request.FILES.get('avatar')
        etudiant_ids = request.POST.getlist('etudiants')  # Get the list of selected etudiants

        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Un utilisateur avec ce nom existe déjà.')
            return redirect('list_parents')

        # Check if email exists
        if email and Parents.objects.filter(email=email).exists():
            messages.error(request, 'Un parent avec cet email existe déjà.')
            return redirect('list_parents')

        # Create a new User
        user = User.objects.create_user(username=username, password=password)

        # Create a new Parents object
        parent = Parents(
            user=user,
            prenom=prenom,
            nom=nom,
            email=email if email else None,
            numéro_de_téléphone=phone,
            avatar=avatar if avatar else None,
        )
        parent.save()

        # Assign etudiants to the parent
        if etudiant_ids:
            parent.etudiants.set(etudiant_ids)

        # Assign the user to the 'Parents' group
        parents_group, created = Group.objects.get_or_create(name='Parents')
        user.groups.add(parents_group)

        messages.success(request, 'Parent ajouté avec succès.')
        return redirect('list_parents')

    
    return render(request, 'platformTK/SuperAdmin/add_parent.html')




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def store_admin(request):
    name_filter = request.GET.get('name', '')
    category_filter = request.GET.get('category', '')

    products = Product.objects.order_by('-date_added')
    
    if name_filter:
        products = products.filter(name__icontains=name_filter)
    if category_filter:
        products = products.filter(category__name__icontains=category_filter)

    # Pagination
    paginator = Paginator(products, 5) 
    page_number = request.GET.get('page', 1)
    paginated_products = paginator.get_page(page_number)

    categories = Category.objects.all()

    return render(request, "platformTK/SuperAdmin/store_admin.html", {
        'products': paginated_products,
        'categories': categories,
        'name_filter': name_filter,
        'category_filter': category_filter,
    })




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
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
@allowedUsers(allowedGroups=['SuperAdmin'])
def update_product(request, product_code):
    product = get_object_or_404(Product, ProductCode=product_code)

    if request.method == 'POST':
        product.name = request.POST['name']
        product.description = request.POST['description']
        
        category_id = request.POST.get('category')
        try:
            category = Category.objects.get(id=category_id)
            product.category = category
        except Category.DoesNotExist:
            messages.error(request, 'Selected category does not exist.')
            return redirect('store_admin')

        product.price = request.POST['price']
        product.stock = request.POST['stock']

        if 'image' in request.FILES:
            product.image = request.FILES['image']

        product.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('store_admin')

    context = {
        'product': product,
        'categories': Category.objects.all(),
    }
    return render(request, 'platformTK/SuperAdmin/update_product.html', context)




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def delete_product(request, product_code):
    product = get_object_or_404(Product, ProductCode=product_code)
    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('store_admin')





@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def commandes_admin(request):
    commande_code_filter = request.GET.get('commande_code', '')
    status_filter = request.GET.get('status', '')

    commandes = Commande.objects.order_by('-date_ordered')
    
    if commande_code_filter:
        commandes = commandes.filter(commande_code__icontains=commande_code_filter)
    if status_filter:
        commandes = commandes.filter(status=status_filter)

    # Pagination
    paginator = Paginator(commandes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'commande_code_filter': commande_code_filter,
        'status_filter': status_filter,
    }
    return render(request, "platformTK/SuperAdmin/commandes_admin.html", context)




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def update_commande_status(request):
    if request.method == 'POST':
        commande_id = request.POST.get('commande_id')
        new_status = request.POST.get('status')
        
        commande = get_object_or_404(Commande, id=commande_id)
        commande.status = new_status
        commande.save()

        messages.success(request, 'Commande status updated successfully.')
        return redirect('commandes_admin')

    return redirect('commandes_admin')




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def list_categories(request):
    categories = Category.objects.all().order_by('-date_added')
    return render(request, 'platformTK/SuperAdmin/list_categories.html', {'categories': categories})



@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
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

    return redirect('list_categories')




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def edit_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category_name = request.POST.get('category_name')
        
        category = get_object_or_404(Category, id=category_id)
        category.name = category_name
        category.save()

        messages.success(request, 'Category updated successfully!')
        return redirect('list_categories')

    return redirect('list_categories')




@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def delete_category(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        
        category = get_object_or_404(Category, id=category_id)
        category.delete()

        messages.success(request, 'Category deleted successfully!')
        return redirect('list_categories')

    return redirect('list_categories')





@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def rapports(request):
    students = Etudiant.objects.all()
    return render(request, 'platformTK/SuperAdmin/rapports.html', {'students': students})



from django.shortcuts import render
from .models import Groups, Attendance

def absence_by_group(request):
    groups = Groups.objects.prefetch_related('etudiants').all()
    
    group_absence_data = []
    for group in groups:
        etudiant_data = []
        for etudiant in group.etudiants.all():
            absences = Attendance.objects.filter(group=group, student=etudiant, is_present=False).count()
            total_sessions = Attendance.objects.filter(group=group, student=etudiant).count()
            etudiant_data.append({
                'id': etudiant.id,  # Include the student's ID for the form
                'prenom': etudiant.prenom,
                'nom': etudiant.nom,
                'absences': absences,
                'total_sessions': total_sessions,
                'attendance_rate': (total_sessions - absences) / total_sessions * 100 if total_sessions > 0 else 0
            })
        
        group_absence_data.append({
            'group_name': group.name,
            'etudiants': etudiant_data
        })
    
    return render(request, 'platformTK/SuperAdmin/absence_by_group.html', {'group_absence_data': group_absence_data})


import csv
from django.http import HttpResponse
from .models import Groups, Attendance

def download_group_report_csv(request, group_name):
    group = Groups.objects.prefetch_related('etudiants').get(name=group_name)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{group_name}_absences.csv"'

    writer = csv.writer(response)
    writer.writerow(['Prénom', 'Nom', 'Absences', 'Total Séances', 'Pourcentage de Présence'])

    for etudiant in group.etudiants.all():
        absences = Attendance.objects.filter(group=group, student=etudiant, is_present=False).count()
        total_sessions = Attendance.objects.filter(group=group, student=etudiant).count()
        attendance_rate = (total_sessions - absences) / total_sessions * 100 if total_sessions > 0 else 0
        writer.writerow([etudiant.prenom, etudiant.nom, absences, total_sessions, f"{attendance_rate:.2f}%"])

    return response


from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from .models import Groups, Attendance

def download_group_report_pdf(request, group_name):
    group = Groups.objects.prefetch_related('etudiants').get(name=group_name)
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{group_name}_absences.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica", 12)
    p.drawString(100, height - 50, f"Rapport d'Absence pour le Groupe: {group_name}")

    y_position = height - 100
    p.drawString(50, y_position, "Prénom")
    p.drawString(150, y_position, "Nom")
    p.drawString(250, y_position, "Absences")
    p.drawString(350, y_position, "Total Séances")
    p.drawString(450, y_position, "Pourcentage de Présence")

    y_position -= 30

    for etudiant in group.etudiants.all():
        absences = Attendance.objects.filter(group=group, student=etudiant, is_present=False).count()
        total_sessions = Attendance.objects.filter(group=group, student=etudiant).count()
        attendance_rate = (total_sessions - absences) / total_sessions * 100 if total_sessions > 0 else 0

        p.drawString(50, y_position, etudiant.prenom)
        p.drawString(150, y_position, etudiant.nom)
        p.drawString(250, y_position, str(absences))
        p.drawString(350, y_position, str(total_sessions))
        p.drawString(450, y_position, f"{attendance_rate:.2f}%")
        
        y_position -= 20
        if y_position < 50:  # Check if we are at the bottom of the page
            p.showPage()  # Start a new page
            p.setFont("Helvetica", 12)
            y_position = height - 50  # Reset y_position

    p.showPage()
    p.save()

    return response



from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
import logging

logger = logging.getLogger(__name__)

def generate_absence_pdf(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        try:
            # Fetch the student from the database
            etudiant = Etudiant.objects.get(id=student_id)
            logger.debug(f"Student Name: {etudiant.prenom} {etudiant.nom}")  # Debug student name

            # Fetch attendance records for the student
            attendance_records = Attendance.objects.filter(student=etudiant)
            total_sessions = attendance_records.count()
            absences = attendance_records.filter(is_present=False).count()

            # Calculate attendance rate
            if total_sessions > 0:
                attendance_rate = ((total_sessions - absences) / total_sessions) * 100
            else:
                attendance_rate = 0

            # Prepare context for the PDF template
            context = {
                'student': etudiant,
                'attendance_records': attendance_records,
                'total_sessions': total_sessions,
                'absences': absences,
                'attendance_rate': attendance_rate,
            }

            # Load the PDF template
            template = get_template('platformTK/SuperAdmin/absence_report_template.html')
            # Render the template with context data
            html = template.render(context)

            # Generate the PDF response
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{etudiant.prenom}_{etudiant.nom}_absence_report.pdf"'  # Filename setup

            # Create PDF using xhtml2pdf
            pisa_status = pisa.CreatePDF(html, dest=response)

            # Check for PDF generation errors
            if pisa_status.err:
                logger.error(f'PDF generation error: {pisa_status.err}')
                return HttpResponse(f'We had some errors <pre>{html}</pre>')

            return response
        except Etudiant.DoesNotExist:
            return render(request, 'student_not_found.html')
    else:
        return HttpResponse("Invalid request method.", status=400)



from django.shortcuts import render

def create_classes_aa(request):
    return render(request, 'platformTK/SuperAdmin/create_classes.html')




from datetime import timedelta, date
from django.http import JsonResponse
from django.utils import timezone
import locale

def create_classes_for_next_week(request):
    if request.method == 'POST':
        try:
            # Set locale for French language
            try:
                locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
            except locale.Error:
                locale.setlocale(locale.LC_TIME, '')  # Fallback locale

            # Get the current date
            current_date = timezone.now().date()
            start_of_week = current_date + timedelta(days=(0 - current_date.weekday()))  # Get this week's Monday
            end_of_week = start_of_week + timedelta(days=6)  # Get this week's Sunday
            
            # Get all schedules for all days
            all_schedules = Schedule.objects.all()

            if not all_schedules.exists():
                return JsonResponse({'message': 'No schedules found to create classes.'}, status=404)

            # Create classes for all schedules
            created_classes = []
            for schedule in all_schedules:
                # Check if classes already exist for this schedule in the current week
                class_exists = Class.objects.filter(schedule=schedule, date_added__range=[start_of_week, end_of_week]).exists()
                
                # If no class exists for this schedule this week, create classes for each day of the week
                if not class_exists:
                    # Get the day of the week for the schedule
                    day_of_week = schedule.day_of_week  # Assuming 'day_of_week' is a field in your Schedule model
                    # Convert the day_of_week to a date (e.g., "Lundi" to Monday)
                    day_offset = (list(["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]).index(day_of_week))
                    next_day = start_of_week + timedelta(days=day_offset)  # Calculate the date for the specific day

                    formatted_date = next_day.strftime('%Y-%m-%d')  # Format date
                    class_name = f"{day_of_week} Cours du {formatted_date}"  # Set the class name

                    # Create the new class
                    new_class = Class.objects.create(
                        schedule=schedule,
                        name=class_name,  # Set the new class name
                        date_added=next_day,  # Set the date for the class
                        prof=None  # You can leave this empty or assign later
                    )
                    created_classes.append(new_class)

            # Response showing how many classes were created
            return JsonResponse({'message': f'Created {len(created_classes)} classes for the week!'})

        except Exception as e:
            return JsonResponse({'message': 'There was an error creating the classes.', 'error': str(e)}, status=500)

    return JsonResponse({'message': 'Invalid request method.'}, status=405)





def absence_by_student(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')

        # Try to find the student by ID
        try:
            etudiant = Etudiant.objects.get(id=student_id)
        except Etudiant.DoesNotExist:
            # If no student is found, render the 'student_not_found.html' template
            return render(request, 'student_not_found.html')

        # If a student is found, retrieve their attendance records
        attendance_records = Attendance.objects.filter(student=etudiant)
        total_sessions = attendance_records.count()
        absences = attendance_records.filter(is_present=False).count()
        
        if total_sessions > 0:
            attendance_rate = ((total_sessions - absences) / total_sessions) * 100
        else:
            attendance_rate = 0

        # Render the report with the context
        return render(request, 'platformTK/SuperAdmin/absence_by_student.html', {
            'student': etudiant,
            'attendance_records': attendance_records,
            'total_sessions': total_sessions,
            'absences': absences,
            'attendance_rate': attendance_rate,
        })
    return render(request, 'student_not_found.html')



from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')

    # Get the student's name from the context dictionary
    student_name = f"{context_dict['student'].prenom}_{context_dict['student'].nom}"
    
    # Sanitize the filename by replacing spaces with underscores and removing any unwanted characters
    sanitized_student_name = ''.join(e if e.isalnum() or e == '_' else '_' for e in student_name)
    
    # Set the filename with the student's name
    response['Content-Disposition'] = f'attachment; filename="rapport_absence_{sanitized_student_name}.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse('We had some errors <pre>' + html + '</pre>')
    
    return response



def download_absence_report(request, student_id):
    # Fetch attendance records for the specific student
    student = Etudiant.objects.get(id=student_id)  # Adjust this line as needed
    attendance_records = Attendance.objects.filter(student=student)

    total_sessions = attendance_records.count()
    absences = attendance_records.filter(is_present=False).count()
    attendance_rate = ((total_sessions - absences) / total_sessions * 100) if total_sessions > 0 else 0

    context = {
        'student': student,
        'attendance_records': attendance_records,
        'total_sessions': total_sessions,
        'absences': absences,
        'attendance_rate': attendance_rate,
    }
    
    return render_to_pdf('platformTK/SuperAdmin/pdf_absence_report_by_student.html', context)




def rapport_soldes(request):
    group_soldes_data = []

    # Fetch all groups with their memberships
    groups = Groups.objects.prefetch_related('membership_set').all()

    for group in groups:
        etudiant_data = []
        for membership in group.membership_set.all():
            if membership.etudiant:  # Ensure the student is not None
                etudiant_data.append({
                    'id': membership.etudiant.id,  # Add the ID of the student
                    'prenom': membership.etudiant.prenom,
                    'nom': membership.etudiant.nom,
                    'pointsG': membership.pointsG,
                })

        group_soldes_data.append({
            'group_name': group.name,
            'etudiants': etudiant_data
        })

    return render(request, 'platformTK/SuperAdmin/rapport_soldes.html', {'group_soldes_data': group_soldes_data})





from django.shortcuts import render, get_object_or_404
from .models import Etudiant, Membership

def student_detail_report(request, id):
    # Get the specific student by id
    etudiant = get_object_or_404(Etudiant, id=id)

    # Fetch the membership instance related to this student
    membership = Membership.objects.filter(etudiant=etudiant).first()  # Get the first membership or None if no memberships exist

    # # Debugging output
    # if membership:
    #     print(f"Membership found: {membership.id}, Points: {membership.pointsG}")
    # else:
    #     print("No membership found for this student.")

    # Get the pointsG from the membership, if it exists
    pointsG = membership.pointsG if membership else 0  # Set to 0 or any default if no membership is found

    # Fetch the first group this student belongs to (assuming one group for simplicity)
    group = etudiant.groups.first()  # Get the first group or None if no groups exist
    group_name = group.name if group else "Aucun groupe"  # Set group name or default

    # Prepare context for the template
    context = {
        'etudiant': etudiant,
        'group_name': group_name,  # Pass group name to context
        'pointsG': pointsG  # Pass pointsG to context
    }

    return render(request, 'platformTK/SuperAdmin/student_detail_report.html', context)




from collections import defaultdict


def competition_history(request):
    competitions = Competitions.objects.all().order_by('-date_created')
    sorted_students = []

    # Loop through each competition
    for competition in competitions:
        students_points = defaultdict(int)

        # Loop through sections in the competition
        for section in competition.sections.all():
            for etudiant in section.etudiants.all():
                students_points[etudiant] += section.points  # Sum points from each section for each student

        # Sort the students by points in descending order
        sorted_students = sorted(students_points.items(), key=lambda x: x[1], reverse=True)

    return render(request, 'platformTK/SuperAdmin/competition_history.html', {
        'competitions': competitions,
        'sorted_students': sorted_students,  # Pass the sorted students to the template
    })



def participation_discipline(request):
    groups = Groups.objects.all()
    students_list = Etudiant.objects.all()  # List all students for user selection modal
    students = []
    selected_group_name = "All Groups"  # Default name for 'all' option
    selected_user = None  # To handle selected user
    attendances = Attendance.objects.none()  # Initialize attendances to avoid UnboundLocalError

    # Check if POST request
    if request.method == "POST":
        selected_group_id = request.POST.get('group_id')
        selected_user_id = request.POST.get('user_id')
    else:
        selected_group_id = groups.first().id if groups.exists() else None
        selected_user_id = None

    # If both group and user are selected, filter attendances by both
    if selected_group_id == 'all':
        attendances = Attendance.objects.all()
    elif selected_group_id:
        attendances = Attendance.objects.filter(group_id=selected_group_id)
        selected_group = Groups.objects.get(id=selected_group_id)
        selected_group_name = selected_group.name

    # Filter by selected user if provided, and adjust attendances accordingly
    if selected_user_id:
        selected_user = Etudiant.objects.get(id=selected_user_id)
        if attendances.exists():  # If attendances were already filtered by group, filter by user
            attendances = attendances.filter(student=selected_user)
        else:  # If no group was selected, just filter by user
            attendances = Attendance.objects.filter(student=selected_user)

    for attendance in attendances:
        try:
            membership = Membership.objects.get(etudiant=attendance.student, group=attendance.group)
            pointsG = membership.pointsG
        except Membership.DoesNotExist:
            pointsG = 'N/A'

        student_data = {
            'student': attendance.student,
            'group': attendance.group.name,
            'participation': attendance.participation,
            'discipline': attendance.discipline,
            'balance': pointsG
        }
        students.append(student_data)

    context = {
        'students': students,
        'groups': groups,
        'students_list': students_list,  # Pass student list to the template for the user modal
        'selected_group_name': selected_group_name,
        'selected_user': selected_user,  # Optional: track selected user
    }
    return render(request, 'platformTK/SuperAdmin/participation_discipline.html', context)





from itertools import groupby
from operator import attrgetter
from django.http import HttpResponse

from itertools import groupby
from operator import attrgetter

@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])  # Restrict access to SuperAdmin only
def validate_absences_history(request):
    # Fetch all validation history and order by class_instance to enable grouping
    history = AbsenceValidationHistory.objects.order_by('class_instance')

    # Group the history by class_instance
    grouped_history = groupby(history, key=attrgetter('class_instance'))

    # Get only the first record from each class_instance
    first_record_per_class = [(key, list(group)[0]) for key, group in grouped_history]

    return render(request, 'platformTK/SuperAdmin/absence_validation_history.html', {
        'first_record_per_class': first_record_per_class
    })



import json
from django.shortcuts import render
from .models import Attendance

def absenteeism_report(request):
    attendances = Attendance.objects.all()
    absenteeism_data = {}

    for attendance in attendances:
        class_instance = attendance.class_instance
        date = str(attendance.date)  # Convert date to string
        
        # Ensure class is tracked separately
        if class_instance.name not in absenteeism_data:
            absenteeism_data[class_instance.name] = {}

        # Ensure date is properly tracked
        if date not in absenteeism_data[class_instance.name]:
            absenteeism_data[class_instance.name][date] = {'absent': 0, 'total': 0}

        absenteeism_data[class_instance.name][date]['total'] += 1
        if not attendance.is_present:
            absenteeism_data[class_instance.name][date]['absent'] += 1

    # Now calculate the absenteeism percentages
    formatted_data = {}
    for class_name, dates in absenteeism_data.items():
        formatted_data[class_name] = {}
        for date, counts in dates.items():
            percentage = (counts['absent'] / counts['total']) * 100 if counts['total'] > 0 else 0
            formatted_data[class_name][date] = percentage

    return render(request, 'platformTK/SuperAdmin/absenteeism_report.html', {
        'absenteeism_data': json.dumps(formatted_data)
    })




# @login_required(login_url='login')
# def dashboard(request):
#     return render(request, 'platformTK/dashboard.html')


from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from datetime import datetime, timedelta
import json
from django.db.models import Sum



@login_required(login_url='login')
@allowedUsers(allowedGroups=['SuperAdmin'])
def dashboard(request):
    groups = Groups.objects.all()
    competitions = Competitions.objects.all()
    etudiants = Etudiant.objects.all()
    commandes = Commande.objects.all()
    

    group_data = []
    competition_data = []
    etudiant_data = []

    total_points = 0
    total_competition_points = 0
    total_etudiant_points = 0

    previous_etudiants = Etudiant.objects.filter(date_created__lt=datetime.now())
    total_previous_etudiant_points = sum([etudiant.points for etudiant in previous_etudiants])
    total_previous_etudiants = len(previous_etudiants)
    previous_avg_etudiant_points = total_previous_etudiant_points / total_previous_etudiants if total_previous_etudiants > 0 else 0

    for group in groups:
        group_points = group.total_points()
        group_data.append({
            'name': group.name,
            'points': group_points
        })
        total_points += group_points

    total_groups = len(groups)
    avg_points = total_points / total_groups if total_groups > 0 else 0

    for competition in competitions:
        competition_points = competition.number_of_sections
        competition_data.append({
            'name': competition.name,
            'points': competition_points
        })
        total_competition_points += competition_points

    total_competitions = len(competitions)
    avg_competition_points = total_competition_points / total_competitions if total_competitions > 0 else 0

    for etudiant in etudiants:
        etudiant_points = etudiant.points
        etudiant_data.append({
            'name': f"{etudiant.prenom} {etudiant.nom}",
            'points': etudiant_points
        })
        total_etudiant_points += etudiant_points

    total_etudiants = len(etudiants)
    avg_etudiant_points = total_etudiant_points / total_etudiants if total_etudiants > 0 else 0

    total_orders = len(commandes)

    # Retrieve the count of Commandes per date
    commandes_per_date = Commande.objects.values('date_ordered__date').annotate(count=Count('id')).order_by('date_ordered__date')
    dates = [item['date_ordered__date'].strftime('%Y-%m-%d') for item in commandes_per_date]
    counts = [item['count'] for item in commandes_per_date]

    # Convert to JSON for JavaScript
    commandes_data = json.dumps({
        'dates': dates,
        'counts': counts
    })

    # Prepare data for the doughnut chart
    chart_data = {
        'labels': ['Pending', 'Completed', 'Cancelled'],
        'data': [
            Commande.objects.filter(status='Pending').count(),
            Commande.objects.filter(status='Completed').count(),
            Commande.objects.filter(status='Cancelled').count()
        ]
    }
    chart_data_json = json.dumps(chart_data)
    
    
# Retrieve the top 4 products based on total quantity ordered
    top_products = Commande.objects.values('product__name').annotate(total_quantity=Sum('quantity')).order_by('-total_quantity')[:4]
    top_product_data = [{
        'name': item['product__name'],
        'total_quantity': item['total_quantity']
    } for item in top_products]

    # Calculate the total quantity for percentage calculations
    total_quantity = sum(item['total_quantity'] for item in top_product_data)

    # Retrieve the top 7 students based on points
    top_etudiants = Etudiant.objects.order_by('-points')[:7]
    top_etudiant_data = [{
        'name': f"{etudiant.prenom} {etudiant.nom}",
        'points': etudiant.points
    } for etudiant in top_etudiants]
    
    
    professors = prof.objects.all()
    prof_data = []
    
    # Correct indentation here
    for professor in professors:
        prof_points = professor.total_points()
        prof_data.append({
            'name': f"{professor.prenom} {professor.nom}",
            'points': prof_points
        })

    # Sort professors by points and get top 4
    top_prof_data = sorted(prof_data, key=lambda x: x['points'], reverse=True)[:4]


    context = {
        'group_data': group_data,
        'competition_data': competition_data,
        'etudiant_data': etudiant_data,
        'top_etudiant_data': top_etudiant_data,
        'top_product_data': top_product_data,  
        'total_quantity': total_quantity, 
        'total_groups': total_groups,
        'total_points': total_points,
        'avg_points': avg_points,
        'avg_competition_points': avg_competition_points,
        'avg_etudiant_points': avg_etudiant_points,
        'previous_avg_etudiant_points': previous_avg_etudiant_points,
        'total_orders': total_orders,
        'commandes_data': commandes_data,
        'chart_data': chart_data_json,
        'top_prof_data': top_prof_data,
    }
    return render(request, 'platformTK/dashboard.html', context)