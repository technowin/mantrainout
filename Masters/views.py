import json
import pydoc
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate, login ,logout,get_user_model
from Account.forms import RegistrationForm
from Account.models import *
from Masters.models import *
import Db 
import bcrypt
from django.contrib.auth.decorators import login_required
from mantra_io.encryption import *
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
from Account.utils import decrypt_email, encrypt_email
import requests
import traceback
import pandas as pd
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.contrib import messages
import openpyxl
from openpyxl.styles import Font, Border, Side
import calendar
from datetime import datetime, timedelta
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, Count

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import AccessToken
from django.utils import timezone
from Account.models import *
from Masters.models import *
from Account.db_utils import callproc
from django.views.decorators.csrf import csrf_exempt
import os
from django.urls import reverse
from mantra_io.settings import *
import logging
from django.http import FileResponse, Http404
import mimetypes
logger = logging.getLogger(__name__)

@login_required
def masters(request):
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    entity,type,name,id,text_name,dpl,dp,em,mb = '','','','','','','','',''
    try:
        if request.user.is_authenticated ==True:                
                global user,role_id
                user = request.user.id    
                role_id = request.user.role_id 
        if request.method=="GET":
            entity = request.GET.get('entity', '')
            type = request.GET.get('type', '')
            datalist1= callproc("stp_get_masters",[entity,type,'name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", [entity, type, 'header',user])
            rows = callproc("stp_get_masters",[entity,type,'data',user])
            if entity == 'su':
                dpl = callproc("stp_get_dropdown_values",['dept'])
            id = request.GET.get('id', '')
            if type=='ed' and id != '0':
                if id != '0' and id != '':
                    id = dec(id)
                rows = callproc("stp_get_masters",[entity,type,'data',id])
                text_name = rows[0][0]
                if entity == 'su':
                    em = rows[0][1]
                    mb = rows[0][2]
                    dp = rows[0][3]
                id = enc(id)
            data = []
            for row in rows:
                encrypted_id = enc(str(row[0]))
                data.append((encrypted_id,) + row[1:])

        if request.method=="POST":
            entity = request.POST.get('entity', '')
            id = request.POST.get('id', '')
            dp = request.POST.get('dp', '')
            em = request.POST.get('em', '')
            mb = request.POST.get('mb', '')
            if id != '0' and id != '':
                id = dec(id)
            name = request.POST.get('text_name', '')
            if entity == 'su':
                datalist1= callproc("stp_post_user_masters",[id,name,em,mb,dp,user])
            else: datalist1= callproc("stp_post_masters",[entity,id,name,user])

            if datalist1[0][0] == 'insert':
                messages.success(request, 'Data inserted successfully !')
            elif datalist1[0][0] == 'update':
                messages.success(request, 'Data updated successfully !')
            elif datalist1[0][0] == 'exist':
                messages.error(request, 'Data already exist !')
            
                          
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        Db.closeConnection()
        if request.method=="GET":
            return render(request,'Master/index.html',
              {'entity':entity,'type':type,'name':name,'header':header,'data':data,
              'id':id,'text_name':text_name,'dp':dp,'em':em,'mb':mb,'dpl':dpl})
        elif request.method=="POST":  
            new_url = f'/masters?entity={entity}&type=i'
            return redirect(new_url) 
 
def sample_xlsx(request):
    pre_url = request.META.get('HTTP_REFERER')
    response =''
    global user
    user  = request.session.get('user_id', '')
    try:
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Sample Format'
        columns = []
        if request.method=="GET":
            entity = request.GET.get('entity', '')
            type = request.GET.get('type', '')
        if request.method=="POST":
            entity = request.POST.get('entity', '')
            type = request.POST.get('type', '')
        file_name = {'em': 'Employee Master','sm': 'Worksite Master','cm': 'Company Master','r': 'Roster'}[entity]
        columns = callproc("stp_get_masters", [entity, type, 'sample_xlsx',user])
        if columns and columns[0]:
            columns = [col[0] for col in columns[0]]

        black_border = Border(
            left=Side(border_style="thin", color="000000"),
            right=Side(border_style="thin", color="000000"),
            top=Side(border_style="thin", color="000000"),
            bottom=Side(border_style="thin", color="000000")
        )
        
        for col_num, header in enumerate(columns, 1):
            cell = sheet.cell(row=1, column=col_num)
            cell.value = header
            cell.font = Font(bold=True)
            cell.border = black_border
        
        for col in sheet.columns:
            max_length = 0
            column = col[0].column_letter  
            for cell in col:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
                    
            adjusted_width = max_length + 2 
            sheet.column_dimensions[column].width = adjusted_width  
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="' + str(file_name) +" "+str(datetime.now().strftime("%d-%m-%Y")) + '.xlsx"'
        workbook.save(response)
    
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return response      


def form_builder(request):
    return render(request, "Master/form_builder.html")

@csrf_exempt
def create_form(request):
    if request.method == "POST":
        data = json.loads(request.body)
        form = Form.objects.create(name=data['name'], description=data.get('description', ''))

        for field_data in data['fields']:
            field = FormField.objects.create(
                form=form,
                label=field_data['label'],
                field_type=field_data['type'],
                required=field_data['required'],
                order=field_data['order'],
                row_position=field_data['row']
            )

            for validation in field_data.get('validations', []):
                FieldValidation.objects.create(field=field, rule=validation['rule'], value=validation['value'])

            for dependency in field_data.get('dependencies', []):
                dependent_field = FormField.objects.get(id=dependency['field_id'])
                FieldDependency.objects.create(field=field, dependent_on=dependent_field, condition=json.dumps(dependency['condition']))

        return JsonResponse({"success": True, "form_id": form.id})

@csrf_exempt
def get_form(request, form_id):
    try:
        form = Form.objects.prefetch_related('fields').get(id=form_id)
        form_data = {
            "name": form.name,
            "description": form.description,
            "fields": []
        }
        
        for field in form.fields.all():
            field_data = {
                "id": field.id,
                "label": field.label,
                "type": field.field_type,
                "required": field.required,
                "order": field.order,
                "row": field.row_position,
                "validations": [{"rule": v.rule, "value": v.value} for v in field.validations.all()],
                "dependencies": [{"field_id": d.dependent_on.id, "condition": json.loads(d.condition)} for d in field.dependencies.all()]
            }
            form_data['fields'].append(field_data)

        return JsonResponse(form_data)
    except Form.DoesNotExist:
        return JsonResponse({"error": "Form not found"}, status=404)