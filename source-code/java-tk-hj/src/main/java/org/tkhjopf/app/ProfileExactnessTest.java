package org.tkhjopf.app;

import org.tkhjopf.core.*;
import org.tkhjopf.miner.*;
import org.tkhjopf.model.PatternData;
import java.util.*;

/**
 * Numeric identity of naive breakpoint PDUB versus depth-UB profiles,
 * plus search-tree identity (prune/alignment counters) on the running example.
 */
public final class ProfileExactnessTest {
    public static void main(String[] args) {
        double[] t = {15, 32, 29, 27, 34, 33, 25, 20, 28, 23};
        double k = 0.1;
        double[] w = Forgetting.weights(t.length, k);
        int n = t.length;
        List<PatternData> seeds = SeedFactory.length2(t, w);
        int mismatches = 0, compared = 0;
        for (int D = 0; D <= 8; D++) {
            for (PatternData p : seeds) for (PatternData q : seeds) {
                if (!p.suffix.equals(q.prefix)) continue;
                double naive = Bounds.pairDescendantUpperBound(p, q, n, k, w, D, false);
                double prof = Bounds.pairDescendantUpperBound(p, q, n, k, w, D, true);
                compared++;
                if (Math.abs(naive - prof) > 1e-12) {
                    mismatches++;
                    System.err.println("PDUB mismatch D=" + D + " naive=" + naive + " profile=" + prof
                            + " p=" + p.pattern + " q=" + q.pattern);
                }
                double dubN = Bounds.descendantUpperBound(p, n, k, w, D, false);
                double dubP = Bounds.descendantUpperBound(p, n, k, w, D, true);
                if (Math.abs(dubN - dubP) > 1e-12) {
                    mismatches++;
                    System.err.println("DUB mismatch D=" + D + " naive=" + dubN + " profile=" + dubP);
                }
            }
        }
        if (mismatches > 0) throw new AssertionError("numeric mismatches=" + mismatches + "/" + compared);

        MiningResult a = new TKHJOPFMiner().mine(t, k, 5, 2, 10, true, true, true);
        MiningResult b = new TKHJOPFMiner().mine(t, k, 5, 2, 10, true, true, false);
        MiningResult bf = new BruteForceMiner().topK(t, k, 5, 2, 10);
        if (a.patterns().size() != b.patterns().size() || a.patterns().size() != bf.patterns().size())
            throw new AssertionError("size");
        for (int i = 0; i < a.patterns().size(); i++) {
            if (!a.patterns().get(i).pattern().equals(b.patterns().get(i).pattern()))
                throw new AssertionError("pattern rank " + i);
            if (Math.abs(a.patterns().get(i).support() - b.patterns().get(i).support()) > 1e-12)
                throw new AssertionError("support rank " + i);
        }
        if (a.metrics().pairDescendantPrunes != b.metrics().pairDescendantPrunes
                || a.metrics().alignedOccurrenceChecks != b.metrics().alignedOccurrenceChecks
                || a.metrics().branchBoundPrunes != b.metrics().branchBoundPrunes)
            throw new AssertionError("search-tree counters differ: profile "
                    + a.metrics().summary() + " naive " + b.metrics().summary());
        System.out.println("PROFILE EXACTNESS PASSED: " + compared
                + " PDUB/DUB numeric identities; running-example counters identical.");
    }
}
