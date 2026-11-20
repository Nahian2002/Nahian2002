# Engineering Portfolio — Repository Index

**Owner:** [Nahian2002](https://github.com/Nahian2002)  
**Reviewed:** 2026-11-10 (portfolio scope and qualitative tiers)  
**Navigation checked:** 2026-11-20 (public project entry points)  
**Scope:** Public repositories only. Private repositories are deliberately excluded from this public index.

This is an **architecture and maintenance index**, not a leaderboard. Complexity reflects the code and workflows visible in each repository, *not* project ambition, personal skill, popularity, or business value.

## Public repositories, sorted by engineering complexity

| Tier | Repository | Engineering scope | Recommended position |
| --- | --- | --- | --- |
| **5/5 — Advanced** | [NightWave](https://github.com/Nahian2002/NightWave) | Kotlin Android app with Jetpack Compose, Media3, release guidance and tests | **Flagship product**; keep independent |
| **3/5 — Intermediate** | [Fitness Tracker — CSE215L](https://github.com/Nahian2002/Fitness-Tracker---CSE215L) | Multi-class Java application with GUI panels, services, authentication and persistence | **Academic application**; keep independent |
| **3/5 — Intermediate** | [Automated Reminder](https://github.com/Nahian2002/Automated-Reminder) | Java Swing reminder application, persisted state, smoke tests and GitHub Actions | **Standalone utility**; keep independent |
| **2/5 — Foundational project** | [Git 115 Group 08](https://github.com/Nahian2002/Git_115_Grp08) | C diary-management program and accompanying academic reports | Group in **Foundations & Coursework**; retain history |
| **2/5 — Foundational project** | [CSE 115L Project](https://github.com/Nahian2002/CSE-115L-Project) | Standalone C employee-management program | Group in **Foundations & Coursework**; retain history |
| **1/5 — Learning exercises** | [Learning C](https://github.com/Nahian2002/Learning-C) | C programming exercises organized by concepts | Group in **Foundations & Coursework** |
| **1/5 — Learning exercises** | [Learning Java](https://github.com/Nahian2002/Learning-JAVA) | Small independent Java programming exercises | Group in **Foundations & Coursework** |

The [Nahian2002 profile repository](https://github.com/Nahian2002/Nahian2002) owns the showcase and portfolio index. As a presentation repository, it is **not ranked** against applications.

## Project entry-point notes

- **NightWave:** Start with the [project overview](https://github.com/Nahian2002/NightWave/blob/main/README.md), [build and release guide](https://github.com/Nahian2002/NightWave/blob/main/docs/BUILD_AND_RELEASE.md), or [contributing guide](https://github.com/Nahian2002/NightWave/blob/main/CONTRIBUTING.md). The latest public release is [NightWave 55.7 (Android build 66)](https://github.com/Nahian2002/NightWave/releases/tag/nightwave-v55.7), and its matching source is the [nightwave-v55.7 source tag](https://github.com/Nahian2002/NightWave/tree/nightwave-v55.7). The default `main` branch is ongoing development with a separate alpha version/build configuration; it is **not** the source for public 55.7. Check out the release tag to reproduce 55.7, and do not treat a `main` build as a direct upgrade to that release.
- **Automated Reminder:** Its [README and run guide](https://github.com/Nahian2002/Automated-Reminder/blob/main/README.md) lists JDK requirements and compile/run commands. It also clarifies that the app displays backup reminders but does **not** copy or back up files itself.
- **Fitness Tracker:** The Java source files are grouped under `project/`; start at the [Java source directory](https://github.com/Nahian2002/Fitness-Tracker---CSE215L/tree/main/project).

## Portfolio structure

### 01 / Flagship engineering

- **NightWave:** an independent product with its own platform, releases, maintenance and roadmap.

### 02 / Standalone applications

- **Fitness Tracker:** multi-component academic desktop app.
- **Automated Reminder:** focused desktop utility with repeatable checks.

### 03 / Foundations & coursework

- **Git 115 Group 08:** personal diary coursework.
- **CSE 115L Project:** employee management coursework.
- **Learning C:** concept-based exercises.
- **Learning Java:** concept-based exercises.

These four repositories are **logically grouped** for navigation, not physically merged. Their original Git histories, URLs, authorship, coursework provenance and collaboration context stay intact.

## Consolidation policy

A repository should be physically merged only when it shares a genuine product lifecycle or reusable codebase with its destination. **Do not combine unrelated applications solely to reduce the number of repositories.**

- **Keep independent:** NightWave, Automated Reminder, Fitness Tracker, and the profile repository.
- **Optional future consolidation:** Foundations & Coursework could become a dedicated learning monorepo, **after** verifying full history, existing links, all branches, binary reports, licenses, and collaborators. Keep source repositories accessible or archived as appropriate; do not delete them automatically.
- **Never mix private and public source:** visibility and secrets need a separate review before any move.
- **Preserve credit:** use history-preserving migration methods when a real consolidation is approved. Copying current files alone is *not* a historical merge.

## Assessment method and limitations

The tiers above are qualitative. They consider modules and source structure, runtime integration, build and test systems, and product maintenance surface. They are based on repository contents inspected on 2026-11-10; they do not imply that every program was executed or that all runtime features are validated.

**Private work is intentionally not inventoried here.** An internal audit may include those projects, but this public file must never expose private repository contents, access paths, local runtime state, credentials, or unreleased plans.

---

[Return to the profile](https://github.com/Nahian2002) · [Explore public repositories](https://github.com/Nahian2002?tab=repositories)
