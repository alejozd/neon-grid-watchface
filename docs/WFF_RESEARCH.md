# Watch Face Format (WFF) — verbatim research report
Target: Samsung Galaxy Watch 6, round 480x480, Wear OS 4 / API 33 (v1) — v2 only if the device has been updated to Wear OS 5 / API 34.

All facts below are quoted or derived directly from the fetched pages listed at the bottom. Where the docs say nothing, it is marked **docs silent**.

---

## 0. CRITICAL VERSION CONSTRAINT (read first)

From <https://developer.android.com/training/wearables/wff>:

| WFF version | Minimum Wear OS version | Minimum API level |
|---|---|---|
| 1 | 4 | 33 |
| 2 | 5 | 34 |
| 3 | 5.1 | 35 |
| 4 | 6 | 36 |

> "WFF version 2 introduced Weather support as a data source, which is not available in WFF version 1."

**A Wear OS 4 (API 33) device can only run format version 1.** If the Galaxy Watch 6 is still on Wear OS 4, `android:value="2"` cannot be used and none of the v2 features exist. Use version **1** unless you know the watch is on Wear OS 5+. Version 2 adds: Flavors, GOAL_PROGRESS + WEIGHTED_ELEMENTS complication types, all `WEATHER.*` data sources, `SECOND_TENS_DIGIT`/`HOUR_TENS_DIGIT`-style digit sources, `icuText(,)`, `icuBestText(,)`, `FIRST_DAY_OF_WEEK`.

From <https://developer.android.com/training/wearables/wff/release-notes>: v3 adds auto-sizing text, blend mode, line weighted constraints, time-zone data sources. v4 adds user-selected photos, ambient transitions, color transforms, `Reference`. v5 adds blendMode on Group/ComplicationSlot, line spacing, `minSize`, `join`, nested settings.

---

## 1. Root element

Reference: <https://developer.android.com/reference/wear-os/wff/watch-face>

```xml
<WatchFace width="positive-integer" height="positive-integer"
           clipShape="NONE | CIRCLE | RECTANGLE" cornerRadiusX="float"
           cornerRadiusY="float">
  <!-- Only the required inner element is shown here. -->
  <Scene>
  </Scene>
</WatchFace>
```

> "The root element of every `watchface.xml` file."

Required attributes: `width`, `height`
> "Width of the visual screen on which watch face components are drawn, in pixels. ... Note that the visual screen might be a different size than the display resolution of a physical Wear OS device."

From setup: "The `height` and `width` define the extent of the coordinate space for use in your watch face, and the watch face is scaled to fit the device it is being used on; `height` and `width` don't represent actual pixels."

Optional: `clipShape` ("The default value is `CIRCLE`."), `cornerRadiusX`, `cornerRadiusY` (only with `clipShape="RECTANGLE"`).

Inner elements:
- `Scene` — required ("The `WatchFace` element must contain at least one `Scene` inner element."). The `Scene` reference states: "Each watch face must contain exactly one `Scene` element."
- `BitmapFonts`, `Metadata`, `UserConfigurations` — optional.

**Namespaces / xsi:** The reference syntax block declares **no** namespace. Both real Google samples are literally:
```xml
<?xml version="1.0"?>
<WatchFace width="450" height="450">
```
No `xmlns`, no `xmlns:xsi`, no `xsi:schemaLocation`. **docs silent** on `xsi`; the samples prove none is needed. (The *manifest* needs `xmlns:android`, see §8.)

### Metadata (preview)
Reference: <https://developer.android.com/reference/wear-os/wff/metadata>

```xml
<Metadata key="string" value="string" />
```
Predefined keys:
- `PREVIEW_TIME` — "Sets the time that appears in the watch face preview. The value must be in HH:MM:SS format; for example, `22:10:00` represents 10:10 PM." Default: system time if invalid/unspecified.
- `CLOCK_TYPE` — "Specifies the primary watch face type, either `DIGITAL` or `ANALOG`. Even if your watch face supports both types, you must specify a primary type to appear in the watch face preview." Default: `ANALOG`.
- `STEP_GOAL` — "Sets the daily 'number of steps' goal that appears in the watch face preview. This value must be a positive integer."

Both samples do include them:
```xml
<Metadata key="CLOCK_TYPE" value="ANALOG" />
<Metadata key="PREVIEW_TIME" value="10:08:32" />
```
Not formally *required* (only the preview defaults change), but include them.

---

## 2. Scene

Reference: <https://developer.android.com/reference/wear-os/wff/scene>

```xml
<Scene backgroundColor="argb-color">
    <Group ... />
</Scene>
```
- `backgroundColor`: "If this attribute is undefined or set to an invalid value, the system uses the default value of `#ff000000` (opaque black)." Transformable from v4.
- "The `Scene` element must contain at least one of the following inner elements: `Group`, `Condition`, `ListConfiguration`, `BooleanConfiguration`, `Variant`, `ComplicationSlot`, `AnalogClock`, `DigitalClock`, `Transform`, `Reference`."

Drawing order (from setup): "Elements that appear closer to the end of the scene appear on top of other elements".

---

## 3. Group, Transform, Variant

### Group
Reference: <https://developer.android.com/reference/wear-os/wff/group/group>

```xml
<Group id="string" x="integer" y="integer" width="integer" height="integer"
          name="string" angle="float" pivotX="float" pivotY="float"
          alpha="integer" renderMode="SOURCE | MASK | ALL"
          tintColor="argb-color | rgb-color">
    <PartText ... />
</Group>
```
Required attributes: **`name`** ("The name of the group.") plus `x`, `y`, `width`, `height`. `name` being required is easy to miss.
Optional: `id`, `pivotX`, `pivotY`, `angle`, `alpha`, `scaleX`, `scaleY`, `renderMode` (`SOURCE` default | `MASK` | `ALL`), `tintColor`, `blendMode` (v5).
Allowed children: `Localization`, `Gyro`, `Launch`, `Transform`, `Variant`, `Group`, `PartText`, `PartImage`, `PartAnimatedImage`, `PartDraw`, `ScreenReader`, `Condition`, `ListConfiguration`, `BooleanConfiguration`, `AnalogClock`, `DigitalClock`, `Reference`.

