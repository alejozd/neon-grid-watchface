# Sample files — provenance

| File | Source URL | Status |
|---|---|---|
| `SimpleAnalog.xml` | https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleAnalog/watchface/src/main/res/raw/watchface.xml | **complete, verbatim** |
| `SimpleDigital.xml` | https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleDigital/watchface/src/main/res/raw/watchface.xml | **complete, verbatim** |
| `Flavors.xml` | https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/Flavors/watchface/src/main/res/raw/watchface.xml | **complete, verbatim** |
| `ActiveAnalogClock.xml` | https://raw.githubusercontent.com/google/watchface/main/play-validations/memory-footprint/src/test/resources/ActiveAnalogClock.xml | **complete, verbatim** |
| `AndroidManifest-SimpleAnalog.xml` | https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleAnalog/watchface/src/main/AndroidManifest.xml | **complete, verbatim** |
| `AndroidManifest-Weather.xml` | https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/Weather/watchface/src/main/AndroidManifest.xml | **complete, verbatim** |
| `watch_face_info-SimpleAnalog.xml` | https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleAnalog/watchface/src/main/res/xml/watch_face_info.xml | **complete, verbatim** |
| `Complications.PARTIAL.xml` | https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/Complications/watchface/src/main/res/raw/watchface.xml | **PARTIAL — see below** |

## About `Complications.PARTIAL.xml`

The upstream file is ~150 KB. The `web_fetch` tool truncates large responses and keeps only
the head plus a small tail, so **50,613 bytes from the middle of this file could not be
retrieved** in this environment (the shell has no network access, so `curl` could not be
used as a fallback). The file on disk is byte-for-byte what was fetched, but it is **not
well-formed XML** and it ends mid-attribute.

What *is* present and trustworthy in it: the `UserConfigurations` block, `ComplicationSlot
slotId="0"` (PHOTO_IMAGE / EMPTY) in full, and the beginning of `ComplicationSlot slotId="1"`
including its `BoundingOval`, the full `type="SHORT_TEXT"` Complication with `PartDraw`/
`Ellipse`/`Fill`/`Stroke`, and a nested `Condition`/`Expressions`/`Compare`/`Default` tree.
The `RANGED_VALUE`, `GOAL_PROGRESS` and `WEIGHTED_ELEMENTS` Complication bodies are the part
that is truncated.

To obtain the complete file, run on a machine with network access:

```shell
git clone --depth 1 https://github.com/android/wear-os-samples
# file: WatchFaceFormat/Complications/watchface/src/main/res/raw/watchface.xml
```

For a **complete, well-formed** sample that does contain a full `ComplicationSlot` — with
`DefaultProviderPolicy` (including `primaryProvider`), `BoundingOval`, `Complication
type="SHORT_TEXT"`, `PartText`, `PartDraw`, `Condition`/`Compare`/`Default`, `Variant
mode="AMBIENT"` dimming on both interactive and ambient copies, and a live `[HEART_RATE]`
data-source expression — use **`Flavors.xml`** instead. Everything in `Flavors.xml` other
than the `<Flavors>`/`<Flavor>` block itself is WFF v1-compatible.

`ActiveAnalogClock.xml` is the smallest complete example of `AnalogClock` + `Localization` +
`HourHand`/`MinuteHand`/`SecondHand` + ambient `Variant` + `<Tick>`.
