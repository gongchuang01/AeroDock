cmake_minimum_required(VERSION 3.8)
project(aerodock_offboard)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(px4_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

add_executable(offboard_mission src/offboard_mission.cpp)
ament_target_dependencies(offboard_mission rclcpp px4_msgs)

add_executable(waypoint_mission src/waypoint_mission.cpp)
ament_target_dependencies(waypoint_mission rclcpp px4_msgs geometry_msgs)
target_compile_features(waypoint_mission PUBLIC cxx_std_17)
target_compile_features(offboard_mission PUBLIC cxx_std_17)

install(TARGETS offboard_mission waypoint_mission DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config launch rviz DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/trajectory_visualizer.py scripts/obstacle_safety.py scripts/local_avoidance.py scripts/avoidance_core.py DESTINATION lib/${PROJECT_NAME})

ament_package()
