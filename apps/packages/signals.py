from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction as db_transaction
from datetime import date
from .models import Package, PackageBuilding, PackageInvoice
from mkani.apps.payments.models import Wallet, Transaction, Invoice
from mkani.apps.notifications.models import Notification


@receiver(post_save, sender=Package)
def generate_invoices_on_package_creation(sender, instance, created, **kwargs):
    """
    Generate PackageInvoice invoices for all residents in the buildings when a Package is created.
    Attempt auto payment immediately for recurring packages.
    """
    if not created:
        return

    package = instance
    package_buildings = PackageBuilding.objects.filter(package=package)

    if not package_buildings:
        return

    for package_building in package_buildings:
        building = package_building.building
        residents = building.residents.all()

        if not residents:
            continue

        # Determine amount and due_date based on package type
        if package.package_type == 'utilities':
            utility = package.packageutility
            amount_per_resident = utility.monthly_amount / len(residents)
            due_date = package.start_date.replace(day=min(utility.due_day, 28))
        elif package.package_type == 'fixed':
            fixed = package.packagefixed
            amount_per_resident = fixed.monthly_amount / len(residents)
            due_date = package.start_date.replace(day=min(fixed.deduction_day, 28))
        elif package.package_type == 'misc':
            misc = package.packagemisc
            amount_per_resident = misc.total_amount / len(residents)
            due_date = misc.deadline
        else:
            continue  # Skip prepaid for now or handle differently

        for resident in residents:
            # Create the PackageInvoice
            package_invoice = PackageInvoice.objects.create(
                package=package,
                building=building,
                resident=resident,
                amount=amount_per_resident,
                due_date=due_date,
                status='pending'
            )

            # Attempt auto payment for recurring packages
            if package.is_recurring:
                try:
                    with db_transaction.atomic():
                        wallet = Wallet.objects.select_for_update().get(owner_type='user', owner_id=resident.user.id)
                        if wallet.current_balance >= amount_per_resident:
                            wallet.current_balance -= amount_per_resident
                            wallet.save()

                            Transaction.objects.create(
                                wallet=wallet,
                                amount=amount_per_resident,
                                method="wallet",
                                status="completed",
                            )

                            package_invoice.status = "paid"
                            package_invoice.payment_method = "wallet"
                            package_invoice.transaction = Transaction.objects.filter(wallet=wallet).last()
                            package_invoice.save()

                            Notification.objects.create(
                                user=resident.user,
                                message=f"تم خصم {amount_per_resident} جنيه من محفظتك مقابل باقة {package.name} الجديدة",
                            )
                        else:
                            Notification.objects.create(
                                user=resident.user,
                                message=f"رصيدك غير كافٍ لدفع فاتورة باقة {package.name} الجديدة بمبلغ {amount_per_resident} جنيه. الرجاء شحن المحفظة.",
                            )

                except Wallet.DoesNotExist:
                    Notification.objects.create(
                        user=resident.user,
                        message=f"لم يتم العثور على محفظتك، برجاء إنشاء محفظة لتفعيل الدفع التلقائي لباقة {package.name}.",
                    )
