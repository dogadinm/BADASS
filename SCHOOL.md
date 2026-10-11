# Запуск BADASS на учебном Linux x86_64

Работать с актуальной копией **main**. Все команды ниже выполняются из корня
BADASS **внутри Linux-VM, в которой работает GNS3 Server**. Subject требует
виртуальную машину, даже если сам учебный компьютер тоже работает на Linux.
Архитектура должна быть `x86_64` / `amd64`, не 32-битная `i386`.

## 1. Перенести проект

Перенести всю папку BADASS или получить её через Git после сохранения и push
изменений с Mac. Простого `git clone` до push недостаточно: новые файлы пока
находятся только на Mac. При переносе нужны исходники и все четыре архива:

- `P1/P1.gns3project`
- `P2/P2.gns3project` — static
- `P2/P2-multicast.gns3project` — multicast
- `P3/P3.gns3project` — BGP EVPN

Не открывать один `P*.gns3` вместо импорта: JSON содержит схему, а конфигурации
и Docker-образы находятся внутри `.gns3project`.

## 2. Подготовить Linux-VM

Нужны Docker Engine, Python 3, GNS3 GUI/Server, uBridge, Dynamips,
`busybox-static` и терминал для Telnet. Для просмотра захвата — Wireshark.
Проверенная версия GNS3 Server: **2.2.55**; GUI и Server должны совпадать.
Практический ориентир для VM: 4 CPU, 8 GB RAM и 15 GB свободного диска;
это рекомендация для удобства, а не требование subject.

