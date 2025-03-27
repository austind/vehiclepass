# vehiclepass

An experimental Python 3+ API for FordPass.

**NOTE**: This API is highly experimental and should not be considered stable.

## Setup

First, copy `example.env` to `.env` with appropriate values.

```python
import vehiclepass

v = vehiclepass.vehicle()
# If you don't use env vars, this is also an option:
# v = vehiclepass.vehicle(username="user@example.com", password="yourpasword", vin="yourvin")
with vehiclepass.vehicle() as v:
    print(v.is_locked)  # True
```