"""
Generates the Watch Face Format project (XML + manifest + resources) from the
design manifest produced by design/render.py.

Everything is derived from design/out/{layout,hands,hands_ambient,labels}.json,
so the face on the watch matches the mock pixel for pixel.

Usage:  python tools/gen_watchface.py [--format 1|2] [--no-events]
        --format 2  -> enables native weather data sources (needs Wear OS 5)
        --format 1  -> weather block is dropped (Wear OS 4 compatible)
"""
import argparse
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "design", "out")
WF = os.path.join(ROOT, "watchface")
RES = os.path.join(WF, "res")
DRAW = os.path.join(RES, "drawable-nodpi")

WHITE = "#FFFFFFFF"
CYAN = "#FF22E7FF"
MAGENTA = "#FFFF2A6D"
VIOLET = "#FFA24BFF"
DIM = "#FF8FB6C9"
TIME = "#FFFFFFFF"   # colour of the big time, overridden by the palette

FAMILY = "monospace"     # bundled system monospace
S = 480                  # design space

# letterSpacing only exists from Watch Face Format v2 onwards
LS_ENABLED = True


def ls_attr(v):
    return f' letterSpacing="{v}"' if LS_ENABLED else ''


def load(name):
    with open(os.path.join(OUT, name), encoding="utf-8") as fh:
        return json.load(fh)


LAYOUT = load("layout.json")["layout"]
HANDS = {}
HANDS_AMB = {}

# Horizontal anchoring. Verified on the Galaxy Watch 6 (Wear OS 6):
#   LEFT   -> the text starts at the box's left edge
#   CENTER -> the text is centred on the box's centre
#   RIGHT  -> the text ends at the box's right edge
# Narrow boxes place text unreliably, so every box spans a whole edge of the scene.
#   key: (alignment, anchor coordinate)
ALIGN = {
    "time":    ("RIGHT", 326),
    "ampm":    ("LEFT", 346),
    "sec":     ("LEFT", 350),
    "date":    ("CENTER", S / 2),
    "temp":    ("CENTER", S / 2),
    "cond":    ("CENTER", S / 2),
    "msg_v":   ("LEFT", 132),
    "evt_v":   ("RIGHT", 348),
    "bat_v":   ("LEFT", 52),
    "hr_v":    ("LEFT", 72),
    "steps_v": ("RIGHT", 404),
    "steps_pct": ("RIGHT", 404),
    "tminmax": ("CENTER", S / 2),
    "wl_lbl":  ("RIGHT", 232),
    "wclock":  ("LEFT", 240),
}

# World clock. `<Localization timezone="..."/>` does NOT work on this watch (the
# runtime ignores it: the part keeps the device zone, verified on device), and
# `[TIMEZONE_OFFSET_DST]` is NOT a valid data source for the runtime either
# (referencing it makes the watch face crash with a NullPointerException and the
# system falls back to the factory face).
# So the clock is shifted with `icuText(pattern, timestamp)`, which formats the
# given instant in the device's own zone, and the shift is
#     (Spain offset - device offset)  hours
# where Spain follows the EU rule (UTC+1, UTC+2 from the last Sunday of March to
# the last Sunday of October) and the device offset is the constant below.
WORLD_TZ = "Europe/Madrid"
WORLD_LABEL = "BCN"
# complication slot box (design px) where the world clock sits, and its slot id
# (7 is taken by the events slot)
WORLD_SLOT = (155, 386, 170, 34)
WORLD_SLOT_ID = 3
WORLD_WINTER = 1           # CET
WORLD_SUMMER = 2           # CEST
DEVICE_UTC_OFFSET = -5     # Bogota; override with --device-utc-offset


