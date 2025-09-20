from django.contrib import admin
from .models import Student, Admission, Locker, Payment, ContactLead, TotalLockers

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'mobile', 'status', 'registration_fees', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'mobile', 'aadhaar_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('name', 'email', 'mobile', 'date_of_birth', 'aadhaar_number', 'address', 'photo')
        }),
        ('Parent Information', {
            'fields': ('father_name', 'mother_name', 'parent_mobile')
        }),
        ('Registration', {
            'fields': ('registration_fees', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = ['student', 'seat_number', 'start_date', 'end_date', 'slot_timing', 'admission_fees']
    list_filter = ['slot_timing', 'seat_type', 'start_date', 'end_date']
    search_fields = ['student__name', 'seat_number']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Locker)
class LockerAdmin(admin.ModelAdmin):
    list_display = ['total_locker_locker_number', 'student', 'required', 'start_date', 'end_date', 'monthly_fees']
    list_filter = ['required', 'start_date', 'end_date']
    search_fields = ['total_locker__locker_number', 'student__name']
    readonly_fields = ['created_at', 'updated_at']

    # Custom method to display locker_number from total_locker
    def total_locker_locker_number(self, obj):
        return obj.total_locker.locker_number if obj.total_locker else ''
    total_locker_locker_number.short_description = 'Locker Number'

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['student', 'amount', 'payment_date', 'payment_mode', 'payment_type']
    list_filter = ['payment_mode', 'payment_type', 'payment_date']
    search_fields = ['student__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'payment_date'

@admin.register(ContactLead)
class ContactLeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'mobile', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'mobile']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(TotalLockers)
class TotalLockersAdmin(admin.ModelAdmin):
    list_display = ['locker_number', 'is_available', 'created_at', 'updated_at']
    list_filter = ['is_available', 'created_at']
    search_fields = ['locker_number']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['make_available', 'make_unavailable']