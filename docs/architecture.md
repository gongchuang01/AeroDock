# Architecture

```text
aerodock_offboard (ROS 2)
  |  OffboardControlMode / TrajectorySetpoint / VehicleCommand
  v
Micro XRCE-DDS Agent <---- UDP 8888 ----> PX4 uXRCE-DDS client
                                             |
                                             v
                                      Gazebo X500 model
  ^
  |  VehicleStatus / VehicleLocalPosition
  +-------------------------------------------
```

The controller uses a 10 Hz loop. PX4 requires a continuous Offboard heartbeat, so the node sends setpoints for two seconds before requesting the mode. State transitions are confirmed through PX4 status messages instead of assuming that commands succeeded.
