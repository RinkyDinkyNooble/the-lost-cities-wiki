import com.rinkynooble.lostcitiesdevtool.core.ProfileOrder;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;

/**
 * The order the Cities screen cycles profiles in, exercised in a plain JVM.
 *
 * <p>Run by {@code check-profile-order.py}. The screen itself needs a client, which
 * the rig does not have, so what is proved here is the ordering and the inverse,
 * and the wiring is checked by reading the sources.
 */
public class ProfileOrderProbe {

    private static int failed;

    public static void main(String[] args) {
        // `default` pinned first, then code point order: a digit sorts before an
        // uppercase letter and an uppercase letter before a lowercase one.
        expect("sorted, default pinned, code point order",
                List.of("default", "2x", "Zed", "alpha", "beta"),
                ProfileOrder.sorted(List.of("beta", "Zed", "default", "alpha", "2x")));

        List<String> cycle = List.of("default", "a", "b");
        expect("back from disabled reaches the last", "b",
                ProfileOrder.previous(cycle, null));
        expect("back from the first reaches disabled", null,
                ProfileOrder.previous(cycle, "default"));
        expect("back from the middle", "a", ProfileOrder.previous(cycle, "b"));
        expect("an unknown name lands on disabled", null,
                ProfileOrder.previous(cycle, "nosuch"));
        expect("an empty list stays disabled", null,
                ProfileOrder.previous(List.of(), "x"));

        // customize appends to the live list. Stepping back from it reaches the
        // last real profile, which a list rebuilt from the profiles cannot do.
        expect("back from the entry customize appended", "b",
                ProfileOrder.previous(List.of("default", "a", "b", "customized"),
                        "customized"));

        // The inverse of the forward cycle, over the whole of it: null, each
        // entry in turn, and back to null.
        List<String> states = new ArrayList<>(Arrays.asList((String) null));
        states.addAll(List.of("default", "Mid", "low", "z9"));
        List<String> list = states.subList(1, states.size());
        for (int i = 0; i < states.size(); i++) {
            String next = states.get((i + 1) % states.size());
            expect("back from " + next + " undoes forward from " + states.get(i),
                    states.get(i), ProfileOrder.previous(list, next));
        }

        System.out.println(failed == 0 ? "all probe cases passed"
                : failed + " probe case(s) failed");
        System.exit(failed == 0 ? 0 : 1);
    }

    private static void expect(String name, Object want, Object got) {
        boolean ok = Objects.equals(want, got);
        System.out.printf("  %-6s %-52s %s%n", ok ? "ok" : "FAIL", name,
                ok ? String.valueOf(got) : "wanted " + want + ", got " + got);
        if (!ok) {
            failed++;
        }
    }
}
