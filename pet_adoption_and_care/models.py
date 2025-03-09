from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.forms import ValidationError
from django.utils import timezone

class Owner(models.Model):
    owner_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=30, unique=True)
    pw = models.CharField(max_length=30)
    owner_name = models.CharField(max_length=30)
    email_id = models.EmailField(max_length=30, blank=True, null=True,unique=True)
    phone_no = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True,unique=True)
    city = models.CharField(max_length=20)
    address = models.TextField()

    # Constraint check for either email_id or phone_no being not null
    def clean(self):
        if not (self.email_id or self.phone_no):
            raise ValidationError("Either phone number or email ID must be provided.")

    def __str__(self):
        return self.user_name


class OwnedPet(models.Model):
    pet_id = models.AutoField(primary_key=True)
    pet_name = models.CharField(max_length=20)
    species = models.CharField(max_length=15)
    breed = models.CharField(max_length=20)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    ADOPTION_SOURCE_CHOICES = [('shop', 'Shop'), ('external', 'External')]
    adoption_source = models.CharField(max_length=8, choices=ADOPTION_SOURCE_CHOICES)
    adoption_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.pet_name


class HealthStatus(models.Model):
    pet = models.OneToOneField(OwnedPet, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    weight = models.PositiveIntegerField()
    allergies = models.CharField(max_length=50, blank=True, null=True)
    medications = models.CharField(max_length=100, blank=True, null=True)
    last_checkup_date = models.DateField(blank=True, null=True)
    next_checkup_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Health status of {self.pet.pet_name}"


class Manager(models.Model):
    manager_id = models.DecimalField(max_digits=3, decimal_places=0, primary_key=True)
    contact_no = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{10}$')])
    man_pw = models.CharField(max_length=10)
    last_login = models.DateTimeField(null=True, blank=True) 
    # branch_id = models.ForeignKey('Branch',on_delete=models.CASCADE,related_name='branches')

    def __str__(self):
        return f"Manager {self.manager_id}"


class Employee(models.Model):
    emp_id = models.AutoField(primary_key=True)
    emp_name = models.CharField(max_length=30)
    manager_id = models.ForeignKey(Manager, on_delete=models.CASCADE)
    salary = models.PositiveIntegerField()
    contact_no = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{10}$')])
    job_role = models.CharField(max_length=15)

    def __str__(self):
        return self.emp_name


class Branch(models.Model):
    branch_id = models.AutoField(primary_key=True)
    manager = models.ForeignKey(Manager, on_delete=models.CASCADE,related_name='managers')
    city = models.CharField(max_length=10)
    contact_no = models.CharField(max_length=10, validators=[RegexValidator(r'^\d{10}$')])
    address = models.CharField(max_length=100)

    def __str__(self):
        return f"Branch {self.branch_id} in {self.city}"


class AvailablePet(models.Model):
    av_id = models.AutoField(primary_key=True)
    species = models.CharField(max_length=15)
    breed = models.CharField(max_length=20)
    price = models.PositiveIntegerField()
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, default='Available')

    def __str__(self):
        return f"{self.species} ({self.breed})"


class AdoptionRequest(models.Model):
    request_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    pet = models.ForeignKey(AvailablePet, on_delete=models.CASCADE)
    request_date = models.DateField(default=timezone.now)
    REQSTATUS_CHOICES = [('Pending', 'Pending'), ('Approved', 'Approved'), ('Denied', 'Denied')]
    reqstatus = models.CharField(max_length=8, choices=REQSTATUS_CHOICES, default='Pending')
    notification = models.BooleanField(default=False)  # New field to track notification status

    def __str__(self):
        return f"Request {self.request_id} - {self.reqstatus}"
    
    class Meta:
        unique_together = ('owner', 'pet')

class Review(models.Model):
    review_id = models.AutoField(primary_key=True)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    SERVICE_CHOICES = [('Medical Care', 'Medical Care'), ('Adoption', 'Adoption'), ('Supplies', 'Supplies')]
    service = models.CharField(max_length=15, choices=SERVICE_CHOICES)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comments = models.TextField(blank=True, null=True)
    review_date = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Review {self.review_id} - {self.service}"


class PetSupply(models.Model):
    supply_id = models.AutoField(primary_key=True)
    SUPPLY_TYPE_CHOICES = [('food', 'Food'), ('toys', 'Toys'), ('grooming', 'Grooming'), ('healthcare', 'Healthcare'), ('accessories', 'Accessories')]
    supply_type = models.CharField(max_length=20, choices=SUPPLY_TYPE_CHOICES)
    product_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    supplier_info = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.product_name


class SupplyOrder(models.Model):
    order_id = models.AutoField(primary_key=True)
    supply = models.ForeignKey(PetSupply, on_delete=models.CASCADE)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE)
    date_placed = models.DateField(default=timezone.now)
    amount = models.PositiveIntegerField()

    def __str__(self):
        return f"Order {self.order_id}"
