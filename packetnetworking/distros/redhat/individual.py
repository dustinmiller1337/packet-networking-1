from .. import NetworkBuilder
from ...utils import generate_persistent_names
import os


# pylama:ignore=E501
class RedhatIndividualNetwork(NetworkBuilder):
    def build(self):
        if self.network.bonding.link_aggregation == "individual":
            self.build_tasks()

    def build_tasks(self):
        self.tasks = {}

        iface0 = self.network.interfaces[0]

        self.tasks[
            "etc/sysconfig/network"
        ] = """\
            NETWORKING=yes
            HOSTNAME={{ hostname }}
            {% if ip4pub %}
            GATEWAY={{ ip4pub.gateway }}
            {% else %}
            GATEWAY={{ ip4priv.gateway }}
            {% endif %}
            GATEWAYDEV={{ iface0.name }}
            NOZEROCONF=yes
        """

        self.tasks[
            "etc/sysconfig/network-scripts/ifcfg-{iface0.name}".format(iface0=iface0)
        ] = """\
            DEVICE={{ iface0.name }}
            NAME={{ iface0.name }}
            {% if ip4pub %}
            IPADDR={{ ip4pub.address }}
            NETMASK={{ ip4pub.netmask }}
            GATEWAY={{ ip4pub.gateway }}
            {% else %}
            IPADDR={{ ip4priv.address }}
            NETMASK={{ ip4priv.netmask }}
            GATEWAY={{ ip4priv.gateway }}
            {% endif %}
            BOOTPROTO=none
            ONBOOT=yes
            USERCTL=no

            {% if ip6pub %}
            IPV6INIT=yes
            IPV6ADDR={{ ip6pub.address }}/{{ ip6pub.cidr }}
            IPV6_DEFAULTGW={{ ip6pub.gateway }}
            {% endif %}
            {% for dns in resolvers %}
            DNS{{ loop.index }}={{ dns }}
            {% endfor %}
        """

        if self.ipv4pub:
            self.tasks[
                "etc/sysconfig/network-scripts/ifcfg-{iface0.name}:0".format(
                    iface0=iface0
                )
            ] = """\
                DEVICE={{ iface0.name }}:0
                NAME={{ iface0.name }}:0
                IPADDR={{ ip4priv.address }}
                NETMASK={{ ip4priv.netmask }}
                GATEWAY={{ ip4priv.gateway }}
                BOOTPROTO=none
                ONBOOT=yes
                USERCTL=no
                {% for dns in resolvers %}
                DNS{{ loop.index }}={{ dns }}
                {% endfor %}
            """

            # If no ip4pub is specified, the ip4priv is configured on the eth0 interface
            # so there is no need to add the custom route
            self.tasks[
                "etc/sysconfig/network-scripts/route-{iface0.name}".format(
                    iface0=iface0
                )
            ] = """\
                10.0.0.0/8 via {{ ip4priv.gateway }} dev {{ iface0.name }}:0
            """

        self.tasks[
            "etc/resolv.conf"
        ] = """\
            {% for server in resolvers %}
            nameserver {{ server }}
            {% endfor %}
        """

        self.tasks[
            "etc/hostname"
        ] = """\
            {{ hostname }}
        """

        self.tasks["etc/hosts"] = (
            "127.0.0.1   localhost localhost.localdomain localhost4 "
            + "localhost4.localdomain4\n"
            + "::1         localhost localhost.localdomain localhost6 "
            + "localhost6.localdomain6\n"
        )

        if self.metadata.operating_system.distro not in (
            "scientificcernslc",
            "redhatenterpriseserver",
            "redhatenterprise",
        ):
            for service in (
                "dbus-org.freedesktop.NetworkManager",
                "dbus-org.freedesktop.nm-dispatcher",
                "multi-user.target.wants/NetworkManager",
            ):
                self.tasks[
                    os.path.join("etc/systemd/system", service + ".service")
                ] = None
        else:
            self.tasks.update(generate_persistent_names())
        return self.tasks