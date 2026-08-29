package com.rinkynooble.lostcitiesdevtool.validate;

import java.util.List;

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

    /**
     * Why a list of findings counts as a failure, in the caller's words.
     *
     * <p>Here rather than at the call site because the answer is about severity, and
     * severity is this record's business. It also makes the question checkable
     * without a server, which the call site was not.
     *
     * <p><b>The first ERROR, not the first finding.</b> A list carries warnings and
     * errors in the order they were discovered, so the first entry is only the cause
     * when nothing warned earlier. The wipe backup reported the first entry, which
     * meant a warning ahead of the error was named as the reason a backup failed,
     * immediately before the wipe it was protecting.
     */
    public static String firstError(List<Finding> findings,
                                    String noneFound) {
        if (findings == null) {
            return noneFound;
        }
        for (Finding f : findings) {
            if (f.severity() == Severity.ERROR) {
                return f.message();
            }
        }
        return noneFound;
    }
}
