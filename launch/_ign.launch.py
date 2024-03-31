import sys

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription, LaunchService
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    ExecuteProcess,
)
from launch.substitutions import (
    Command,
    FindExecutable,
    PathJoinSubstitution,
    Command,
    LaunchConfiguration,
    TextSubstitution,
    PythonExpression,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ld = LaunchDescription()

    robot_name_arg = DeclareLaunchArgument(
        "robot_name", description="robot", default_value=""
    )
    ld.add_action(robot_name_arg)

    simulation_sync_arg = DeclareLaunchArgument(
        "simulation_sync",
        description="Run event based simulation",
        default_value="False",
    )
    ld.add_action(simulation_sync_arg)

    # GZ
    world_filename = "ign_world.world"
    world_path = PathJoinSubstitution(
        [FindPackageShare("hidro_robots"), "worlds", world_filename]
    )

    # Use the line when RViz is ready
    # enable_gui = PythonExpression(["' -s' if ", LaunchConfiguration('simulation_sync'), " else ''"])
    enable_gui = PythonExpression(
        ["' ' if ", LaunchConfiguration("simulation_sync"), " else ' '"]
    )

    gz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                PathJoinSubstitution(
                    [FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py"]
                )
            ]
        ),
        launch_arguments={"gz_args": [world_path, enable_gui]}.items(),
    )

    ld.add_action(gz)

    # XACRO GAZEBO
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("hidro_robots"),
                    "robots",
                    LaunchConfiguration("robot_name"),
                    "xacro",
                    "description.urdf.xacro",
                ]
            ),
            " simulation_sync:=",
            LaunchConfiguration("simulation_sync"),
            " simulation_px4:=False",
        ]
    )

    robot_description = {"robot_description": robot_description_content}

    # ROBOT STATE PUBLISHER GAZEBO
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        namespace="gazebo",
        parameters=[robot_description],
    )

    ld.add_action(node_robot_state_publisher)

    # SPAWN ENTITY
    # spawn_entity = Node(
    #     package="ros_gz_sim",
    #     executable="create",
    #     arguments=[
    #         "-topic",
    #         ["gazebo", "/robot_description"],
    #         "-entity",
    #         LaunchConfiguration("robot_name"),
    #         "-x 0",
    #         "-y 0",
    #         "-z 1.0",
    #     ],
    #     output="screen",
    # )

    # TODO: this is a workaround. The proper command is to call the command above, 
    # with Node. But that command does not place the robot at the specified initial position.
    spawn_entity = ExecuteProcess(
        cmd=[
            [
                "ros2 run ros_gz_sim create -topic /gazebo/robot_description -z 1.0"
            ]
        ],
        shell=True,
    )

    ld.add_action(spawn_entity)

    return ld


if __name__ == "__main__":
    ls = LaunchService()
    ls.include_launch_description(generate_launch_description())
    sys.exit(ls.run())
