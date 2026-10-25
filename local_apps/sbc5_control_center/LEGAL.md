# Legal and safety notice

## Software licence

SBC5 Control Center original source code is licensed under the **Apache License, Version 2.0**. See `LICENSE`. The software is provided on an **AS IS** basis, without warranties or conditions except where applicable law requires otherwise.

## Hardware and system changes

SBC5 Control Center can perform privileged operations on the Home Assistant host and Raspberry Pi 5, including fan control, `config.txt` edits, boot-related settings, CPU/GPU clock configuration, voltage/turbo settings, USB power settings and restart requests. Incorrect or overly aggressive settings may cause instability, failed boot, data loss, thermal problems, increased power consumption or reduced hardware lifetime.

Use advanced/overclocking functions only when you understand the affected Raspberry Pi configuration. Keep recoverable backups and maintain a recovery path that does not depend on this application.

## No substitute for platform safety

The application's guards, backups, calibration and recovery logic supplement but do not replace Raspberry Pi firmware protections, kernel thermal management, suitable cooling, a compliant power supply, Home Assistant backups or normal system administration practices.

## Independent project

SBC5 Control Center is an independent open-source project. It is not affiliated with, endorsed by, sponsored by, or an official product of Raspberry Pi Ltd, Home Assistant or the Open Home Foundation.

**Raspberry Pi is a trademark of Raspberry Pi Ltd.** “for Raspberry Pi 5” is used only to describe compatibility with genuine Raspberry Pi 5 hardware. See `TRADEMARKS.md`.

## Third-party software

Container images and runtime environments include third-party software under separate licences. Those components are not relicensed by Apache-2.0. See `THIRD_PARTY_NOTICES.md` and `LICENSE_AUDIT.md`.

## Technical notice

The legal/compliance files in this repository are a technical publication record and are not individual legal advice. Contributors and redistributors remain responsible for compliance with laws and third-party licence terms applicable to their distribution and jurisdiction.
