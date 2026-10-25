# License and IP audit — SBC5 Control Center 2.6.19

**Audit date:** 2026-10-22  
**Scope:** Home Assistant application, HACS/Marketplace bridge, dashboard assets, branding and release packaging.  
**Project license:** **Apache License 2.0**.

## Result

### PASS — original project source

No vendored third-party source library requiring relicensing of the original project source was identified in the inspected tree. The bridge declares no Python package requirements of its own (`requirements: []`). Original SBC5 Control Center source is therefore distributed under Apache-2.0, subject to the third-party obligations documented below.

### PASS WITH OBLIGATIONS — application container

The application image installs third-party Alpine packages. Some are permissively licensed and some utilities are GPL/LGPL licensed. They are executed as separate command-line programs/processes rather than incorporated into the project source as linked libraries. Public distribution of the resulting container must still preserve applicable notices and satisfy the source-availability obligations of the exact third-party components shipped in that image.

### BRANDING CHANGE — 2.6.19

The public-facing project name is now **SBC5 Control Center**. The hardware reference is presented separately as **“for Raspberry Pi 5”**, solely to indicate compatibility. Public repository recommendations use the SBC5 project brand rather than a Raspberry Pi-derived repository identity.

The project artwork does not reproduce the official Raspberry Pi raspberry logo. The current icon is an original stylized board/cooling illustration.

This substantially reduces the specific branding issues identified in the 2.6.18 audit, but this technical review is **not a formal trademark clearance opinion** and cannot guarantee non-infringement in every jurisdiction.

**Raspberry Pi is a trademark of Raspberry Pi Ltd.**

Raspberry Pi trademark guidance reviewed for this release: https://www.raspberrypi.com/trademark-rules/

## Compatibility identifiers

The code intentionally retains existing `rpi5_*` entity IDs, domains, storage paths and migration names. Those strings are part of the established software interface and are retained to avoid breaking existing Home Assistant installations. They are not the public-facing project name.

## Apache-2.0 implementation

The release tree includes `LICENSE`, `NOTICE`, `TRADEMARKS.md`, `LEGAL.md`, `THIRD_PARTY_NOTICES.md` and this audit. Apache-2.0 applies to the project's original copyrightable source; third-party components remain under their original terms.

## What this audit does not certify

This is a technical source/dependency review, not formal legal advice. It does not establish patent clearance, trademark registration availability, jurisdiction-specific rights, or ownership of contributions not visible in the inspected source history.
