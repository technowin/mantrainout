import json
import random
import string
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import  CustomUser, password_storage
# import mysql.connector as sql
from Account.serializers import *
import Db 
import bcrypt
from django.contrib.auth.decorators import login_required
# from .models import SignUpModel
# from .forms import SignUpForm
from mantra_io.encryption import *
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from Account.utils import decrypt_email, encrypt_email
import traceback
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.backends import ModelBackend
from .db_utils import callproc
from django.utils import timezone
from Account.models import *
from Masters.models import *
from MenuManager.models import *
from django.db import IntegrityError
from django.urls import reverse
from django.http import HttpResponseBadRequest
import logging
import requests
from django.db import models

# Set up logging
logger = logging.getLogger(__name__)

@csrf_exempt
def Login(request):
    if request.method=="GET":
       request.session.flush()
       return render(request,'Account/login.html')
    
    if request.method=="POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            request.session.cycle_key()
            request.session["username"]=(str(username))
            request.session["full_name"]=(str(user.full_name))
            request.session["user_id"]=(str(user.id))
            request.session["role_id"] = str(user.role_id)
            
            if remember_me == 'on':
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # Browser close
            return redirect('home') 
        else:
            messages.error(request, 'Invalid Credentials')
            return redirect("Login")



def logoutView(request):
    logout(request)
    return redirect("Account")  

def register_new_user(request):
    if request.method=="GET":
        id = request.GET.get('id', '0')
        roles = callproc("stp_get_dropdown_values",['roles'])
       
        
        if id != '0':
            id1 = decrypt_parameter(id)
            users = get_object_or_404(CustomUser, id=id1)
            full_name = users.full_name.split(" ", 1) 
            first_name = full_name[0] 
            last_name = full_name[1] if len(full_name) > 1 else ""  
            context = {'users':users,'first_name':first_name,'last_name':last_name,'roles':roles}
            
        else:
            context = {'id':id,'roles': roles,}
        return render(request,'Account/register_new_user.html',context)

    if request.method == "POST":
        id = request.POST.get('id', '')
        try:  
            if id == '0':                
                firstname = request.POST.get('firstname')
                lastname = request.POST.get('lastname')
                email = request.POST.get('email')
                password = request.POST.get('password') 
                phone = request.POST.get('mobileNumber')
                role_id = request.POST.get('role_id')
                full_name = f"{firstname} {lastname}"
                existing_user = CustomUser.objects.filter(email=email, phone=phone, role_id=role_id).exists()
                if existing_user:
                    messages.error(request, "A user with the same email, phone, and role already exists.")
                    return redirect('/register_new_user?id=0')
                else:
                    from django.db import transaction

                    user = CustomUser(
                        full_name=full_name,email=email,phone=phone,role_id=role_id
                    )
                    user.username = user.email
                    user.is_active = True 
                    try:
                        validate_password(password, user=user)
                        user.set_password(password)
                        if existing_user:
                            user = CustomUser.objects.get(email=email, phone=phone, role_id=role_id)
                            user_id = user.id
                        else:
                            with transaction.atomic(using='default'):
                                user.save(using='default') 
                                password_storage.objects.using('default').create(user=user, passwordText=password)
                            user_id = user.id
                       
                        assigned_menus = RoleMenuMaster.objects.filter(role_id=role_id)
                        for menu in assigned_menus:
                            UserMenuDetails.objects.create(
                                user_id=user.id,
                                menu_id=menu.menu_id,
                                role_id=role_id
                        )

                        messages.success(request, "User registered successfully!")

                    except ValidationError as e:
                        messages.error(request, ' '.join(e.messages))
                    
            else:
                firstname = request.POST.get('firstname')
                lastname = request.POST.get('lastname')
                email = request.POST.get('email')
                full_name = f"{firstname} {lastname}"
                phone = request.POST.get('mobileNumber')
                role_id = request.POST.get('role_id')

                user = CustomUser.objects.get(id=id)
                user.full_name = full_name
                user.email = email
                user.phone = phone
                user.role_id = role_id
                user.save()

                messages.success(request, "User details updated successfully!")
            return redirect('/masters?entity=user&type=i')

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log",[fun,str(e),request.user.id])  
            print(f"error: {e}")
            messages.error(request, 'Oops...! Something went wrong!')
            response = {'result': 'fail','messages ':'something went wrong !'}   

