cmake_minimum_required(VERSION 3.8)
project(e5_arm_sim)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY
    launch
    urdf
    worlds
    config
    models
  DESTINATION share/${PROJECT_NAME}
)

ament_package()

