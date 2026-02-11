from aws import launch_byovpn_ec2

import pulumi.automation as auto



def main():
    """Launches the BYOVPN Instance and configures the client to connect."""
    def aws_

    stack = auto.create_stack(stack_name="byovpn-aws",
                                project_name="byovpn",
                                program=launch_byovpn_ec2)
                              


if __name__ == "__main__":
    main()