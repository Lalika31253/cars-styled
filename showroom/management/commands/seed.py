from django.core.management.base import BaseCommand
from showroom.models import Branch, Seller, Car
import datetime


class Command(BaseCommand):
    def handle(self, *args, **options):
        # 4 branches
        b1 = Branch.objects.create(
            name='North End',
            city='Toronto',
            opened_date=datetime.date(2010, 3, 15),
        )
        b2 = Branch.objects.create(
            name='Lakeshore',
            city='Toronto',
            opened_date=datetime.date(2015, 7, 1),
        )
        b3 = Branch.objects.create(
            name='Westgate',
            city='Mississauga',
            opened_date=datetime.date(2018, 1, 20),
        )
        b4 = Branch.objects.create(
            name='Eastview',
            city='Scarborough',
            opened_date=datetime.date(2021, 9, 5),
        )

        # 3 sellers — some work at multiple branches
        s1 = Seller.objects.create(first_name='Alice', last_name='Martin')
        s2 = Seller.objects.create(first_name='Bob',   last_name='Chen')
        s3 = Seller.objects.create(first_name='Carol', last_name='Patel')

        s1.branches.set([b1, b2])   # Alice works at two branches
        s2.branches.set([b1, b3])
        s3.branches.set([b2, b3, b4])

        # a few cars
        Car.objects.create(make='Toyota', model='Camry',    year=2022,
                           price=28500, branch=b1, seller=s1)
        Car.objects.create(make='Honda',  model='Civic',    year=2023,
                           price=26000, branch=b1, seller=s2)
        Car.objects.create(make='Ford',   model='F-150',    year=2021,
                           price=45000, branch=b2, seller=s3,
                           transmission='manual')
        Car.objects.create(make='BMW',    model='3 Series', year=2023,
                           price=55000, branch=b3, seller=s2)

        self.stdout.write(self.style.SUCCESS('Database seeded!'))