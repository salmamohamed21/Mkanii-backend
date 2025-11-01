from datetime import date
from django.utils import timezone
from apps.packages.models import RecurringPackage, RecurringInstance
from apps.payments.models import ResidentWallet, Transaction
from apps.notifications.models import Notification
from django.db import transaction as db_transaction
from celery import shared_task
from apps.accounts.models import ResidentProfile
from apps.buildings.models import Unit


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


@shared_task
def check_rental_end_dates():
    """
    فحص تواريخ انتهاء الإيجارات وإنهاء الإيجارات المنتهية
    - إلغاء تفعيل المستأجر إذا لم يتم التجديد
    - تحرير الوحدة (جعلها متاحة)
    - إشعار المالك والمستأجر
    """
    today = date.today()

    # العثور على جميع المستأجرين المعتمدين الذين انتهت إيجاراتهم
    expired_tenants = ResidentProfile.objects.filter(
        resident_type='tenant',
        status='approved',
        rental_end_date__lt=today
    )

    for tenant in expired_tenants:
        with db_transaction.atomic():
            # إلغاء تفعيل المستأجر
            tenant.status = 'inactive'
            tenant.is_present = False
            tenant.save()

            # تحرير الوحدة
            if tenant.unit:
                tenant.unit.status = 'available'
                tenant.unit.save()

            # إشعار المستأجر
            Notification.objects.create(
                user=tenant.user,
                title="انتهاء فترة الإيجار",
                message=f"انتهت فترة إيجار الوحدة {tenant.unit.apartment_number if tenant.unit else ''} في العمارة {tenant.unit.building.name if tenant.unit and tenant.unit.building else ''}. يرجى التواصل مع المالك للتجديد."
            )

            # إشعار المالك (رئيس الاتحاد)
            if tenant.unit and tenant.unit.building and tenant.unit.building.union_head:
                Notification.objects.create(
                    user=tenant.unit.building.union_head,
                    title="انتهاء إيجار وحدة",
                    message=f"انتهت فترة إيجار الوحدة {tenant.unit.apartment_number} في العمارة {tenant.unit.building.name}. الوحدة متاحة الآن للإيجار مرة أخرى."
                )