def world_clock_expression():
    """icuText("HH:mm", now + (Spain - device) hours), DST rule included.

    Only basic, well supported data sources are used: the weekday of the 31st is
    derived from today's weekday and day number, so the season is right on the
    device without rebuilding.
    """
    # the day of the month is [DAY] in Watch Face Format; [DAY_1_31] is the
    # editor's internal name and the runtime does NOT know it (it crashes)
    last_sunday = "32 - (([DAY_OF_WEEK] + 30 - [DAY]) % 7)"
    summer = ("([MONTH] > 3 && [MONTH] < 10)"
              " || ([MONTH] == 3 && [DAY] >= %s)"
              " || ([MONTH] == 10 && [DAY] < %s)" % (last_sunday, last_sunday))
    shift = "(%g + (%s ? 1 : 0))" % (WORLD_WINTER - DEVICE_UTC_OFFSET, summer)
    return 'icuText("HH:mm", [UTC_TIMESTAMP] + %s * 3600000)' % shift


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def esc_attr(s):
    """XML-escape a value that goes inside an attribute.

    Expressions live in `expression="..."`, so quotes (icuText("HH:mm", ...))
    and `&&` must be escaped; without this the XML is malformed and the runtime
    dies with a NullPointerException while resolving the "tag" it parsed.
    """
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;"))


def text_part(key, fmt, params, color, box_h=None, indent="    ", mode="active",
              y_override=None, size_override=None, localize=None):
    """A PartText placed according to ALIGN[key].

    `fmt` is a printf-style template whose `%s` slots are filled, in order, by
    `<Parameter expression="..."/>` data sources.  Data sources must NOT sit
    inside the CDATA text: the renderer would print them literally.
    `localize` is a time zone id: the part then reads the clock data sources in
    that zone (this is how WFS itself emits world clocks).

    mode="active"  -> visible while interacting, hidden in ambient
    mode="ambient" -> hidden while interacting, visible in ambient
    """
    L = LAYOUT[key]
    size = size_override or L["size"]
    align, anchor = ALIGN[key]
    # NOTE: coordinates MUST be integers. The Galaxy Watch 6 runtime silently
    # drops any PartText whose x/y/width/height carry a decimal point
    # (verified on device: x="0.0" renders nothing, x="0" renders fine).
    h = int(round(box_h if box_h else size * 1.45))
    if align == "CENTER":
        x, w = 0, S
    elif align == "LEFT":
        x, w = int(anchor), S - int(anchor)
    else:  # RIGHT
        x, w = 0, int(anchor)
    y = int(round((y_override if y_override is not None else L["y"]) - h / 2))
    ls = round(L.get("ls", 0) / size, 4) if size else 0
    param_xml = "".join(
        f'\n{indent}          <Parameter expression="{esc_attr(p)}"/>' for p in params)
    if mode == "ambient":
        attrs = ' alpha="0"'
        variant = f'{indent}  <Variant mode="AMBIENT" target="alpha" value="255"/>\n'
    else:
        attrs = ""
        variant = f'{indent}  <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
    tz = f'{indent}  <Localization timezone="{localize}"/>\n' if localize else ""
    return (
        f'{indent}<PartText x="{x}" y="{y}" width="{w}" height="{h}"{attrs}>\n'
        f'{tz}'
        f'{variant}'
        f'{indent}  <Text align="{align}">\n'
        f'{indent}    <Font family="{FAMILY}" size="{int(round(size))}" color="{color}"'
        f'{ls_attr(ls)} weight="BOLD">\n'
        f'{indent}      <Template><![CDATA[{fmt}]]>{param_xml}\n'
        f'{indent}      </Template>\n'
        f'{indent}    </Font>\n'
        f'{indent}  </Text>\n'
        f'{indent}</PartText>\n'
    )


def label_parts(labels_json):
    """Baked HUD labels, placed at their exact crop offsets (hidden in ambient)."""
    out = []
    for name, m in labels_json.items():
        out.append(
            f'    <PartImage x="{int(m["x"])}" y="{int(m["y"])}" width="{m["w"]}" height="{m["h"]}">\n'
            f'      <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
            f'      <Image resource="{name}"/>\n'
            f'    </PartImage>\n'
        )
    return "".join(out)


def hand(tag, m, resource):
    return (
        f'    <{tag} resource="{resource}" x="{int(m["x"])}" y="{int(m["y"])}" '
        f'width="{m["w"]}" height="{m["h"]}" pivotX="{m["pivotX"]}" pivotY="{m["pivotY"]}"/>\n'
    )


