package com.rinkynooble.lostcitiesdevtool.diagnostics;

/**
 * Carries the caught exception the few instructions from where it is printed to
 * where the chunk is described.
 *
 * <p>{@code LostCityFeature}'s catch block calls {@code printStackTrace} on the
 * exception and then calls {@code ErrorLogger.logChunkInfo}, which does not receive
 * it. Both calls are redirected, so the first stores the exception and the second
 * takes it.
 *
 * <p>Thread local because chunks generate on worker threads, several at once.
 */
public final class LastFault {

    private static final ThreadLocal<Throwable> CURRENT = new ThreadLocal<>();

    private LastFault() {
    }

    public static void set(Throwable fault) {
        CURRENT.set(fault);
    }

    /** Reads and clears, so a later report can never quote a stale fault. */
    public static Throwable take() {
        Throwable fault = CURRENT.get();
        CURRENT.remove();
        return fault;
    }
}
