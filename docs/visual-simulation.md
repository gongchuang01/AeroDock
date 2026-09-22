# Visual simulation

AeroDock provides two synchronized views:

- **Gazebo:** the X500 vehicle and physical simulation.
- **RViz2:** planned waypoints, the cyan planned route, and the red measured trajectory.

The visual launcher uses Mesa software rendering because the development VM exposes a VMware SVGA
adapter.

## Run

Open three terminals on the Ubuntu desktop.

Terminal 1:

```bash
cd ~/aerodock/AeroDock
./scripts/run_visual_sim.sh
```

Terminal 2:

```bash
cd ~/aerodock/AeroDock
./scripts/run_visualization.sh
```

Terminal 3:

```bash
cd ~/aerodock/AeroDock
./scripts/run_waypoints.sh
```

After the aircraft lands:

```bash
./scripts/stop.sh
```

The NED coordinates from PX4 are converted to ROS ENU coordinates before publishing the RViz path.
