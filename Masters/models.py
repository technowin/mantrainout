from django.db import models
from django.db import models
from Account.models import *

class application_search(models.Model):
    id = models.AutoField(primary_key=True)
    name =models.TextField(null=True,blank=True)
    description =models.TextField(null=True,blank=True)
    href =models.TextField(null=True,blank=True)
    menu_id =models.TextField(null=True,blank=True)
    is_active =models.BooleanField(null=True,blank=True,default=True)
    created_at = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='app_search_created',blank=True, null=True,db_column='created_by')
    updated_at = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='app_search_updated',blank=True, null=True,db_column='updated_by')
    
    class Meta:
        db_table = 'application_search'
    def __str__(self):
        return self.name
         
class parameter_master(models.Model):
    parameter_id = models.AutoField(primary_key=True)
    parameter_name =models.TextField(null=True,blank=True)
    parameter_value =models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='parameter_created_by',blank=True, null=True,db_column='created_by')
    updated_at = models.DateTimeField(null=True,blank=True,auto_now_add=True)
    updated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='parameter_updated_by',blank=True, null=True,db_column='updated_by')
    
    class Meta:
        db_table = 'parameter_master'
    def __str__(self):
        return self.parameter_name


class status_master(models.Model):
    status_id = models.AutoField(primary_key=True)
    status_name = models.TextField(null=True, blank=True)
    status_type = models.TextField(null=True, blank=True)
    status_color = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1)  
    level = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'status_master'

class status_color(models.Model):
    id = models.AutoField(primary_key=True)
    color = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'status_color'

class document_master(models.Model):
    doc_id = models.AutoField(primary_key=True)
    doc_name = models.TextField(null=True, blank=True)
    doc_subpath =models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.TextField(null=True, blank=True)
    is_active = models.IntegerField(default=1)
    mandatory = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'document_master'


class department_master(models.Model):
    id = models.AutoField(primary_key=True)
    name =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'department_master'

class branch_master(models.Model):
    id = models.AutoField(primary_key=True)
    name =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'branch_master'

class stakeholders(models.Model):
    id = models.AutoField(primary_key=True)
    name =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'stakeholders'

class send_user(models.Model):
    id = models.AutoField(primary_key=True)
    name =  models.TextField(null=True, blank=True)
    email =  models.TextField(null=True, blank=True)
    mobile =  models.TextField(null=True, blank=True)
    department =  models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    created_by =  models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    updated_by =  models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'send_user'       

class Log(models.Model):
    log_text = models.TextField(null=True,blank=True)
    
    class Meta:
        db_table = 'logs'


class Form(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class FormField(models.Model):
    form = models.ForeignKey(Form, on_delete=models.CASCADE, related_name='fields')
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=50, choices=[('text', 'Text'), ('number', 'Number'), ('email', 'Email'),
                                                           ('select', 'Dropdown'), ('checkbox', 'Checkbox'),
                                                           ('radio', 'Radio'), ('textarea', 'Textarea')])
    required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)  # Drag-drop order
    row_position = models.IntegerField(default=1)  # Defines row placement

class FieldValidation(models.Model):
    field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name='validations')
    rule = models.CharField(max_length=50, choices=[('min_length', 'Min Length'), ('max_length', 'Max Length'),
                                                     ('regex', 'Regex'), ('custom', 'Custom Rule')])
    value = models.CharField(max_length=255)

class FieldDependency(models.Model):
    field = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name='dependencies')
    dependent_on = models.ForeignKey(FormField, on_delete=models.CASCADE, related_name='dependent_fields')
    condition = models.CharField(max_length=255)  # JSON-based logic (e.g., {'value': 'yes'})


