from datetime import datetime, timezone,date
from functools import reduce
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse
from .forms import OwnerRegistrationForm,LoginForm
from django.urls import reverse
from django.contrib.auth import authenticate, login
from .models import Owner,Manager,AvailablePet,Branch,AdoptionRequest,Employee,OwnedPet,HealthStatus,PetSupply
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from decimal import Decimal
from datetime import timedelta,datetime
from django.db import IntegrityError
from .forms import AvailablePetForm,EmployeeForm
from django.conf import settings
from django.templatetags.static import static

def homepage(request):
    return render(request,'home_guest.html')




def register_page(request):
    return render(request,'register_page.html')

def profile(request):
    owner_id = request.session.get('owner_id')
    
    if not owner_id:
        return redirect('login')  # Redirect to login if not logged in
    
    # Retrieve the Owner's details and their adoption requests with notifications
    owner = get_object_or_404(Owner, owner_id=owner_id)
    adoption_requests = AdoptionRequest.objects.filter(owner=owner, notification=True)
    
    # Set notification to False after displaying in profile
    adoption_requests.update(notification=False)

    return render(request, 'profile.html', {'owner': owner, 'adoption_requests': adoption_requests})

def home2(request):
    return render(request,'home_user.html')

@never_cache
def about_guest(request):
    return render(request,'about_guest.html')


def about_user(request):
    return render(request,'about_user.html')

def register_page(request):
    if request.method == "POST":
        form = OwnerRegistrationForm(request.POST)
        repassword = request.POST.get('repassword')
        
        if form.is_valid() and form.cleaned_data.get("pw") == repassword:
            form.save()
            return redirect(reverse('login_page'))
        else:
            if form.cleaned_data.get("pw") != repassword:
                form.add_error("pw", "Passwords do not match")
    else:
        form = OwnerRegistrationForm()
    return render(request, 'register_page.html', {'form': form})


@never_cache
def login_page(request):
    # Get the 'next' parameter from the URL query string
    next_page = request.GET.get('next', 'Profile')  # Default to 'Profile' if 'next' isn't provided

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Check if the username and password match an entry in the Owner model
        try:
            owner = Owner.objects.get(user_name=username, pw=password)
            request.session['owner_id'] = owner.owner_id  # Save the owner ID in the session
            
            # Redirect to the next page after successful login
            return redirect(next_page)
        
        except Owner.DoesNotExist:
            # If no match is found, add an error message to be displayed in the template
            return render(request, 'login_page_user.html', {
                'error_message': "Invalid username or password",
                'next': next_page  # Include the next page in the context for the form
            })
    else:
        # Render the login page, passing the next page in the context
        return render(request, 'login_page_user.html', {'next': next_page})

@never_cache
def manager_login(request):
    # Check if the manager is already logged in
    if 'manager_id' in request.session:
        return redirect('manager_dashboard')  # Redirect to the about page if already logged in
    
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")

        try:
            manager = Manager.objects.get(manager_id=username, man_pw=password)
            request.session['manager_id'] = str(manager.manager_id)  # Save the manager ID in the session
            return redirect('manager_dashboard')  # Redirect to the About page upon successful login
        except Manager.DoesNotExist:
            # If no match is found, add an error message to be displayed in the template
            return render(request, 'login_page_manager.html', {
                'error_message': "Invalid username or password"
            })
    else:
        return render(request, 'login_page_manager.html')

@never_cache
def logout(request):
    # Clear the session data to log out
    request.session.flush()
    return redirect('home_guest') 

def search_pets(request):
    # Prepare the species and branch options for the form
    species_options = AvailablePet.objects.values_list('species', flat=True).distinct()
    branch_options = Branch.objects.values_list('city', flat=True).distinct()

    # Define price ranges with corresponding labels
    price_ranges = [
        ('0-5000', 'Up to ₹5,000'),
        ('5000-10000', '₹5,000 - ₹10,000'),
        ('10000-20000', '₹10,000 - ₹20,000'),
        ('20000+', 'Above ₹20,000'),
    ]

    return render(request, 'search_pets.html', {
        'species_options': species_options,
        'branch_options': branch_options,
        'price_ranges': price_ranges,
    })


import os