def events_slot(display=None):
    """Calendar / events complication slot, upper right.

    Shows two lines (title = usually the time of the event, text = the event
    name) so there is more information than a single chip. LONG_TEXT providers
    get their own two-line layout.
    """
    # raised: the violet line used to sit too low, so the box starts higher and
    # the two lines are packed together
    x, y, w, h = 262, 148, 156, 54
    return f'''    <ComplicationSlot x="{x}" y="{y}" width="{w}" height="{h}" slotId="7"
        displayName="@string/slot_events" supportedTypes="SHORT_TEXT LONG_TEXT EMPTY">
      <BoundingOval x="0" y="0" width="{w}" height="{h}"/>
      <Complication type="SHORT_TEXT">
        <PartText x="0" y="0" width="{w}" height="24">
          <Text align="CENTER" ellipsis="TRUE">
            <Font family="{FAMILY}" size="13" color="{DIM}" weight="BOLD">
              <Template><![CDATA[%s]]>
                <Parameter expression="[COMPLICATION.TITLE]"/>
              </Template>
            </Font>
          </Text>
        </PartText>
        <PartText x="0" y="22" width="{w}" height="30">
          <Text align="CENTER" ellipsis="TRUE">
            <Font family="{FAMILY}" size="17" color="{VIOLET}" weight="BOLD">
              <Template><![CDATA[%s]]>
                <Parameter expression="[COMPLICATION.TEXT]"/>
              </Template>
            </Font>
          </Text>
        </PartText>
      </Complication>
      <Complication type="LONG_TEXT">
        <PartText x="0" y="0" width="{w}" height="24">
          <Text align="CENTER" ellipsis="TRUE">
            <Font family="{FAMILY}" size="12" color="{DIM}" weight="BOLD">
              <Template><![CDATA[%s]]>
                <Parameter expression="[COMPLICATION.LONG_TITLE]"/>
              </Template>
            </Font>
          </Text>
        </PartText>
        <PartText x="0" y="22" width="{w}" height="30">
          <Text align="CENTER" ellipsis="TRUE">
            <Font family="{FAMILY}" size="15" color="{VIOLET}" weight="BOLD">
              <Template><![CDATA[%s]]>
                <Parameter expression="[COMPLICATION.LONG_TEXT]"/>
              </Template>
            </Font>
          </Text>
        </PartText>
      </Complication>
    </ComplicationSlot>
'''


def tap_target(index, x, y, w, h, target):
    """An (almost) invisible PartDraw that only exists to receive taps.

    The text parts use edge-to-edge boxes for alignment, so they cannot carry the
    <Launch> themselves without making a huge tap area. These small overlays fix
    that: they are drawn on top with an almost transparent fill.
    """
    return (
        '    <PartDraw x="%d" y="%d" width="%d" height="%d">\n'
        '      <Launch target="%s"/>\n'
        '      <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
        '      <Rectangle x="0" y="0" width="%d" height="%d">\n'
        '        <Fill color="#02000000"/>\n'
        '      </Rectangle>\n'
        '    </PartDraw>\n' % (x, y, w, h, target, w, h)
    )


# (x, y, w, h, launch target) - hit areas for the taps
TAP_TARGETS = [
    (196, 52, 90, 54, "com.samsung.android.watch.weather"),   # temperature
    (124, 160, 70, 56, "com.whatsapp"),                        # MSG -> WhatsApp
    (44, 206, 84, 52, "BATTERY_STATUS"),                       # battery
    (60, 272, 76, 52, "com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.heartrate.view.HeartRateActivity"),  # heart rate (screen with the "Medir" button)
    (146, 352, 190, 46, "com.samsung.android.calendar"),       # date
    (326, 228, 84, 52, "com.samsung.android.wear.shealth/com.samsung.android.wear.shealth.app.steps.view.StepsActivity"),  # steps
]


