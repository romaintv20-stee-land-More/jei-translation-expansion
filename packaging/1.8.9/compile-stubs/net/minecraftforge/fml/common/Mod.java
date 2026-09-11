package net.minecraftforge.fml.common;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Compile-only subset of Forge 1.8.9's @Mod annotation.
 *
 * This class is NEVER packaged in the addon JAR. It only lets javac encode the
 * runtime-visible annotation on the tiny client-only entrypoint without relying
 * on old ForgeGradle repositories during CI. The member names/types used here
 * match FML's public Mod annotation for the fields used by this project.
 */
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Mod {
    String modid();
    String name() default "";
    String version() default "";
    String dependencies() default "";
    boolean clientSideOnly() default false;
    String acceptedMinecraftVersions() default "";
    String acceptableRemoteVersions() default "";
}