def search_results(request):
    pets = AvailablePet.objects.filter(status='Available')

    selected_species = request.GET.getlist('species')
    if selected_species:
        pets = pets.filter(species__in=selected_species)

    selected_branches = request.GET.getlist('branch')
    if selected_branches:
        pets = pets.filter(branch__city__in=selected_branches)

    # Convert breed names to image filenames with dynamic extensions


    def get_breed_image_filename(breed_name):
        base_filename = breed_name.lower().replace(" ", "_")
        static_dir = os.path.join(settings.STATICFILES_DIRS[0], 'breeds')

        for ext in ['jpg', 'png']:  # Check both jpg and png
            if os.path.exists(os.path.join(static_dir, f"{base_filename}.{ext}")):
                return f"{base_filename}.{ext}"  # ✅ Only return the filename

        return "default_pet.jpg"  # Fallback if no image is found

    for pet in pets:
        pet.image_filename = get_breed_image_filename(pet.breed)

    paginator = Paginator(pets, 5)
    page_number = request.GET.get('page')
    pets_page = paginator.get_page(page_number)

    if request.method == "POST":
        owner_id = request.session.get('owner_id')
        if not owner_id:
            return redirect('login_page')

        pet_id = request.POST.get('pet_id')
        if pet_id:
            pet = get_object_or_404(AvailablePet, pk=pet_id)
            owner = get_object_or_404(Owner, pk=owner_id)

            if not AdoptionRequest.objects.filter(owner=owner, pet=pet).exists():
                adoption_request = AdoptionRequest(owner=owner, pet=pet)
                adoption_request.save()
                messages.success(request, "Your adoption request has been submitted successfully!")
            else:
                messages.warning(request, "You have already requested adoption for this pet.")

            return redirect('search_results')

    return render(request, 'search_results.html', {
        'pets': pets_page,
        'selected_species': selected_species,
        'selected_branches': selected_branches,
    })

# @never_cache
def manager_dashboard(request):
    # Check if the manager is logged in
    if 'manager_id' not in request.session:
        return redirect('manager_login')  # Redirect to login if not logged in

    manager_id = request.session['manager_id']  # Get the manager ID from the session

    try:
        # Retrieve the branch associated with the manager
        branch = Branch.objects.get(manager_id=manager_id)

        # Get employees managed by this branch
        employees = Employee.objects.filter(manager_id=Decimal(manager_id))
        print(f"Number of employees: {employees.count()}")

        # Fetch only available pets related to this branch
        available_pets = AvailablePet.objects.filter(branch=branch, status='Available')  # Filter by status
        print(f"Number of available pets: {available_pets.count()}")

        # Fetch only pending adoption requests related to this branch
        pending_adoption_requests = AdoptionRequest.objects.filter(
            pet__branch=branch,
            reqstatus='Pending'
        )
        print(f"Number of pending requests: {pending_adoption_requests.count() if pending_adoption_requests.exists() else 0}")

        context = {
            'employees': employees,
            'available_pets': available_pets,
            'pending_adoption_requests': pending_adoption_requests,  # Pass only pending requests
        }
        return render(request, 'manager_dashboard.html', context)

    except Branch.DoesNotExist:
        return redirect('manager_login')  # Redirect if the branch does not exist
    except Exception as e:
        return render(request, 'manager_dashboard.html', {
            'error_message': "An error occurred: " + str(e),
        })
# View for All Employees
def view_all_employees(request):
    # Check if the manager is logged in
    if 'manager_id' not in request.session:
        return redirect('manager_login')

    manager_id = request.session['manager_id']

    try:
        # Retrieve the branch associated with the manager
        branch = Branch.objects.get(manager_id=manager_id)
        
        # Get employees managed by this branch
        employees = Employee.objects.filter(manager_id=Decimal(manager_id))
        context = {'employees': employees}
        return render(request, 'view_all_employees.html', context)
    except Branch.DoesNotExist:
        return redirect('manager_login')
    except Exception as e:
        return render(request, 'view_all_employees.html', {
            'error_message': "An error occurred: " + str(e),
        })


# View for All Available Pets
def view_all_available_pets(request):
    # Check if the manager is logged in
    if 'manager_id' not in request.session:
        return redirect('manager_login')

    manager_id = request.session['manager_id']

    try:
        # Retrieve the branch associated with the manager
        branch = Branch.objects.get(manager_id=manager_id)
        
        # Fetch available pets related to this branch
        available_pets = AvailablePet.objects.filter(branch=branch)
        context = {'available_pets': available_pets}
        return render(request, 'view_all_available_pets.html', context)
    except Branch.DoesNotExist:
        return redirect('manager_login')
    except Exception as e:
        return render(request, 'view_all_available_pets.html', {
            'error_message': "An error occurred: " + str(e),
        })


