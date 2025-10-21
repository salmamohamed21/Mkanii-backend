"""
Shared payment-related utilities and services for the core app.
This module can be extended to include common payment processing,
wallet management, transaction helpers, and integration with payment gateways.
"""

def calculate_monthly_amount(package, residents_count):
    """
    Calculate the monthly amount per resident for a given package.
    """
    if residents_count == 0:
        return 0
    return package.monthly_amount / residents_count

# Additional shared payment utilities can be added here.
