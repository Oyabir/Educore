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
    points = models.IntegerField(default=0, blank=True, null=True) 
    EtudiantCode = models.CharField(max_length=100, unique=True, null=True, blank=True, default=generate_etudiant_code)

    def save(self, *args, **kwargs):
        # Ensure slugEtudiant is set based on username if not provided
        if not self.slugEtudiant:
            self.slugEtudiant = slugify(self.user.username)

        # Ensure a unique EtudiantCode is generated if it's not already set
        if self._state.adding:  # This is a new instance
            while True:
                code = generate_etudiant_code()
                if not Etudiant.objects.filter(EtudiantCode=code).exists():
                    self.EtudiantCode = code
                    break
        else:  # This is an existing instance
            if not self.EtudiantCode:
                while True:
                    code = generate_etudiant_code()
                    if not Etudiant.objects.filter(EtudiantCode=code).exists():
                        self.EtudiantCode = code
                        break

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
    
    # method to calculate total points for professor
    def total_points(self):
        # Sum points from students of the professor's groups
        total_points = sum(
            etudiant.points for group in self.groups.all() for etudiant in group.etudiants.all()
        )
        return total_points



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
    
    
    @property
    def student_names(self):
        return ', '.join(f'{student.prenom} {student.nom}' for student in self.etudiants.all())

    @property
    def professor_names(self):
        return ', '.join(f'{professeur.prenom} {professeur.nom}' for professeur in self.profs.all())


    def total_points(self):
        # Sum pointsG from Membership model for this group
        return Membership.objects.filter(group=self).aggregate(total_points=models.Sum('pointsG'))['total_points'] or 0




# class Competitions(models.Model):
#     name = models.CharField(max_length=100)
#     number_of_sections = models.PositiveIntegerField()  # Number of sections for the competition
#     groups = models.ManyToManyField('Groups', related_name='competitions', blank=True)  # Add ManyToManyField

#     def __str__(self):
#         return self.name





class Competitions(models.Model):
    name = models.CharField(max_length=100)
    number_of_sections = models.PositiveIntegerField()  # Number of sections for the competition
    group = models.ForeignKey('Groups', related_name='competitions', on_delete=models.SET_NULL, null=True, blank=True)  # Set null on delete
    date_created = models.DateField(auto_now_add=True, null=True, blank=True)
    is_finished = models.BooleanField(default=False)  # New field to track if competition is finished
    prof = models.ForeignKey('Prof', related_name='competitions', on_delete=models.SET_NULL, null=True, blank=True)  # Set null on delete

    def __str__(self):
        return self.name






class Sections(models.Model):
    competition = models.ForeignKey('Competitions', on_delete=models.SET_NULL, null=True, blank=True, related_name='sections')  # Set null on delete
    section_name = models.CharField(max_length=100)  
    etudiants = models.ManyToManyField('Etudiant', related_name='sections')  
    points = models.PositiveIntegerField(default=0)  

    def __str__(self):
        return f"{self.competition.name if self.competition else 'No Competition'} - {self.section_name} - Points: {self.points}"




class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    date_added = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name




def generate_product_code():
    unique_id = str(uuid.uuid4()).replace('-', '')[:8]  
    return f"PRO-{unique_id}"



class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True, blank=True)  # Set null on delete
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    ProductCode = models.CharField(max_length=100, null=True, blank=True, default=generate_product_code)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    def __str__(self):
        return self.name






from django.core.exceptions import ValidationError


def generate_commande_code():
    unique_id = str(uuid.uuid4()).replace('-', '')[:8]  # Generates a unique 8-character string
    return f"CMD-{unique_id}"



class Commande(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]

    etudiant = models.ForeignKey('Etudiant', on_delete=models.SET_NULL, null=True, blank=True)  # Set null on delete
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True)  # Set null on delete
    date_ordered = models.DateTimeField(auto_now_add=True)
    quantity = models.PositiveIntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    commande_code = models.CharField(max_length=100, null=True, blank=True, unique=True, default=generate_commande_code)

    def save(self, *args, **kwargs):
        # Ensure the command code is unique
        if not self.commande_code:
            self.commande_code = generate_commande_code()

        # Ensure the code is unique
        if Commande.objects.filter(commande_code=self.commande_code).exists():
            self.commande_code = generate_commande_code()

        super(Commande, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.commande_code} - {self.etudiant.user.username if self.etudiant else 'No Etudiant'} - {self.product.name if self.product else 'No Product'} - {self.status}"





class Membership(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.SET_NULL, null=True, blank=True)  # Set null on delete
    group = models.ForeignKey(Groups, on_delete=models.SET_NULL, null=True, blank=True)  # Set null on delete
    pointsG = models.IntegerField(default=0)


    def __str__(self):
        return f"{self.etudiant if self.etudiant else 'No Etudiant'} in {self.group if self.group else 'No Group'}"

