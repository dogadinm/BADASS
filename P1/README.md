# P1 — GNS3 и Docker

P1 содержит два устройства из схемы задания: `host_dogadinm-1` и
`router_dogadinm-1`. В P1 они **не соединены кабелем**. Нужно показать,
что оба запускаются и их консоли доступны через GNS3. VXLAN относится к P2,
а BGP EVPN — к P3.

По subject итоговый проект запускается в виртуальной машине. Подготовка
и предварительные проверки на Mac не заменяют проверку в школьной Linux-VM.

## Состав

| Файл | Назначение |
| --- | --- |
| `host/Dockerfile` | Alpine, BusyBox, iproute2, iputils, tcpdump |
| `router/Dockerfile` | Alpine, FRRouting, сетевые инструменты и tini |
| `router/daemons` | Включённые службы BGP, OSPF и IS-IS |
| `router/frr.conf` | Базовые экземпляры протоколов без адресов интерфейсов |
| `router/vtysh.conf` | Единый файл сохранения конфигурации FRR |
| `router/entrypoint.sh` | Очистка временных PID-файлов и запуск watchfrr |
| `router/check.sh` | Проверка процессов и управляющих сокетов FRR |
| `scripts/build.sh` | Сборка обоих образов для linux/amd64 |
| `scripts/check.sh` | Проверки образов и повторного запуска |
| `scripts/package.py` | Добавление Docker-образов в экспорт GNS3 |
| `scripts/load-images.py` | Загрузка образов из готового архива |
| `P1.gns3` | Текстовая схема для просмотра изменений в Git |
| `P1.gns3project` | Portable export с обоими Docker-образами внутри |
| `VALIDATION.md` | Что проверено и что проверить в школе |

## Быстрый запуск в школе

Выполнять **внутри Linux-виртуалки, где работает GNS3 Server**, из корня
репозитория BADASS. Нужны Docker, Python 3 и GNS3 GUI/Server совместимых версий.
Проект подготовлен и проверен с GNS3 Server 2.2.55.

1. Загрузить уже собранные образы из архива:

   ```sh
   python3 P1/scripts/load-images.py
   ```

   Это локальная загрузка: Docker Hub для неё не нужен. Образы имеют имена
   `badass-host:p1` и `badass-router:p1`, архитектура — `linux/amd64`.

2. Проверить образы:

   ```sh
   sh P1/scripts/check.sh
   ```

3. В GNS3 выбрать **File → Import portable project**, указать
   `P1/P1.gns3project` и выбрать новую папку проекта. Если GNS3 предлагает
   сервер для устройств, выбрать Linux-сервер, на котором загружены образы.

4. Запустить оба устройства. Для команд открыть **Auxiliary console**
   в контекстном меню каждого устройства (основная Console маршрутизатора
   показывает вывод служб). Нажать Enter и выполнить `exec /bin/sh`, затем
   проверки из раздела ниже.

5. Остановить оба устройства, запустить снова и повторить проверки.

`P1.gns3project` — ZIP, его не нужно переименовывать. GNS3 2.2 пропускает
Docker-образы в обычном экспорте даже при Include images. Поэтому в наш архив
добавлен `docker-images/images.tar`, а загрузка выполняется отдельным шагом
**до импорта**. Сам GNS3 этот TAR автоматически не загружает.

Альтернатива Python-скрипту загрузки:

```sh
unzip -p P1/P1.gns3project docker-images/images.tar | docker load
```

## Сборка из исходников

Из корня BADASS:

```sh
sh P1/scripts/build.sh
sh P1/scripts/check.sh
```

По умолчанию собирается `linux/amd64`, включая сборку на Apple Silicon
через эмуляцию. Для локального эксперимента можно использовать
`PLATFORM=linux/arm64 sh P1/scripts/build.sh` и аналогично запустить проверку.
Перед упаковкой для школы снова собрать `linux/amd64`.

Образы не задают IP-адреса интерфейсов. Обычный `docker run` может сам назначить
адрес из Docker bridge; для проверки этого требования используется
`--network none`. Стандартные адреса loopback не являются настройкой сети P1.

## Ручная проверка на Mac или Linux

Хост:

```sh
docker run --rm -it --platform linux/amd64 --network none badass-host:p1
```

Внутри:

```sh
hostname
command -v busybox
ip -br addr
ping -c 3 127.0.0.1
tcpdump --version
exit
```

Маршрутизатор:

```sh
docker run -d --platform linux/amd64 --network none \
  --cap-add NET_ADMIN --cap-add NET_RAW --cap-add SYS_ADMIN \
  --ulimit nofile=4096:4096 \
  --name p1-router-local badass-router:p1
docker exec -it p1-router-local /bin/sh
```