Если программы ещё не установлены, использовать
[официальную инструкцию GNS3 для Linux](https://docs.gns3.com/docs/getting-started/installation/linux)
для дистрибутива VM. На учебном хосте без административных прав установку
выполнять в своей VM. Не смешивать пакеты разных версий GNS3.

Проверить:

```sh
uname -m
python3 --version
docker info
gns3server --version
command -v ubridge
command -v dynamips
command -v busybox
```

`uname -m` должен показать `x86_64`. Пользователь, запускающий GNS3 Server,
должен иметь доступ к Docker и uBridge. Если Docker установлен, но пишет
`permission denied`, проверить членство в группе `docker`; после добавления
в группу выйти из сессии VM и войти снова. Не запускать весь GNS3 GUI через sudo.

В GNS3 выбрать локальный сервер **внутри VM**. Если GUI работает на хосте,
а Server — в VM, загрузку образов и проверки Docker выполнять именно в VM.

## 3. Загрузить готовые образы и проверить P1/P2

```sh
python3 P1/scripts/load-images.py
docker image inspect badass-host:p1 badass-router:p1 --format '{{.RepoTags}} {{.Os}}/{{.Architecture}}'
sh P2/scripts/check.sh
```

Оба образа должны быть `linux/amd64`, последняя команда должна завершиться
`PASS`. Она включает проверки P1 и обеих конфигураций P2. Сборка из Docker Hub
не требуется: образы уже внутри архива. Интернет нужен только для установки
самих инструментов, если их ещё нет.

Если изменялись Dockerfile и нужно пересобрать образы:

```sh
sh P1/scripts/build.sh
```

Обычный запуск сдаваемых архивов не требует этой команды.

## 4. Импортировать проекты в GUI

Для каждого архива: **File → Import portable project**, выбрать архив и
новую папку проекта. Если GNS3 спрашивает сервер — выбрать сервер VM с
загруженными образами. Теги `badass-host:p1` и `badass-router:p1` уже готовы;
вручную создавать Docker templates не требуется.

Проверять проекты по очереди. После каждого останавливать устройства.
Для команд использовать правую кнопку на устройстве → **Auxiliary console**,
нажать Enter и выполнить:

```sh
exec /bin/sh
```

Если консоль не открывается, настроить установленный terminal/Telnet client
в Preferences → General → Console applications.

### P1

Запустить оба устройства. Отсутствие кабеля в P1 — правильно.

На host:

```sh
hostname
command -v busybox
ip -br addr
```

На router:

```sh
hostname
/usr/local/bin/router-check
vtysh -c 'show running-config'
vtysh -c 'show ip ospf'
vtysh -c 'show bgp summary'
vtysh -c 'show isis summary'
```

Нет заранее назначенных глобальных IP и соседей. `router-check` при успехе
молчит. Имена включают `dogadinm`.

### P2 static и P2 multicast

Запустить все устройства соответствующего проекта. Настройки применяются
автоматически. На host 1:

```sh
ping -c 3 192.168.10.2
ping -c 3 -M do -s 1422 192.168.10.2
```

На обоих router:

```sh
ip -d link show vxlan10
bridge link
bridge fdb show br br0
```

Ожидаются VNI 10, UDP 4789, `br0`, два порта моста и удалённый MAC.
Для multicast дополнительно:

```sh
ip maddr show dev eth0
tcpdump -ni eth0 'udp port 4789 or igmp'
```

Группа — `239.1.1.1`. Для выхода из tcpdump — Ctrl+C. Показать оба проекта.

### P3

Сначала запустить только четыре router. Дать OSPF/BGP время сойтись.
На RR (`router_dogadinm-1`):

```sh
vtysh -c 'show ip ospf neighbor'
vtysh -c 'show bgp l2vpn evpn summary'
vtysh -c 'show bgp l2vpn evpn route'
```

Ожидаются три OSPF-соседа Full, три BGP-сессии с leaf и EVPN type 3.
Затем запустить три host. На host 1:

```sh
ping -c 3 192.168.10.2
ping -c 3 192.168.10.3
ping -c 3 -M do -s 1422 192.168.10.3
```

На leaf (`router_dogadinm-2/3/4`):

```sh
vtysh -c 'show ip route ospf'
vtysh -c 'show bgp l2vpn evpn route'
vtysh -c 'show evpn vni'
vtysh -c 'show evpn mac vni 10'
bridge fdb show dev vxlan10
tcpdump -ni eth0 'udp port 4789 or ip proto 89 or tcp port 179'
```

После трафика видны MAC/type 2, VNI 10 и удалённые FDB записи `extern_learn`.
Сценарий демонстрации обучения MAC без IP описан в [P3/README.md](P3/README.md).

## 5. Проверить перезапуск и сохранить результат

В каждом проекте выполнить Stop all → Start all и повторить ping/проверки.
P2/P3 восстанавливают сеть автоматически. Если исправляли конфигурацию через
vtysh, сохранить её `write memory`; сетевые изменения должны быть записаны
в `/etc/network/lab.sh`, иначе после перезапуска они исчезнут.

Дополнительная полная автопроверка GNS3 через локальный API (в той же VM):

```sh
python3 scripts/check-gns3.py
```

Она создаёт временные копии, проверяет P2 static/multicast и P3, затем удаляет
только свои копии. GNS3 Server должен работать на `127.0.0.1:3080`; другой
адрес задаётся `--url`, адрес консольных портов — `--console-host`.
При включённой HTTP-аутентификации использовать `--user LOGIN` и переменную
`GNS3_PASSWORD` (не публиковать пароль в репозитории).

Готовые архивы уже есть. Если в школе что-то меняли, остановить проект и
сделать **File → Export portable project**. В GNS3 2.2 галочка Include images
сама не гарантирует включение Docker-образов; добавить их нашим скриптом:

```sh
# Пример для P3. В качестве первого аргумента — новый экспорт из GUI.
python3 P1/scripts/package.py /tmp/P3-export.gns3project --output P3/P3.gns3project
```

Скрипт подходит всем этим проектам: они используют одинаковые два образа.
Аналогично для P1/P2, указав нужный выходной путь. Изменения в исходниках тоже
сохранить в Git. Перед защитой проверить `git status`, наличие архивов и
передачу всех изменений в сдаваемый репозиторий.

## Что уметь объяснить

Underlay/overlay, VXLAN/VNI/VTEP, `br0` и MAC/FDB, static против multicast,
зачем MTU 1450, OSPF для loopback, iBGP/Route Reflector, EVPN type 2 и type 3,
почему хостам в одной L2-подсети не нужен шлюз. Термины привязать к выводу
команд и реальному захвату пакетов, а не только выучить определения.


sudo apt install pipx python3-pyqt6 python3-pyqt6.qtsvg python3-pyqt6.qtwebsockets busybox-static

pipx install 'gns3-server==2.2.55'
pipx install 'gns3-gui==2.2.55'
pipx inject gns3-gui 'gns3-server==2.2.55' PyQt6
gns3server --version


sudo apt update
sudo apt install git build-essential cmake libpcap-dev libelf-dev libcap2-bin

mkdir -p ~/gns3-build
cd ~/gns3-build

git clone --depth 1 --branch v0.9.19 https://github.com/GNS3/ubridge.git
make -C ubridge
sudo make -C ubridge install

git clone --depth 1 --branch v0.2.23 https://github.com/GNS3/dynamips.git
cmake -S dynamips -B dynamips/build
cmake --build dynamips/build -j2
sudo cmake --install dynamips/build