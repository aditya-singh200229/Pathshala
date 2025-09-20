from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
import os

class Student(models.Model):
    SEAT_CHOICES = [
        ('Reserved', 'Reserved'),
        ('Non-Reserved', 'Non-Reserved'),
    ]
    
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Expiring Soon', 'Expiring Soon'),
    ]
    
    # Personal Information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')])
    date_of_birth = models.DateField()
    aadhaar_number = models.CharField(max_length=12, validators=[RegexValidator(regex=r'^\d{12}$')])
    address = models.TextField()
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    
    # Parent Information
    father_name = models.CharField(max_length=100)
    mother_name = models.CharField(max_length=100)
    parent_mobile = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')])
    
    # Registration
    registration_fees = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.email}"
    
    class Meta:
        ordering = ['-created_at']

class Admission(models.Model):
    HOUR_CHOICES = [
        ('1', '1 Hour'),
        ('2', '2 Hours'),
        ('3', '3 Hours'),
        ('4', '4 Hours'),
        ('6', '6 Hours'),
        ('8', '8 Hours'),
        ('10', '10 Hours'),
        ('12', '12 Hours'),
        ('15', 'Full Day'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='admissions')
    start_date = models.DateField()
    end_date = models.DateField()
    hours = models.CharField(max_length=2, choices=HOUR_CHOICES, default='2')
    slot_timing = models.CharField(max_length=20)
    seat_number = models.CharField(max_length=10)
    seat_type = models.CharField(max_length=20, choices=Student.SEAT_CHOICES, default='Non-Reserved')
    admission_fees = models.DecimalField(max_digits=10, decimal_places=2, default=1900.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.name} - Seat {self.seat_number} ({self.start_date} to {self.end_date})"
    
    class Meta:
        ordering = ['-created_at']

class TotalLockers(models.Model):
    locker_number = models.CharField(max_length=10, unique=True)  # e.g., "L001", "L002", etc.
    is_available = models.BooleanField(default=True)  # Tracks if the locker is available
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.locker_number
    
    class Meta:
        verbose_name_plural = "Total Lockers"
        ordering = ['locker_number']

class Locker(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='lockers')
    total_locker = models.OneToOneField(TotalLockers, on_delete=models.CASCADE, related_name='assigned_locker')
    required = models.BooleanField()
    security_fees = models.DecimalField(max_digits=10, decimal_places=2, default=300.00)
    start_date = models.DateField()
    end_date = models.DateField()
    monthly_fees = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.name} - {self.total_locker.locker_number}"
    
    class Meta:
        ordering = ['total_locker__locker_number']

    def save(self, *args, **kwargs):
        if not self.pk and self.total_locker:  # Only on creation
            self.total_locker.is_available = False
            self.total_locker.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.total_locker:
            self.total_locker.is_available = True
            self.total_locker.save()
        super().delete(*args, **kwargs)

class Payment(models.Model):
    PAYMENT_MODE_CHOICES = [
        ('Cash', 'Cash'),
        ('Online', 'Online'),
        ('Card', 'Card'),
        ('UPI', 'UPI'),
    ]
    
    PAYMENT_TYPE_CHOICES = [
        ('Registration', 'Registration Fees'),
        ('Admission', 'Admission Fees'),
        ('Locker', 'Locker Fees'),
        ('Monthly', 'Monthly Fees'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_mode = models.CharField(max_length=20, choices=PAYMENT_MODE_CHOICES, default='Cash')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='Registration')
    remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.name} - ₹{self.amount} ({self.payment_type})"
    
    class Meta:
        ordering = ['-payment_date']

class ContactLead(models.Model):
    STATUS_CHOICES = [
        ('New', 'New'),
        ('Contacted', 'Contacted'),
        ('Interested', 'Interested'),
        ('Converted', 'Converted'),
        ('Not Interested', 'Not Interested'),
    ]
    
    name = models.CharField(max_length=100)
    email = models.EmailField()
    mobile = models.CharField(max_length=15, validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')])
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']