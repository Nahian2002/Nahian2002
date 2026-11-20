# Engineering Portfolio — Repository Index

**Owner:** [Nahian2002](https://github.com/Nahian2002)  
**Reviewed:** 2026-11-10 (portfolio scope and qualitative tiers)  
**Navigation checked:** 2026-11-20 (public project entry points)  
**Scope:** Public repositories only. Private repositories are deliberately excluded from this public index.

This is an **architecture and maintenance index**, not a leaderboard. Complexity reflects the code and workflows visible in each repository, *not* project ambition, personal skill, popularity, or business value.

## Public repositories, sorted by engineering complexity

| Tier | Repository | Engineering scope | Start here | Recommended position |
| --- | --- | --- | --- | --- |
| **5/5 — Advanced** | [NightWave](https://github.com/Nahian2002/NightWave) | Kotlin Android app with Jetpack Compose, Media3, release guidance and tests | [Overview](https://github.com/Nahian2002/NightWave/blob/main/README.md) · [Build & release](https://github.com/Nahian2002/NightWave/blob/main/docs/BUILD_AND_RELEASE.md) · [Contributing](https://github.com/Nahian2002/NightWave/blob/main/CONTRIBUTING.md) | **Flagship product**; keep independent |
| **3/5 — Intermediate** | [Fitness Tracker — CSE215L](https://github.com/Nahian2002/Fitness-Tracker---CSE215L) | Multi-class Java application with GUI panels, services, authentication and persistence | [Java source directory](https://github.com/Nahian2002/Fitness-Tracker---CSE215L/tree/main/project) | **Academic application**; keep independent |
| **3/5 — Intermediate** | [Automated Reminder](https://github.com/Nahian2002/Automated-Reminder) | Java Swing reminder application, persisted state, smoke tests and GitHub Actions | [README and run guide](https://github.com/Nahian2002/Automated-Reminder/blob/main/README.md) | **Standalone utility**; keep independent |
| **2/5 — Foundational project** | [Git 115 Group 08](https://github.com/Nahian2002/Git_115_Grp08) | C diary-management program and accompanying academic reports | — | Group in **Foundations & Coursework**; retain history |
| **2/5 — Foundational project** | [CSE 115L Project](https://github.com/Nahian2002/CSE-115L-Project) | Standalone C employee-management program | — | Group in **Foundations & Coursework**; retain history |
| **1/5 — Learning exercises** | [Learning C](https://github.com/Nahian2002/Learning-C) | C programming exercises organized by concepts | — | Group in **Foundations & Coursework** |
| **1/5 — Learning exercises** | [Learning Java](https://github.com/Nahian2002/Learning-JAVA) | Small independent Java programming exercises | — | Group in **Foundations & Coursework** |

The linked project names remain the starting points for the coursework archive; an em dash means this index does not add a separate guide for that entry.

The [Nahian2002 profile repository](https://github.com/Nahian2002/Nahian2002) owns the showcase and portfolio index. As a presentation repository, it is **not ranked** against applications.

## Project entry-point notes

- **NightWave:** The public 55.7 release corresponds to the `nightwave-v55.7` source tag. The repository's `main` branch is a separate development configuration, so use the matching tag when reproducing the public release. The build guide covers the release workflow; the contributing guide covers the project-specific contribution expectations.
- **Automated Reminder:** Its README contains JDK requirements and compile/run commands. It also clarifies that the app displays backup reminders but does **not** copy or back up files itself.
- **Fitness Tracker:** The Java source files are grouped under `project/`; the linked directory is the most direct code entry point.

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
