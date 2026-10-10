#!/bin/bash
# Build on macOS; GitHub Actions runs this for both supported architectures.
set -euo pipefail
if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "The macOS bundle must be built on macOS (or by GitHub Actions)." >&2
    exit 1
fi
cd "$(dirname "$0")"
source_dir="$(pwd)"
python_executable="${PYTHON_EXECUTABLE:-python3}"
architecture="${1:-$(uname -m)}"
case "$architecture" in
    arm64|x86_64) ;;
    *) echo "Expected arm64 or x86_64." >&2; exit 1 ;;
esac

# Convert the existing artwork with Apple's tools; no extra image dependency.
iconset="build/macos/ATAIcon.iconset"
mkdir -p "$iconset"
for size in 16 32 128 256 512; do
    sips -z "$size" "$size" ATAIcon.png --out "$iconset/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    sips -z "$double" "$double" ATAIcon.png --out "$iconset/icon_${size}x${size}@2x.png" >/dev/null
done
iconutil -c icns "$iconset" -o build/macos/ATAIcon.icns

"$python_executable" -m PyInstaller --noconfirm --clean --onedir --windowed \
    --name AltTrackingAssistantCompanion \
    --distpath dist/macos --workpath build/macos/pyinstaller --specpath build/macos \
    --target-arch "$architecture" --osx-bundle-identifier com.thegildedcanary.ata.companion \
    --icon "$source_dir/build/macos/ATAIcon.icns" --add-data "$source_dir/fonts:fonts" \
    --add-data "$source_dir/ATAIcon.png:." "$source_dir/app.py"
echo "Built Companion/dist/macos/AltTrackingAssistantCompanion.app ($architecture)"