def tap_targets_block():
    return "".join(tap_target(i, *t) for i, t in enumerate(TAP_TARGETS))


def gauges_block():
    """Two real gauges drawn as arcs: battery (left) and step goal (upper left).

    Each value is driven by <Transform target="endAngle"> with an arithmetic
    expression, so the arcs actually measure something instead of decorating.
    """
    track_batt = "#33" + CYAN[3:]
    track_steps = "#33" + MAGENTA[3:]
    return (
        '    <!-- ===== gauges: battery (left) + step goal (upper left) ===== -->\n'
        '    <PartDraw x="0" y="0" width="%d" height="%d">\n'
        '      <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
        '      <Arc centerX="240" centerY="240" width="410" height="410" startAngle="246" endAngle="294">\n'
        '        <Stroke thickness="4" color="%s" cap="ROUND"/>\n'
        '      </Arc>\n'
        '      <Arc centerX="240" centerY="240" width="410" height="410" startAngle="246" endAngle="294">\n'
        '        <Stroke thickness="4" color="%s" cap="ROUND"/>\n'
        '        <Transform target="endAngle" value="246 + 0.48 * [BATTERY_PERCENT]"/>\n'
        '      </Arc>\n'
        '      <Arc centerX="240" centerY="240" width="410" height="410" startAngle="300" endAngle="340">\n'
        '        <Stroke thickness="4" color="%s" cap="ROUND"/>\n'
        '      </Arc>\n'
        '      <Arc centerX="240" centerY="240" width="410" height="410" startAngle="300" endAngle="340">\n'
        '        <Stroke thickness="4" color="%s" cap="ROUND"/>\n'
        '        <Transform target="endAngle" value="300 + 0.40 * [STEP_PERCENT]"/>\n'
        '      </Arc>\n'
        '    </PartDraw>\n'
        % (S, S, track_batt, CYAN, track_steps, MAGENTA)
    )


WEATHER_LABELS = [
    # (expression name, WEATHER.CONDITION values, label)
    ("c_clear", [1, 8], "DESPEJADO"),    ("c_cloudy", [2, 14], "NUBLADO"),
    ("c_rain", [4, 6, 12], "LLUVIA"),
    ("c_snow", [5, 7, 11], "NIEVE"),
    ("c_fog", [3, 13], "NIEBLA"),
    ("c_storm", [9], "TORMENTA"),
    ("c_sleet", [10], "AGUANIEVE"),
    ("c_windy", [15], "VIENTO"),
]


def weather_block():
    """Temperature + daily min/max, hidden behind WEATHER.IS_AVAILABLE.

    When the phone has not pushed weather data, the runtime reports 0 for
    [WEATHER.TEMPERATURE] and the face used to show "0° / 0°"; with the guard it
    shows a single dim dash instead.
    """
    return ('    <Condition>\n'
            '      <Expressions>\n'
            '        <Expression name="wx_ok"><![CDATA[[WEATHER.IS_AVAILABLE]]]></Expression>\n'
            '      </Expressions>\n'
            '      <Compare expression="wx_ok">\n'
            + text_part("temp", "%s\u00b0", ["[WEATHER.TEMPERATURE]"], CYAN,
                        indent="        ")
            + text_part("tminmax", "%s\u00b0 / %s\u00b0",
                        ["[WEATHER.DAY_TEMPERATURE_HIGH]",
                         "[WEATHER.DAY_TEMPERATURE_LOW]"], DIM, indent="        ")
            + '      </Compare>\n'
            '      <Default>\n'
            + text_part("temp", "\u2014", [], DIM, indent="        ")
            + '      </Default>\n'
            '    </Condition>\n')


