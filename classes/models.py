from django.db import models
from django.contrib.auth.models import User

class FitnessClass(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    instructor = models.CharField(max_length=100)
    max_participants = models.PositiveIntegerField(default=10)

    def __str__(self):
        return f"{self.title} on {self.date} at {self.time}"

    def spots_left(self):
        return self.max_participants - self.bookings.count()

class Booking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    fitness_class = models.ForeignKey(FitnessClass, on_delete=models.CASCADE, related_name='bookings')
    booked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} booked {self.fitness_class}"
