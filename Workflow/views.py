from django.shortcuts import render
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render,redirect
from Account.models import *
from Masters.models import *
from Workflow.models import *
import traceback
from Account.db_utils import callproc
from django.contrib import messages
from django.conf import settings
from mantra_io.encryption import *
import os
from mantra_io.settings import *
from django.contrib.auth.decorators import login_required
import openpyxl
import mimetypes
from openpyxl.styles import Font, Border, Side
import pandas as pd
import calendar
from django.utils import timezone
from datetime import timedelta
# Create your views here.



@login_required 
def index(request):
    pre_url = request.META.get('HTTP_REFERER')
    header, data = [], []
    name = ''
    try:
        if request.user.is_authenticated ==True:                
                global user,role_id
                user = request.user.id    
                role_id = request.user.role_id
        if request.method == "GET":
            datalist1= callproc("stp_get_masters",['wf','','name',user])
            name = datalist1[0][0]
            header = callproc("stp_get_masters", ['wf','','header',user])
            rows = callproc("stp_get_masters",['wf','','data',user])
            for row in rows:
                id = encrypt_parameter(str(row[0]))
                data.append((id) + row[1:])
        context = {'role_id':role_id,'name':name,'header':header,'data':data,'user_id':request.user.id,'pre_url':pre_url}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'Workflow/index.html', context)

@login_required    
def work_flow(request):
    data = []
    context,wf_id  = '',''
    try:
        if request.user.is_authenticated ==True:                
            global user,role_id
            user = request.user.id   
            role_id = request.user.role_id   
        if request.method == "GET":
            wf_id = decrypt_parameter(wf_id) if (wf_id := request.GET.get('wf', '')) else ''
            wf = workflow.objects.get(id=wf_id) 
            header = callproc("stp_get_masters", ['iud','','header',wf_id])
            rows = callproc("stp_get_masters",['iud','','data',wf_id])
            for row in rows:
                if os.path.exists(os.path.join(MEDIA_ROOT, str(row[5]))):
                    encrypted_id = encrypt_parameter(str(row[5]))
                else: encrypted_id = None
                new_row = row[:5] + (encrypted_id,)
                data.append(new_row)
            context = {'role_id':role_id,'user_id':request.user.id,'header': header,'data': data,'ac':ac,'wf_id':encrypt_parameter(wf_id),'wf':wf}

        if request.method == "POST":
            response = None
            wf_id = decrypt_parameter(wf_id) if (wf_id := request.POST.get('wf_id', '')) else ''
            wf = workflow.objects.get(id=wf_id)
            files = request.FILES.getlist('files[]')
            comment =  request.POST.get('comment', '')
          
            for file in files:
                 response =  internal_docs_upload(file,role_id,user,wf)

            r = callproc("stp_post_workflow", [wf_id,user])
            if r[0][0] not in (""):
                messages.success(request, str(r[0][0]))
            else: messages.error(request, 'Oops...! Something went wrong!')
            return redirect(f'/matrix_flow?wf={encrypt_parameter(wf_id)}')
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         if request.method == "GET" :
            return render(request,'Workflow/workflow.html', context)

def internal_docs_upload(file,role_id,user,wf,ser,name1):
    file_resp = None
    role = roles.objects.get(id=role_id)
    sub_path = f'{role.role_name}/user_{user}/workflow_{str(wf.id)}/{file.name}'
    full_path = os.path.join(MEDIA_ROOT, sub_path)
    folder_path = os.path.dirname(full_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    file_exists_in_folder = os.path.exists(full_path)
    file_exists_in_db = workflow_document.objects.filter(file_path=sub_path,workflow=wf,name=name1).exists()
    if file_exists_in_db:
        document = workflow_document.objects.filter(file_path=sub_path,workflow=wf,name=name1).first()
        document.updated_at = datetime.now()
        document.updated_by = str(user)
        document.name=name1
        document.save()
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        if name1 =='':
            file_resp =  f"File has been updated."
        else: file_resp =  f"File '{file.name}' has been updated."
    else:
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        workflow_document.objects.create(
            workflow=wf, file_name=file.name,file_path=sub_path,name=name1,
            created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
        )  
        if name1 =='':
            file_resp =  f"File has been inserted."
        else: file_resp =  f"File '{file.name}' has been inserted."
    return file_resp