def weather_condition_block():
    """Maps the integer WEATHER.CONDITION to a Spanish label with <Condition>.

    `<Condition>` is a legal child of `<Scene>` (WFF v2 schema) and picks the
    first matching <Compare>; <Default> covers UNKNOWN_VALUE (0).
    """
    lines = []
    for name, values, _label in WEATHER_LABELS:
        cond = " || ".join("[WEATHER.CONDITION] == %d" % v for v in values)
        lines.append('        <Expression name="%s"><![CDATA[%s]]></Expression>\n'
                     % (name, cond))
    exprs = "".join(lines)

    compares = []
    for name, _values, label in WEATHER_LABELS:
        body = text_part("cond", label, [], DIM, indent="        ")
        compares.append('      <Compare expression="%s">\n%s      </Compare>\n'
                        % (name, body))
    default = ('      <Default>\n%s      </Default>\n'
               % text_part("cond", "\u2014", [], DIM, indent="        "))

    return ('    <!-- ===== weather condition ===== -->\n'
            '    <Condition>\n'
            '      <Expressions>\n' + exprs + '      </Expressions>\n'
            + "".join(compares) + default + '    </Condition>\n')


def world_clock_block():
    """Barcelona clock as plain text.

    NOTE: the complication-slot variant (world_clock_slot_block, below) is NOT
    used. Tested on the watch: with DefaultProviderPolicy the system bound a
    provider that rendered a bare placeholder ("12:00p.m.") instead of the
    computed time and the city label was lost; without the policy the runtime
    crashed and the watch fell back to the factory face. See HANDOFF 4.13.
    """
    return (text_part("wl_lbl", WORLD_LABEL, [], DIM)
            + text_part("wclock", "%s", [world_clock_expression()], CYAN))


def world_clock_slot_block():
    """Experimento no usado: ranura de complicacion con reloj mundial."""
    x, y, w, h = WORLD_SLOT
    exp = esc_attr(world_clock_expression())
    return f'''    <ComplicationSlot x="{x}" y="{y}" width="{w}" height="{h}" slotId="{WORLD_SLOT_ID}"
        displayName="@string/slot_world" supportedTypes="SHORT_TEXT">
      <BoundingBox x="0" y="0" width="{w}" height="{h}"/>
      <Complication type="SHORT_TEXT">
        <Condition>
          <Expressions>
            <Expression name="text_only"><![CDATA[[COMPLICATION.TITLE] == null && [COMPLICATION.TEXT] != null]]></Expression>
            <Expression name="with_title"><![CDATA[[COMPLICATION.TITLE] != null]]></Expression>
          </Expressions>
          <Compare expression="text_only">
            <PartText x="0" y="0" width="{w}" height="{h}">
              <Text align="CENTER" ellipsis="TRUE">
                <Font family="{FAMILY}" size="20" color="{CYAN}" weight="BOLD">
                  <Template><![CDATA[%s]]>
                    <Parameter expression="[COMPLICATION.TEXT]"/>
                  </Template>
                </Font>
              </Text>
            </PartText>
          </Compare>
          <Compare expression="with_title">
            <PartText x="0" y="1" width="{w}" height="14">
              <Text align="CENTER" ellipsis="TRUE">
                <Font family="{FAMILY}" size="11" color="{DIM}" weight="BOLD">
                  <Template><![CDATA[%s]]>
                    <Parameter expression="[COMPLICATION.TITLE]"/>
                  </Template>
                </Font>
              </Text>
            </PartText>
            <PartText x="0" y="15" width="{w}" height="21">
              <Text align="CENTER" ellipsis="TRUE">
                <Font family="{FAMILY}" size="17" color="{CYAN}" weight="BOLD">
                  <Template><![CDATA[%s]]>
                    <Parameter expression="[COMPLICATION.TEXT]"/>
                  </Template>
                </Font>
              </Text>
            </PartText>
          </Compare>
          <Default>
            <PartText x="0" y="0" width="78" height="{h}">
              <Text align="END" ellipsis="FALSE">
                <Font family="{FAMILY}" size="13" color="{DIM}" weight="BOLD">
                  <Template><![CDATA[{WORLD_LABEL}]]></Template>
                </Font>
              </Text>
            </PartText>
            <PartText x="82" y="0" width="{w - 82}" height="{h}">
              <Text align="START" ellipsis="FALSE">
                <Font family="{FAMILY}" size="24" color="{CYAN}" weight="BOLD">
                  <Template><![CDATA[%s]]>
                    <Parameter expression="{exp}"/>
                  </Template>
                </Font>
              </Text>
            </PartText>
          </Default>
        </Condition>
      </Complication>
    </ComplicationSlot>
'''