# View for All Adoption Requests
def view_all_adoption_requests(request):
    # Check if the manager is logged in
    if 'manager_id' not in request.session:
        return redirect('manager_login')

    manager_id = request.session['manager_id']

    try:
        # Retrieve the branch associated with the manager
        branch = Branch.objects.get(manager_id=manager_id)
        
        # Fetch only adoption requests related to this branch that are pending
        adoption_requests = AdoptionRequest.objects.filter(pet__branch=branch, reqstatus='Pending')
        
        context = {'adoption_requests': adoption_requests}
        return render(request, 'view_all_adoption_requests.html', context)
    except Branch.DoesNotExist:
        return redirect('manager_login')
    except Exception as e:
        return render(request, 'view_all_adoption_requests.html', {
            'error_message': "An error occurred: " + str(e),
        })




# def request_adoption(request):
#     if request.method == 'POST':
#         pet_id = request.POST.get('pet_id')
#         owner = get_object_or_404(Owner, user=request.user)
#         pet = get_object_or_404(AvailablePet, av_id=pet_id)
        
#         try:
#             # Attempt to create a new AdoptionRequest
#             AdoptionRequest.objects.create(owner=owner, pet=pet, reqstatus='Pending')
#             messages.success(request, "Your adoption request has been submitted successfully!")
#         except IntegrityError:
#             # Handle duplicate request
#             messages.warning(request, "You have already requested adoption for this pet.")

#         return redirect('search_results')

#     return redirect('search_results')


def approve_decline_adoption(request, request_id):
    adoption_request = get_object_or_404(AdoptionRequest, pk=request_id)

    if request.method == 'POST':
        if 'approve' in request.POST:
            adoption_request.reqstatus = 'Approved'
            adoption_request.notification = True  # Mark as notified
            adoption_request.save()

            # Update pet status to 'Adopted'
            pet = adoption_request.pet
            if pet.status == 'Available':
                pet.status = 'Adopted'  # Mark as adopted
                pet.save()

            return redirect('register_pet_and_health_status', request_id=adoption_request.request_id)

        elif 'decline' in request.POST:
            adoption_request.reqstatus = 'Denied'
            adoption_request.notification = True  # Mark as notified
            adoption_request.save()
            return redirect('manager_dashboard')

    return redirect('manager_dashboard')

def register_pet_and_health_status(request, request_id):
    adoption_request = get_object_or_404(AdoptionRequest, request_id=request_id)

    if request.method == 'POST':
        pet_name = request.POST.get('pet_name')
        species = request.POST.get('species')
        breed = request.POST.get('breed')
        adoption_source = request.POST.get('adoption_source')
        age = request.POST.get('age')
        weight = request.POST.get('weight')
        allergies = request.POST.get('allergies', '')
        medications = request.POST.get('medications', '')

        if pet_name and species and breed and adoption_source and age and weight:
            # Create OwnedPet and HealthStatus records
            owned_pet = OwnedPet.objects.create(
                pet_name=pet_name,
                species=species,
                breed=breed,
                adoption_source=adoption_source,
                adoption_date = date.today(),
                owner=adoption_request.owner,
            )

            last_checkup_date = datetime.today().date()
            next_checkup_date = last_checkup_date + timedelta(days=180)

            HealthStatus.objects.create(
                pet=owned_pet,
                age=age,
                weight=weight,
                allergies=allergies,
                medications=medications,
                last_checkup_date=last_checkup_date,
                next_checkup_date=next_checkup_date,
            )

            # Decline other requests for this pet
            AdoptionRequest.objects.filter(pet_id=adoption_request.pet_id).exclude(owner=adoption_request.owner).update(reqstatus='Denied')

            # Update pet status to Adopted after successful registration
            pet = adoption_request.pet
            pet.status = 'Adopted'
            pet.save()

            return redirect('view_all_adoption_requests')
        else:
            # Show error message if form is incomplete
            return render(request, 'register_pet_and_health_status.html', {
                'adoption_request': adoption_request,
                'error': "Please fill in all required fields."
            })

    return render(request, 'register_pet_and_health_status.html', {'adoption_request': adoption_request})
# Create your views here.
def test(request):
    employees = Employee.objects.all()
    return render(request,'test.html',{'employees':employees})

def crud_operations_employee(request):
    return render(request, 'crud_operations_employee.html')

def crud_operations_available_pet(request):
    return render(request, 'crud_operations_available_pet.html')

def create_employee(request):
    if request.method == "POST":
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)  # Don't save to the database yet
            employee.manager_id_id = request.session.get('manager_id')  # Set manager_id from session
            employee.save()  # Now save the employee
            return redirect('crud_operations_employee')  # Redirect to CRUD operations page after saving
    else:
        form = EmployeeForm()
    return render(request, 'create_employee.html', {'form': form})

