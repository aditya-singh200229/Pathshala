from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from django.utils.timezone import now
from .models import Student, Admission, Locker, Payment, ContactLead, TotalLockers
from django.core.paginator import Paginator
import csv
from django.core.serializers.json import DjangoJSONEncoder
import json

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Finance calculations
    total_registration = Payment.objects.filter(payment_type='Registration').aggregate(Sum('amount'))['amount__sum'] or 0
    total_admission = Payment.objects.filter(payment_type='Admission').aggregate(Sum('amount'))['amount__sum'] or 0
    total_locker = Payment.objects.filter(payment_type='Locker').aggregate(Sum('amount'))['amount__sum'] or 0
    total_revenue = total_registration + total_admission + total_locker
    
    # Student counts
    total_students = Student.objects.count()
    active_students = Student.objects.filter(status='Active').count()
    inactive_students = Student.objects.filter(status='Inactive').count()
    expiring_soon = Student.objects.filter(status='Expiring Soon').count()
    
    context = {
        'total_revenue': total_revenue,
        'total_registration': total_registration,
        'total_admission': total_admission,
        'total_locker': total_locker,
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'expiring_soon': expiring_soon,
    }
    return render(request, 'dashboard.html', context)

@login_required
def students_list(request):
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '')
    hours_filter = request.GET.get('hours', '')
    
    if filter_type == 'active':
        students = Student.objects.filter(status='Active')
    elif filter_type == 'inactive':
        students = Student.objects.filter(status='Inactive')
    elif filter_type == 'expiring':
        students = Student.objects.filter(status='Expiring Soon')
    elif filter_type == 'reserved':
        students = Student.objects.filter(admissions__seat_type='Reserved').distinct()
    elif filter_type == 'non_reserved':
        students = Student.objects.filter(admissions__seat_type='Non-Reserved').distinct()
    else:
        students = Student.objects.all()
    
    if hours_filter:
        students = students.filter(admissions__hours=hours_filter).distinct()
    
    if search_query:
        students = students.filter(
            Q(id__icontains=search_query) |
            Q(name__icontains=search_query)
        )

    paginator = Paginator(students, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_string = query_params.urlencode()

    context = {
        'students': page_obj,
        'filter_type': filter_type,
        'search_query': search_query,
        'hours_filter': hours_filter,
        'query_string': query_string,
        'hour_choices': Admission.HOUR_CHOICES,
    }
    return render(request, 'students/list.html', context)

@login_required
def student_detail(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    admissions = student.admissions.all()
    lockers = student.lockers.all()
    payments = student.payments.all()
    
    context = {
        'student': student,
        'admissions': admissions,
        'lockers': lockers,
        'payments': payments,
    }
    return render(request, 'students/detail.html', context)

@login_required
def student_create(request):
    if request.method == 'POST':
        try:
            student = Student.objects.create(
                name=request.POST['name'],
                email=request.POST['email'],
                mobile=request.POST['mobile'],
                date_of_birth=request.POST['date_of_birth'],
                aadhaar_number=request.POST['aadhaar_number'],
                address=request.POST['address'],
                father_name=request.POST['father_name'],
                mother_name=request.POST['mother_name'],
                parent_mobile=request.POST['parent_mobile'],
                registration_fees=request.POST.get('registration_fees', 200.00),
                photo=request.FILES.get('photo')
            )
            messages.success(request, 'Student added successfully!')
            return redirect('student_detail', student_id=student.id)
        except Exception as e:
            messages.error(request, f'Error creating student: {str(e)}')
    
    return render(request, 'students/create.html')

@login_required
def student_update(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            student.name = request.POST['name']
            student.email = request.POST['email']
            student.mobile = request.POST['mobile']
            student.date_of_birth = request.POST['date_of_birth']
            student.aadhaar_number = request.POST['aadhaar_number']
            student.address = request.POST['address']
            student.father_name = request.POST['father_name']
            student.mother_name = request.POST['mother_name']
            student.parent_mobile = request.POST['parent_mobile']
            student.registration_fees = request.POST.get('registration_fees', 200.00)
            student.status = request.POST['status']
            
            if request.FILES.get('photo'):
                student.photo = request.FILES['photo']
                
            student.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_detail', student_id=student.id)
        except Exception as e:
            messages.error(request, f'Error updating student: {str(e)}')
    
    context = {'student': student}
    return render(request, 'students/edit.html', context)

@login_required
def student_delete(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            student.delete()
            messages.success(request, 'Student deleted successfully!')
            return redirect('students_list')
        except Exception as e:
            messages.error(request, f'Error deleting student: {str(e)}')
            return redirect('student_detail', student_id=student_id)
    
    context = {'student': student}
    return render(request, 'students/confirm_delete.html', context)

@login_required
def admission_create(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            Admission.objects.filter(student=student).delete()
            admission = Admission.objects.create(
                student=student,
                start_date=request.POST['start_date'],
                end_date=request.POST['end_date'],
                hours=request.POST['hours'],
                slot_timing=request.POST['slot_timing'],
                seat_number=request.POST['seat_number'],
                seat_type=request.POST['seat_type'],
                admission_fees=request.POST.get('admission_fees', 1900.00)
            )
            messages.success(request, 'Admission details added successfully!')
            return redirect('student_detail', student_id=student.id)
        except Exception as e:
            messages.error(request, f'Error creating admission: {str(e)}')
    
    context = {'student': student}
    return render(request, 'admissions/create.html', context)

@login_required
def locker_create(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            locker_number = request.POST['locker_number']
            total_locker = get_object_or_404(TotalLockers, locker_number=locker_number, is_available=True)
            locker = Locker.objects.create(
                student=student,
                total_locker=total_locker,
                required=request.POST.get('required') == 'on',
                security_fees=request.POST.get('security_fees', 300.00),
                start_date=request.POST['start_date'],
                end_date=request.POST['end_date'],
                monthly_fees=request.POST.get('monthly_fees', 100.00)
            )
            messages.success(request, 'Locker assigned successfully!')
            return redirect('student_detail', student_id=student.id)
        except TotalLockers.DoesNotExist:
            messages.error(request, 'Selected locker is not available.')
        except Exception as e:
            messages.error(request, f'Error creating locker: {str(e)}')
    
    available_lockers = TotalLockers.objects.filter(is_available=True)
    context = {'student': student, 'available_lockers': available_lockers}
    return render(request, 'lockers/create.html', context)

@login_required
def locker_update(request, locker_id):
    locker = get_object_or_404(Locker, id=locker_id)
    
    if request.method == 'POST':
        try:
            locker.required = request.POST.get('required') == 'on'
            locker.security_fees = request.POST.get('security_fees', 300.00)
            locker.start_date = request.POST['start_date']
            locker.end_date = request.POST['end_date']
            locker.monthly_fees = request.POST.get('monthly_fees', 100.00)
            
            locker.save()
            messages.success(request, 'Locker updated successfully!')
            return redirect('student_detail', student_id=locker.student.id)
        except Exception as e:
            messages.error(request, f'Error updating locker: {str(e)}')
    
    context = {'locker': locker, 'student': locker.student}
    return render(request, 'lockers/edit.html', context)

@login_required
def locker_delete(request, locker_id):
    locker = get_object_or_404(Locker, id=locker_id)
    student_id = locker.student.id
    
    if request.method == 'POST':
        try:
            locker.delete()
            messages.success(request, 'Locker removed successfully!')
            return redirect('student_detail', student_id=student_id)
        except Exception as e:
            messages.error(request, f'Error deleting locker: {str(e)}')
            return redirect('student_detail', student_id=student_id)
    
    context = {'locker': locker, 'student': locker.student}
    return render(request, 'lockers/confirm_delete.html', context)

@login_required
def payment_create(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        try:
            payment = Payment.objects.create(
                student=student,
                amount=request.POST['amount'],
                payment_date=request.POST['payment_date'],
                payment_mode=request.POST['payment_mode'],
                payment_type=request.POST['payment_type'],
                remarks=request.POST.get('remarks', '')
            )
            messages.success(request, 'Payment recorded successfully!')
            return redirect('student_detail', student_id=student.id)
        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')
    
    context = {'student': student}
    return render(request, 'payments/create.html', context)

@login_required
def payment_update(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        try:
            payment.amount = request.POST['amount']
            payment.payment_date = request.POST['payment_date']
            payment.payment_mode = request.POST['payment_mode']
            payment.payment_type = request.POST['payment_type']
            payment.remarks = request.POST.get('remarks', '')
            
            payment.save()
            messages.success(request, 'Payment updated successfully!')
            return redirect('student_detail', student_id=payment.student.id)
        except Exception as e:
            messages.error(request, f'Error updating payment: {str(e)}')
    
    context = {'payment': payment, 'student': payment.student}
    return render(request, 'payments/edit.html', context)

@login_required
def payment_delete(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)
    student_id = payment.student.id
    
    if request.method == 'POST':
        try:
            payment.delete()
            messages.success(request, 'Payment deleted successfully!')
            return redirect('student_detail', student_id=student_id)
        except Exception as e:
            messages.error(request, f'Error deleting payment: {str(e)}')
            return redirect('student_detail', student_id=student_id)
    
    context = {'payment': payment, 'student': payment.student}
    return render(request, 'payments/confirm_delete.html', context)

@login_required
def contact_leads(request):
    leads = ContactLead.objects.all()
    paginator = Paginator(leads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'leads': page_obj}
    return render(request, 'leads/list.html', context)

@login_required
def finance_dashboard(request):
    today = datetime.now()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    
    current_month_revenue = Payment.objects.filter(
        payment_date__gte=current_month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    last_month_revenue = Payment.objects.filter(
        payment_date__gte=last_month_start,
        payment_date__lt=current_month_start
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    percentage_change = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else (100 if current_month_revenue > 0 else 0)
    
    total_registration = Payment.objects.filter(payment_type='Registration').aggregate(Sum('amount'))['amount__sum'] or 0
    total_admission = Payment.objects.filter(payment_type='Admission').aggregate(Sum('amount'))['amount__sum'] or 0
    total_locker = Payment.objects.filter(payment_type='Locker').aggregate(Sum('amount'))['amount__sum'] or 0
    total_monthly = Payment.objects.filter(payment_type='Monthly').aggregate(Sum('amount'))['amount__sum'] or 0
    
    total_revenue = total_registration + total_admission + total_locker + total_monthly
    
    recent_payments = Payment.objects.all()[:10]
    
    context = {
        'total_revenue': total_revenue,
        'current_month_revenue': current_month_revenue,
        'percentage_change': round(percentage_change, 1),
        'total_registration': total_registration,
        'total_admission': total_admission,
        'total_locker': total_locker,
        'total_monthly': total_monthly,
        'recent_payments': recent_payments,
    }
    return render(request, 'finance/dashboard.html', context)

@login_required
def export_students_csv(request):
    filter_type = request.GET.get('filter', 'all')
    search_query = request.GET.get('q', '')
    hours_filter = request.GET.get('hours', '')

    if filter_type == 'active':
        students = Student.objects.filter(status='Active')
    elif filter_type == 'inactive':
        students = Student.objects.filter(status='Inactive')
    elif filter_type == 'expiring':
        students = Student.objects.filter(status='Expiring Soon')
    elif filter_type == 'reserved':
        students = Student.objects.filter(admissions__seat_type='Reserved').distinct()
    elif filter_type == 'non_reserved':
        students = Student.objects.filter(admissions__seat_type='Non-Reserved').distinct()
    else:
        students = Student.objects.all()

    if hours_filter:
        students = students.filter(admissions__hours=hours_filter).distinct()

    if search_query:
        students = students.filter(
            Q(id__icontains=search_query) |
            Q(name__icontains=search_query)
        )

    students = students.prefetch_related('admissions', 'lockers', 'payments')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="students_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Name', 'Email', 'Mobile', 'Date of Birth', 'Aadhaar Number', 'Address',
        'Father Name', 'Mother Name', 'Parent Mobile', 'Registration Fees', 'Status',
        'Date Added', 'Photo URL', 'Admissions', 'Lockers', 'Payments'
    ])

    for student in students:
        admissions_data = json.dumps([
            {
                'start_date': a.start_date.strftime('%Y-%m-%d') if a.start_date else '',
                'end_date': a.end_date.strftime('%Y-%m-%d') if a.end_date else '',
                'hours': a.hours,
                'slot_timing': a.slot_timing,
                'seat_number': a.seat_number,
                'seat_type': a.seat_type,
                'admission_fees': str(a.admission_fees)
            } for a in student.admissions.all()
        ], cls=DjangoJSONEncoder)

        lockers_data = json.dumps([
            {
                'required': l.required,
                'security_fees': str(l.security_fees),
                'start_date': l.start_date.strftime('%Y-%m-%d') if l.start_date else '',
                'end_date': l.end_date.strftime('%Y-%m-%d') if l.end_date else '',
                'locker_number': l.total_locker.locker_number,
                'monthly_fees': str(l.monthly_fees)
            } for l in student.lockers.all()
        ], cls=DjangoJSONEncoder)

        payments_data = json.dumps([
            {
                'amount': str(p.amount),
                'payment_date': p.payment_date.strftime('%Y-%m-%d') if p.payment_date else '',
                'payment_mode': p.payment_mode,
                'payment_type': p.payment_type,
                'remarks': p.remarks
            } for p in student.payments.all()
        ], cls=DjangoJSONEncoder)

        writer.writerow([
            student.id,
            student.name,
            student.email,
            student.mobile,
            student.date_of_birth.strftime('%Y-%m-%d') if student.date_of_birth else '',
            student.aadhaar_number,
            student.address,
            student.father_name,
            student.mother_name,
            student.parent_mobile,
            str(student.registration_fees),
            student.status,
            student.created_at.strftime('%Y-%m-%d'),
            student.photo.url if student.photo else '',
            admissions_data,
            lockers_data,
            payments_data
        ])

    return response

@login_required
def lockers_list(request):
    search_query = request.GET.get('q', '')
    assigned_lockers = Locker.objects.select_related('student', 'total_locker')
    available_lockers = TotalLockers.objects.filter(is_available=True)

    if search_query:
        assigned_lockers = assigned_lockers.filter(
            Q(student__name__icontains=search_query) |
            Q(total_locker__locker_number__icontains=search_query)
        )
        available_lockers = available_lockers.filter(
            locker_number__icontains=search_query
        )

    paginator_assigned = Paginator(assigned_lockers, 10)
    page_number_assigned = request.GET.get('page_assigned', 1)
    page_obj_assigned = paginator_assigned.get_page(page_number_assigned)

    paginator_available = Paginator(available_lockers, 10)
    page_number_available = request.GET.get('page_available', 1)
    page_obj_available = paginator_available.get_page(page_number_available)

    context = {
        'assigned_lockers': page_obj_assigned,
        'available_lockers': page_obj_available,
        'search_query': search_query,
    }
    return render(request, 'lockers/list.html', context)


@login_required
def add_locker(request):
    if request.method == 'POST':
        try:
            locker_number = request.POST['new_locker_number']
            if TotalLockers.objects.filter(locker_number=locker_number).exists():
                messages.error(request, 'Locker number already exists.')
            else:
                TotalLockers.objects.create(locker_number=locker_number, is_available=True)
                messages.success(request, f'Locker {locker_number} added successfully!')
            return redirect('lockers_list')
        except Exception as e:
            messages.error(request, f'Error adding locker: {str(e)}')
    return redirect('lockers_list')