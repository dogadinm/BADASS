# P3 — OSPF, BGP EVPN и VXLAN

Готовый portable project: `P3.gns3project`. Импортировать через GNS3
**File → Import portable project** после загрузки образов из P1.
Образы общие: `badass-host:p1` и `badass-router:p1`, `linux/amd64`.
Инструкция для учебного компьютера: [SCHOOL.md](../SCHOOL.md).

## Топология

```text
                    router_dogadinm-1 (RR)
                    /        |         \
      router_dogadinm-2  router_dogadinm-3  router_dogadinm-4
               |                |                 |
       host_dogadinm-1   host_dogadinm-2    host_dogadinm-3
```

Все три канала RR — отдельные /30 сети. На RR eth0/eth1/eth2 подключены
к eth0 соответствующего leaf. На каждом leaf eth1 подключён к eth0 хоста.

| Устройство | Loopback | Underlay | Overlay |
|---|---|---|---|
| router 1 / RR | 1.1.1.1/32 | eth0 10.1.1.1/30; eth1 10.1.1.5/30; eth2 10.1.1.9/30 | — |
| router 2 | 1.1.1.2/32 | eth0 10.1.1.2/30 | VNI 10 / br0 |
| router 3 | 1.1.1.3/32 | eth0 10.1.1.6/30 | VNI 10 / br0 |
| router 4 | 1.1.1.4/32 | eth0 10.1.1.10/30 | VNI 10 / br0 |
| host 1 | — | — | 192.168.10.1/24 |
| host 2 | — | — | 192.168.10.2/24 |
| host 3 | — | — | 192.168.10.3/24 |

## Как работает сеть

OSPF area 0 распространяет маршруты к loopback-адресам. iBGP AS 65000
установлен между loopback leaf и RR и переносит только `l2vpn evpn`.
RR принимает динамических клиентов из `1.1.1.0/29` через peer-group LEAVES;
leaf знает только RR. Полносвязной BGP-сетки между leaf нет.

VXLAN использует VNI 10 и UDP 4789. У туннелей нет `remote` или multicast
group: удалённые VTEP и MAC устанавливает FRR через EVPN. Type 3 сообщает
об участниках VNI, type 2 — о MAC хостов. Обучение на access-порту включено,
а на VXLAN-порту отключено (`nolearning`, `learning off`).

`br0` — L2-мост без IP. Шлюз хостам для связи в одной подсети не нужен.
MTU хостов/моста/VXLAN — 1450, underlay — 1500. RR отражает BGP-маршруты;
в этой физической топологии он также маршрутизирует underlay-пакеты между
leaf, но не терминирует VXLAN.

Сетевые команды находятся в `router*/network.sh`, FRR — в `router*/frr.conf`,
хосты — в `hosts/`. Архив содержит их в сохраняемых каталогах `/etc/network`
и `/etc/frr`. Start command `/bin/sh /etc/network/start.sh` применяет сеть,
затем запускает FRR или shell. После Stop/Start ничего вставлять не нужно.
Настройки P3 не добавляются в базовые образы P1.

## Проверки через Auxiliary console

В каждой консоли сначала `exec /bin/sh`.

На RR и leaf:

```sh
vtysh -c 'show ip ospf neighbor'
vtysh -c 'show ip route ospf'
vtysh -c 'show bgp l2vpn evpn summary'
vtysh -c 'show bgp l2vpn evpn route'
```

На leaf:

```sh
vtysh -c 'show evpn vni'
vtysh -c 'show evpn mac vni 10'
ip -d link show vxlan10
bridge fdb show dev vxlan10
```

На host 1:

```sh
ping -c 3 192.168.10.2
ping -c 3 192.168.10.3
ping -c 3 -M do -s 1422 192.168.10.3
```

Для демонстрации MAC без IP сначала запустить только маршрутизаторы:
ожидаются type 3 и отсутствие хостовых type 2. Затем запустить хост,
убрать его IP и отправить Ethernet/ARP кадры:

```sh
ip addr flush dev eth0
arping -D -I eth0 -c 3 192.168.10.254
```

На остальных leaf проверить появление MAC в `show bgp l2vpn evpn route`.
Порт учит MAC при поступлении кадра, одного включения молчащего хоста
недостаточно. Восстановить адрес: `sh /etc/network/lab.sh`.

Захват на eth0 leaf:

```sh
tcpdump -ni eth0 'udp port 4789 or ip proto 89 or tcp port 179'
```

Автопроверка на машине GNS3 Server (локальный API и консоли):

```sh
python3 scripts/check-gns3.py --projects P3
```

Она импортирует отдельную временную копию и удаляет только её.
Исходный проект в GUI не затрагивается. Подробности проверки: [CHECKS.md](../CHECKS.md).

## Пересборка

После изменения конфигураций выполнить из корня репозитория:

```sh
python3 scripts/build-projects.py
```

Команда обновляет P2/P3 из исходников с теми же образами, что лежат в P1.
После пересборки снова проверить импорт/сеть. Редактирование рабочего
контейнера не меняет файлы Git: перенести правки в исходники либо экспортировать
проект заново. Для сохранения FRR в рабочем проекте: `vtysh -c 'write memory'`.

Основа конфигурации: [FRR 10.5 EVPN](https://docs.frrouting.org/en/stable-10.5/evpn.html),
[FRR BGP](https://docs.frrouting.org/en/stable-10.5/bgp.html), subject BADASS 2.1.
