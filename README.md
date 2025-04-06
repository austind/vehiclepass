# vehiclepass

A Python 3.9+ API to manage your FordPass-enabled vehicle. Requires a FordPass account and a vehicle registered to it.

**NOTE**: This project is in early development. The API may change significantly before reaching v1.0.0.

Reads many status values, such as outside temperature, engine RPM, and door lock status. Full documentation pending.

Currently supports these commands:

* Remote start
* Cancel remote start
* Lock
* Unlock

## Install

```sh
pip install vehiclepass
```

## Quickstart

```python
import vehiclepass

with vehiclepass.vehicle(
    username="you@example.com",
    password="s3cr3t",
    vin="YOURVIN12345"
) as v:
    print(v.doors.are_locked)  # False
    # By default, this issues the unlock command, waits 30s, and verifies it took effect.
    # Pass verify=False to skip this check.
    v.doors.unlock()
    print(v.doors.are_locked)  # True

    # Most status values return a unit object that makes converting and printing the
    # value convenient.
    print(v.engine_coolant_temp.f)  # 55.4
    print(v.engine_coolant_temp.c)  # 13.0
    
    # When casting to string, uses the unit defined in env var VEHICLEPASS_DEFAULT_TEMP_UNIT.
    print(v.engine_coolant_temp)  # 55.4°F

    # Request a remote start. By default, the vehicle will automatically shut off after 15 minutes. Pass extend_shutoff=True to add another 15 minutes (30 minutes total).
    v.start()
    print(v.is_running)  # True
    print(v.is_remotely_started)  # True
    # Remotely started isn't the same as starting manually from the ignition in the vehicle.
    print(v.is_ignition_started)  # False
    print(v.shutoff_countdown)  # 14m 58s
    print(v.shutoff_countdown.s)  # 898.0
    print(v.shutoff_time)  # 2025-04-02 10:41:53.175933
```

## Contributing

Contributions welcome! Please [open an issue](https://github.com/austind/vehiclepass/issues/new) to discuss what you'd like to do first.

### Development

#### Prerequisites

* [uv](https://docs.astral.sh/uv/getting-started/installation/)

#### Environment

1. [Fork this repo](https://github.com/austind/vehiclepass/fork) to your personal GitHub account
1. Clone the repo locally
    ```sh
    USERNAME=<your-github-username>
    git clone https://github.com/$USERNAME/vehiclepass.git
    cd vehiclepass
    ```
1. Create a feature branch off of the `develop` branch
    ```sh
    git checkout develop
    git checkout -b 1234-short-description  # 1234 is the issue number you opened
1. Make your changes
1. Add at least one new test that covers your code, but as many as necessary
1. Ensure all tests pass
    ```sh
    nox -r  # The -r flag re-uses virtualenvs for faster re-runs
    ```
1. [Open a pull request](https://github.com/austind/vehiclepass/compare)