def build_xml(fmt=2, with_events=True, with_weather=True, with_ambient=True, h12=True,
              with_conditions=True, with_gauges=True, with_taps=True):
    # Flat scene: every part is a direct child of <Scene>. A wrapping <Group>
    # is not used because on the Galaxy Watch 6 it silently suppressed the
    # render of its children.
    parts = []
    parts.append(text_part("sec", "%s", ["[SECOND_Z]"], CYAN))
    if h12:
        parts.append(text_part("time", "%s:%s", ["[HOUR_1_12]", "[MINUTE_Z]"], TIME))
        parts.append(text_part("ampm", "%s", ["[AMPM_STRING]"], CYAN))
    else:
        parts.append(text_part("time", "%s:%s", ["[HOUR_0_23_Z]", "[MINUTE_Z]"], TIME))
    parts.append(text_part("date", "%s %s %s",
                           ["[DAY_OF_WEEK_S]", "[DAY_Z]", "[MONTH_S]"], MAGENTA))

    if with_weather:
        # guarded by WEATHER.IS_AVAILABLE so a phone without weather data shows a
        # dash instead of "0° / 0°" (see weather_block below); NOTE:
        # WEATHER.CONDITION_NAME renders empty on this firmware, so the condition
        # label is derived from the integer WEATHER.CONDITION instead.
        parts.append(weather_block())

    parts.append(text_part("msg_v", "%s", ["clamp([UNREAD_NOTIFICATION_COUNT],0,99)"], MAGENTA))
    parts.append(text_part("bat_v", "%s%%", ["[BATTERY_PERCENT]"], CYAN))
    parts.append(text_part("hr_v", "%s", ["[HEART_RATE]"], MAGENTA))
    parts.append(text_part("steps_v", "%s", ["[STEP_COUNT]"], CYAN))
    parts.append(text_part("steps_pct", "%s%%", ["[STEP_PERCENT]"], DIM))

    # world clock under the date: complication slot (pick the city by tapping it
    # in the editor) with the computed Barcelona time as fallback
    parts.append(world_clock_block())

    hud = "".join(parts)
    labels = label_parts(load(os.path.join("labels", "labels.json")))
    ev = events_slot() if with_events else ""
    gauges = gauges_block() if with_gauges else ""
    taps = tap_targets_block() if with_taps else ""
    cond_block = weather_condition_block() if (with_weather and with_conditions) else ""

    # ---------- always-on (ambient) layer: dim grey, burn-in friendly ----------
    if with_ambient:
        ambient_parts = (
            text_part("time", "%s:%s",
                      ["[HOUR_1_12]" if h12 else "[HOUR_0_23_Z]", "[MINUTE_Z]"],
                      "#FFAEBCC6", box_h=72, mode="ambient")
            + text_part("date", "%s %s %s",
                        ["[DAY_OF_WEEK_S]", "[DAY_Z]", "[MONTH_S]"], "#FF7C8C98",
                        mode="ambient")
        )
        bg_layer = (
            '    <PartImage x="0" y="0" width="%d" height="%d">\n'
            '      <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
            '      <Image resource="bg"/>\n'
            '    </PartImage>\n'
            '    <PartImage x="0" y="0" width="%d" height="%d" alpha="0">\n'
            '      <Variant mode="AMBIENT" target="alpha" value="255"/>\n'
            '      <Image resource="bg_ambient"/>\n'
            '    </PartImage>\n' % (S, S, S, S)
        )
        clocks = (
            '    <AnalogClock x="0" y="0" width="%d" height="%d">\n'
            '      <Variant mode="AMBIENT" target="alpha" value="0"/>\n'
            '%s%s%s'
            '    </AnalogClock>\n'
            '    <AnalogClock x="0" y="0" width="%d" height="%d" alpha="0">\n'
            '      <Variant mode="AMBIENT" target="alpha" value="255"/>\n'
            '%s%s'
            '    </AnalogClock>\n' % (
                S, S,
                hand("HourHand", HANDS["hour"], "hand_hour"),
                hand("MinuteHand", HANDS["minute"], "hand_minute"),
                hand("SecondHand", HANDS["second"], "hand_second"),
                S, S,
                hand("HourHand", HANDS_AMB["hour"], "hand_hour_ambient"),
                hand("MinuteHand", HANDS_AMB["minute"], "hand_minute_ambient"),
            )
        )
        ambient_layer = f'''
    <!-- ===== always-on text ===== -->
{ambient_parts}'''
    else:
        bg_layer = (
            '    <PartImage x="0" y="0" width="%d" height="%d">\n'
            '      <Image resource="bg"/>\n'
            '    </PartImage>\n' % (S, S)
        )
        clocks = (
            '    <AnalogClock x="0" y="0" width="%d" height="%d">\n'
            '%s%s%s'
            '    </AnalogClock>\n' % (
                S, S,
                hand("HourHand", HANDS["hour"], "hand_hour"),
                hand("MinuteHand", HANDS["minute"], "hand_minute"),
                hand("SecondHand", HANDS["second"], "hand_second"),
            )
        )
        ambient_layer = ""

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- Neon Grid - cyberpunk watch face for Galaxy Watch 6 (480x480)
     Watch Face Format v{fmt}. Generated by tools/gen_watchface.py -->