### Transform
Reference: <https://developer.android.com/reference/wear-os/wff/common/transform/transform>

```xml
<Transform target="string" value="arithmetic-expression"
           mode="TO | BY">
    <Animation ... >
</Transform>
```
- `target` (required): "The name of the element to transform. This must be a transformable attribute." — i.e. an **attribute name** such as `angle`, `x`, `alpha`, `endAngle`; not an element id.
- `value` (required): "An arithmetic expression that evaluates to a distance or new position."
- `mode` (optional): "it specifies whether you want to transform an element `BY` a specific number of units or `TO` a specific position. The default value is `TO`."

### Variant
Reference: <https://developer.android.com/reference/wear-os/wff/common/variant/variant>

```xml
<Variant mode="AMBIENT" target="attribute-name" value="valid-value" />
```
- `mode` (required): "As of Wear OS 4, this value must be `AMBIENT`."
- `target` (required): "This must be a transformable attribute."
- `value` (required).
- Optional v4+: `duration` (0.0–1.0), `startOffset`, `interpolation` (`LINEAR` default, `EASE_IN`, `EASE_OUT`, `EASE_IN_OUT`, `OVERSHOOT`, `CUBIC_BEZIER`), `controls`, `angleDirection` (`NONE`/`CLOCKWISE`/`COUNTER_CLOCKWISE`).

Usage in the samples (how you do ambient dimming):
```xml
<Group x="100" y="100" width="250" height="250" name="background" alpha="127">
  <Variant mode="AMBIENT" target="alpha" value="0" />
```
and the ambient second-hand trick:
```xml
<SecondHand resource="second" ... >
  <Variant mode="AMBIENT" target="alpha" value="0" />
  <Sweep frequency="15" />
</SecondHand>
```

---

## 4. PartDraw, PartText, PartImage

### PartDraw
Reference: <https://developer.android.com/reference/wear-os/wff/group/part/draw/part-draw>

```xml
<PartDraw x="integer" y="integer" width="integer" height="integer"
          name="string" angle="float-degrees" pivotX="float" pivotY="float"
          alpha="integer" renderMode="SOURCE | MASK | ALL"
          tintColor="argb-color | rgb-color" blendMode="string">
    <Line />
</PartDraw>
```
Required: `x`, `y`, `width`, `height`. Optional: `pivotX`, `pivotY`, `angle`, `alpha`, `name`, `scaleX`, `scaleY`, `renderMode`, `tintColor` (transformable from v4), `blendMode`.
Children: `Localization`, `Gyro`, `Launch`, `Transform`, `Variant`, `ScreenReader`, `Line`, `Arc`, `Rectangle`, `Ellipse`, `RoundRectangle`, `Reference`.

Real shapes from the samples:
```xml
<PartDraw x="0" y="0" width="250" height="250">
  <Ellipse x="0" y="0" width="250" height="250">
    <Fill color="[CONFIGURATION.themeColor.3]" />
  </Ellipse>
  <Ellipse x="50" y="50" width="150" height="150">
    <Fill color="#000000" />
  </Ellipse>
</PartDraw>
```
Arc/Stroke/Transform (from complications sample and memory doc):
```xml
<PartDraw x="10" y="10" width="93" height="93">
  <Arc centerX="46.5" centerY="46.5" width="93" height="93" startAngle="-150" endAngle="150">
    <Stroke thickness="10" color="[CONFIGURATION.themeColor.2]" cap="ROUND"/>
  </Arc>
</PartDraw>
```
```xml
<PartDraw angle="0" width="400" height="400" name="ProgressBar"
    pivotX="0.5" pivotY="0.5" x="25" y="25">
  <Arc centerX="200" centerY="200" width="400" height="400"
      startAngle="0" endAngle="360">
    <!-- Completes a "progress loop" every minute. -->
    <Transform target="endAngle"
        value="0 + (clamp([SECOND], 0, 60) - 0) * 6" />
    <Stroke cap="ROUND" color="#654456" thickness="10" />
  </Arc>
</PartDraw>
```

### PartText
Reference: <https://developer.android.com/reference/wear-os/wff/group/part/text/part-text>

```xml
<PartText x="integer" y="integer" width="integer" height="integer"
           pivotX="float" pivotY="float" angle="float-degrees" alpha="integer"
           name="string" scaleX="float" scaleY="float"
           renderMode="[SOURCE | MASK | ALL]"
           blendMode="string"
           tintColor="argb-color | rgb-color">
    <Text>
        <Font family="font" size="20" color="#00FFFF">Hello world
        </Font>
    </Text>
</PartText>
```
Required: `x`, `y`, `width`, `height`. "All elements are optional, except that either `Text` or `TextCircular` must be one of the inner elements."
Children: `Text`, `TextCircular`, `Localization`, `Transform`, `Variant`, `Gyro`, `Launch`, `ScreenReader`, `Reference`.

### PartImage / Image
Reference: <https://developer.android.com/reference/wear-os/wff/group/part/image/part-image> and <https://developer.android.com/reference/wear-os/wff/group/part/image/image>

```xml
<PartImage x="integer" y="integer" width="integer" height="integer"
           pivotX="float" pivotY="float" angle="float-degrees" alpha="integer"
           name="string" scaleX="float" scaleY="float"
           renderMode="[SOURCE | MASK | ALL]"
           blendMode="string"
           tintColor="argb-color | rgb-color">
    <Image resource="string" />
</PartImage>
```
PartImage "must contain a single `Image`, `Images` or `Photos` element." Optional `ImageFilters`.
Image has exactly one attribute, `resource`, required. Verbatim warning:
> "You shouldn't include `drawable/` or `@drawable/` or the file suffix in the `resource` attribute value."

i.e. `res/drawable/dial.png` → `<Image resource="dial"/>`.

`Images` (hourly rotation):
```xml
<PartImage x="150" y="150" width="150" height="150">
    <Images change="ON_NEXT_HOUR">
        <Image resource="red"/>
        <Image resource="orange"/>
        <Image resource="green"/>
    </Images>
</PartImage>
```

---

