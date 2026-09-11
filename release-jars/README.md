# Release JAR archive

This directory is the repository-side archive for finalized JEI Translation Expansion JARs.

Project policy:

- one Minecraft version per release JAR;
- never package several Minecraft versions into one artifact;
- loader-specific JARs may exist for the same Minecraft version when technically required;
- every archived JAR must have been rebuilt reproducibly from the checked-in translation/version data and must pass the relevant validation before being committed here.

Planned layout:

```text
release-jars/
  1.8/
    jei-translation-expansion-<project-version>-mc1.8-forge.jar
  1.8.9/
    jei-translation-expansion-<project-version>-mc1.8.9-forge.jar
  ...
```

When a Minecraft version has more than one required loader artifact, keep all artifacts for that Minecraft version in the same version folder and include the loader in the filename.

These repository copies are intended to make already-built JARs easy to retrieve later. GitHub Releases may additionally be used for public downloads, but the repository archive remains the project-side canonical location for retained final JAR files.

Do not place draft, unvalidated or temporary build outputs here.
