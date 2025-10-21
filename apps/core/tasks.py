from datetime import date
from django.utils import timezone
from mkani.apps.packages.models import RecurringPackage, RecurringInstance
from mkani.apps.payments.models import ResidentWallet, Transaction
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

    active_packages = RecurringPackage.objects.filter(is_active=True)

    for pkg in active_packages:
        residents = pkg.building.residents.all()

        for resident in residents:
            # المبلغ بالتساوي
            amount = pkg.monthly_amount / len(residents) if len(residents) else 0

            instance, created = RecurringInstance.objects.get_or_create(
                package=pkg,
                resident=resident,
                due_date=date(current_year, current_month, pkg.due_day),
                defaults={"amount": amount, "status": "pending"},
            )

            if created:
                # محاولة خصم المبلغ تلقائيًا من محفظة الساكن
                try:
                    with db_transaction.atomic():
                        wallet = ResidentWallet.objects.select_for_update().get(resident=resident)
                        if wallet.balance >= amount:
                            wallet.balance -= amount
                            wallet.save()

                            Transaction.objects.create(
                                resident=resident,
                                instance=instance,
                                amount=amount,
                                method="wallet",
                                status="paid",
                            )

                            instance.status = "paid"
                            instance.save()

                            Notification.objects.create(
                                user=resident.user,
                                message=f"تم خصم {amount} جنيه من محفظتك مقابل باقة {pkg.name} لشهر {today.strftime('%B')}",
                            )

                        else:
                            instance.status = "unpaid"
                            instance.save()
                            Notification.objects.create(
                                user=resident.user,
                                message=f"رصيدك غير كافٍ لدفع فاتورة باقة {pkg.name} بمبلغ {amount} جنيه. الرجاء شحن المحفظة.",
                            )

                except ResidentWallet.DoesNotExist:
                    Notification.objects.create(
                        user=resident.user,
                        message=f"لم يتم العثور على محفظتك، برجاء إنشاء محفظة لتفعيل الدفع التلقائي.",
                    )
