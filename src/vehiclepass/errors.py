
class VehiclePassError(Exception):
    pass

class VehiclePassCommandError(VehiclePassError):
    pass

class VehiclePassStatusError(VehiclePassError):
    pass