Внутри, после нескольких секунд запуска:

```sh
/usr/local/bin/router-check
ps
vtysh -c 'show running-config'
vtysh -c 'show ip ospf'
vtysh -c 'show bgp summary'
vtysh -c 'show isis summary'
ip -br addr
exit
```

После проверки удалить только созданный тестовый контейнер и его том:

```sh
docker rm -fv p1-router-local
```

FRR требует сетевые capabilities и SYS_ADMIN для работы с пространствами
имён. При запуске из GNS3 нужные права предоставляет сам GNS3.

## Что показывать в консолях GNS3

В GNS3 использовать **Auxiliary console**. Сначала выполнить:

```sh
exec /bin/sh
```

Вспомогательная оболочка GNS3 использует собственный BusyBox: его `ip`
не поддерживает все параметры iproute2. Переключение запускает оболочку
из образа. Для явного вызова полного iproute2 также можно использовать
`/sbin/ip`.

На хосте: `hostname`, `command -v busybox`, `ip -br addr`, `tcpdump --version`.
Имя должно быть `host_dogadinm-1`; у Ethernet-интерфейса нет заданного IPv4-адреса. Linux может автоматически
создать IPv6 link-local адрес `fe80::...`; он не записан в конфигурацию образа.

На маршрутизаторе: `hostname`, `ps`, `/usr/local/bin/router-check`,
`vtysh -c 'show running-config'` и команды протоколов выше.
Имя — `router_dogadinm-1`. Работают `zebra`, `bgpd`, `ospfd`, `isisd`;
также FRR использует `mgmtd`, `staticd` и супервизор `watchfrr`.

- BGP настроен с частной AS 65000; соседей в P1 нет.
- OSPF настроен, интерфейсы по умолчанию passive; соседей и областей нет.
- Router ID OSPF может быть 0.0.0.0, поскольку адреса ещё не назначены.
- IS-IS запущен с экземпляром P1; NET и интерфейсы пока не назначаются.
- Сообщение `No BGP neighbors found` в этой топологии ожидаемо.
- `router-check` завершается с кодом 0 без текста при успешной проверке.

`/etc/frr` сохраняется как том GNS3. Для сохранения изменений через vtysh
использовать `write memory`. Для передачи изменений напарнице нужно также
перенести конфигурацию в файлы Git — изменения внутри контейнера сами туда
не попадают.

## Если собирать схему вручную

В **Edit → Preferences → Docker containers → New → Existing image** создать
два шаблона. Выбрать консоль Telnet:

| Устройство | Образ | Адаптеры | Start command |
| --- | --- | --- | --- |
| host_dogadinm-1 | badass-host:p1 | 1 | /bin/sh |
| router_dogadinm-1 | badass-router:p1 | 3 | /usr/local/bin/router-start |

Три адаптера маршрутизатора позволяют использовать образ в следующих
частях; в P1 они не подключены. Разместить устройства рядом, без кабеля.
Не подменять Start command маршрутизатора на `/bin/sh`: иначе FRR не стартует.
Консоль GNS3 открывает отдельную оболочку автоматически.

## Обновление сдаваемого архива

После изменений сначала пересобрать образы и проверить проект в GNS3.
Остановить устройства. Экспортировать **File → Export portable project**
с Include base images, например в `/tmp/P1-export.gns3project`.
Затем добавить фактические Docker-образы:

```sh
python3 P1/scripts/package.py /tmp/P1-export.gns3project
```

Это обновит `P1/P1.gns3project`. Текстовый `P1.gns3` можно обновить из экспорта:

```sh
unzip -p P1/P1.gns3project project.gns3 > P1/P1.gns3
```

В сдаваемом Git-репозитории должен быть именно архив с образами, а также
комментированные конфигурации. Если образы изменились, старый архив остаётся
старой версией до повторной упаковки.

## Передача для P2

Напарница использует те же теги `badass-host:p1` и `badass-router:p1`.
Образы можно загрузить из архива или собрать из P1. Адреса, мосты и VXLAN
настраиваются отдельно для устройств P2. IS-IS не заменяет OSPF в P3:
subject отдельно требует использовать OSPF в третьей части.

## Источники

- Subject BADASS, версия 2.1, раздел IV.1.
- https://docs.gns3.com/docs/emulators/create-a-docker-container-for-gns3
- https://docs.frrouting.org/en/latest/setup.html
- https://github.com/GNS3/gns3-server/blob/v2.2.55/gns3server/controller/export_project.py
