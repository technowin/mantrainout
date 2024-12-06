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
    name,def_dt = '',''
    try:
        if request.user.is_authenticated ==True:                
                global user,role_id
                user = request.user.id    
                role_id = request.user.role_id
        if request.method == "GET":
            disp_type = callproc("stp_get_dropdown_values",['disp_type'])
            datalist1= callproc("stp_get_masters",['wf','','name',user])
            name = datalist1[0][0]
            if role_id == 2 :def_dt = 'Inward'
            elif role_id == 3 :def_dt = 'Outward'
            dt = dec(dt) if (dt := request.GET.get('dt', '')) else def_dt
            header = callproc("stp_get_masters", ['wf',dt,'header',user])
            rows = callproc("stp_get_masters",['wf',dt,'data',user])
            for row in rows:
                id = enc(str(row[0]))
                data.append((id,) + row[1:])
        context = {'role_id':role_id,'name':name,'header':header,'data':data,'user_id':request.user.id,'dt':disp_type}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'Workflow/index.html', context)
    
import random

def random_number(type):
    random_number = random.randint(1000, 9999)
    result = f"{type}{random_number}"
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
            dt = callproc("stp_get_dropdown_values",['disp_type'])
            dp = callproc("stp_get_dropdown_values",['dept'])
            su = callproc("stp_get_dropdown_values",['send_user'])
            bh = callproc("stp_get_dropdown_values",['branch'])
            sh = callproc("stp_get_dropdown_values",['stakeholder'])
            if role_id == 2 :def_dt = 'Inward'
            elif role_id == 3 :def_dt = 'Outward'
            wf_id = dec(wf_id) if (wf_id := request.GET.get('wf', '')) else ''
            if wf_id: wf,enc_wfid = workflow.objects.get(id=wf_id),enc(wf_id)
            else: wf,enc_wfid='',''
            header = callproc("stp_get_masters", ['wd','','header',wf_id])
            rows = callproc("stp_get_masters",['wd','','data','1'])
            for row in rows:
                if os.path.exists(os.path.join(MEDIA_ROOT, str(row[4]))):
                    encrypted_id = enc(str(row[4]))
                else: encrypted_id = ''
                new_row = row[:4] + (encrypted_id,)
                data.append(new_row)
            context = {'role_id':role_id,'user_id':request.user.id,'header': header,'data': data,'wf_id':enc_wfid,
                       'wf':wf,'dt':dt,'def_dt':def_dt,'su':su,'dp':dp,'bh':bh,'sh':sh}

        if request.method == "POST":
            response = None
            wf_id = dec(wf_id) if (wf_id := request.POST.get('wf_id', '')) else ''
            wf = workflow.objects.get(id=wf_id)
            files = request.FILES.getlist('fileInput[]')          
            for file in files:
                 response =  docs_upload(file,role_id,user,wf)
            if(wf): dispatch_no =  request.POST.get('dispatch_no', '')
            disp_type =  request.POST.get('disp_type', '')
            if disp_type == 'Inward' :type = 'IN-'
            elif disp_type == 'Outward' :type = 'OUT-'
            dispatch_no = random_number(type)
            received_date =  request.POST.get('received_date', '')
            from_field =  request.POST.get('from', '')
            to =  request.POST.get('to', '')
            subject =  request.POST.get('subject', '')
            comment =  request.POST.get('comment', '')
            department =  request.POST.get('department', '')
            send_user =  request.POST.get('send_user', '')
            branch =  request.POST.get('branch', '')
            stakeholder =  request.POST.get('stakeholder', '')

            r = callproc("stp_post_workflow", [disp_type,dispatch_no,received_date,from_field,to,subject,comment,department,send_user,branch,stakeholder])
            if r[0][0] not in (""):
                messages.success(request, str(r[0][0]))
            else: messages.error(request, 'Oops...! Something went wrong!')
            return redirect(f'/matrix_flow?wf={enc(wf_id)}')
                
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         if request.method == "GET" :
            return render(request,'Workflow/workflow.html', context)


def download_doc(request, filepath):
    file = dec(filepath)
    file_path = os.path.join(settings.MEDIA_ROOT, file)
    file_name = os.path.basename(file_path)
    try:
        if os.path.exists(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream'
            
            with open(file_path, 'rb') as file:
                response = HttpResponse(file.read(), content_type=mime_type)
                response['Content-Disposition'] = f'inline; filename="{file_name}"'
                return response
        else:
            return HttpResponse("File not found", status=404)

    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log", [fun, str(e), ''])  
        return HttpResponse("An error occurred while trying to download the file.", status=500)
    
def docs_upload(file,role_id,user,wf,ser,name1):
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