<WatchFace width="{S}" height="{S}">
  <Metadata key="CLOCK_TYPE" value="ANALOG"/>
  <Metadata key="PREVIEW_TIME" value="22:47:05"/>
  <Scene backgroundColor="#FF05080E">

    <!-- ===== background (interactive + always-on) ===== -->
{bg_layer}{gauges}
    <!-- ===== hands ===== -->
{clocks}
    <!-- ===== HUD labels (baked art) ===== -->
{labels}
    <!-- ===== HUD data ===== -->
{hud}
{ev}{cond_block}{ambient_layer}{taps}
  </Scene>
</WatchFace>
'''
    return xml



MANIFEST = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{package}">

  <uses-feature android:name="android.hardware.type.watch" />

  <application
      android:label="@string/watch_face_name"
      android:hasCode="false">

    <meta-data
        android:name="com.google.android.wearable.standalone"
        android:value="true" />

    <property
        android:name="com.google.wear.watchface.format.version"
        android:value="{fmt}" />

    <property
        android:name="com.google.wear.watchface.format.publisher"
        android:value="neongrid-1.0" />
  </application>
</manifest>
'''

WATCH_FACE_INFO = '''<?xml version="1.0" encoding="utf-8"?>
<WatchFaceInfo>
  <Preview value="@drawable/preview" />
  <Category value="CATEGORY_EMPTY" />
  <AvailableInRetail value="false" />
  <MultipleInstancesAllowed value="true" />
  <Editable value="true" />
</WatchFaceInfo>
'''

STRINGS = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
  <string name="watch_face_name">{label}</string>
  <string name="slot_events">{slot_events}</string>
  <string name="slot_world">{slot_world}</string>
