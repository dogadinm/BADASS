# BADASS

GNS3 + Docker: VXLAN static/multicast и BGP EVPN. Общие образы —
`badass-host:p1`, `badass-router:p1`, архитектура **linux/amd64**.

**Начать с [SCHOOL.md](SCHOOL.md)** — пошаговый запуск на учебном Linux x86_64.
Результаты проверок и ограничения: [CHECKS.md](CHECKS.md).

| Часть | Документация | Portable project |
|---|---|---|
| P1: Docker и службы FRR | [P1](P1/README.md) | [P1.gns3project](P1/P1.gns3project) |
| P2: static VXLAN | [P2](P2/README.md) | [P2.gns3project](P2/P2.gns3project) |
| P2: multicast VXLAN | [P2](P2/README.md) | [P2-multicast.gns3project](P2/P2-multicast.gns3project) |
| P3: OSPF + BGP EVPN | [P3](P3/README.md) | [P3.gns3project](P3/P3.gns3project) |

```sh
# На Linux-машине, где работает GNS3 Server:
python3 P1/scripts/load-images.py
sh P2/scripts/check.sh
# При запущенном GNS3 Server: отдельные временные проекты, реальные консоли.
python3 scripts/check-gns3.py
```

В GUI использовать **Import portable project**. P2/P3 автоматически применяют
сохранённые конфигурации при каждом запуске. Образы не содержат IP по умолчанию.

После изменения исходных конфигураций пересобрать P2/P3:

```sh
python3 scripts/build-projects.py
```

Эта команда берёт готовые amd64-образы из P1, не скачивает и не пересобирает их.
После изменений требуется повторная интеграционная проверка. Для сборки самих
образов: `sh P1/scripts/build.sh`; затем обновить архив P1 по его README.
