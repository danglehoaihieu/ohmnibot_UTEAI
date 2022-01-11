execute_process(COMMAND "/home/hieu/catkin_ws/build/geometry2-melodic-devel/tf2_py/catkin_generated/python_distutils_install.sh" RESULT_VARIABLE res)

if(NOT res EQUAL 0)
  message(FATAL_ERROR "execute_process(/home/hieu/catkin_ws/build/geometry2-melodic-devel/tf2_py/catkin_generated/python_distutils_install.sh) returned error code ")
endif()
