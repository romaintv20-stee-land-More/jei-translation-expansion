package net.minecraftforge.fml.common;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/** Compile-only subset of Forge 1.8's @Mod annotation. Never packaged. */
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
