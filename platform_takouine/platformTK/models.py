from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
import uuid



def generate_etudiant_code():
    unique_id = str(uuid.uuid4()).replace('-', '')[:8]  # Take the first 8 characters of the UUID
    return f"TK-{unique_id}"


class Etudiant(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    prenom = models.CharField(max_length=50)
    nom = models.CharField(max_length=50)
    date_de_naissance = models.DateField()
    email = models.EmailField(unique=True)
    numéro_de_téléphone = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(null=True, blank=True)
    slugEtudiant = models.SlugField(blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, null=True, blank=True)
    points = models.IntegerField(default=0,blank=True, null=True) 
    EtudiantCode = models.CharField(max_length=100, null=True, blank=True, default=generate_etudiant_code)


    def save(self, *args, **kwargs):
        if not self.slugEtudiant:
            self.slugEtudiant = slugify(self.user.username) #slugify(self.user.username) 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prenom} {self.nom}"






def generate_prof_code():
    unique_id = str(uuid.uuid4()).replace('-', '')[:8]  
    return f"TK-P-{unique_id}"


class prof(models.Model):
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    prenom = models.CharField(max_length=50)
    nom = models.CharField(max_length=50)
    date_de_naissance = models.DateField()
    email = models.EmailField(unique=True)
    numéro_de_téléphone = models.CharField(max_length=15, blank=True, null=True)
    avatar = models.ImageField(null=True, blank=True)
    slugProf = models.SlugField(blank=True, null=True)
    date_created = models.DateField(auto_now_add=True, null=True, blank=True)
    ProfCode = models.CharField(max_length=100, null=True, blank=True, default=generate_prof_code)


    def save(self, *args, **kwargs):
        if not self.slugProf:
            self.slugProf = slugify(self.user.username) #slugify(self.user.username) 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.prenom} {self.nom}"



def generate_group_code():
    unique_id = str(uuid.uuid4()).replace('-', '')[:8]  # Generate a unique ID
    return f"GRP-{unique_id}"



class Groups(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    code_group = models.CharField(max_length=100, unique=True, blank=True, editable=False)
    etudiants = models.ManyToManyField(Etudiant, related_name='groups')
    profs = models.ManyToManyField(prof, related_name='groups')
    date_created = models.DateField(auto_now_add=True, null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.code_group:
            self.code_group = generate_group_code()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def total_points(self):
        return self.etudiants.aggregate(total_points=models.Sum('points'))['total_points'] or 0






class Competitions(models.Model):
    name = models.CharField(max_length=100)
    number_of_sections = models.PositiveIntegerField()  # Number of sections for the competition

    def __str__(self):
        return self.name



class Sections(models.Model):
    competition = models.ForeignKey(Competitions, on_delete=models.CASCADE, related_name='sections')
    section_name = models.CharField(max_length=100)  # Name of the section
    etudiants = models.ManyToManyField('Etudiant', related_name='sections')  # Many-to-many relationship with Etudiants

    def __str__(self):
        return f"{self.competition.name} - {self.section_name}"