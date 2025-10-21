from datetime import date
from django.utils import timezone
from mkani.apps.packages.models import Package, PackageBuilding, PackageInvoice
from mkani.apps.payments.models import Wallet, Transaction, Invoice
from mkani.apps.notifications.models import Notification
from django.db import transaction as db_transaction
from celery import shared_task


@shared_task
def generate_monthly_invoices():
    """
    توليد فواتير الباقات الشهرية لجميع المباني والسكان
    + خصم تلقائي من المحفظة إن أمكن
    """
    today = date.today()
    current_month = today.month
    current_year = today.year

    active_packages = Package.objects.filter(is_recurring=True)

    for pkg in active_packages:
        package_buildings = PackageBuilding.objects.filter(package=pkg)

        for package_building in package_buildings:
            building = package_building.building
            residents = building.residents.all()

            for resident in residents:
                # Determine amount based on package type
                if pkg.package_type == 'utilities':
                    utility = pkg.packageutility
                    amount = utility.monthly_amount / len(residents) if len(residents) else 0
                    due_day = utility.due_day
                elif pkg.package_type == 'fixed':
                    fixed = pkg.packagefixed
                    amount = fixed.monthly_amount / len(residents) if len(residents) else 0
                    due_day = fixed.deduction_day
                else:
                    continue  # Skip non-recurring or unsupported types

                package_invoice, created = PackageInvoice.objects.get_or_create(
                    package=pkg,
                    building=building,
                    resident=resident,
                    due_date=date(current_year, current_month, min(due_day, 28)),
                    defaults={"amount": amount, "status": "pending"},
                )

                if created:
                    # محاولة خصم المبلغ تلقائيًا من محفظة الساكن
                    try:
                        with db_transaction.atomic():
                            wallet = Wallet.objects.select_for_update().get(owner_type='user', owner_id=resident.user.id)
                            if wallet.current_balance >= amount:
                                wallet.current_balance -= amount
                                wallet.save()

                                Transaction.objects.create(
                                    wallet=wallet,
                                    amount=amount,
                                    method="wallet",
                                    status="completed",
                                )

                                package_invoice.status = "paid"
                                package_invoice.payment_method = "wallet"
                                package_invoice.transaction = Transaction.objects.filter(wallet=wallet).last()
                                package_invoice.save()

                                Notification.objects.create(
                                    user=resident.user,
                                    message=f"تم خصم {amount} جنيه من محفظتك مقابل باقة {pkg.name} لشهر {today.strftime('%B')}",
                                )

                            else:
                                Notification.objects.create(
                                    user=resident.user,
                                    message=f"رصيدك غير كافٍ لدفع فاتورة باقة {pkg.name} بمبلغ {amount} جنيه. الرجاء شحن المحفظة.",
                                )

                    except Wallet.DoesNotExist:
                        Notification.objects.create(
                            user=resident.user,
                            message=f"لم يتم العثور على محفظتك، برجاء إنشاء محفظة لتفعيل الدفع التلقائي.",
                        )
