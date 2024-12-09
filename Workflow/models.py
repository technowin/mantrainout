from django.db import models

# Create your models here.

class workflow(models.Model):
    id = models.AutoField(primary_key=True)
    dispatch_type =  models.TextField(null=True, blank=True)
    dispatch_no =  models.TextField(null=True, blank=True)
    received_date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    from_field = models.TextField(null=True, blank=True, db_column='from') 
    to =  models.TextField(null=True, blank=True)
    subject =  models.TextField(null=True, blank=True)
    comment =  models.TextField(null=True, blank=True)
    status = models.ForeignKey('Masters.status_master', on_delete=models.CASCADE, null=True, blank=True, related_name='status_wf')
    department = models.TextField(null=True, blank=True)
    send_user = models.TextField(null=True, blank=True)
    branch = models.TextField(null=True, blank=True)
    stakeholders = models.TextField(null=True, blank=True)
    # department = models.ForeignKey('Masters.department_master', on_delete=models.CASCADE, null=True, blank=True, related_name='dep_wf')
    # branch = models.ForeignKey('Masters.branch_master', on_delete=models.CASCADE, null=True, blank=True, related_name='branch_wf')
    # stakeholders = models.ForeignKey('Masters.stakeholders', on_delete=models.CASCADE, null=True, blank=True, related_name='sh_wf')
    user = models.ForeignKey('Account.CustomUser', on_delete=models.CASCADE, null=True, blank=True, related_name='user_wf')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'workflow'

class workflow_document(models.Model):
    id = models.AutoField(primary_key=True) 
    dispatch_no = models.TextField(null=True, blank=True)  
    file_name = models.TextField(null=True, blank=True)  
    file_path = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)             
    created_by = models.TextField(null=True, blank=True) 
    updated_at = models.DateTimeField(null=True, blank=True)               
    updated_by = models.TextField(null=True, blank=True) 
    class Meta:
        db_table = 'workflow_document'