def forgot_password(request):
    try:
        if request.method =="GET":
            type = request.GET.get('type')
            return render(request,'Account/forgot-password.html',{'type':type}) 
        if request.method == "POST":
            email = request.POST.get('email')
            if CustomUser.objects.filter(email=email).exists():
                messages.success(request, 'User id valid...Please update your password')
                type = 'pass'
            else:
                messages.error(request, 'User does not exist.Please Enter Correct Email.')
                type='email'
            return render(request,'Account/forgot-password.html',{'type':type,'email':email}) 

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')


def home(request):
    return render(request,'Account/home.html') 

@login_required
def search(request):
    results = []
    try:
        query = request.GET.get('q')
        if query != "":
           results = callproc("stp_get_application_search",[query])        
    except Exception as e:
        print("error-"+e)
    finally:
        return render(request, 'Bootstrap/search_results.html', {'query': query, 'results': results})

@login_required       
def change_password(request):
    try:
        if request.method == "POST":
            password = request.POST.get('password')  # The password entered by the user
            username = request.session.get('username', '')  # The username from the session
            user = CustomUser.objects.get(email=username)
            if check_password(password, user.password):
                status = "1"
            else:
                status = "0" 

    except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            fun = tb[0].name
            callproc("stp_error_log",[fun,str(e),request.user.id])  
            print(f"error: {e}")
            messages.error(request, 'Oops...! Something went wrong!')
            response = {'result': 'fail','messages ':'something went wrong !'}
    finally:
        if request.method == "GET":
            return render(request,'Account/change_password.html')
        else:
           return JsonResponse({'status': status})
        
@login_required
def reset_password(request):
    try:
        email = request.POST.get('email')
        if not email:
            email = request.session.get('username', '')
        password = request.POST.get('password')
        user = CustomUser.objects.get(email=email)
        # Update password
        user.set_password(password)
        user.save()
        messages.success(request, 'Password has been successfully updated.')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')
    
    finally:
        return redirect( f'change_password')
    
@login_required    
def forget_password_change(request):
    try:
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = CustomUser.objects.get(email=email)
        user.set_password(password)
        user.save()
        messages.success(request, 'Password has been successfully updated.')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), request.user.id])
        messages.error(request, 'Oops...! Something went wrong!')
    
    finally:
        return redirect( f'Login')
        
def dashboard(request):
    return render(request,'Bootstrap/index.html') 

def buttons(request):
    return render(request,'Bootstrap/buttons.html') 

def cards(request):
    return render(request,'Bootstrap/cards.html') 

def utilities_color(request):
    return render(request,'Bootstrap/utilities-color.html') 

def utilities_border(request):
    return render(request,'Bootstrap/utilities-border.html') 

def utilities_animation(request):
    return render(request,'Bootstrap/utilities-animation.html') 

def utilities_other(request):
    return render(request,'Bootstrap/utilities-other.html') 

def error_page(request):
    return render(request,'Bootstrap/404.html')

def blank(request):
    return render(request,'Bootstrap/blank.html')

def charts(request):
    return render(request,'Bootstrap/charts.html')

def tables(request):
    return render(request,'Bootstrap/tables.html')

    try:
        if request.method == "GET":
            request.session.flush()            
            service_db = request.GET.get('service_db')
            request.session['service_db'] = service_db
            return render(request, 'citizenAccount/aplesarkarLogin.html',{'service_db':service_db})

        elif request.method == "POST":
            service_db = request.POST.get('service_db')
            request.session['service_db'] = service_db
            phone_number = request.POST.get('username', '').strip()

            if phone_number:
                if CustomUser.objects.filter(phone=phone_number, role_id=2).exists():
                    request.session['phone_number'] = phone_number
                    return redirect(f'/OTPScreen?service_db={service_db}')
                else:
                    messages.warning(request, "The phone number entered is not registered. Please register yourself.")
                    return redirect(f'/aple_sarkar_Register?service_db={service_db}')

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),phone_number])  
        messages.error(request, 'Oops...! Something went wrong!')
        return redirect(f'/aple_sarkar_Register?service_db={service_db}')