</resources>
'''


def copy_assets(suffix=""):
    """Copies the palette-specific art from design/out into the WFF resources."""
    pairs = [
        ("bg%s.png" % suffix, "bg.png"),
        ("bg_ambient%s.png" % suffix, "bg_ambient.png"),
        ("hand_hour%s.png" % suffix, "hand_hour.png"),
        ("hand_minute%s.png" % suffix, "hand_minute.png"),
        ("hand_second%s.png" % suffix, "hand_second.png"),
        ("hand_hour_ambient%s.png" % suffix, "hand_hour_ambient.png"),
        ("hand_minute_ambient%s.png" % suffix, "hand_minute_ambient.png"),
    ]
    for src_name, dst_name in pairs:
        src = os.path.join(OUT, src_name)
        if not os.path.exists(src):
            raise SystemExit("missing asset: " + src)
        shutil.copyfile(src, os.path.join(DRAW, dst_name))
    # labels are palette independent
    lab = os.path.join(OUT, "labels")
    for f in os.listdir(lab):
        if f.endswith(".png"):
            shutil.copyfile(os.path.join(lab, f), os.path.join(DRAW, f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", type=int, default=2, choices=[1, 2])
    ap.add_argument("--no-events", action="store_true")
    ap.add_argument("--no-weather", action="store_true")
    ap.add_argument("--no-ambient", action="store_true")
    ap.add_argument("--no-conditions", action="store_true")
    ap.add_argument("--no-gauges", action="store_true")
    ap.add_argument("--no-taps", action="store_true")
    ap.add_argument("--h24", action="store_true", help="24-hour clock instead of 12-hour")
    ap.add_argument("--palette", default="neon", help="palette suffix written by render.py")
    ap.add_argument("--package", default="com.relog.neongrid")
    ap.add_argument("--label", default="Neon Grid")
    ap.add_argument("--slot-events", default="Eventos")
    ap.add_argument("--slot-world", default="Hora mundial")
    ap.add_argument("--device-utc-offset", type=float, default=-5.0,
                    help="UTC offset of the watch, in hours (Bogota = -5); the "
                         "world clock shift is Spain minus this")
    args = ap.parse_args()

    sfx = "" if args.palette == "neon" else "-" + args.palette
    global HANDS, HANDS_AMB
    HANDS = load("hands%s.json" % sfx)
    HANDS_AMB = load("hands_ambient%s.json" % sfx)

    fmt = args.format
    global DEVICE_UTC_OFFSET
    DEVICE_UTC_OFFSET = args.device_utc_offset
    global LS_ENABLED, CYAN, MAGENTA, VIOLET, DIM
    LS_ENABLED = fmt >= 2
    with_weather = (fmt >= 2) and not args.no_weather
    h12 = not args.h24

    # palette written by design/render.py --palette
    pal_path = os.path.join(OUT, "palette%s.json" % sfx)
    if os.path.exists(pal_path):
        with open(pal_path, encoding="utf-8") as fh:
            pal = json.load(fh)
        global TIME
        CYAN, MAGENTA = pal["cyan"], pal["magenta"]
        VIOLET, DIM = pal["violet"], pal["dim"]
        TIME = pal.get("time", "#FFFFFFFF")

    xml = build_xml(fmt=fmt, with_events=not args.no_events,
                    with_weather=with_weather, h12=h12,
                    with_conditions=not args.no_conditions,
                    with_gauges=not args.no_gauges,
                    with_taps=not args.no_taps)

    for d in ("raw", "xml", "values"):
        os.makedirs(os.path.join(RES, d), exist_ok=True)

    with open(os.path.join(RES, "raw", "watchface.xml"), "w", encoding="utf-8") as fh:
        fh.write(xml)
    with open(os.path.join(WF, "AndroidManifest.xml"), "w", encoding="utf-8") as fh:
        fh.write(MANIFEST.format(fmt=fmt, package=args.package,
                                 label=args.label))
    with open(os.path.join(RES, "xml", "watch_face_info.xml"), "w", encoding="utf-8") as fh:
        fh.write(WATCH_FACE_INFO)
    with open(os.path.join(RES, "values", "strings.xml"), "w", encoding="utf-8") as fh:
        fh.write(STRINGS.format(label=args.label, slot_events=args.slot_events,
                                slot_world=args.slot_world))

    # preview for the picker: prefer the real device render over the mock
    dev = os.path.join(OUT, "device-render" + sfx + ".png")
    src = dev if os.path.exists(dev) else os.path.join(OUT, "preview_full%s.png" % sfx)
    shutil.copyfile(src, os.path.join(DRAW, "preview.png"))

    copy_assets(sfx)
    print(f"generated watchface.xml (format v{fmt}, h12={h12}, events={not args.no_events}, "
          f"weather={with_weather}, package={args.package}, label={args.label})")
    print("  ", os.path.join(RES, "raw", "watchface.xml"))


if __name__ == "__main__":
    main()
