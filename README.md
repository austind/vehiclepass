# vehiclepass

An experimental Python 3+ API for FordPass.

**NOTE**: This API is highly experimental and should not be considered stable.

## Setup

First, copy `example.env` to `.env` with appropriate values.

```python
import vehiclepass

vp = vehiclepass.VehiclePass()
vp.login()
print(vp.is_locked)  # True
```