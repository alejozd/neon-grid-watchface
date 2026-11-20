# Offline WFF validators — what actually exists

Sources fetched:
- <https://github.com/google/watchface> (README)
- <https://raw.githubusercontent.com/google/watchface/main/third_party/wff/README.md>
- <https://raw.githubusercontent.com/google/watchface/main/third_party/wff/specification/validator/build.gradle>
- <https://raw.githubusercontent.com/google/watchface/main/README.md>
- <https://developer.android.com/training/wearables/wff/setup> ("Check your watch face correctness and performance")

## 1. Official XSD validator — Java, not Python

From `third_party/wff/README.md`, verbatim:

> ## Format validator
> In addition to the XSD files, a validator is provided that can be used to check
> specific watch face XML files.
>
> ### Building the validator
> ```shell
> cd third_party/wff
> ./gradlew :specification:validator:executable-jar
> ```
> The resulting JAR file can then be found at: `specification/validator/build/libs/wff-validator.jar`
>
> ### Usage
> To check whether a watch face is valid, invoke the validator as follows:
> ```shell
> java -jar wff-validator.jar <format-version> <any options> <your-watchface.xml> <more-watchface.xml>
> ```
> For example:
> ```shell
> java -jar wff-validator.jar 5 ~/MyWatchface/res/raw/watchface.xml
> ```

### Exact identity

| Item | Value |
|---|---|
| Artifact name | `wff-validator.jar` (Gradle project `:specification:validator`, `executable-jar` task) |
| Main class | `com.samsung.watchface.DWFValidationApplication` |
| Maven coordinates (published) | group/version as published by `maven-publish`, `artifactId 'wff-validator'` |
| Java version required | `sourceCompatibility = JavaVersion.VERSION_17`, `targetCompatibility = JavaVersion.VERSION_17` |
| Build system | Gradle (`third_party/wff/settings.gradle`, `gradlew`) |

Runtime dependencies (from `build.gradle`, verbatim):

```groovy
dependencies {
    implementation 'xml-apis:xml-apis:1.4.01'
    implementation 'org.exist-db.thirdparty.xerces:xercesImpl:2.12.0:xml-schema-1.1'
    implementation 'com.rackspace.eclipse.webtools.sourceediting:org.eclipse.wst.xml.xpath2.processor:2.1.100'
    implementation 'edu.princeton.cup:java-cup:10k'
}
```

Notes:
- The XSDs are **bundled into the JAR** as `docs.zip` (`tasks.register("bundleDocs", Zip) { from '../documents/' ... }` and `jar { from ('build/libs') { include 'docs.zip' } }`). So the JAR is self-contained — no network needed at validation time, and no separate schema checkout.
- It uses **Xerces `xml-schema-1.1`**, i.e. it is an XSD 1.1 engine plus an XPath2 processor. Both artifact coordinates are on Maven Central, so building once requires network; running does not.
- The version argument supports at least `1`..`5` per the example (`java -jar wff-validator.jar 5 ...`), even though the repo only publishes XSD trees for versions 1 and 2 (see `XSD_INDEX.md`).

**Bottom line: there is no Python-based official validator, and no `watchface` PyPI package is referenced anywhere in the docs or the repo.** Anything claiming to be one is unofficial.

## 2. Can it run with only Python + lxml (no network)?

**Partly — but not out of the box.**

There is no pip package. However, because the spec is pure XSD, you *can* validate offline with Python if you have the schema tree on disk:

```python
from lxml import etree
schema = etree.XMLSchema(etree.parse("xsd/1/watchface.xsd"))
schema.assertValid(etree.parse("res/raw/watchface.xml"))
```

Caveats, all verified against the fetched XSDs:

1. **You need the whole tree, not one file.** `watchface.xsd` only `xs:include`s four files, which transitively include ~159 XSD files (`XSD_INDEX.md` lists every path). Getting them requires `git clone` of `google/watchface` — i.e. network, once.
2. **lxml/libxml2 is an XSD 1.0 engine.** The official tool bundles Xerces `xml-schema-1.1`. Spot-checking the files that decide this: `watchface.xsd`, `sceneElement.xsd`, `metadataElement.xsd`, `complicationElement.xsd`, `complicationSlotElement.xsd`, `fontElement.xsd`, `secondHand.xsd`, `timeText.xsd` (v1 and v2) and `common/attributes/geometricAttributes.xsd` use only XSD 1.0 constructs (`xs:all`, `xs:unique`, `xs:include`, `xs:group`, `xs:attributeGroup`, `xs:list`, `xs:union`, `xs:pattern`, `xs:enumeration`, `xs:restriction`) — **no `xs:assert`, `xs:alternative` or `xs:override` was observed in those files**. So lxml should load the v1 schema root. This was **not** exhaustively checked across all 159 files; if lxml fails to compile the schema, that is the first thing to blame.
3. **Attribute-level expression syntax is only loosely constrained.** Geometry attributes are typed via `dimensionType` (a union that also admits an arithmetic-expression string), so an XSD-valid file can still contain a semantically invalid expression. The XSD will not catch bad `[DATA_SOURCE]` names. Only the runtime / Android Studio linter does that.

Practical recommendation for a no-network, Python-only environment: **use the XSDs saved in `research/xsd/` only as a structural reference, and validate the hand-written XML by careful conformance to the element/attribute lists in `NOTES.md`.** If you do manage to get the full tree onto disk, `lxml` + `xsd/1/watchface.xsd` is the cheapest offline check.

## 3. Other validation tooling in the repo

From `google/watchface` README:

| Tool | Path | What it does |
|---|---|---|
| XSD specification | `third_party/wff/specification/documents/1/` and `/2/` | The schema itself |
| XSD validator | `third_party/wff/specification/validator/` | Java JAR described above |
| Memory footprint evaluator | `play-validations/` (`memory-footprint/`) | Play-submission memory limits (10 MB ambient / 100 MB interactive) |
| WFF optimizer | `tools/wff-optimizer/` | Rewrites XML/resources to lower runtime memory |

Android Studio also ships a **version-aware** WFF linter — from the setup guide, verbatim:

> "During development, and before uploading to Google Play, check that your watch face is free from syntax errors by using the in-built Watch Face Format validation in Android Studio. This automatically highlights errors in your code and is version-aware."

## 4. Runtime debugging (docs, verbatim)

From the samples README:

```shell
adb logcat --pid=$(adb shell pidof -s com.google.wear.watchface.runtime)
```

> "Use `logcat` to look for any error messages from the WFF runtime, such as potential errors in WFF expressions."

This is the fastest way to find out why a hand-written face is silently ignored: the runtime process logs parse/expression failures there.
