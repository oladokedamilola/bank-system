from django.core.management.base import BaseCommand
from accounts.models import NINDatabase, BVNDatabase
from datetime import date

class Command(BaseCommand):
    help = 'Seed sample data into NINDatabase and BVNDatabase'

    def handle(self, *args, **kwargs):
        nin_records = [
            {
                "nin": "12345678901",
                "first_name": "John",
                "middle_name": "Michael",
                "last_name": "Doe",
                "date_of_birth": date(1990, 1, 1),
                "address": "123 Lagos Street, Ikeja",
                "phone_number": "08011111111"
            },
            {
                "nin": "23456789012",
                "first_name": "Jane",
                "middle_name": "Alice",
                "last_name": "Smith",
                "date_of_birth": date(1992, 2, 2),
                "address": "45 Abuja Road, Gwarinpa",
                "phone_number": "08022222222"
            },
            {
                "nin": "34567890123",
                "first_name": "Samuel",
                "middle_name": "Peter",
                "last_name": "Johnson",
                "date_of_birth": date(1988, 3, 3),
                "address": "78 Port Harcourt Ave, PH",
                "phone_number": "08033333333"
            },
            {
                "nin": "45678901234",
                "first_name": "Fatima",
                "middle_name": "Zainab",
                "last_name": "Bello",
                "date_of_birth": date(1995, 4, 4),
                "address": "9 Zaria Close, Kaduna",
                "phone_number": "08044444444"
            },
            {
                "nin": "56789012345",
                "first_name": "Chinedu",
                "middle_name": "Ifeanyi",
                "last_name": "Okeke",
                "date_of_birth": date(1993, 5, 5),
                "address": "11 Owerri Street, Imo",
                "phone_number": "08055555555"
            },
        ]

        bvn_records = [
            {
                "bvn": "11122233344",
                "first_name": "Linda",
                "middle_name": "Chioma",
                "last_name": "Eze",
                "date_of_birth": date(1989, 6, 6),
                "address": "22 Enugu Lane, Enugu",
                "phone_number": "08066666666"
            },
            {
                "bvn": "22233344455",
                "first_name": "Ahmed",
                "middle_name": "Ibrahim",
                "last_name": "Yusuf",
                "date_of_birth": date(1991, 7, 7),
                "address": "33 Kano Road, Kano",
                "phone_number": "08077777777"
            },
            {
                "bvn": "33344455566",
                "first_name": "Blessing",
                "middle_name": "Ruth",
                "last_name": "Okon",
                "date_of_birth": date(1994, 8, 8),
                "address": "14 Calabar Way, Cross River",
                "phone_number": "08088888888"
            },
            {
                "bvn": "44455566677",
                "first_name": "Tunde",
                "middle_name": "Ayodele",
                "last_name": "Adebayo",
                "date_of_birth": date(1987, 9, 9),
                "address": "88 Ibadan Close, Oyo",
                "phone_number": "08099999999"
            },
            {
                "bvn": "55566677788",
                "first_name": "Maryam",
                "middle_name": "Aisha",
                "last_name": "Umar",
                "date_of_birth": date(1996, 10, 10),
                "address": "100 Sokoto Road, Sokoto",
                "phone_number": "08100000000"
            },
        ]

        # Insert into NINDatabase
        for record in nin_records:
            NINDatabase.objects.update_or_create(nin=record["nin"], defaults=record)

        # Insert into BVNDatabase
        for record in bvn_records:
            BVNDatabase.objects.update_or_create(bvn=record["bvn"], defaults=record)

        self.stdout.write(self.style.SUCCESS("✅ NIN and BVN data seeded successfully."))
