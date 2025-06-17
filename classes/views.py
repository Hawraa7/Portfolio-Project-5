from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import FitnessClass, Booking
from .forms import FitnessClassForm

def class_list(request):
    classes = FitnessClass.objects.all()

    user_bookings = []
    if request.user.is_authenticated:
        user_bookings = Booking.objects.filter(user=request.user).values_list('fitness_class_id', flat=True)

    return render(request, 'classes/class_list.html', {
        'classes': classes,
        'user_bookings': user_bookings,
    })

@login_required
def book_class(request, class_id):
    fitness_class = get_object_or_404(FitnessClass, id=class_id)
    if Booking.objects.filter(user=request.user, fitness_class=fitness_class).exists():
        messages.warning(request, "You have already booked this class.")
    elif fitness_class.bookings.count() >= fitness_class.max_participants:
        messages.error(request, "This class is fully booked.")
    else:
        Booking.objects.create(user=request.user, fitness_class=fitness_class)
        messages.success(request, "You successfully booked the class.")
    return redirect('class_list')

@login_required
def cancel_booking(request, class_id):
    fitness_class = get_object_or_404(FitnessClass, id=class_id)
    booking = Booking.objects.filter(user=request.user, fitness_class=fitness_class).first()
    if booking:
        booking.delete()
        messages.success(request, "Booking cancelled.")
    else:
        messages.warning(request, "You have no booking for this class.")
    return redirect('class_list')

def class_detail(request, class_id):
    fitness_class = get_object_or_404(FitnessClass, id=class_id)
    booked = False
    if request.user.is_authenticated:
        booked = Booking.objects.filter(user=request.user, fitness_class=fitness_class).exists()
    spots_left = fitness_class.max_participants - fitness_class.bookings.count()
    return render(request, 'classes/class_detail.html', {
        'class': fitness_class,
        'booked': booked,
        'spots_left': spots_left,
    })

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(user=request.user).select_related('fitness_class').order_by('fitness_class__date', 'fitness_class__time')
    return render(request, 'classes/my_bookings.html', {'bookings': bookings})

@staff_member_required
def create_class(request):
    if request.method == 'POST':
        form = FitnessClassForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New class created successfully.")
            return redirect('class_list')
    else:
        form = FitnessClassForm()
    return render(request, 'classes/create_class.html', {'form': form})
