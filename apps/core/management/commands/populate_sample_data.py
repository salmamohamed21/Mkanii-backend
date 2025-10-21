from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
import random
from mkani.apps.accounts.models import User, ResidentProfile, TechnicianProfile
from mkani.apps.buildings.models import Building
from mkani.apps.packages.models import (
    Package, PackageUtility, PackagePrepaid, PackageFixed, PackageMisc,
    PackageBuilding, PackageInvoice
)
from mkani.apps.payments.models import Wallet, WalletTransaction, Invoice, Transaction
from mkani.apps.maintenance.models import MaintenanceRequest, MaintenanceInvoice


class Command(BaseCommand):
    help = 'Populate sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Starting to populate sample data...')

        # Get existing data
        users = list(User.objects.all())
        buildings = list(Building.objects.all())
        residents = list(ResidentProfile.objects.filter(status='accepted'))
        technicians = list(TechnicianProfile.objects.all())

        if not users or not buildings:
            self.stdout.write(self.style.ERROR('No users or buildings found. Please create some first.'))
            return

        # Create sample packages
        self.create_packages(users, buildings, residents)

        # Create wallets and transactions
        self.create_wallets_and_transactions(users, buildings, technicians)

        # Create maintenance requests
        self.create_maintenance_requests(buildings, residents, technicians)

        self.stdout.write(self.style.SUCCESS('Sample data populated successfully!'))

    def create_packages(self, users, buildings, residents):
        self.stdout.write('Creating sample packages...')

        # Create utility packages
        for i in range(5):
            user = random.choice(users)
            package = Package.objects.create(
                package_type='utilities',
                name=f'Utility Package {i+1}',
                description=f'Sample utility package {i+1}',
                is_recurring=True,
                created_by=user,
                start_date=date.today() - timedelta(days=random.randint(0, 30))
            )
            PackageUtility.objects.create(
                package=package,
                service_type=random.choice(['electricity', 'water', 'gas', 'internet']),
                company_name=f'Company {i+1}',
                meter_number=f'METER{i+1:04d}',
                customer_code=f'CUST{i+1:04d}',
                monthly_amount=random.uniform(100, 500),
                due_day=random.randint(1, 28)
            )
            # Link to random buildings
            for building in random.sample(buildings, random.randint(1, 3)):
                PackageBuilding.objects.create(package=package, building=building)

        # Create prepaid packages
        for i in range(3):
            user = random.choice(users)
            package = Package.objects.create(
                package_type='prepaid',
                name=f'Prepaid Package {i+1}',
                description=f'Sample prepaid package {i+1}',
                is_recurring=False,
                created_by=user,
                start_date=date.today() - timedelta(days=random.randint(0, 30))
            )
            PackagePrepaid.objects.create(
                package=package,
                meter_type=random.choice(['electricity', 'water']),
                manufacturer=f'Manufacturer {i+1}',
                meter_number=f'PREPAID{i+1:04d}',
                average_monthly_charge=random.uniform(200, 800)
            )
            for building in random.sample(buildings, random.randint(1, 2)):
                PackageBuilding.objects.create(package=package, building=building)

        # Create fixed packages
        for i in range(4):
            user = random.choice(users)
            package = Package.objects.create(
                package_type='fixed',
                name=f'Fixed Package {i+1}',
                description=f'Sample fixed package {i+1}',
                is_recurring=True,
                created_by=user,
                start_date=date.today() - timedelta(days=random.randint(0, 30))
            )
            PackageFixed.objects.create(
                package=package,
                monthly_amount=random.uniform(300, 1000),
                deduction_day=random.randint(1, 28),
                payment_method=random.choice(['union_head', 'direct_person']),
                beneficiary_name=f'Beneficiary {i+1}',
                beneficiary_phone=f'0123456789{i}',
                national_id=f'1234567890123{i}'
            )
            for building in random.sample(buildings, random.randint(1, 2)):
                PackageBuilding.objects.create(package=package, building=building)

        # Create misc packages
        for i in range(2):
            user = random.choice(users)
            package = Package.objects.create(
                package_type='misc',
                name=f'Misc Package {i+1}',
                description=f'Sample misc package {i+1}',
                is_recurring=False,
                created_by=user,
                start_date=date.today() - timedelta(days=random.randint(0, 30))
            )
            PackageMisc.objects.create(
                package=package,
                total_amount=random.uniform(500, 2000),
                payment_date=date.today() + timedelta(days=random.randint(1, 30)),
                deadline=date.today() + timedelta(days=random.randint(31, 60))
            )
            for building in random.sample(buildings, random.randint(1, 2)):
                PackageBuilding.objects.create(package=package, building=building)

        # Create package invoices
        packages = list(Package.objects.all())
        for package in packages:
            package_buildings = PackageBuilding.objects.filter(package=package)
            for pb in package_buildings:
                # Create invoices for the last 3 months
                for months_back in range(3):
                    due_date = date.today().replace(day=1) - timedelta(days=1) - timedelta(days=months_back*30)
                    amount = random.uniform(100, 1000)
                    status = random.choice(['pending', 'paid', 'overdue'])
                    PackageInvoice.objects.create(
                        package=package,
                        building=pb.building,
                        resident=random.choice(residents) if residents else None,
                        amount=amount,
                        due_date=due_date,
                        status=status,
                        payment_method=random.choice(['sahl', 'fawry', 'wallet']) if status == 'paid' else None
                    )

    def create_wallets_and_transactions(self, users, buildings, technicians):
        self.stdout.write('Creating wallets and transactions...')

        # Create wallets for users
        for user in users:
            wallet, created = Wallet.objects.get_or_create(
                owner_type='user',
                owner_id=user.id,
                defaults={'current_balance': random.uniform(0, 5000)}
            )
            if created:
                # Create some transactions
                for _ in range(random.randint(3, 10)):
                    amount = random.uniform(-500, 500)
                    transaction_type = 'credit' if amount > 0 else 'debit'
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=abs(amount),
                        transaction_type=transaction_type,
                        description=f'Sample {transaction_type} transaction'
                    )
                    wallet.current_balance += amount
                    wallet.save()

        # Create wallets for buildings
        for building in buildings:
            wallet, created = Wallet.objects.get_or_create(
                owner_type='building',
                owner_id=building.id,
                defaults={'current_balance': random.uniform(0, 10000)}
            )
            if created:
                for _ in range(random.randint(5, 15)):
                    amount = random.uniform(-1000, 1000)
                    transaction_type = 'credit' if amount > 0 else 'debit'
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=abs(amount),
                        transaction_type=transaction_type,
                        description=f'Building {transaction_type} transaction'
                    )
                    wallet.current_balance += amount
                    wallet.save()

        # Create wallets for technicians
        for tech in technicians:
            wallet, created = Wallet.objects.get_or_create(
                owner_type='technician',
                owner_id=tech.id,
                defaults={'current_balance': random.uniform(0, 2000)}
            )
            if created:
                for _ in range(random.randint(2, 8)):
                    amount = random.uniform(-200, 200)
                    transaction_type = 'credit' if amount > 0 else 'debit'
                    WalletTransaction.objects.create(
                        wallet=wallet,
                        amount=abs(amount),
                        transaction_type=transaction_type,
                        description=f'Technician {transaction_type} transaction'
                    )
                    wallet.current_balance += amount
                    wallet.save()

        # Create some invoices and transactions
        wallets = list(Wallet.objects.all())
        for _ in range(20):
            wallet = random.choice(wallets)
            user = User.objects.filter(id=wallet.owner_id).first() if wallet.owner_type == 'user' else random.choice(users)
            invoice = Invoice.objects.create(
                user=user,
                source_type='sample',
                source_id=random.randint(1, 100),
                amount=random.uniform(50, 1000),
                due_date=date.today() + timedelta(days=random.randint(1, 30)),
                status=random.choice(['pending', 'paid', 'overdue']),
                method=random.choice(['sahl', 'fawry', 'wallet'])
            )
            if invoice.status == 'paid':
                Transaction.objects.create(
                    wallet=wallet,
                    invoice=invoice,
                    amount=invoice.amount,
                    method=invoice.method,
                    status='completed',
                    transaction_reference=f'TXN{random.randint(100000, 999999)}',
                    description=f'Payment for invoice {invoice.id}'
                )

    def create_maintenance_requests(self, buildings, residents, technicians):
        self.stdout.write('Creating maintenance requests...')

        issues = [
            'Leaky faucet in kitchen',
            'Broken light fixture in hallway',
            'Clogged drain in bathroom',
            'Faulty electrical outlet',
            'Cracked window pane',
            'Malfunctioning elevator',
            'Pest control needed',
            'Painting required in common area',
            'Broken door lock',
            'Heating system repair'
        ]

        for _ in range(15):
            building = random.choice(buildings)
            resident = random.choice(residents) if residents else None
            technician = random.choice(technicians) if technicians else None

            request = MaintenanceRequest.objects.create(
                building=building,
                resident=resident,
                technician=technician,
                description=random.choice(issues),
                cost=random.uniform(50, 500),
                status=random.choice(['pending', 'in_progress', 'completed', 'cancelled'])
            )

            # Create invoice for completed requests
            if request.status == 'completed':
                MaintenanceInvoice.objects.create(
                    maintenance_request=request,
                    amount=request.cost,
                    status='paid'
                )
