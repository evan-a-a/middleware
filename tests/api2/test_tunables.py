import pytest

from middlewared.client import ValidationErrors
from middlewared.test.integration.utils import call, ssh
from middlewared.test.integration.utils.mock_binary import mock_binary

SYSCTL = "kernel.watchdog"
SYSCTL_DEFAULT_VALUE = "1"
SYSCTL_NEW_VALUE = "0"

ZFS = "zil_nocacheflush"
ZFS_DEFAULT_VALUE = "0"
ZFS_NEW_VALUE = "1"


def test_create_invalid_sysctl():
    with pytest.raises(ValidationErrors) as ve:
        call("tunable.create", {
            "type": "SYSCTL",
            "var": "kernel.truenas",
            "value": "1",
        }, job=True)

    assert ve.value.errors[0].attribute == "tunable_create.var"


def test_create_invalid_udev():
    with pytest.raises(ValidationErrors) as ve:
        call("tunable.create", {
            "type": "UDEV",
            "var": "61-truenas-pmem",
            "value": "# disable built-in truenas rule to enable memory loss",
        }, job=True)

    assert ve.value.errors[0].attribute == "tunable_create.var"


def test_create_invalid_zfs():
    with pytest.raises(ValidationErrors) as ve:
        call("tunable.create", {
            "type": "ZFS",
            "var": "zfs_truenas",
            "value": "1",
        }, job=True)

    assert ve.value.errors[0].attribute == "tunable_create.var"


def test_sysctl_lifecycle():
    def assert_default_value():
        assert ssh("cat /etc/sysctl.d/tunables.conf", check=False) == f""
        assert ssh(f"sysctl -n {SYSCTL}") == f"{SYSCTL_DEFAULT_VALUE}\n"

    def assert_new_value():
        assert ssh("cat /etc/sysctl.d/tunables.conf") == f"{SYSCTL}={SYSCTL_NEW_VALUE}\n"
        assert ssh(f"sysctl -n {SYSCTL}") == f"{SYSCTL_NEW_VALUE}\n"

    assert_default_value()

    tunable = call("tunable.create", {
        "type": "SYSCTL",
        "var": SYSCTL,
        "value": SYSCTL_NEW_VALUE,
    }, job=True)

    assert_new_value()

    call("tunable.update", tunable["id"], {
        "enabled": False,
    }, job=True)

    assert_default_value()

    call("tunable.update", tunable["id"], {
        "enabled": True,
    }, job=True)

    assert_new_value()

    call("tunable.delete", tunable["id"], job=True)

    assert_default_value()


def test_udev_lifecycle():
    def assert_exists():
        assert ssh("cat /etc/udev/rules.d/10-disable-usb.rules") == f"BUS==\"usb\", OPTIONS+=\"ignore_device\"\n"

    def assert_does_not_exist():
        assert ssh("cat /etc/udev/rules.d/10-disable-usb.rules", check=False) == f""

    tunable = call("tunable.create", {
        "type": "UDEV",
        "var": "10-disable-usb",
        "value": "BUS==\"usb\", OPTIONS+=\"ignore_device\""
    }, job=True)

    assert_exists()

    call("tunable.update", tunable["id"], {
        "enabled": False,
    }, job=True)

    assert_does_not_exist()

    call("tunable.update", tunable["id"], {
        "enabled": True,
    }, job=True)

    assert_exists()

    call("tunable.delete", tunable["id"], job=True)

    assert_does_not_exist()


def test_zfs_lifecycle():
    with mock_binary("/usr/sbin/update-initramfs", exitcode=0):
        def assert_default_value():
            assert ssh("cat /etc/modprobe.d/zfs.conf", check=False) == f""
            assert ssh(f"cat /sys/module/zfs/parameters/{ZFS}") == f"{ZFS_DEFAULT_VALUE}\n"

        def assert_new_value():
            assert ssh("cat /etc/modprobe.d/zfs.conf", check=False) == f"options zfs {ZFS}={ZFS_NEW_VALUE}\n"
            assert ssh(f"cat /sys/module/zfs/parameters/{ZFS}") == f"{ZFS_NEW_VALUE}\n"

        assert_default_value()

        tunable = call("tunable.create", {
            "type": "ZFS",
            "var": ZFS,
            "value": ZFS_NEW_VALUE,
        }, job=True)

        assert_new_value()

        call("tunable.update", tunable["id"], {
            "enabled": False,
        }, job=True)

        assert_default_value()

        call("tunable.update", tunable["id"], {
            "enabled": True,
        }, job=True)

        assert_new_value()

        call("tunable.delete", tunable["id"], job=True)

        assert_default_value()
