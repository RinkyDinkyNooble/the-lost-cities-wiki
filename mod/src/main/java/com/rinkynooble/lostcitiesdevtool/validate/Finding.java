package com.rinkynooble.lostcitiesdevtool.validate;

/**
 * One problem in one file.
 *
 * <p>Carries a line number because a load-time check still has the source text. A
 * fault found during generation cannot: by then only the parsed object survives, and
 * the file and offset are gone.
 */
public record Finding(String file, int line, Severity severity, String message,
                      String fix) {

    public enum Severity {
        /** Generation will fail, or the value will be read as something else. */
        ERROR,
        /** Loads and runs, but does not do what it appears to. */
        WARN
    }

    public static Finding error(String file, int line, String message, String fix) {
        return new Finding(file, line, Severity.ERROR, message, fix);
    }

    public static Finding warn(String file, int line, String message, String fix) {
        return new Finding(file, line, Severity.WARN, message, fix);
    }

    /** {@code path/file.json:12} is the shape an editor jumps to. */
    public String location() {
        return line > 0 ? file + ":" + line : file;
    }
}
