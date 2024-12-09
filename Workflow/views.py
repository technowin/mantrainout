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
from django.template.loader import render_to_string
import time
import xlsxwriter
import io
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
            dp = callproc("stp_get_dropdown_values",['dept'])
            su = callproc("stp_get_dropdown_values",['send_user'])
            bh = callproc("stp_get_dropdown_values",['branch'])
            sh = callproc("stp_get_dropdown_values",['stakeholder'])
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
        context = {'role_id':role_id,'name':name,'header':header,'data':data,'user_id':request.user.id,'dt':disp_type,'su':su,'dp':dp,'bh':bh,'sh':sh,'def_dt':def_dt}
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),user])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally: 
         return render(request,'Workflow/index.html', context)
    

@login_required
def partial_table(request):
    data = []
    try:
        if request.user.is_authenticated ==True:                
            global user
            user = request.user.id    
            role_id = request.user.role_id
            if request.method == "GET":
                dt = request.GET.get('dt', '')
                if(dt!=''):
                    ca = request.GET.get('ca', '')
                    dp = request.GET.get('dp', '')
                    su = request.GET.get('su', '')
                    bh = request.GET.get('bh', '')
                    sh = request.GET.get('sh', '')
                    header = callproc("stp_get_masters", ['wf',dt,'header',user])
                    rows = callproc("stp_get_workflow",[dt,dp,su,bh,sh,ca,user,'data'])
                    for row in rows:
                        id = enc(str(row[0]))
                        data.append((id,) + row[1:])
                context = {'header':header,'data':data}
                html = render_to_string('Workflow/_partial_table.html', context)
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        data = {'html': html}
        return JsonResponse(data, safe=False)
    
@login_required    
def work_flow(request):
    data = []
    context,wf_id,dispatch_no1  = '','',''
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
            if wf :def_dt = wf.dispatch_type
            if wf :dispatch_no1 = wf.dispatch_no
            header = callproc("stp_get_masters", ['wd','','header',dispatch_no1])
            rows = callproc("stp_get_masters",['wd','','data',dispatch_no1])
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
            if wf_id : wf = workflow.objects.get(id=wf_id) 
            else: wf = ''
            
            files = request.FILES.getlist('fileInput')          
            
            if(wf): dispatch_no =  request.POST.get('dispatch_no', '')
            else: dispatch_no = ''
            disp_type =  request.POST.get('disp_type', '')
            received_date =  request.POST.get('received_date', '')
            from_field =  request.POST.get('from', '')
            to =  request.POST.get('to', '')
            subject =  request.POST.get('subject', '')
            comment =  request.POST.get('comment', '')
            department =  request.POST.get('department', '')
            send_user =  request.POST.get('send_user', '')
            branch =  request.POST.get('branch', '')
            stakeholder =  request.POST.get('stakeholder', '')

            r = callproc("stp_post_workflow", [disp_type,dispatch_no,received_date,from_field,to,subject,comment,department,send_user,branch,stakeholder,wf_id,user])
            if r[0][0] == 'update':
                for file in files:
                    response =  docs_upload(file,role_id,user,dispatch_no)
                messages.success(request, "Data Updated Successfully")
            elif r[0][0] != "":
                for file in files:
                    response =  docs_upload(file,role_id,user,str(r[0][0]))
                messages.success(request, "Data Added Successfully")
            else: messages.error(request, 'Oops...! Something went wrong!')
            return redirect(f'/index')
                
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
    
def docs_upload(file,role_id,user,dispatch_no1):
    file_resp = None
    role = roles.objects.get(id=role_id)
    sub_path = f'{role.role_name}/User_{user}/{dispatch_no1}/{file.name}'
    full_path = os.path.join(MEDIA_ROOT, sub_path)
    folder_path = os.path.dirname(full_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)
    file_exists_in_folder = os.path.exists(full_path)
    file_exists_in_db = workflow_document.objects.filter(file_path=sub_path,dispatch_no=dispatch_no1).exists()
    if file_exists_in_db:
        document = workflow_document.objects.filter(file_path=sub_path,dispatch_no=dispatch_no1).first()
        document.updated_at = datetime.now()
        document.updated_by = str(user)
        document.save()
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        file_resp =  f"Files has been updated."
    else:
        with open(full_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
        workflow_document.objects.create(
            dispatch_no=dispatch_no1, file_name=file.name,file_path=sub_path,
            created_at=datetime.now(),created_by=str(user),updated_at=datetime.now(),updated_by=str(user)
        )  
        file_resp =  f"Files has been inserted."
    return file_resp
 
@login_required
def download_xls(request):
    response = ''
    try:
        if request.user.is_authenticated ==True:                
            global user,role_id
            user = request.user.id   
            role_id = request.user.role_id  
            if request.method == "POST":
                dt =str(request.POST.get('disp_typeh', ''))
                ca =str(request.POST.get('created_ath', ''))
                dp =str(request.POST.get('departmenth', ''))
                su =str(request.POST.get('send_userh', ''))
                bh =str(request.POST.get('branchh', ''))
                sh =str(request.POST.get('stakeholderh', ''))

                header = callproc("stp_get_masters", ['wf',dt,'sample_xlsx',user])
                rows = callproc("stp_get_workflow",[dt,dp,su,bh,sh,ca,user,'xls'])
                output = io.BytesIO()
                workbook = xlsxwriter.Workbook(output)
                worksheet = workbook.add_worksheet(str(dt) + ' Report')

                worksheet.insert_image('A1', 'static/images/technologo1.png', {'x_offset': 10, 'y_offset': 10, 'x_scale': 0.5, 'y_scale': 0.5})

                header_format = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 14})
                data_format = workbook.add_format({'border': 1})
                worksheet.merge_range('A1:Z1', dt +' Report', workbook.add_format({'bold': True, 'align': 'center', 'font_size': 16}))

                # worksheet.merge_range('A4:{}'.format(chr(65+len(header)-1)+'2'), dt + ' Report', header_format)

                header_format = workbook.add_format({'bold': True, 'bg_color': '#DD8C8D', 'font_color': 'black'})
                for i, column_name in enumerate(header):
                    worksheet.write(6, i, column_name, header_format)

                for row_num, row_data in enumerate(rows, start=7):
                    for col_num, col_data in enumerate(row_data):
                        worksheet.write(row_num, col_num, col_data, data_format)
                workbook.close()
                response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename="' + str(dt) + ' Report' + '.xlsx"'
                output.seek(0)
                response.write(output.read())
    except Exception as e:
        tb = traceback.extract_tb(e.__traceback__)
        fun = tb[0].name
        callproc("stp_error_log",[fun,str(e),request.user.id])  
        messages.error(request, 'Oops...! Something went wrong!')
    finally:
        return response