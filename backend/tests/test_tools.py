from app.tools import get_vm, list_vms, nutanix_alerts, power_action


def test_list_powered_off_vms():
    result = list_vms(power_state="poweredOff")
    names = [vm["name"] for vm in result["vms"]]
    assert "batch-etl-01" in names
    assert result["count"] == 1


def test_get_vm():
    vm = get_vm("payments-api-01")
    assert vm["cluster"] == "prod-west-01"
    assert vm["power_state"] == "poweredOn"


def test_power_action_is_mock():
    result = power_action("jump-lab-01", "on")
    assert result["simulated_state"] == "poweredOn"
    assert "Mock" in result["note"]


def test_critical_alerts():
    result = nutanix_alerts(severity="critical")
    assert result["count"] == 1
    assert "disk" in result["alerts"][0]["title"].lower()
