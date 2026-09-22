cmake_minimum_required(VERSION 3.8)
project(aerodock_offboard)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(px4_msgs REQUIRED)

add_executable(offboard_mission src/offboard_mission.cpp)
ament_target_dependencies(offboard_mission rclcpp px4_msgs)
target_compile_features(offboard_mission PUBLIC cxx_std_17)

install(TARGETS offboard_mission DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})

ament_package()
