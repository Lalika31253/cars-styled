from django.db import models


class Branch(models.Model):
    name        = models.CharField(max_length=100)   # CharField → str
    city        = models.CharField(max_length=80)
    opened_date = models.DateField()                 # DateField
    notes       = models.TextField(blank=True)       # TextField (optional)

    def __str__(self):
        return f'{self.name} ({self.city})'


class Seller(models.Model):
    first_name = models.CharField(max_length=50)
    last_name  = models.CharField(max_length=50)
    # ManyToManyField: a seller can work at multiple branches
    branches   = models.ManyToManyField(
        Branch,
        related_name='sellers',  # branch.sellers.all()
    )
    is_active  = models.BooleanField(default=True)   # BooleanField

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Car(models.Model):
    TRANSMISSION_CHOICES = [
        ('auto',   'Automatic'),
        ('manual', 'Manual'),
    ]

    make         = models.CharField(max_length=60)
    model        = models.CharField(max_length=60)
    year         = models.IntegerField()             # IntegerField
    price        = models.DecimalField(              # DecimalField
                       max_digits=10, decimal_places=2
                   )
    transmission = models.CharField(
                       max_length=10,
                       choices=TRANSMISSION_CHOICES,
                       default='auto',
                   )
    # ForeignKey: each car belongs to one branch
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        related_name='cars',   # branch.cars.all()
    )
    # ForeignKey: each car is managed by one seller
    seller = models.ForeignKey(
        Seller,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cars',   # seller.cars.all()
    )

    def __str__(self):
        return f'{self.year} {self.make} {self.model}'