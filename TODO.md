# TODO: Fix RegisterView Resident Creation Logic

## Completed Tasks
- [x] Add validation for owner: require 'area' and 'rooms_count' fields
- [x] Add validation for tenant: require 'owner_national_id', 'rental_start_date', 'rental_end_date', 'rental_value' fields
- [x] For tenant: query User by national_id, raise ValidationError if not found, set 'owner' in resident_profile_data
- [x] Remove 'owner_national_id' from resident_profile_data for tenant
- [x] For owner: set 'area' and 'rooms_count' in resident_profile_data

## Pending Tasks
- [ ] Test the changes to ensure data is saved correctly
- [ ] Verify error handling for missing required fields and invalid owner_national_id