def select_employee_to_update(request):
    # Check if the manager is logged in
    if 'manager_id' not in request.session:
        return redirect('manager_login')

    manager_id = request.session['manager_id']

    try:
        # Retrieve the branch associated with the manager
        branch = Branch.objects.get(manager_id=manager_id)

        # Get employees managed by this branch
        employees = Employee.objects.filter(manager_id=manager_id)

        return render(request, 'select_employee.html', {'employees': employees})

    except Branch.DoesNotExist:
        return redirect('manager_login')
    except Exception as e:
        return render(request, 'select_employee.html', {
            'error_message': "An error occurred: " + str(e),
        })

def update_employee(request, employee_id):
    employee = get_object_or_404(Employee, emp_id=employee_id)

    if request.method == "POST":
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('crud_operations_employee')  # Redirect after saving
    else:
        form = EmployeeForm(instance=employee)

    return render(request, 'update_employee.html', {'form': form, 'employee': employee})


def delete_employee(request):
    # Check if the manager is logged in
    if 'manager_id' not in request.session:
        return redirect('manager_login')

    manager_id = request.session['manager_id']
    
    # Retrieve the employees managed by the logged-in manager
    employees = Employee.objects.filter(manager_id=Decimal(manager_id))

    if request.method == "POST":
        employee_id = request.POST.get('employee_id')
        employee = get_object_or_404(Employee, emp_id=employee_id)  # Get employee by emp_id
        employee.delete()
        return redirect('crud_operations_employee')  # Redirect after deleting

    return render(request, 'delete_employee.html', {'employees': employees})

def create_available_pet(request):
    if request.method == "POST":
        form = AvailablePetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('crud_operations_available_pet')  # Redirect after saving
    else:
        form = AvailablePetForm()
    return render(request, 'create_available_pet.html', {'form': form})

def select_available_pet_to_update(request):
    # Check if the manager is logged in
    if 'manager_id' not in request.session:
        return redirect('manager_login')

    manager_id = request.session['manager_id']

    try:
        # Retrieve the branch associated with the manager
        branch = Branch.objects.get(manager_id=manager_id)

        # Get available pets related to this branch with status 'Available'
        available_pets = AvailablePet.objects.filter(branch=branch, status='Available')

        return render(request, 'select_available_pet.html', {'available_pets': available_pets})

    except Branch.DoesNotExist:
        return redirect('manager_login')
    except Exception as e:
        return render(request, 'select_available_pet.html', {
            'error_message': "An error occurred: " + str(e),
        })




def update_available_pet(request, pet_id):
    pet = get_object_or_404(AvailablePet, av_id=pet_id)

    if request.method == "POST":
        form = AvailablePetForm(request.POST, instance=pet)
        if form.is_valid():
            form.save()
            return redirect('crud_operations_available_pet')  # Redirect after saving
    else:
        form = AvailablePetForm(instance=pet)

    return render(request, 'update_available_pet.html', {'form': form, 'pet': pet})

def delete_available_pet(request):
    # Check if the manager is logged in
    if 'manager_id' not in request.session:
        return redirect('manager_login')

    manager_id = request.session['manager_id']
    
    try:
        # Retrieve the branch associated with the manager
        branch = Branch.objects.get(manager_id=manager_id)
        
        # Fetch available pets related to this branch
        pets = AvailablePet.objects.filter(branch=branch,status='Available')

        if request.method == "POST":
            pet_id = request.POST.get('pet_id')
            pet = get_object_or_404(AvailablePet, av_id=pet_id)  # Get pet by av_id
            pet.delete()
            return redirect('crud_operations_available_pet')  # Redirect after deleting

        return render(request, 'delete_available_pet.html', {'pets': pets})

    except Branch.DoesNotExist:
        return redirect('manager_login')
    except Exception as e:
        return render(request, 'delete_available_pet.html', {
            'error_message': "An error occurred: " + str(e),
        })
