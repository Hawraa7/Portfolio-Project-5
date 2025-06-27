from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import FitnessClass, Booking
from .forms import BookingForm, FitnessClassForm
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def create_class(request):
    if request.method == 'POST':
        form = FitnessClassForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('class_list')
    else:
        form = FitnessClassForm()
    return render(request, 'classes/create_class.html', {'form': form})


def class_list(request):
    classes = FitnessClass.objects.all().order_by("date", "time")
    return render(request, 'classes/class_list.html', {'classes': classes})


def class_detail(request, pk):
    fitness_class = get_object_or_404(FitnessClass, pk=pk)
    return render(request, 'classes/class_detail.html', {'class': fitness_class})


@login_required
def book_class(request, pk):
    fitness_class = get_object_or_404(FitnessClass, pk=pk)
    if request.method == 'POST':
        Booking.objects.create(user=request.user, fitness_class=fitness_class)
        return redirect('class_list')
    return render(request, 'classes/book_class.html', {'class': fitness_class})