## 5. Analog hands — EXACT documented structure

This is the important correction: **hands are NOT rotated by `Transform` and there is no `[HOUR_0_11]`-driven angle recipe. `AnalogClock` rotates `HourHand`/`MinuteHand`/`SecondHand` automatically.**

Reference: <https://developer.android.com/reference/wear-os/wff/clock/analog-clock>

```xml
<AnalogClock x="integer" y="integer" width="integer" height="integer"
             pivotX="float" pivotY="float" angle="float-degrees" alpha="integer"
             scaleX="float" scaleY="float"
             renderMode="[SOURCE | MASK | ALL]"
             tintColor="argb-color | rgb-color">
    <!-- This is the maximum number of hands that you can define. -->
    <HourHand ... />
    <HourHand ... />
    <MinuteHand ... />
    <MinuteHand ... />
    <SecondHand ... />
    <SecondHand ... />
</AnalogClock>
```
> "An analog clock is a container for `AnalogHands` inner elements, which display a series of clock hands that rotate around a watch face."
> "`AnalogClock` can contain at most 2 hour hands, 2 minute hands, and 2 second hands."

HourHand (<https://developer.android.com/reference/wear-os/wff/clock/hour-hand>):
```xml
<HourHand resource="string" x="integer" y="integer" width="integer"
             height="integer" pivotX="float" pivotY="float" alpha="integer"
             tintColor="argb-color | rgb-color" />
```
> "An hour hand is a clock hand that rotates around a watch face once every 12 hours."
Required: `resource` ("A resource ID corresponding to the name of a drawable in the res directory."), `x`, `y`, `width`, `height`. Optional: `pivotX`, `pivotY`, `alpha`, `tintColor`.

MinuteHand — identical attributes ("rotates around a watch face once every minute" is SecondHand; MinuteHand reference at `/clock/minute-hand`).
SecondHand adds `<Sweep>` or `<Tick>`:
> "`Sweep`: Causes the element to move around the watch face in a continuous motion." / "`Tick`: Causes the element to move around the watch face in short, discrete bursts."

Canonical snippet from the time guide (<https://developer.android.com/training/wearables/wff/time>):
```xml
<AnalogClock x="0" y="0" width="450" height="450">
    <HourHand resource="hour" x="220" y="55" width="20" height="190"
        pivotX="0.5" pivotY="0.9210" />
    <MinuteHand resource="minute" x="222" y="30" width="16" height="220"
        pivotX="0.5" pivotY="0.9" />
    <SecondHand resource="second" x="226" y="20" width="8" height="245"
        pivotX="0.5" pivotY="0.8571" />
</AnalogClock>
```
Pivot rule (verbatim): "`<HourHand ... pivotY="(pivot_ratio)" />` where: pivot_ratio = pivot_height / full_height" — "In some situations, the pivot point is not quite at the bottom of the hand, and is centered horizontally."

Tinting: "use the `tintColor` on each of the hands to separately tint each hand, or on `AnalogClock`, to tint all hands the same color." e.g. `tintColor="[CONFIGURATION.handColors.0]"`.

Drop shadow: "use two of each hand type within a single `AnalogClock`, offsetting one behind the other, and use a separate resource for the hand that represents the shadow." (Both samples do this.)

**Angle tokens:** there is **no** `ANALOG_SECONDS_ANGLE`, `SECOND_ANGLE`, `HOUR_ANGLE` or similar in the complete v1–v3 data-source table. **docs silent** on any hand-angle data source. If you want a `PartDraw`-based hand you must build the angle yourself with `Transform target="angle"` and arithmetic, e.g. `[SECOND] * 6` (the documented pattern used for arcs). No documented formula for hour/minute hand angles exists — **docs silent**.

---

## 6. DigitalClock / TimeText

Reference: <https://developer.android.com/reference/wear-os/wff/clock/digital-clock>

```xml
<DigitalClock x="integer" y="integer" width="integer" height="integer"
             pivotX="float" pivotY="float" angle="float-degrees" alpha="integer"
             scaleX="float" scaleY="float"
             renderMode="[SOURCE | MASK | ALL]"
             tintColor="argb-color | rgb-color">
    <!-- This is the only required inner element. -->
    <TimeText ... />
</DigitalClock>
```

TimeText (<https://developer.android.com/reference/wear-os/wff/clock/time-text>):
```xml
<TimeText format="string" hourFormat="12 | 24 | SYNC_TO_DEVICE"
             align="START | CENTER | END" x="integer" y="integer"
             width="integer" height="integer" pivotX="float" pivotY="float"
             angle="float-degrees" alpha="integer"
             tintColor="argb-color | rgb-color" />
```
`format` is **required**. Verbatim list ("for showing the time 12:34:56 PM"):
- `hh:mm:ss` renders as "12:34:56".
- `h:mm` renders as "12:34"
- `hh_10` renders as "1".
- `hh_1` renders as "2".
- `m` renders as "34"
- `mm_10` renders as "3".
- `mm_1` renders as "4".
- `ss` renders as "56"
- `ss_10` renders as "5".
- `ss_1` renders as "6".

Optional: `hourFormat` (defaults `SYNC_TO_DEVICE`), `align` (defaults `START`), `verticalAlign` (`TOP`/`BOTTOM`/`CENTER`/`CENTER_ON_BASELINE`), `pivotX/Y`, `angle`, `alpha`, `tintColor`.
Children: `Variant`, `BitmapFont`, `Font`.
"version 2 expands the options here" for `format` (per the time guide).

Working sample (SimpleDigital):
```xml
<DigitalClock x="0" y="0" width="450" height="450">
  <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER" x="0" y="175" width="450" height="100" alpha="255">
    <Variant mode="AMBIENT" target="alpha" value="0"/>
    <Font family="SYNC_TO_DEVICE" size="128" weight="NORMAL" slant="NORMAL" color="#ffffffff"/>
  </TimeText>
</DigitalClock>
```

---

## 7. Complications

### ComplicationSlot
Reference: <https://developer.android.com/reference/wear-os/wff/complication/complication-slot>

```xml
<ComplicationSlot x="integer" y="integer" width="integer"
             height="integer" pivotX="float" pivotY="float"
             angle="float-degrees" alpha="integer" slotId="integer"
             name="string" displayName="string" scaleX="float" scaleY="float"
             supportedTypes="SHORT_TEXT | LONG_TEXT | MONOCHROMATIC_IMAGE | SMALL_IMAGE | PHOTO_IMAGE | RANGED_VALUE | EMPTY"
             isCustomizable="boolean"
             tintColor="argb-color | rgb-color" />
```
Required: `x`, `y`, `width`, `height`, **`slotId`**, **`supportedTypes`**.
> "A watch face can have at most eight instances of `ComplicationSlot`, total."
> "Multiple complication types can be supported by separating them with a space (for example, `SHORT_TEXT RANGED_VALUE`)."

Optional: `pivotX`, `pivotY`, `angle`, `alpha`, `scaleX`, `scaleY`, `tintColor`, `displayName` ("A resource ID corresponding to a localized name for the complication slot, which is displayed in the watch face editor."), `isCustomizable` ("Defaults to `TRUE`."), `blendMode`.

Inner elements (important):
> "The `ComplicationSlot` element must contain exactly one Bounding Area element."
> "A `ComplicationSlot` element must contain at least a `Complication` element per supported Complication Type."
Plus optional `DefaultProviderPolicy`, `Variant`, `ScreenReader`.

Bounding areas (<https://developer.android.com/reference/wear-os/wff/complication/bounding>):
- `<BoundingBox x y width height outlinePadding="float"/>`
- `<BoundingRoundBox x y width height outlinePadding cornerRadius/>`
- `<BoundingOval x y width height outlinePadding/>`
- `<BoundingArc centerX centerY width height thickness startAngle endAngle isRoundEdge direction outlinePadding/>` — "An angle of 0 degrees corresponds to the 12 o'clock position on the watch."
"Any content outside of the bounding area is cropped."

### Complication child
Reference: <https://developer.android.com/reference/wear-os/wff/complication/complication>

```xml
<Complication type="SHORT_TEXT | LONG_TEXT | MONOCHROMATIC_IMAGE | SMALL_IMAGE | PHOTO_IMAGE | RANGED_VALUE | EMPTY">
      <Group>
      </Group>
</Complication>
```
(The `EMPTY` type is used with `supportedTypes`; the reference's syntax line lists it too. `GOAL_PROGRESS` and `WEIGHTED_ELEMENTS` are v2 types used in the samples.)
Inner elements: `Group`, `Condition`, `PartText`, `PartImage`, `PartAnimatedImage`, `PartDraw`.

Available `COMPLICATION.*` sources per type (verbatim highlights):
- `SHORT_TEXT`: `COMPLICATION.MONOCHROMATIC_IMAGE`, `COMPLICATION.MONOCHROMATIC_IMAGE_AMBIENT`, `COMPLICATION.TEXT`, `COMPLICATION.TITLE`
- `LONG_TEXT`: `COMPLICATION.MONOCHROMATIC_IMAGE`, `COMPLICATION.SMALL_IMAGE`, `COMPLICATION.TEXT`, `COMPLICATION.TITLE`
- `SMALL_IMAGE`: `COMPLICATION.SMALL_IMAGE`, `COMPLICATION.SMALL_IMAGE_AMBIENT`, `COMPLICATION.IMAGE_STYLE` (`PHOTO` = 1, `ICON` = 2)
- `RANGED_VALUE`: `COMPLICATION.RANGED_VALUE_MIN`, `_MAX`, `_VALUE`, `_COLORS`, `_COLORS_INTERPOLATE` + image/text/title
- `GOAL_PROGRESS` (v2): `COMPLICATION.GOAL_PROGRESS_VALUE`, `COMPLICATION.GOAL_PROGRESS_TARGET_VALUE`, `_COLORS`, `_COLORS_INTERPOLATE`
- `WEIGHTED_ELEMENTS` (v2): `COMPLICATION.WEIGHTED_ELEMENTS_COLORS`, `_WEIGHTS`, `_BACKGROUND_COLOR`
- `PHOTO_IMAGE`: `COMPLICATION.PHOTO_IMAGE`

Actual v1-safe slot from the Google Complications sample:
```xml
<ComplicationSlot x="169" y="45" width="113" height="113" slotId="1"
    displayName="top_complication_label"
    supportedTypes="RANGED_VALUE GOAL_PROGRESS WEIGHTED_ELEMENTS SHORT_TEXT SMALL_IMAGE MONOCHROMATIC_IMAGE EMPTY">
    <BoundingOval x="0" y="0" width="113" height="113" outlinePadding="2.0"/>
    <Complication type="SHORT_TEXT">
        <PartText x="23" y="40" width="68" height="34" tintColor="[CONFIGURATION.themeColor.1]">
            <Text ellipsis="TRUE">
                <Font family="SYNC_TO_DEVICE" size="20.0">
                    <Template><![CDATA[%s]]>
                        <Parameter expression="[COMPLICATION.TEXT]"/>
                    </Template>
                </Font>
            </Text>
        </PartText>
    </Complication>
    <Complication type="SMALL_IMAGE">
        <PartImage x="23" y="23" width="68" height="68">
            <Image resource="[COMPLICATION.SMALL_IMAGE]"/>
        </PartImage>
    </Complication>
</ComplicationSlot>
```

### DefaultProviderPolicy
Reference: <https://developer.android.com/reference/wear-os/wff/complication/default-provider-policy>

```xml
<DefaultProviderPolicy defaultSystemProvider="string" defaultSystemProviderType="string" />
```
Required: both. `defaultSystemProvider` values (verbatim list): `APP_SHORTCUT`, `DATE`, `DAY_OF_WEEK`, `FAVORITE_CONTACT`, `HEART_RATE`, `NEXT_EVENT`, `STEP_COUNT`, `SUNRISE_SUNSET`, `TIME_AND_DATE`, `UNREAD_NOTIFICATION_COUNT`, `WATCH_BATTERY`, `WORLD_CLOCK`, `DAY_AND_DATE`, `EMPTY`.
`defaultSystemProviderType` supported: `SHORT_TEXT`, `LONG_TEXT`, `MONOCHROMATIC_IMAGE`, `SMALL_IMAGE`, `PHOTO_IMAGE`, `RANGED_VALUE`, `EMPTY`.
Optional: `primaryProvider`, `primaryProviderType`, `secondaryProvider`, `secondaryProviderType`.
Note: "You must also set the default source for the `ComplicationSlot` unless you allow the `EMPTY` type, in which case setting a default is optional."

Sample:
```xml
<ComplicationSlot slotId="2" supportedTypes="SHORT_TEXT SMALL_IMAGE EMPTY"
    x="250" y="100" width="100" height="100">
    <DefaultProviderPolicy
        defaultSystemProvider="STEP_COUNT"
        defaultSystemProviderType="SHORT_TEXT" />
</ComplicationSlot>
```

**slotId in the companion editor:** **docs silent**. The reference only says "A unique numeric identifier for the slot." The editor-facing label is `displayName` ("displayed in the watch face editor"). There is no documented mapping of `slotId` to companion-app API in the fetched pages.

---

## 8. Data sources — full v1/v2 list (verbatim from the reference)

Source: <https://developer.android.com/reference/wear-os/wff/common/attributes/source-type>

### Time (all Version 1 unless noted)
| Token | Type | Meaning |
|---|---|---|
| `UTC_TIMESTAMP` | Integer | ms since midnight UTC 1970-01-01 |
| `MILLISECOND` | Integer | 0–999 |
| `SECOND` | Integer | 0–59 |
| `SECOND_Z` | String | `00`–`59` |
| `SECOND_TENS_DIGIT` / `SECOND_UNITS_DIGIT` | Integer | **Version 2** |
| `SECOND_MILLISECOND` | Float | 0.0–59.999 |
| `SECONDS_IN_DAY` | Integer | 0–86399 |
| `SECONDS_SINCE_EPOCH` | Integer | **Version 3** |
| `MINUTE` | Integer | 0–59 |
| `MINUTE_Z` | String | `00`–`59` |
| `MINUTE_TENS_DIGIT` / `MINUTE_UNITS_DIGIT` | Integer | **Version 2** |
| `MINUTE_SECOND` | Float | 0.0–59 59/60 |
| `MINUTES_SINCE_EPOCH` | Integer | **Version 3** |
| `HOUR_0_11` | Integer | 0–11 (12 → 0) |
| `HOUR_0_11_Z` | String | `00`–`11` |
| `HOUR_0_11_MINUTE` | Float | 0.0–11 59/60 |
| `HOUR_1_12` | Integer | 1–12 |
| `HOUR_1_12_Z` | String | `01`–`12` |
| `HOUR_1_12_MINUTE` | Float | 1.0–12 59/60 |
| `HOUR_0_23` | Integer | 0–23 |
| `HOUR_0_23_Z` | String | `00`–`23` |
| `HOUR_0_23_MINUTE` | Float | 0.0–23 59/60 |
| `HOUR_1_24` | Integer | 1–24 |
| `HOUR_1_24_Z` | String | `01`–`24` |
| `HOUR_1_24_MINUTE` | Float | 1.0–24 59/60 |
| `HOUR_TENS_DIGIT` / `HOUR_UNITS_DIGIT` | Integer | **Version 2** |
| `HOURS_SINCE_EPOCH` | Integer | **Version 3** |
| `AMPM_STATE` | Integer | `0` AM, `1` PM |
| `AMPM_POSITION` | Integer | `0` begin, `1` end, `-1` unknown |
| `AMPM_STRING` | String | `"AM"` / `"PM"` |
| `IS_24_HOUR_MODE` | Boolean | |
| `TIMEZONE`, `TIMEZONE_ABB`, `TIMEZONE_ID`, `TIMEZONE_OFFSET`, `TIMEZONE_OFFSET_DST` | String | v1 |
| `TIMEZONE_OFFSET_MINUTES`, `TIMEZONE_OFFSET_MINUTES_DST` | Integer | **Version 3** |
| `IS_DAYLIGHT_SAVING_TIME` | Boolean | v1 |

### Date / calendar (all Version 1)
`DAY` (1–31), `DAY_Z`, `DAY_HOUR`, `DAY_0_30`, `DAY_0_30_HOUR`, `DAY_OF_YEAR` (1–366), `DAY_OF_WEEK` ("assigns a value of `1` to represent Sunday and a value of `7` to represent Saturday"), `DAY_OF_WEEK_F` (e.g. `Sunday`), `DAY_OF_WEEK_S` (e.g. `Sun`), `FIRST_DAY_OF_WEEK` (**Version 2**), `MONTH` (1–12), `MONTH_Z`, `MONTH_F`, `MONTH_S`, `DAYS_IN_MONTH`, `MONTH_DAY`, `MONTH_0_11`, `MONTH_0_11_DAY`, `YEAR` (clamped 1902–2100), `YEAR_S`, `YEAR_MONTH`, `YEAR_MONTH_DAY`, `WEEK_IN_MONTH`, `WEEK_IN_YEAR`.
Moon: `MOON_PHASE_POSITION`, `MOON_PHASE_TYPE`, `MOON_PHASE_TYPE_STRING`.
Locale: `LANGUAGE_LOCALE_NAME`.

### Health / steps
- `STEP_COUNT` — "The number of steps that the user has taken so far today" (Integer, v1)
- `STEP_GOAL` — "This value is never less than `1000`." (Integer, v1)
- `STEP_PERCENT` — "progress ... expressed as a rounded percentage. This value is always between `0` and `100`" (Integer, v1)
- `HEART_RATE` — "Float or String, depending on the device"; "To always represent the heart rate as an integer, use the expression `round(HEART_RATE)`." (v1)
- `HEART_RATE_Z` — String, zero-padded to ≥2 chars (v1)
- `ACCELEROMETER_IS_SUPPORTED`, `ACCELEROMETER_X/Y/Z`, `ACCELEROMETER_ANGLE_X/Y/Z/XY` (v1)

### Battery / device
- `BATTERY_PERCENT` (Integer, 0–100, v1)
- `BATTERY_CHARGING_STATUS` (Boolean, v1)
- `BATTERY_IS_LOW` (Boolean, v1) — "The exact threshold for this is manufacturer dependent. If the battery is charging, this value is `false`."
- `BATTERY_TEMPERATURE_CELSIUS`, `BATTERY_TEMPERATURE_FAHRENHEIT` (Float, v1)

### Notifications
- `UNREAD_NOTIFICATION_COUNT` (v1). **There is no `NOTIFICATION_COUNT` token.** The docs table labels its type "String" but describes it as "a string that represents the number of notifications" — verbatim inconsistency in the docs; treat as numeric-ish. **docs silent** on the discrepancy.

### Weather — ALL Version 2 (unavailable on a Wear OS 4 / API 33 device)
`WEATHER.IS_AVAILABLE`, `WEATHER.IS_ERROR`, `WEATHER.CONDITION` (enum 0–15: `UNKNOWN_VALUE`, `CLEAR`, `CLOUDY`, `FOG`, `HEAVY_RAIN`, `HEAVY_SNOW`, `RAIN`, `SNOW`, `SUNNY`, `THUNDERSTORM`, `SLEET`, `LIGHT_SNOW`, `LIGHT_RAIN`, `MIST`, `PARTLY_CLOUDY`, `WINDY`), `WEATHER.CONDITION_NAME`, `WEATHER.IS_DAY`, **`WEATHER.TEMPERATURE`** ("The current temperature, in the user's preferred unit."), `WEATHER.TEMPERATURE_UNIT` (`1` CELSIUS / `2` FAHRENHEIT), `WEATHER.DAY_TEMPERATURE_LOW`, `WEATHER.DAY_TEMPERATURE_HIGH`, `WEATHER.CHANCE_OF_PRECIPITATION` (0–100), `WEATHER.UV_INDEX`, `WEATHER.LAST_UPDATED`, plus `WEATHER.HOURS.{index}.*` and `WEATHER.DAYS.{index}.*`.
**There is no bare `TEMPERATURE` token.** Only `WEATHER.TEMPERATURE`.

---

## 9. Text formatting

### Zero-padding
The documented zero-pad mechanism is the `_Z` suffix on the data source itself: `HOUR_0_23_Z`, `HOUR_1_12_Z`, `HOUR_0_11_Z`, `MINUTE_Z`, `SECOND_Z`, `DAY_Z`, `MONTH_Z`, `HEART_RATE_Z`.
**`[HOUR_0_23_Z2]` does not exist — docs silent on any `Z2` suffix.** For arbitrary widths use `numberFormat("#00", [HOUR_0_23])`. Do not invent a `Z<n>` form.

### Template / Parameter
Reference: <https://developer.android.com/reference/wear-os/wff/group/part/text/formatter/template>

```xml
<Template>template-string
    <Parameter expression="arithmetic-expression" />
</Template>
```
> "Allows watch face developers to specify a string format, such as `%s %d`. The string format is very similar to `printf()` ... or `String.format()`"
> "The `Template` element must contain at least one `Parameter` inner element."
> "The expressions in the different `Parameter` inner elements are evaluated left-to-right in the `Template` element's format string."

Verbatim example:
```xml
<Template>%s %d
    <Parameter expression="Current heart rate: " />
    <Parameter expression="[HEART_RATE]" />
</Template>
```
String-resource form (verbatim): `<Template>%s<Parameter expression="greeting"></Parameter></Template>` with `<string name="greeting">Hello, world!</string>`; and
```xml
<Template>day_of_week
    <Parameter expression="[DAY_OF_WEEK_S]" />
</Template>
```
with `<string name="day_of_week">Day: %1$s</string>`.

**There is no `concat()` and no `format()` function.** **docs silent** on both — string building is done via `Template`/`Parameter` and string resources.

### Functions (Version 1 unless noted)
`round()`, `floor()`, `ceil()`, `fract()`, `sin()`, `cos()`, `tan()`, `asin()`, `acos()`, `atan()`, `abs()`, `clamp(,,)`, `rand(,)`, `log()`, `log2()`, `log10()`, `sqrt()`, `cbrt()`, `exp()`, `expm1()`, `deg()`, `rad()`, `pow(,)`, `numberFormat(,)`, `icuText()`, `icuBestText()`, `subText(,,)`, `textLength()`.
Version 2: `icuText(,)`, `icuBestText(,)`. Version 4: `colorRgb(,,)`, `colorArgb(,,)`, `extractColorFromColors(,,)`, `extractColorFromWeightedColors(,,)`.
Operators: `+ - * / % ~ ! | || & && ( ) < <= > >= ? : , " == !=` and ternary `condition ? value_if_true : value_if_false`.

XML escaping (verbatim): "In `Expression` elements, use `CNAME` [sic — CDATA] to avoid the need for special handling"; "In attributes, use character references ... `&amp;`, `&gt;`, `&lt;`, `'` and `&quot;`".
```xml
<Transform target="alpha" value="[STEP_COUNT] &gt; 5000 ? 255 : 0" />
```
```xml
<Expression name="my-expression">
    <![CDATA[[STEP_COUNT] > 5000]]
</Expression>
```

Performance rule (verbatim): "it is important to always use data sources that re-evaluate as infrequently as possible." Prefer `[AMPM_STATE] == 1` over `[SECONDS_IN_DAY] > 43200`.

### Text / Font
```xml
<Font family="string | SYNC_TO_DEVICE" size="float"
      color="argb-color | rgb-color" slant="NORMAL | ITALIC"
      letterSpacing="em-value"
      width="ULTRA_CONDENSED | ... | ULTRA_EXPANDED"
      weight="THIN | ULTRA_LIGHT | EXTRA_LIGHT | LIGHT | NORMAL | MEDIUM |
              BOLD | SEMI_BOLD | ULTRA_BOLD | EXTRA_BOLD | BLACK | EXTRA_BLACK">
```
`family` and `size` are required. Fonts: "place the font file in `res/font/`, using one of the following accepted font file extensions: TTF, OTF, TTC, or XML. Then, set this value to the name of the font file, excluding the extension". Decorations: `Shadow`, `Outline`, `OutGlow`, `Underline`, `StrikeThrough`, `InlineImage`, `Template`, `Upper`, `Lower`, `Transform`, `Reference`.
Spacing advice (verbatim): "wrap your `Font` contents in a `CDATA` element".

---

## 10. Drawable formats for hands/images

- Hands: `resource` — "A resource ID corresponding to the name of a drawable in the res directory." Referenced **without** extension or `@drawable/`.
- Google's samples use **PNG** only: `watchface/src/main/res/drawable/hour.png`, `minute.png`, `second.png`, `preview.png`.
- **docs silent** on whether WebP or a vector `res/drawable/*.xml` drawable is accepted for `Image`/hand `resource`. Nothing in the WFF pages I fetched states a supported raster/vector list. (The memory doc discusses images vs "vector fonts" and RGBA8888/RGB565/ALPHA_8 compression but never enumerates file formats.)
- Recommendation for a hand-written face: use PNG (documented by example) and keep them tightly cropped — ambient budget is 10 MB, interactive 100 MB.

---

## 11. Packaging: manifest, watch_face_info.xml, watch_face_shapes.xml

### Minimal working AndroidManifest.xml (verbatim from `WatchFaceFormat/SimpleAnalog`)
```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
  xmlns:tools="http://schemas.android.com/tools">

  <uses-feature android:name="android.hardware.type.watch" />

  <!-- Note: hasCode is required to be false for Watch Face Format -->
  <application
      android:label="@string/watch_face_name"
      android:hasCode="false">

    <meta-data
        android:name="com.google.android.wearable.standalone"
        android:value="true" />
    <property
        android:name="com.google.wear.watchface.format.version"
        android:value="1" />
  </application>
</manifest>
```
- The `<property>` sits **inside `<application>`**, as a direct child, after `<meta-data>`.
- `android:hasCode="false"` is mandatory: "The `<application>` element must also include the attribute `android:hasCode="false"`. Watch Face Format bundles are resource-only and cannot contain any code."
- `android:label` on `<application>`: "In your app's manifest file (`AndroidManifest.xml`), set the `android:label` attribute on the `application` element to the name of your watch face."
- **No `<service>`, no `<activity>`, no `<intent-filter>` at all.** Both Google samples contain zero components. A resource-only WFF APK needs **no** service element — confirmed by the samples and by the setup guide, which never mentions one.
- Optional publisher property:
```xml
<property
    android:name="com.google.wear.watchface.format.publisher"
    android:value="{toolName}-{toolVersion}" />
```

### Gradle (from `SimpleAnalog/watchface/build.gradle.kts`)
```kotlin
android {
    enableKotlin = false
    namespace = "com.example.simpleanalog"
    compileSdk = 33
    defaultConfig {
        applicationId = "com.example.simpleanalog"
        minSdk = 33
        targetSdk = 33
        versionCode = 1
        versionName = "1.0.0"
    }
    buildTypes {
        release {
            isMinifyEnabled = true
            // Ensure shrink resources is false, to avoid potential for them
            // being removed.
            isShrinkResources = false
        }
    }
}
```
`minSdk = 33` for v1. Setup guide: "Set this property to the lowest value that supports the features you need, to maximize device compatibility, and also set the `minSdkVersion` to match."

### res/xml/watch_face_info.xml (verbatim sample)
```xml
<WatchFaceInfo>
  <!--
    Preview is the only required element here.
    -->
  <Preview value="@drawable/preview" />
  <Editable value="true" />
</WatchFaceInfo>
```
Full documented field set:
```xml
<WatchFaceInfo>
    <Preview value="@drawable/preview" />
    <Category value="CATEGORY_EMPTY" />
    <AvailableInRetail value="true" />
    <MultipleInstancesAllowed value="true" />
    <Editable value="true" />
    <FlavorsSupported value="true" />
</WatchFaceInfo>
```
Defaults per setup: `Category` → `empty_category_meta`; `AvailableInRetail` → `false`; `MultipleInstancesAllowed` → `false`; `Editable` → `false`.
`Editable`: "Whether the watch face is *editable*, which means that the watch face has a setting or at least one non-fixed complication."

**How watch_face_info.xml is discovered:** the manifest contains **no** reference to it in either sample. Discovery is by the fixed resource path `res/xml/watch_face_info.xml`. **docs silent** on the mechanism (no meta-data key or property is documented for it).

### res/xml/watch_face_shapes.xml (optional)
```xml
<WatchFaces>
    <WatchFace shape="CIRCLE" width="300" height="300"
        file="@raw/watchface_basic"/>
    <WatchFace shape="CIRCLE" width="450" height="450"
        file="@raw/watchface"/>
</WatchFaces>
```
"If you did not define a shapes file, then you only need one file, `watchface.xml`."
For a single 480x480 round face, skip `watch_face_shapes.xml` and put `res/raw/watchface.xml` with `width="450" height="450"` (or 480) — it is scaled to the device.

### Rejection / validation constraints documented
- WFF XML must be at `res/raw/watchface.xml`.
- `android:hasCode="false"`, resource-only, "cannot contain any code".
- Format-version property must match the features used; a v2 feature under `value="1"` (or on an API 33 device) is invalid.
- Memory: "Ambient mode: 10 MB maximum memory use. Interactive mode: 100 MB maximum memory use."
- Google Play: "the Android App Bundle that includes the custom watch face file must be completely separate from the Android App Bundle that contains your Wear OS app's logic. Some app stores, including Google Play, prevent you from uploading an Android App Bundle that includes both Wear OS logic and a custom watch face."
- Validators: <https://github.com/google/watchface> (XML validator + memory footprint tool).
- Debugging: `adb logcat --pid=$(adb shell pidof -s com.google.wear.watchface.runtime)`.

---

## 12. Minimal correct v1 skeleton for 480x480 round, with analog hands + 2 complication slots

```xml
<?xml version="1.0" encoding="UTF-8"?>
<WatchFace width="480" height="480">
  <Metadata key="CLOCK_TYPE" value="ANALOG" />
  <Metadata key="PREVIEW_TIME" value="10:08:32" />

  <Scene backgroundColor="#ff000000">

    <!-- background dial (PNG in res/drawable, no extension here) -->
    <PartImage x="0" y="0" width="480" height="480">
      <Image resource="dial" />
    </PartImage>

    <!-- digital readout -->
    <DigitalClock x="0" y="330" width="480" height="60">
      <TimeText format="hh:mm" hourFormat="SYNC_TO_DEVICE" align="CENTER"
                x="0" y="0" width="480" height="60">
        <Font family="SYNC_TO_DEVICE" size="34" color="#ffffffff" />
      </TimeText>
    </DigitalClock>

    <!-- complication: steps -->
    <ComplicationSlot x="60" y="150" width="80" height="80" slotId="1"
        supportedTypes="SHORT_TEXT RANGED_VALUE EMPTY">
      <BoundingOval x="0" y="0" width="80" height="80" outlinePadding="2.0" />
      <DefaultProviderPolicy defaultSystemProvider="STEP_COUNT"
                             defaultSystemProviderType="SHORT_TEXT" />
      <Complication type="SHORT_TEXT">
        <PartText x="4" y="26" width="72" height="28">
          <Text align="CENTER" ellipsis="TRUE">
            <Font family="SYNC_TO_DEVICE" size="20" color="#ffffffff">
              <Template><![CDATA[%s]]>
                <Parameter expression="[COMPLICATION.TEXT]" />
              </Template>
            </Font>
          </Text>
        </PartText>
      </Complication>
    </ComplicationSlot>

    <!-- complication: battery -->
    <ComplicationSlot x="340" y="150" width="80" height="80" slotId="2"
        supportedTypes="SHORT_TEXT RANGED_VALUE EMPTY">
      <BoundingOval x="0" y="0" width="80" height="80" outlinePadding="2.0" />
      <DefaultProviderPolicy defaultSystemProvider="WATCH_BATTERY"
                             defaultSystemProviderType="SHORT_TEXT" />
      <Complication type="SHORT_TEXT">
        <PartText x="4" y="26" width="72" height="28">
          <Text align="CENTER" ellipsis="TRUE">
            <Font family="SYNC_TO_DEVICE" size="20" color="#ffffffff">
              <Template><![CDATA[%s]]>
                <Parameter expression="[COMPLICATION.TEXT]" />
              </Template>
            </Font>
          </Text>
        </PartText>
      </Complication>
    </ComplicationSlot>

    <!-- hands: AnalogClock rotates them automatically -->
    <AnalogClock x="0" y="0" width="480" height="480" tintColor="#ffffffff">
      <Variant mode="AMBIENT" target="alpha" value="192" />
      <HourHand   resource="hour"   x="228" y="120" width="24" height="150" pivotX="0.5" pivotY="0.9" />
      <MinuteHand resource="minute" x="230" y="90"  width="20" height="180" pivotX="0.5" pivotY="0.9" />
      <SecondHand resource="second" x="233" y="80"  width="14" height="200" pivotX="0.5" pivotY="0.9">
        <Variant mode="AMBIENT" target="alpha" value="0" />
        <Sweep frequency="15" />
      </SecondHand>
    </AnalogClock>
  </Scene>
</WatchFace>
```

---

## 13. Doc URLs used

- <https://developer.android.com/training/wearables/wff> (version table)
- <https://developer.android.com/training/wearables/wff/setup>
- <https://developer.android.com/training/wearables/wff/time>
- <https://developer.android.com/training/wearables/wff/text>
- <https://developer.android.com/training/wearables/wff/images>
- <https://developer.android.com/training/wearables/wff/expressions>
- <https://developer.android.com/training/wearables/wff/complications>
- <https://developer.android.com/training/wearables/wff/release-notes>
- <https://developer.android.com/training/wearables/wff/memory-usage>
- <https://developer.android.com/reference/wear-os/wff/watch-face>
- <https://developer.android.com/reference/wear-os/wff/scene>
- <https://developer.android.com/reference/wear-os/wff/metadata>
- <https://developer.android.com/reference/wear-os/wff/group/group>
- <https://developer.android.com/reference/wear-os/wff/group/part/draw/part-draw>
- <https://developer.android.com/reference/wear-os/wff/group/part/text/part-text>
- <https://developer.android.com/reference/wear-os/wff/group/part/image/part-image>
- <https://developer.android.com/reference/wear-os/wff/group/part/image/image>
- <https://developer.android.com/reference/wear-os/wff/group/part/text/font>
- <https://developer.android.com/reference/wear-os/wff/group/part/text/formatter/template>
- <https://developer.android.com/reference/wear-os/wff/clock/analog-clock>
- <https://developer.android.com/reference/wear-os/wff/clock/hour-hand>
- <https://developer.android.com/reference/wear-os/wff/clock/second-hand>
- <https://developer.android.com/reference/wear-os/wff/clock/digital-clock>
- <https://developer.android.com/reference/wear-os/wff/clock/time-text>
- <https://developer.android.com/reference/wear-os/wff/common/transform/transform>
- <https://developer.android.com/reference/wear-os/wff/common/variant/variant>
- <https://developer.android.com/reference/wear-os/wff/common/attributes/source-type>
- <https://developer.android.com/reference/wear-os/wff/common/attributes/arithmetic-expression>
- <https://developer.android.com/reference/wear-os/wff/complication/complication-slot>
- <https://developer.android.com/reference/wear-os/wff/complication/complication>
- <https://developer.android.com/reference/wear-os/wff/complication/bounding>
- <https://developer.android.com/reference/wear-os/wff/complication/default-provider-policy>
- <https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleAnalog/watchface/src/main/res/raw/watchface.xml>
- <https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleAnalog/watchface/src/main/AndroidManifest.xml>
- <https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleAnalog/watchface/src/main/res/xml/watch_face_info.xml>
- <https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleAnalog/watchface/build.gradle.kts>
- <https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/SimpleDigital/watchface/src/main/res/raw/watchface.xml>
- <https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/Complications/watchface/src/main/res/raw/watchface.xml>
- <https://raw.githubusercontent.com/android/wear-os-samples/main/WatchFaceFormat/Weather/watchface/src/main/AndroidManifest.xml>