def register_pet_page(request):
    if request.method == 'POST':
        pet_name = request.POST.get('pet_name')
        species = request.POST.get('species')
        breed = request.POST.get('breed')
        adoption_source = request.POST.get('adoption_source')
        age = request.POST.get('age')
        weight = request.POST.get('weight')
        allergies = request.POST.get('allergies', '')
        medications = request.POST.get('medications', '')

        if pet_name and species and breed and adoption_source and age and weight:
            # Create OwnedPet and HealthStatus records
            owned_pet = OwnedPet.objects.create(
                pet_name=pet_name,
                species=species,
                breed=breed,
                adoption_source=adoption_source,
                adoption_date=date.today(),
                # Assume owner is obtained from the current logged-in user
                owner=request.user,
            )

            last_checkup_date = datetime.today().date()
            next_checkup_date = last_checkup_date + timedelta(days=180)

            HealthStatus.objects.create(
                pet=owned_pet,
                age=age,
                weight=weight,
                allergies=allergies,
                medications=medications,
                last_checkup_date=last_checkup_date,
                next_checkup_date=next_checkup_date,
            )

            return redirect('appointment')  # Redirect to a success page or another view
        else:
            # Show error message if form is incomplete
            return render(request, 'register_pet_page.html', {
                'error': "Please fill in all required fields."
            })

    return render(request, 'register_pet_page.html')

def appointment(request):
    return render(request,'appointment.html')

def supplies(request):
    pet_supplies = PetSupply.objects.all()  # Fetch all pet supplies from the database
    return render(request, 'supplies.html', {'pet_supplies': pet_supplies})

def ordered(request):
    return render(request,'ordered.html')

# from .models import PetSupply, SupplyOrder

# @login_required
# def proceed_to_payment(request):
#     cart = request.session.get('cart', {})
#     user = request.user

#     if not cart:
#         # If the cart is empty, redirect to the cart page with a message
#         return redirect('cart_page')

#     # Process each item in the cart
#     for supply_id, quantity in cart.items():
#         try:
#             supply_item = PetSupply.objects.get(supply_id=supply_id)
#             total_price = supply_item.unit_price * quantity

#             # Create a new SupplyOrder entry for each cart item
#             SupplyOrder.objects.create(
#                 user=user,
#                 product=supply_item,
#                 quantity=quantity,
#                 total_price=total_price
#             )
#         except PetSupply.DoesNotExist:
#             continue

#     # Clear the cart after saving the order
#     request.session['cart'] = {}

#     # Redirect to a confirmation page or success message
#     return redirect('supplies')

def book_appointment(request):
    if request.method == 'POST':
        pet_id = request.POST.get('pet_id')
        appointment_date = request.POST.get('appointment_date')
        time_slot = request.POST.get('time_slot')
        city = request.POST.get('city')

        # Update the next checkup date for the pet
        try:
            pet_health_status = HealthStatus.objects.get(pet_id=pet_id)
            pet_health_status.next_checkup_date = appointment_date  # Update to current date
            pet_health_status.save()
            # You can add a success message or redirect to another page
            return HttpResponse(f'Appointment booked successfully for Pet ID {pet_id}. Next checkup date updated.')
        except HealthStatus.DoesNotExist:
            return HttpResponse('Error: Pet ID does not exist.')
        
    return redirect('appointment')  # Redirect back to the appointment page if method is not POST

def owned_pets(request):
    # Get the logged-in user's owner ID
    owner_id = request.session.get('owner_id')
    # Fetch pets owned by the owner
    pets = OwnedPet.objects.filter(owner_id=owner_id)

    # Implement pagination
    paginator = Paginator(pets, 4)  # Show 6 pets per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    print(page_obj)

    return render(request, 'owned_pets.html', {'page_obj': page_obj})

def view_health_status(request, pet_id):
    # Retrieve the health status for the specified pet
    health_status = get_object_or_404(HealthStatus, pet_id=pet_id)
    
    return render(request, 'health_status.html', {'health_status': health_status})

def view_contacts(request):
    branches = Branch.objects.select_related('manager').all()  # Fetch all branches with related managers
    context = {
        'branches': branches,
    }
    return render(request, 'view_contacts.html', context)

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
import pdfkit
from .models import HealthStatus  # Adjust the import as needed

# Configuration for pdfkit
config = pdfkit.configuration(wkhtmltopdf=r"C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe")


def download_health_status(request, pet_id):
    # Get the health status instance
    health_status = get_object_or_404(HealthStatus, pet_id=pet_id)

    # Render the HTML template with the context
    html_content = render(request, 'health_status.html', {'health_status': health_status}).content.decode('utf-8')

    # Options for pdfkit
    options = {
        'page-size': 'A4',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
        'encoding': 'UTF-8',
        'no-stop-slow-scripts': None,
        'enable-local-file-access': None,
        'zoom': 1.0, 
    }

    # Generate PDF from HTML
    pdf = pdfkit.from_string(html_content, False, configuration=config, options=options)

    # Create the response
    response = HttpResponse(pdf, content_type='application/pdf')
    file_name = f"health_status_pet_{pet_id}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'

    return response
