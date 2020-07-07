from middlewared.schema import Int
from middlewared.service import accepts, ServicePartBase


class VMInfoBase(ServicePartBase):

    flags_base = {
        'intel_vmx': False,
        'unrestricted_guest': False,
        'amd_rvi': False,
        'amd_asids': False,
    }

    @accepts()
    async def supports_virtualization(self):
        """
        Returns "true" if system supports virtualization, "false" otherwise
        """

    @accepts()
    async def available_slots(self):
        """
        Returns available number of slots which can be used for attaching devices to a VM
        """

    @accepts()
    def flags(self):
        """
        Returns a dictionary with CPU flags for the hypervisor.
        """

    @accepts(Int('id'))
    async def get_console(self, id):
        """
        Get the console device from a given guest.

        Returns:
            str: with the device path or False.
        """
