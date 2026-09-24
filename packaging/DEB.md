# Debian / Ubuntu package

Troika D can be built as a native `.deb` package without requiring root privileges.

## Build

```bash
bash scripts/build-deb.sh
```

Default output:

```text
dist-deb/troika-d_0.1.0~beta1-1_all.deb
```

The Debian version uses `~beta1` so it sorts before a future stable `0.1.0`.

## Verify

```bash
bash scripts/verify-deb.sh dist-deb/troika-d_0.1.0~beta1-1_all.deb
```

## Install on Ubuntu/Debian

```bash
sudo apt install ./dist-deb/troika-d_0.1.0~beta1-1_all.deb
```

Using `apt install ./...` rather than `dpkg -i` allows APT to resolve Troika D's runtime dependencies.

## Remove

```bash
sudo apt remove troika-d
```

The package installs:

- `/usr/bin/troika-d`
- Python application code under `/usr/lib/troika-d`
- desktop launcher, AppStream metadata, and icon under `/usr/share`
- license and project-policy documents under `/usr/share/doc/troika-d`

The existing user-local installer remains supported separately. For clean package testing, remove the user-local installation first so `~/.local/share/applications` does not shadow the system launcher.
