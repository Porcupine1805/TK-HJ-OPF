package org.tkhjopf.app;

import org.tkhjopf.io.TimeSeriesIO;
import org.tkhjopf.miner.MiningResult;
import java.nio.file.Path;
import java.util.Locale;

/**
 * One dataset, one mode, one JVM. Warmups then measured runs.
 * Prints CSV rows to stdout; metrics summary to stderr.
 */
public final class OneShot {
    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: OneShot input.txt mode [warm] [rep] [K] [maxLen]");
            System.exit(2);
        }
        Path input = Path.of(args[0]);
        String mode = args[1];
        int warm = args.length > 2 ? Integer.parseInt(args[2]) : 5;
        int rep = args.length > 3 ? Integer.parseInt(args[3]) : 10;
        int K = args.length > 4 ? Integer.parseInt(args[4]) : 50;
        int maxLen = args.length > 5 ? Integer.parseInt(args[5]) : 12;
        double[] t = TimeSeriesIO.read(input);
        double k = 1.0 / t.length;
        String name = input.getFileName().toString();
        System.out.println("phase,dataset,n,mode,k,topk,minlen,maxlen,rep,runtime_ms,patterns,pair_attempts,compatible_pairs,pdub_prunes,dub_prunes,aligned_checks,peak_heap_mb");
        for (int r = -warm; r < rep; r++) {
            MiningResult x = CampaignRunner.run(mode, t, k, K, 2, maxLen);
            if (r < 0) continue;
            var z = x.metrics();
            System.out.printf(Locale.ROOT, "%s,%s,%d,%s,%.17g,%d,%d,%d,%d,%.6f,%d,%d,%d,%d,%d,%d,%.3f%n",
                    "oneshot", name, t.length, mode, k, K, 2, maxLen, r,
                    z.runtimeNanos / 1e6, x.patterns().size(), z.pairAttempts, z.compatiblePairs,
                    z.pairDescendantPrunes, z.branchBoundPrunes, z.alignedOccurrenceChecks,
                    z.approxPeakHeapBytes / 1048576.0);
        }
    }
}
