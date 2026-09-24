# Release Checklist — v0.1.0-beta.1

## Automated gates

- [x] Unit tests.
- [x] Native GTK/GDK import smoke test.
- [x] User-local install → verify → uninstall smoke cycle.
- [x] Desktop file validation — CI #240.
- [x] AppStream validation — CI #240.
- [x] Python wheel build — CI #240.
- [x] Python source-distribution build — CI #240.
- [x] Release metadata consistency test — CI #240.

## Human release-candidate gate

Run from `release/v0.1.0-beta.1` after CI passes.

- [ ] Application opens from the Ubuntu application menu with the approved Troika D icon.
- [ ] Full Screen / Balanced / 30 FPS / no audio / no webcam produces a playable file.
- [ ] Window / Balanced / 30 FPS produces satisfactory motion quality.
- [ ] Area / Balanced / 15 or 30 FPS records only the selected area.
- [ ] Microphone recording works.
- [ ] System audio recording works.
- [ ] Microphone + system audio works together.
- [ ] Webcam overlay works.
- [ ] Pause / Resume works.
- [ ] Screenshot system workflow opens and returns cleanly.
- [ ] Cancel from the portal is treated as normal cancellation.
- [ ] Stop/finalization produces a playable output.

## Publication gate

Only after automated and human gates pass:

- [ ] Merge release PR to `main`.
- [ ] Create tag `v0.1.0-beta.1` on the exact accepted merge commit.
- [ ] Create GitHub pre-release using the reviewed release notes.
- [ ] Create post-release recovery baseline.
- [ ] Verify GitHub release page and source archives.
