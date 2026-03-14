# Push 2 Display Bridge

VDMX → Syphon → Python → Push 2 LCD display bridge for macOS.

## Architecture

Pipeline: VDMX publishes a Syphon server → `syphon-python` receives GPU-shared frames
→ resize/convert to 960×160 BGR565 → `push2-python` sends via USB bulk transfer.

## Key specs

- Push 2 USB: VID `0x2982`, PID `0x1967`, Interface 0, Endpoint `0x01`
- Display: 960×160, 16-bit BGR565, 2048-byte line stride, XOR mask `E7 F3 E7 FF`
- Frame = 16-byte header (`FF CC AA 88` + 12×`00`) + 327,680 bytes pixel data
- Display blacks out after 2s without a frame — must send keep-alive frames
- Target: 30+ fps. BGR565 native path gets ~36 fps; RGB float path is slower (~14 fps)

## VDMX Setup

Create a dedicated Syphon output in VDMX named **"Push2"** at **960×160**.
The bridge looks for a server named "Push2" by default. Setting the layer to
the exact display resolution avoids resize overhead and gives you pixel-perfect
control over cropping/composition in VDMX.

## Modules

- `src/push2_bridge/syphon_receiver.py` — Syphon client, discovers VDMX server
- `src/push2_bridge/display.py` — Push 2 display wrapper
- `src/push2_bridge/converter.py` — Frame resize & color conversion
- `src/push2_bridge/bridge.py` — Main loop tying it all together

## Prerequisites

```bash
brew install libusb
```

Only one app can access the Push 2 display at a time — close Ableton Live first.

## Dev

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```
