# syntax=docker/dockerfile:1
FROM ros:humble-ros-base-jammy

ARG PX4_MSGS_REF=release/1.16
ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
      git \
      python3-colcon-common-extensions \
      ros-humble-geometry-msgs \
      ros-humble-nav-msgs \
      ros-humble-sensor-msgs \
      ros-humble-std-msgs \
      ros-humble-visualization-msgs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/aerodock_ws
RUN git clone --depth 1 --branch "$PX4_MSGS_REF" \
      https://github.com/PX4/px4_msgs.git src/px4_msgs
COPY src/aerodock_offboard src/aerodock_offboard

RUN source /opt/ros/humble/setup.bash \
    && colcon build --merge-install --packages-up-to aerodock_offboard

COPY tests /opt/aerodock_tests
RUN PYTHONPATH=/opt/aerodock_ws/src/aerodock_offboard/scripts \
    python3 -m unittest discover -s /opt/aerodock_tests -v

COPY --chmod=755 docker/entrypoint.sh /aerodock_entrypoint.sh
ENTRYPOINT ["/aerodock_entrypoint.sh"]
CMD ["bash"]
